import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

// ─── CONSTANTES ───────────────────────────────────────────────────────────────
const VALID_PLANS  = new Set(["essencial", "pro"]);
const VALID_CYCLES = new Set(["mensal", "semestral", "anual"]);
const VALID_DAYS   = new Map([["mensal", 30], ["semestral", 180], ["anual", 365]]);

// ─── HMAC — verifica que o POST veio realmente do Mercado Pago ────────────────
async function verifyMPSignature(req: Request, rawBody: string): Promise<boolean> {
  const secret = Deno.env.get("MP_WEBHOOK_SECRET");
  if (!secret) {
    console.error("[SECURITY] MP_WEBHOOK_SECRET não configurado — rejeitando webhook");
    return false;
  }

  const xSignature = req.headers.get("x-signature");
  const xRequestId = req.headers.get("x-request-id");
  const dataId     = new URL(req.url).searchParams.get("data.id");

  if (!xSignature || !xRequestId) {
    console.error("[SECURITY] Headers de assinatura ausentes");
    return false;
  }

  const parts: Record<string, string> = {};
  for (const part of xSignature.split(",")) {
    const [k, v] = part.split("=");
    if (k && v) parts[k.trim()] = v.trim();
  }

  if (!parts.ts || !parts.v1) {
    console.error("[SECURITY] Formato de x-signature inválido");
    return false;
  }

  const signedTemplate = `id:${dataId};request-id:${xRequestId};ts:${parts.ts};`;

  const encoder  = new TextEncoder();
  const cryptoKey = await crypto.subtle.importKey(
    "raw", encoder.encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]
  );

  const signatureBuffer = await crypto.subtle.sign("HMAC", cryptoKey, encoder.encode(signedTemplate));
  const computed = Array.from(new Uint8Array(signatureBuffer))
    .map(b => b.toString(16).padStart(2, "0"))
    .join("");

  if (computed.length !== parts.v1.length) return false;
  let result = 0;
  for (let i = 0; i < computed.length; i++) {
    result |= computed.charCodeAt(i) ^ parts.v1.charCodeAt(i);
  }

  const valid = result === 0;
  if (!valid) console.error("[SECURITY] Assinatura MP inválida — webhook rejeitado");
  return valid;
}

serve(async (req) => {
  if (req.method !== "POST") return new Response("Method Not Allowed", { status: 405 });

  let rawBody: string;
  try { rawBody = await req.text(); }
  catch { return new Response("Bad Request", { status: 400 }); }

  const signatureValid = await verifyMPSignature(req, rawBody);
  if (!signatureValid) {
    console.error("[SECURITY] Webhook rejeitado — IP:", req.headers.get("x-forwarded-for") ?? "unknown");
    return new Response("ok", { status: 200 });
  }

  let body: Record<string, unknown>;
  try { body = JSON.parse(rawBody); }
  catch { return new Response("ok", { status: 200 }); }

  if (body.type !== "payment") return new Response("ok", { status: 200 });

  const paymentId = (body.data as Record<string, unknown>)?.id;
  if (!paymentId) return new Response("ok", { status: 200 });

  // Buscar dados reais do MP — nunca confia no body do webhook
  const MP_TOKEN = Deno.env.get("MP_ACCESS_TOKEN")!;
  let payment: Record<string, unknown>;
  try {
    const mpRes = await fetch(`https://api.mercadopago.com/v1/payments/${paymentId}`, {
      headers: { "Authorization": `Bearer ${MP_TOKEN}` },
    });
    if (!mpRes.ok) { console.error("[MP] Erro ao buscar pagamento:", mpRes.status); return new Response("error", { status: 500 }); }
    payment = await mpRes.json() as Record<string, unknown>;
  } catch (err) { console.error("[MP] Falha na requisição:", err); return new Response("error", { status: 500 }); }

  if (payment.status !== "approved") return new Response("ok", { status: 200 });

  // Validar metadata com whitelist
  const meta   = payment.metadata as Record<string, unknown> | undefined;
  const user_id = typeof meta?.user_id === "string" ? meta.user_id : null;
  const plan    = typeof meta?.plan    === "string" ? meta.plan    : null;
  const cycle   = typeof meta?.cycle   === "string" ? meta.cycle   : null;

  if (!user_id || !plan || !cycle) {
    console.error("[WEBHOOK] Metadata incompleta:", meta);
    return new Response("ok", { status: 200 });
  }

  if (!VALID_PLANS.has(plan) || !VALID_CYCLES.has(cycle)) {
    console.error("[SECURITY] Plano/ciclo inválido na metadata:", { plan, cycle });
    return new Response("ok", { status: 200 });
  }

  const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
  if (!UUID_RE.test(user_id)) {
    console.error("[SECURITY] user_id inválido:", user_id);
    return new Response("ok", { status: 200 });
  }

  const days = VALID_DAYS.get(cycle)!;

  const supabase = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!);

  // Idempotência: verifica se já foi processado
  const { data: existing } = await supabase.from("subscriptions")
    .select("id").eq("payment_ref", String(paymentId)).maybeSingle();

  if (existing) { console.log("[WEBHOOK] Já processado:", paymentId); return new Response("ok", { status: 200 }); }

  // Verificar que o usuário existe
  const { data: userExists } = await supabase.from("users").select("id").eq("id", user_id).maybeSingle();
  if (!userExists) { console.error("[WEBHOOK] user_id não encontrado:", user_id); return new Response("ok", { status: 200 }); }

  const expiresAt = new Date();
  expiresAt.setDate(expiresAt.getDate() + days);

  const paymentMethod =
    payment.payment_type_id === "bank_transfer" ? "pix" :
    payment.payment_type_id === "debit_card"    ? "cartao_debito" : "cartao";

  const { error } = await supabase.from("subscriptions").insert({
    user_id, plan, cycle,
    expires_at:     expiresAt.toISOString(),
    status:         "active",
    payment_method: paymentMethod,
    payment_ref:    String(paymentId),
  });

  if (error) {
    if (error.code === "23505") { console.log("[WEBHOOK] Race condition — já criada:", paymentId); return new Response("ok", { status: 200 }); }
    console.error("[WEBHOOK] Erro ao criar assinatura:", error);
    return new Response("error", { status: 500 });
  }

  console.log("[WEBHOOK] Assinatura criada — user:", user_id, "plano:", plan, "ciclo:", cycle);

  // ── Disparar e-mail de confirmação ──
  // Fire-and-forget: não bloqueia o retorno do webhook ao Mercado Pago
  const supabaseUrl = Deno.env.get("SUPABASE_URL")!;
  const serviceKey  = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;

  fetch(`${supabaseUrl}/functions/v1/send-email`, {
    method: "POST",
    headers: {
      "Content-Type":  "application/json",
      "Authorization": `Bearer ${serviceKey}`,
    },
    body: JSON.stringify({
      user_id,
      email_type: "subscription_confirmed",
      metadata: {
        plan,
        cycle,
        expires_at: expiresAt.toISOString(),
      },
    }),
  }).catch((err) => console.error("[WEBHOOK] Falha ao disparar e-mail de confirmação:", err));

  return new Response("ok", { status: 200 });
});

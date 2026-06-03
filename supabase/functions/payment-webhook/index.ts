import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

// ─── CONSTANTES ───────────────────────────────────────────────────────────────
const VALID_PLANS  = new Set(["starter", "advanced", "elite"]);
const VALID_CYCLES = new Set(["mensal", "semestral", "anual"]);
const VALID_DAYS   = new Map([["mensal", 30], ["semestral", 180], ["anual", 365]]);
const UUID_RE      = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

// ─── HMAC — verifica assinatura do Mercado Pago (apenas formato v2) ─────────
async function verifyMPSignature(req: Request, _rawBody: string): Promise<boolean> {
  const secret = Deno.env.get("MP_WEBHOOK_SECRET");
  if (!secret) {
    console.error("[SECURITY] MP_WEBHOOK_SECRET não configurado — rejeitando webhook v2");
    return false;
  }

  const xSignature = req.headers.get("x-signature");
  const xRequestId = req.headers.get("x-request-id");
  const dataId     = new URL(req.url).searchParams.get("data.id");

  if (!xSignature || !xRequestId) return false;

  const parts: Record<string, string> = {};
  for (const part of xSignature.split(",")) {
    const [k, v] = part.split("=");
    if (k && v) parts[k.trim()] = v.trim();
  }

  if (!parts.ts || !parts.v1) return false;

  const signedTemplate = `id:${dataId};request-id:${xRequestId};ts:${parts.ts};`;

  const encoder   = new TextEncoder();
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

  return result === 0;
}

// ─── EXTRAIR PAYMENT ID — aceita todos os formatos de notificação do MP ─────
function extractPaymentId(req: Request, body: Record<string, unknown>): string | null {
  // Formato v2 (Webhooks): body JSON com { type: "payment", data: { id } }
  if (body.type === "payment") {
    const dataId = (body.data as Record<string, unknown>)?.id;
    if (dataId) return String(dataId);
  }

  const url    = new URL(req.url);
  const topic  = url.searchParams.get("topic");
  const type   = url.searchParams.get("type");

  // IPN tipo 1: ?type=payment&data.id=X
  if (type === "payment") {
    const id = url.searchParams.get("data.id");
    if (id) return id;
  }

  // IPN tipo 2: ?topic=payment&id=X
  if (topic === "payment") {
    const id = url.searchParams.get("id");
    if (id) return id;
  }

  return null;
}

// ─── Verificar se é merchant_order (ignorar) ────────────────────────────────
function isMerchantOrder(req: Request, body: Record<string, unknown>): boolean {
  if (body.type === "merchant_order") return true;
  const topic = new URL(req.url).searchParams.get("topic");
  return topic === "merchant_order";
}

serve(async (req) => {
  if (req.method !== "POST") return new Response("Method Not Allowed", { status: 405 });

  try {
    let rawBody: string;
    try { rawBody = await req.text(); }
    catch { return new Response("ok", { status: 200 }); }

    // Parsear body JSON (pode ser vazio em IPNs via query string)
    let body: Record<string, unknown>;
    try { body = JSON.parse(rawBody); }
    catch { body = {}; }

    // Ignorar merchant_order
    if (isMerchantOrder(req, body)) return new Response("ok", { status: 200 });

    // Verificar HMAC apenas quando headers estão presentes (formato v2)
    const hasHmacHeaders = req.headers.has("x-signature") && req.headers.has("x-request-id");
    if (hasHmacHeaders) {
      const valid = await verifyMPSignature(req, rawBody);
      if (!valid) {
        console.error("[SECURITY] Assinatura HMAC inválida — IP:", req.headers.get("x-forwarded-for") ?? "unknown");
        return new Response("ok", { status: 200 });
      }
    }

    // Extrair payment ID de qualquer formato
    const paymentId = extractPaymentId(req, body);
    if (!paymentId) {
      console.log("[WEBHOOK] Formato não reconhecido ou sem payment ID — ignorando");
      return new Response("ok", { status: 200 });
    }

    // Buscar dados reais do MP — nunca confia no body do webhook
    const MP_TOKEN = Deno.env.get("MP_ACCESS_TOKEN")!;
    let payment: Record<string, unknown>;
    try {
      const mpRes = await fetch(`https://api.mercadopago.com/v1/payments/${paymentId}`, {
        headers: { "Authorization": `Bearer ${MP_TOKEN}` },
      });
      if (!mpRes.ok) {
        console.error("[MP] Erro ao buscar pagamento:", mpRes.status);
        return new Response("ok", { status: 200 });
      }
      payment = await mpRes.json() as Record<string, unknown>;
    } catch (err) {
      console.error("[MP] Falha na requisição:", err);
      return new Response("ok", { status: 200 });
    }

    if (payment.status !== "approved") return new Response("ok", { status: 200 });

    // Validar metadata com whitelist
    const meta    = payment.metadata as Record<string, unknown> | undefined;
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

    if (!UUID_RE.test(user_id)) {
      console.error("[SECURITY] user_id inválido:", user_id);
      return new Response("ok", { status: 200 });
    }

    const days = VALID_DAYS.get(cycle)!;

    const supabase = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SERVICE_ROLE_KEY")!);

    // Idempotência: verifica se já foi processado
    const { data: existing } = await supabase.from("subscriptions")
      .select("id").eq("payment_ref", String(paymentId)).maybeSingle();

    if (existing) {
      console.log("[WEBHOOK] Já processado:", paymentId);
      return new Response("ok", { status: 200 });
    }

    // Verificar que o usuário existe
    const { data: userExists } = await supabase.from("users").select("id").eq("id", user_id).maybeSingle();
    if (!userExists) {
      console.error("[WEBHOOK] user_id não encontrado:", user_id);
      return new Response("ok", { status: 200 });
    }

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
      if (error.code === "23505") {
        console.log("[WEBHOOK] Race condition — já criada:", paymentId);
        return new Response("ok", { status: 200 });
      }
      console.error("[WEBHOOK] Erro ao criar assinatura:", error);
      return new Response("ok", { status: 200 });
    }

    console.log("[WEBHOOK] Assinatura criada — user:", user_id, "plano:", plan, "ciclo:", cycle);

    // Disparar email de confirmação via send-email (fire-and-forget)
    try {
      const supabaseUrl = Deno.env.get("SUPABASE_URL")!;
      const serviceKey  = Deno.env.get("SERVICE_ROLE_KEY")!;
      await fetch(`${supabaseUrl}/functions/v1/send-email`, {
        method: "POST",
        headers: {
          "Content-Type":  "application/json",
          "Authorization": `Bearer ${serviceKey}`,
        },
        body: JSON.stringify({
          user_id,
          email_type: "subscription_confirmed",
          metadata: { plan, cycle, expires_at: expiresAt.toISOString() },
        }),
      });
    } catch (emailErr) {
      console.error("[WEBHOOK] Falha ao disparar email:", emailErr);
    }

    return new Response("ok", { status: 200 });

  } catch (err) {
    console.error("[WEBHOOK] Erro interno:", err);
    return new Response("ok", { status: 200 });
  }
});

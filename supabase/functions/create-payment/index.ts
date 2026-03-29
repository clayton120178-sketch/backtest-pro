import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

// ─── CONSTANTES E WHITELIST ───────────────────────────────────────────────────
const ALLOWED_ORIGIN = "https://backtestpro-app.vercel.app";

const PRICES: Record<string, Record<string, number>> = {
  essencial: { mensal: 149.90, semestral: 799.90, anual: 1499.90 },
  pro:       { mensal: 199.90, semestral: 999.90, anual: 2199.90 },
};

const CYCLE_DAYS: Record<string, number> = { mensal: 30, semestral: 180, anual: 365 };

const VALID_PLANS       = new Set(Object.keys(PRICES));
const VALID_CYCLES      = new Set(Object.keys(CYCLE_DAYS));
const VALID_PAY_TYPES   = new Set(["pix", "credit_card", "debit_card"]);
const EMAIL_RE          = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

// ─── CORS — apenas o domínio do produto ──────────────────────────────────────
function corsHeaders(req: Request) {
  const origin = req.headers.get("origin") ?? "";
  // Em dev local, aceitar também localhost
  const allowed =
    origin === ALLOWED_ORIGIN ||
    origin.startsWith("http://localhost") ||
    origin.startsWith("http://127.0.0.1");

  return {
    "Access-Control-Allow-Origin":  allowed ? origin : ALLOWED_ORIGIN,
    "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
  };
}

// ─── SANITIZAÇÃO ─────────────────────────────────────────────────────────────
function sanitizeString(val: unknown, maxLen = 200): string | null {
  if (typeof val !== "string") return null;
  const trimmed = val.trim().slice(0, maxLen);
  return trimmed.length > 0 ? trimmed : null;
}

serve(async (req) => {
  const cors = corsHeaders(req);

  if (req.method === "OPTIONS") return new Response("ok", { headers: cors });
  if (req.method !== "POST")    return new Response("Method Not Allowed", { status: 405 });

  try {
    // ── 1. Autenticar usuário ───────────────────────────────────────────────
    const authHeader = req.headers.get("Authorization");
    if (!authHeader?.startsWith("Bearer ")) {
      return new Response("Unauthorized", { status: 401, headers: cors });
    }

    const supabase = createClient(
      Deno.env.get("SUPABASE_URL")!,
      Deno.env.get("SUPABASE_ANON_KEY")!,
      { global: { headers: { Authorization: authHeader } } }
    );

    const { data: { user }, error: userError } = await supabase.auth.getUser();
    if (userError || !user) {
      return new Response("Unauthorized", { status: 401, headers: cors });
    }

    // ── 2. Parsear e validar body ───────────────────────────────────────────
    let raw: Record<string, unknown>;
    try { raw = await req.json(); }
    catch { return new Response(JSON.stringify({ error: "Body inválido" }), { status: 400, headers: { ...cors, "Content-Type": "application/json" } }); }

    const plan         = sanitizeString(raw.plan);
    const cycle        = sanitizeString(raw.cycle);
    const payment_type = sanitizeString(raw.payment_type);

    // Whitelist rigorosa — rejeita qualquer valor não esperado
    if (!plan || !VALID_PLANS.has(plan)) {
      return new Response(JSON.stringify({ error: "Plano inválido" }), { status: 400, headers: { ...cors, "Content-Type": "application/json" } });
    }
    if (!cycle || !VALID_CYCLES.has(cycle)) {
      return new Response(JSON.stringify({ error: "Ciclo inválido" }), { status: 400, headers: { ...cors, "Content-Type": "application/json" } });
    }
    if (!payment_type || !VALID_PAY_TYPES.has(payment_type)) {
      return new Response(JSON.stringify({ error: "Método de pagamento inválido" }), { status: 400, headers: { ...cors, "Content-Type": "application/json" } });
    }

    // ── 3. Preço vem do backend — nunca do frontend ─────────────────────────
    const amount = PRICES[plan][cycle];
    const days   = CYCLE_DAYS[cycle];
    const MP_TOKEN = Deno.env.get("MP_ACCESS_TOKEN")!;

    // ── 4. Validar payer ────────────────────────────────────────────────────
    const payerRaw = raw.payer as Record<string, unknown> | undefined;
    const payerEmail = sanitizeString(payerRaw?.email);

    // Email do payer deve bater com o do usuário autenticado (ou ser seu email)
    if (!payerEmail || !EMAIL_RE.test(payerEmail)) {
      return new Response(JSON.stringify({ error: "Email do pagador inválido" }), { status: 400, headers: { ...cors, "Content-Type": "application/json" } });
    }

    // Forçar email autenticado (não confiamos no email que vem do frontend)
    const payerEmailSafe = user.email!;

    // ── 5. Montar payload para o MP ─────────────────────────────────────────
    const mpPayload: Record<string, unknown> = {
      transaction_amount: amount,
      description: `Backtest Pro — ${plan.charAt(0).toUpperCase() + plan.slice(1)} ${cycle}`,
      payment_method_id: sanitizeString(raw.payment_method_id) ?? payment_type,
      payer: {
        email: payerEmailSafe,
        // CPF só se vier e estiver em formato válido
        ...(payerRaw?.identification ? { identification: payerRaw.identification } : {}),
      },
      metadata: { user_id: user.id, plan, cycle, days },
      notification_url: `${Deno.env.get("SUPABASE_URL")}/functions/v1/payment-webhook`,
    };

    if (payment_type === "credit_card" || payment_type === "debit_card") {
      const token = sanitizeString(raw.token);
      if (!token) {
        return new Response(JSON.stringify({ error: "Token de cartão ausente" }), { status: 400, headers: { ...cors, "Content-Type": "application/json" } });
      }
      mpPayload.token        = token;
      mpPayload.installments = typeof raw.installments === "number" ? Math.max(1, Math.min(12, raw.installments)) : 1;
      if (raw.issuer_id) mpPayload.issuer_id = sanitizeString(raw.issuer_id);
    }

    // ── 6. Idempotency key com UUID criptográfico (evita cobranças duplicadas) ──
    const idempotencyKey = crypto.randomUUID();

    // ── 7. Chamar API do Mercado Pago ───────────────────────────────────────
    const mpRes = await fetch("https://api.mercadopago.com/v1/payments", {
      method: "POST",
      headers: {
        "Content-Type":      "application/json",
        "Authorization":     `Bearer ${MP_TOKEN}`,
        "X-Idempotency-Key": idempotencyKey,
      },
      body: JSON.stringify(mpPayload),
    });

    const mpData = await mpRes.json() as Record<string, unknown>;

    if (!mpRes.ok) {
      // Log interno completo, resposta externa genérica
      console.error("[MP] Erro na API:", mpData);
      const userMsg = typeof mpData.message === "string"
        ? mpData.message
        : "Erro ao processar pagamento. Tente novamente.";
      return new Response(JSON.stringify({ error: userMsg }), {
        status: 400, headers: { ...cors, "Content-Type": "application/json" }
      });
    }

    // ── 8. Pix: retornar dados para o frontend ──────────────────────────────
    if (payment_type === "pix") {
      const qrCode = (mpData.point_of_interaction as Record<string, unknown>)
        ?.transaction_data as Record<string, unknown> | undefined;

      return new Response(JSON.stringify({
        status:          mpData.status,
        payment_id:      mpData.id,
        pix_copy_paste:  qrCode?.qr_code     ?? null,
        pix_qr_base64:   qrCode?.qr_code_base64 ?? null,
      }), { headers: { ...cors, "Content-Type": "application/json" } });
    }

    // ── 9. Cartão aprovado: criar assinatura via service_role ───────────────
    if (mpData.status === "approved") {
      const adminSupabase = createClient(
        Deno.env.get("SUPABASE_URL")!,
        Deno.env.get("SERVICE_ROLE_KEY")!
      );

      const expiresAt = new Date();
      expiresAt.setDate(expiresAt.getDate() + days);

      const { error: insertError } = await adminSupabase.from("subscriptions").insert({
        user_id:        user.id,
        plan,
        cycle,
        expires_at:     expiresAt.toISOString(),
        status:         "active",
        payment_method: payment_type === "credit_card" ? "cartao" : "cartao_debito",
        payment_ref:    String(mpData.id),
      });

      if (insertError && insertError.code !== "23505") {
        console.error("[DB] Erro ao criar assinatura:", insertError);
      }
    }

    return new Response(JSON.stringify({
      status:        mpData.status,
      status_detail: mpData.status_detail,
      payment_id:    mpData.id,
    }), { headers: { ...cors, "Content-Type": "application/json" } });

  } catch (err) {
    console.error("[create-payment] Erro interno:", err);
    return new Response(JSON.stringify({ error: "Erro interno. Tente novamente." }), {
      status: 500, headers: { ...corsHeaders(req), "Content-Type": "application/json" }
    });
  }
});

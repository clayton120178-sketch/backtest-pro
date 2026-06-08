import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

// ─── CONSTANTES ───────────────────────────────────────────────────────────────
const ALLOWED_ORIGINS = [
  "https://backtestpro-app.vercel.app",
  "https://backtestpro.com.br",
  "https://www.backtestpro.com.br",
];

const VALID_PLANS  = new Set(["starter", "advanced", "elite"]);
const VALID_CYCLES = new Set(["mensal", "semestral", "anual"]);
const CYCLE_DAYS   = new Map([["mensal", 30], ["semestral", 180], ["anual", 365]]);
const UUID_RE      = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

function corsHeaders(req: Request) {
  const origin = req.headers.get("origin") ?? "";
  const allowed =
    ALLOWED_ORIGINS.includes(origin) ||
    origin.startsWith("http://localhost") ||
    origin.startsWith("http://127.0.0.1");
  return {
    "Access-Control-Allow-Origin":  allowed ? origin : ALLOWED_ORIGINS[0],
    "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
  };
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

    const anonClient = createClient(
      Deno.env.get("SUPABASE_URL")!,
      Deno.env.get("SUPABASE_ANON_KEY")!,
      { global: { headers: { Authorization: authHeader } } }
    );

    const { data: { user }, error: userError } = await anonClient.auth.getUser();
    if (userError || !user) {
      return new Response("Unauthorized", { status: 401, headers: cors });
    }

    // ── 2. Parsear body ─────────────────────────────────────────────────────
    let body: Record<string, unknown>;
    try { body = await req.json(); }
    catch { return new Response(JSON.stringify({ error: "Body inválido" }), { status: 400, headers: { ...cors, "Content-Type": "application/json" } }); }

    const payment_id = typeof body.payment_id === "string" ? body.payment_id.trim() : null;
    if (!payment_id) {
      return new Response(JSON.stringify({ error: "payment_id ausente" }), { status: 400, headers: { ...cors, "Content-Type": "application/json" } });
    }

    // ── 3. Consultar pagamento no MP ────────────────────────────────────────
    const MP_TOKEN = Deno.env.get("MP_ACCESS_TOKEN")!;
    let payment: Record<string, unknown>;
    try {
      const mpRes = await fetch(`https://api.mercadopago.com/v1/payments/${payment_id}`, {
        headers: { Authorization: `Bearer ${MP_TOKEN}` },
      });
      if (!mpRes.ok) {
        console.error("[confirm-payment] MP retornou erro:", mpRes.status);
        return new Response(JSON.stringify({ status: "error", provisioned: false }), {
          status: 502, headers: { ...cors, "Content-Type": "application/json" }
        });
      }
      payment = await mpRes.json() as Record<string, unknown>;
    } catch (err) {
      console.error("[confirm-payment] Falha na chamada ao MP:", err);
      return new Response(JSON.stringify({ status: "error", provisioned: false }), {
        status: 502, headers: { ...cors, "Content-Type": "application/json" }
      });
    }

    const mpStatus = String(payment.status ?? "");

    // ── 4. Anti-spoofing: metadata.user_id deve bater com o usuário autenticado
    const meta    = payment.metadata as Record<string, unknown> | undefined;
    const metaUid = typeof meta?.user_id === "string" ? meta.user_id : null;

    if (!metaUid || !UUID_RE.test(metaUid) || metaUid !== user.id) {
      console.error("[confirm-payment] Spoofing detectado — metaUid:", metaUid, "userId:", user.id);
      return new Response(JSON.stringify({ status: mpStatus, provisioned: false }), {
        headers: { ...cors, "Content-Type": "application/json" }
      });
    }

    // ── 5. Se não aprovado, retornar status atual sem provisionar ───────────
    if (mpStatus !== "approved") {
      return new Response(JSON.stringify({ status: mpStatus, provisioned: false }), {
        headers: { ...cors, "Content-Type": "application/json" }
      });
    }

    // ── 6. Validar metadata ─────────────────────────────────────────────────
    const plan  = typeof meta?.plan  === "string" ? meta.plan  : null;
    const cycle = typeof meta?.cycle === "string" ? meta.cycle : null;

    if (!plan || !VALID_PLANS.has(plan) || !cycle || !VALID_CYCLES.has(cycle)) {
      console.error("[confirm-payment] Metadata inválida:", meta);
      return new Response(JSON.stringify({ status: mpStatus, provisioned: false }), {
        headers: { ...cors, "Content-Type": "application/json" }
      });
    }

    const adminClient = createClient(
      Deno.env.get("SUPABASE_URL")!,
      Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!
    );

    // ── 7. Idempotência: já existe assinatura para este pagamento? ──────────
    const { data: existing } = await adminClient
      .from("subscriptions")
      .select("id")
      .eq("payment_ref", payment_id)
      .maybeSingle();

    if (existing) {
      // Atualizar payments para approved se ainda estava pending
      await adminClient.from("payments").update({ status: "approved", subscription_id: existing.id, updated_at: new Date().toISOString() })
        .eq("mp_payment_id", payment_id).eq("status", "pending");
      return new Response(JSON.stringify({ status: "approved", provisioned: true }), {
        headers: { ...cors, "Content-Type": "application/json" }
      });
    }

    // ── 8. Provisionar assinatura ───────────────────────────────────────────
    const days      = CYCLE_DAYS.get(cycle)!;
    const expiresAt = new Date();
    expiresAt.setDate(expiresAt.getDate() + days);

    const paymentTypeId = String(payment.payment_type_id ?? "");
    const paymentMethod = paymentTypeId === "bank_transfer" ? "pix"
                        : paymentTypeId === "debit_card"    ? "cartao_debito"
                        : "cartao";

    const { data: sub, error: insertError } = await adminClient
      .from("subscriptions").insert({
        user_id:        user.id,
        plan,
        cycle,
        expires_at:     expiresAt.toISOString(),
        status:         "active",
        payment_method: paymentMethod,
        payment_ref:    payment_id,
      }).select("id").single();

    if (insertError && (insertError as { code?: string }).code === "23505") {
      // Criado por race condition — ainda OK
      const { data: raceRow } = await adminClient.from("subscriptions").select("id").eq("payment_ref", payment_id).maybeSingle();
      if (raceRow) {
        await adminClient.from("payments").upsert({
          user_id: user.id, mp_payment_id: payment_id, plan, cycle,
          amount: Number(payment.transaction_amount ?? 0), method: paymentMethod,
          status: "approved", subscription_id: raceRow.id, updated_at: new Date().toISOString(),
        }, { onConflict: "mp_payment_id" });
      }
      return new Response(JSON.stringify({ status: "approved", provisioned: true }), {
        headers: { ...cors, "Content-Type": "application/json" }
      });
    }

    if (insertError) {
      console.error("[confirm-payment] Erro ao criar assinatura:", insertError);
      return new Response(JSON.stringify({ status: "approved", provisioned: false }), {
        status: 500, headers: { ...cors, "Content-Type": "application/json" }
      });
    }

    // ── 9. Atualizar payments + disparar e-mail ─────────────────────────────
    const subscriptionId = (sub as { id: string } | null)?.id ?? null;
    await adminClient.from("payments").upsert({
      user_id:         user.id,
      mp_payment_id:   payment_id,
      plan,
      cycle,
      amount:          Number(payment.transaction_amount ?? 0),
      method:          paymentMethod,
      status:          "approved",
      subscription_id: subscriptionId,
      updated_at:      new Date().toISOString(),
    }, { onConflict: "mp_payment_id" });

    const supabaseUrl  = Deno.env.get("SUPABASE_URL")!;
    const serviceKey   = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
    fetch(`${supabaseUrl}/functions/v1/send-email`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "Authorization": `Bearer ${serviceKey}` },
      body: JSON.stringify({
        user_id:    user.id,
        email_type: "subscription_confirmed",
        metadata:   { plan, cycle, expires_at: expiresAt.toISOString() },
      }),
    }).catch((e) => console.error("[confirm-payment] Falha ao disparar email:", e));

    console.log("[confirm-payment] Provisionado — user:", user.id, "plano:", plan);
    return new Response(JSON.stringify({ status: "approved", provisioned: true }), {
      headers: { ...cors, "Content-Type": "application/json" }
    });

  } catch (err) {
    console.error("[confirm-payment] Erro interno:", err);
    return new Response(JSON.stringify({ error: "Erro interno" }), {
      status: 500, headers: { ...corsHeaders(req), "Content-Type": "application/json" }
    });
  }
});

import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: CORS });

  try {
    const authHeader = req.headers.get("Authorization");
    if (!authHeader) return new Response("Unauthorized", { status: 401 });

    const supabase = createClient(
      Deno.env.get("SUPABASE_URL")!,
      Deno.env.get("SUPABASE_ANON_KEY")!,
      { global: { headers: { Authorization: authHeader } } }
    );

    const { data: { user }, error: userError } = await supabase.auth.getUser();
    if (userError || !user) return new Response("Unauthorized", { status: 401 });

    const { plan, cycle, payment_method_id, token, issuer_id, installments, payer, payment_type } = await req.json();

    const PRICES: Record<string, Record<string, number>> = {
      essencial: { mensal: 149.90, semestral: 799.90, anual: 1499.90 },
      pro:       { mensal: 199.90, semestral: 999.90, anual: 2199.90 },
    };

    const amount = PRICES[plan]?.[cycle];
    if (!amount) return new Response("Plano inválido", { status: 400 });

    const DAYS: Record<string, number> = { mensal: 30, semestral: 180, anual: 365 };
    const MP_TOKEN = Deno.env.get("MP_ACCESS_TOKEN")!;

    const mpPayload: Record<string, unknown> = {
      transaction_amount: amount,
      description: `Backtest Pro — ${plan.charAt(0).toUpperCase() + plan.slice(1)} ${cycle}`,
      payment_method_id,
      payer: { email: payer.email, ...(payer.identification ? { identification: payer.identification } : {}) },
      metadata: { user_id: user.id, plan, cycle, days: DAYS[cycle] },
      notification_url: `${Deno.env.get("SUPABASE_URL")}/functions/v1/payment-webhook`,
    };

    if (payment_type === "credit_card" || payment_type === "debit_card") {
      mpPayload.token = token;
      mpPayload.installments = installments || 1;
      if (issuer_id) mpPayload.issuer_id = issuer_id;
    }

    const mpRes = await fetch("https://api.mercadopago.com/v1/payments", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${MP_TOKEN}`,
        "X-Idempotency-Key": `${user.id}-${plan}-${cycle}-${Date.now()}`,
      },
      body: JSON.stringify(mpPayload),
    });

    const mpData = await mpRes.json();

    if (!mpRes.ok) {
      return new Response(JSON.stringify({ error: mpData.message || "Erro no pagamento" }), {
        status: 400, headers: { ...CORS, "Content-Type": "application/json" }
      });
    }

    if (payment_type === "pix") {
      return new Response(JSON.stringify({
        status: mpData.status,
        payment_id: mpData.id,
        pix_copy_paste: mpData.point_of_interaction?.transaction_data?.qr_code,
        pix_qr_base64: mpData.point_of_interaction?.transaction_data?.qr_code_base64,
      }), { headers: { ...CORS, "Content-Type": "application/json" } });
    }

    if (mpData.status === "approved") {
      const expiresAt = new Date();
      expiresAt.setDate(expiresAt.getDate() + DAYS[cycle]);
      const adminSupabase = createClient(
        Deno.env.get("SUPABASE_URL")!,
        Deno.env.get("SERVICE_ROLE_KEY")!
      );
      await adminSupabase.from("subscriptions").insert({
        user_id: user.id, plan, cycle,
        expires_at: expiresAt.toISOString(),
        status: "active",
        payment_method: payment_type === "credit_card" ? "cartao" : "cartao_debito",
        payment_ref: String(mpData.id),
      });
    }

    return new Response(JSON.stringify({
      status: mpData.status,
      status_detail: mpData.status_detail,
      payment_id: mpData.id,
    }), { headers: { ...CORS, "Content-Type": "application/json" } });

  } catch (err) {
    console.error(err);
    return new Response(JSON.stringify({ error: "Erro interno" }), {
      status: 500, headers: { ...CORS, "Content-Type": "application/json" }
    });
  }
});

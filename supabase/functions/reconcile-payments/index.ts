/**
 * reconcile-payments — cron de reconciliação
 *
 * Agendada via pg_cron a cada 15 minutos (ver migration 011).
 * Varre payments com status='pending' criados nas últimas 24h,
 * consulta o MP e provisiona os aprovados. Idempotente via payment_ref.
 */

import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const VALID_PLANS  = new Set(["starter", "advanced", "elite"]);
const VALID_CYCLES = new Set(["mensal", "semestral", "anual"]);
const CYCLE_DAYS   = new Map([["mensal", 30], ["semestral", 180], ["anual", 365]]);

serve(async (req) => {
  if (req.method !== "POST") return new Response("Method Not Allowed", { status: 405 });

  const authHeader = req.headers.get("Authorization") ?? "";
  const serviceKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
  if (authHeader !== `Bearer ${serviceKey}`) {
    return new Response("Unauthorized", { status: 401 });
  }

  const supabase = createClient(Deno.env.get("SUPABASE_URL")!, serviceKey);
  const MP_TOKEN = Deno.env.get("MP_ACCESS_TOKEN")!;

  // Buscar payments pending das últimas 24h ainda sem subscription_id
  const { data: pending, error: fetchErr } = await supabase
    .from("payments")
    .select("id, user_id, mp_payment_id, plan, cycle, amount, method")
    .eq("status", "pending")
    .is("subscription_id", null)
    .gte("created_at", new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString());

  if (fetchErr) {
    console.error("[reconcile] Erro ao buscar pending:", fetchErr);
    return new Response("error", { status: 500 });
  }

  if (!pending || pending.length === 0) {
    console.log("[reconcile] Nenhum pagamento pending encontrado.");
    return new Response("ok", { status: 200 });
  }

  console.log(`[reconcile] ${pending.length} pagamento(s) pending para verificar.`);

  for (const pmt of pending) {
    if (!pmt.mp_payment_id) continue;

    let mpPayment: Record<string, unknown>;
    try {
      const mpRes = await fetch(`https://api.mercadopago.com/v1/payments/${pmt.mp_payment_id}`, {
        headers: { Authorization: `Bearer ${MP_TOKEN}` },
      });
      if (!mpRes.ok) {
        console.error(`[reconcile] MP erro para ${pmt.mp_payment_id}:`, mpRes.status);
        continue;
      }
      mpPayment = await mpRes.json() as Record<string, unknown>;
    } catch (e) {
      console.error(`[reconcile] Falha ao consultar MP ${pmt.mp_payment_id}:`, e);
      continue;
    }

    const mpStatus = String(mpPayment.status ?? "");

    // Marcar rejected/cancelled no banco
    if (mpStatus === "rejected" || mpStatus === "cancelled" || mpStatus === "expired") {
      await supabase.from("payments")
        .update({ status: mpStatus === "rejected" ? "rejected" : "cancelled", updated_at: new Date().toISOString() })
        .eq("id", pmt.id);
      console.log(`[reconcile] ${pmt.mp_payment_id} → ${mpStatus}`);
      continue;
    }

    if (mpStatus !== "approved") continue;

    // Verificar se já foi provisionado (race condition entre webhook e reconcile)
    const { data: existingSub } = await supabase
      .from("subscriptions")
      .select("id")
      .eq("payment_ref", pmt.mp_payment_id)
      .maybeSingle();

    if (existingSub) {
      await supabase.from("payments")
        .update({ status: "approved", subscription_id: existingSub.id, updated_at: new Date().toISOString() })
        .eq("id", pmt.id);
      continue;
    }

    // Validar plan/cycle
    const plan  = pmt.plan;
    const cycle = pmt.cycle;
    if (!VALID_PLANS.has(plan) || !VALID_CYCLES.has(cycle)) {
      console.error(`[reconcile] plan/cycle inválido para ${pmt.mp_payment_id}:`, { plan, cycle });
      continue;
    }

    const days      = CYCLE_DAYS.get(cycle)!;
    const expiresAt = new Date();
    expiresAt.setDate(expiresAt.getDate() + days);

    const paymentTypeId = String(mpPayment.payment_type_id ?? "");
    const paymentMethod = paymentTypeId === "bank_transfer" ? "pix"
                        : paymentTypeId === "debit_card"    ? "cartao_debito"
                        : "cartao";

    const { data: newSub, error: insertErr } = await supabase
      .from("subscriptions").insert({
        user_id:        pmt.user_id,
        plan,
        cycle,
        expires_at:     expiresAt.toISOString(),
        status:         "active",
        payment_method: paymentMethod,
        payment_ref:    pmt.mp_payment_id,
      }).select("id").single();

    if (insertErr) {
      if ((insertErr as { code?: string }).code === "23505") {
        console.log(`[reconcile] Race condition — ${pmt.mp_payment_id} já provisionado`);
      } else {
        console.error(`[reconcile] Erro ao criar assinatura ${pmt.mp_payment_id}:`, insertErr);
      }
      continue;
    }

    const subscriptionId = (newSub as { id: string } | null)?.id ?? null;
    await supabase.from("payments")
      .update({ status: "approved", subscription_id: subscriptionId, updated_at: new Date().toISOString() })
      .eq("id", pmt.id);

    // Disparar e-mail de confirmação
    const supabaseUrl = Deno.env.get("SUPABASE_URL")!;
    fetch(`${supabaseUrl}/functions/v1/send-email`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "Authorization": `Bearer ${serviceKey}` },
      body: JSON.stringify({
        user_id:    pmt.user_id,
        email_type: "subscription_confirmed",
        metadata:   { plan, cycle, expires_at: expiresAt.toISOString() },
      }),
    }).catch((e) => console.error("[reconcile] Falha ao disparar email:", e));

    console.log(`[reconcile] Provisionado — user:${pmt.user_id} mp:${pmt.mp_payment_id} plano:${plan}`);
  }

  return new Response("ok", { status: 200 });
});

/**
 * check-expired-subscriptions — cron job diário
 *
 * Agendada via pg_cron (ver migration 005):
 *   0 12 * * *  → todo dia às 09h00 de Brasília (12h00 UTC)
 *
 * Lógica:
 * 1. Busca todas as assinaturas com status='active' e expires_at < now()
 * 2. Para cada uma: atualiza status para 'expired' no banco
 * 3. Chama send-email com tipo subscription_expired
 *    (send-email cuida de idempotência via email_logs)
 */

import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

serve(async (req) => {
  if (req.method !== "POST") {
    return new Response("Method Not Allowed", { status: 405 });
  }

  const supabase = createClient(
    Deno.env.get("SUPABASE_URL")!,
    Deno.env.get("SERVICE_ROLE_KEY")!
  );

  const now = new Date().toISOString();

  // ── Buscar assinaturas vencidas ainda marcadas como active ──
  const { data: expired, error } = await supabase
    .from("subscriptions")
    .select("id, user_id, plan, cycle, expires_at")
    .eq("status", "active")
    .lt("expires_at", now);

  if (error) {
    console.error("[CHECK-EXPIRED] Erro ao buscar assinaturas:", error);
    return new Response("error", { status: 500 });
  }

  if (!expired || expired.length === 0) {
    console.log("[CHECK-EXPIRED] Nenhuma assinatura vencida encontrada.");
    return new Response("ok", { status: 200 });
  }

  console.log(`[CHECK-EXPIRED] ${expired.length} assinatura(s) vencida(s) encontrada(s).`);

  const supabaseUrl = Deno.env.get("SUPABASE_URL")!;
  const serviceKey  = Deno.env.get("SERVICE_ROLE_KEY")!;

  for (const sub of expired) {
    // ── Atualizar status para 'expired' ──
    const { error: updateError } = await supabase
      .from("subscriptions")
      .update({ status: "expired" })
      .eq("id", sub.id);

    if (updateError) {
      console.error(`[CHECK-EXPIRED] Erro ao atualizar subscription ${sub.id}:`, updateError);
      continue;
    }

    console.log(`[CHECK-EXPIRED] Assinatura ${sub.id} → expired (user: ${sub.user_id})`);

    // ── Disparar e-mail via send-email ──
    // send-email cuida de idempotência — se já enviou, ignora silenciosamente
    const emailRes = await fetch(`${supabaseUrl}/functions/v1/send-email`, {
      method: "POST",
      headers: {
        "Content-Type":  "application/json",
        "Authorization": `Bearer ${serviceKey}`,
      },
      body: JSON.stringify({
        user_id:    sub.user_id,
        email_type: "subscription_expired",
        metadata: {
          plan:       sub.plan,
          cycle:      sub.cycle,
          expires_at: sub.expires_at,
        },
      }),
    });

    if (!emailRes.ok) {
      console.error(`[CHECK-EXPIRED] Falha ao chamar send-email para user ${sub.user_id}:`, emailRes.status);
    }
  }

  return new Response("ok", { status: 200 });
});

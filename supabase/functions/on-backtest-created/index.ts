/**
 * on-backtest-created — detecta esgotamento do free trial
 *
 * Chamada via Database Webhook configurado no Supabase Dashboard:
 *   Table: public.backtests
 *   Events: INSERT
 *   URL: /functions/v1/on-backtest-created
 *
 * Lógica:
 * 1. Recebe o evento de INSERT em backtests
 * 2. Conta quantos backtests o usuário já tem
 * 3. Verifica se tem assinatura ativa
 * 4. Se count == 3 e sem assinatura → dispara trial_exhausted via send-email
 */

import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const TRIAL_LIMIT = 3;

serve(async (req) => {
  if (req.method !== "POST") {
    return new Response("Method Not Allowed", { status: 405 });
  }

  let body: Record<string, unknown>;
  try {
    body = await req.json() as Record<string, unknown>;
  } catch {
    return new Response("Bad Request", { status: 400 });
  }

  // O Database Webhook entrega o payload no formato:
  // { type: "INSERT", table: "backtests", record: { ... }, ... }
  const record = body.record as Record<string, unknown> | undefined;
  const userId = typeof record?.user_id === "string" ? record.user_id : null;

  if (!userId) {
    console.error("[ON-BACKTEST] user_id ausente no payload:", body);
    return new Response("ok", { status: 200 });
  }

  const supabase = createClient(
    Deno.env.get("SUPABASE_URL")!,
    Deno.env.get("SERVICE_ROLE_KEY")!
  );

  // ── Contar total de backtests deste usuário ──
  const { count, error: countError } = await supabase
    .from("backtests")
    .select("id", { count: "exact", head: true })
    .eq("user_id", userId);

  if (countError) {
    console.error("[ON-BACKTEST] Erro ao contar backtests:", countError);
    return new Response("ok", { status: 200 });
  }

  // Só dispara exatamente quando atingir o limite (não a cada backtest após)
  if (count !== TRIAL_LIMIT) {
    return new Response("ok", { status: 200 });
  }

  // ── Verificar se tem assinatura ativa ──
  const now = new Date().toISOString();
  const { data: activeSub } = await supabase
    .from("subscriptions")
    .select("id")
    .eq("user_id", userId)
    .eq("status", "active")
    .gt("expires_at", now)
    .maybeSingle();

  if (activeSub) {
    // Tem assinatura ativa — os 3 backtests foram do período free antes de assinar.
    // Não disparar e-mail de ativação.
    console.log("[ON-BACKTEST] Usuário tem assinatura ativa, ignorando trial_exhausted:", userId);
    return new Response("ok", { status: 200 });
  }

  // ── Disparar send-email ──
  const supabaseUrl = Deno.env.get("SUPABASE_URL")!;
  const serviceKey  = Deno.env.get("SERVICE_ROLE_KEY")!;

  const emailRes = await fetch(`${supabaseUrl}/functions/v1/send-email`, {
    method: "POST",
    headers: {
      "Content-Type":  "application/json",
      "Authorization": `Bearer ${serviceKey}`,
    },
    body: JSON.stringify({
      user_id:    userId,
      email_type: "trial_exhausted",
    }),
  });

  if (!emailRes.ok) {
    console.error("[ON-BACKTEST] Falha ao chamar send-email:", emailRes.status);
  } else {
    console.log("[ON-BACKTEST] trial_exhausted disparado para:", userId);
  }

  return new Response("ok", { status: 200 });
});

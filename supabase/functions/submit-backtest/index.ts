import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

// ─── CONSTANTES ──────────────────────────────────────────────────────────────
const ALLOWED_ORIGIN = "https://backtestpro-app.vercel.app";

// ─── CORS ────────────────────────────────────────────────────────────────────
function corsHeaders(req: Request) {
  const origin = req.headers.get("origin") ?? "";
  const allowed =
    origin === ALLOWED_ORIGIN ||
    origin.startsWith("http://localhost") ||
    origin.startsWith("http://127.0.0.1");

  return {
    "Access-Control-Allow-Origin": allowed ? origin : ALLOWED_ORIGIN,
    "Access-Control-Allow-Headers":
      "authorization, x-client-info, apikey, content-type",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
  };
}

// ─── HANDLER ─────────────────────────────────────────────────────────────────
serve(async (req: Request) => {
  const cors = corsHeaders(req);

  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: cors });
  }

  if (req.method !== "POST") {
    return new Response(JSON.stringify({ error: "Method not allowed" }), {
      status: 405,
      headers: { ...cors, "Content-Type": "application/json" },
    });
  }

  try {
    // 1. Autenticar usuario via JWT
    const authHeader = req.headers.get("authorization") ?? "";
    if (!authHeader.startsWith("Bearer ")) {
      return new Response(
        JSON.stringify({ error: "Token de autenticacao ausente" }),
        { status: 401, headers: { ...cors, "Content-Type": "application/json" } }
      );
    }

    const supabaseUrl = Deno.env.get("SUPABASE_URL")!;
    const supabaseAnonKey = Deno.env.get("SUPABASE_ANON_KEY")!;
    const supabaseServiceKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;

    // Cliente com token do usuario (para validar identidade)
    const userClient = createClient(supabaseUrl, supabaseAnonKey, {
      global: { headers: { Authorization: authHeader } },
    });

    const {
      data: { user },
      error: authError,
    } = await userClient.auth.getUser();

    if (authError || !user) {
      return new Response(
        JSON.stringify({ error: "Usuario nao autenticado" }),
        { status: 401, headers: { ...cors, "Content-Type": "application/json" } }
      );
    }

    // 2. Verificar assinatura ativa
    const serviceClient = createClient(supabaseUrl, supabaseServiceKey);
    const now = new Date().toISOString();

    const { data: subs } = await serviceClient
      .from("subscriptions")
      .select("id, plan, expires_at")
      .eq("user_id", user.id)
      .eq("status", "active")
      .gte("expires_at", now)
      .order("expires_at", { ascending: false })
      .limit(1);

    if (!subs || subs.length === 0) {
      return new Response(
        JSON.stringify({ error: "Assinatura ativa necessaria para rodar backtests" }),
        { status: 403, headers: { ...cors, "Content-Type": "application/json" } }
      );
    }

    // 3. Parsear body (state.cfg do frontend)
    const body = await req.json();
    const cfg = body.cfg;

    if (!cfg || typeof cfg !== "object") {
      return new Response(
        JSON.stringify({ error: "Campo 'cfg' ausente ou invalido" }),
        { status: 400, headers: { ...cors, "Content-Type": "application/json" } }
      );
    }

    // Validacao basica no frontend config
    if (!cfg.conditions || !Array.isArray(cfg.conditions) || cfg.conditions.length === 0) {
      return new Response(
        JSON.stringify({ error: "Nenhuma condicao de entrada definida" }),
        { status: 400, headers: { ...cors, "Content-Type": "application/json" } }
      );
    }

    // 4. Verificar limite de backtests em fila (anti-abuse)
    const { count: queuedCount } = await serviceClient
      .from("backtests")
      .select("id", { count: "exact", head: true })
      .eq("user_id", user.id)
      .in("status", ["queued", "running"]);

    const MAX_CONCURRENT = 3;
    if ((queuedCount ?? 0) >= MAX_CONCURRENT) {
      return new Response(
        JSON.stringify({
          error: `Limite de ${MAX_CONCURRENT} backtests simultaneos. Aguarde os anteriores finalizarem.`,
        }),
        { status: 429, headers: { ...cors, "Content-Type": "application/json" } }
      );
    }

    // 5. Inserir na fila (status = 'queued')
    const { data: bt, error: insertError } = await serviceClient
      .from("backtests")
      .insert({
        user_id: user.id,
        config: cfg,
        status: "queued",
      })
      .select("id, status, created_at")
      .single();

    if (insertError) {
      console.error("Insert error:", insertError);
      return new Response(
        JSON.stringify({ error: "Erro ao enfileirar backtest" }),
        { status: 500, headers: { ...cors, "Content-Type": "application/json" } }
      );
    }

    // 6. Retornar ID para o frontend fazer polling
    return new Response(
      JSON.stringify({
        success: true,
        backtest_id: bt.id,
        status: bt.status,
        message: "Backtest enfileirado. Use GET /backtests?id=eq.{id} para acompanhar.",
      }),
      {
        status: 201,
        headers: { ...cors, "Content-Type": "application/json" },
      }
    );
  } catch (err) {
    console.error("Unexpected error:", err);
    return new Response(
      JSON.stringify({ error: "Erro interno do servidor" }),
      { status: 500, headers: { ...cors, "Content-Type": "application/json" } }
    );
  }
});

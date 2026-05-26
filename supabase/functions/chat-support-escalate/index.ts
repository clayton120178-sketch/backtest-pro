import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const CORS_HEADERS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

interface EscalateRequest {
  user_id: string;
  user_name: string;
  user_email: string;
  user_plan: string;
  user_whatsapp: string;
  category: string;
  conversation_history: Array<{ role: string; content: string }>;
}

serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: CORS_HEADERS });
  }

  if (req.method !== "POST") {
    return new Response("Method Not Allowed", { status: 405, headers: CORS_HEADERS });
  }

  // Validar sessão
  const authHeader = req.headers.get("Authorization");
  if (!authHeader) {
    return new Response(JSON.stringify({ error: "Não autorizado" }), {
      status: 401, headers: { ...CORS_HEADERS, "Content-Type": "application/json" },
    });
  }

  const supabaseAnon = createClient(
    Deno.env.get("SUPABASE_URL")!,
    Deno.env.get("SUPABASE_ANON_KEY")!,
    { global: { headers: { Authorization: authHeader } } }
  );

  const { data: { user }, error: authError } = await supabaseAnon.auth.getUser();
  if (authError || !user) {
    return new Response(JSON.stringify({ error: "Sessão inválida" }), {
      status: 401, headers: { ...CORS_HEADERS, "Content-Type": "application/json" },
    });
  }

  let body: EscalateRequest;
  try {
    body = await req.json() as EscalateRequest;
  } catch {
    return new Response(JSON.stringify({ error: "Payload inválido" }), {
      status: 400, headers: { ...CORS_HEADERS, "Content-Type": "application/json" },
    });
  }

  if (body.user_id !== user.id) {
    return new Response(JSON.stringify({ error: "user_id não corresponde à sessão" }), {
      status: 403, headers: { ...CORS_HEADERS, "Content-Type": "application/json" },
    });
  }

  if (!body.user_whatsapp || !body.category) {
    return new Response(JSON.stringify({ error: "Dados obrigatórios ausentes" }), {
      status: 400, headers: { ...CORS_HEADERS, "Content-Type": "application/json" },
    });
  }

  // Inserir via service_role (ignora RLS)
  const supabaseAdmin = createClient(
    Deno.env.get("SUPABASE_URL")!,
    Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!
  );

  const { error: insertError } = await supabaseAdmin
    .from("support_tickets")
    .insert({
      user_id: body.user_id,
      user_name: body.user_name,
      user_email: body.user_email,
      user_plan: body.user_plan,
      user_whatsapp: body.user_whatsapp,
      category: body.category,
      conversation: body.conversation_history,
      status: "pending",
    });

  if (insertError) {
    console.error("[chat-support-escalate] Erro ao inserir ticket:", insertError);
    return new Response(JSON.stringify({ error: "Erro ao registrar atendimento" }), {
      status: 500, headers: { ...CORS_HEADERS, "Content-Type": "application/json" },
    });
  }

  return new Response(
    JSON.stringify({ success: true }),
    { status: 200, headers: { ...CORS_HEADERS, "Content-Type": "application/json" } }
  );
});

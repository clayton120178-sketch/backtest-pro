import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const ALLOWED_ORIGINS = [
  "https://backtestpro-app.vercel.app",
  "https://backtestpro.com.br",
  "https://www.backtestpro.com.br",
];

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

const PIX_TYPES = new Set(["cpf","cnpj","email","phone","random"]);

serve(async (req) => {
  const cors = corsHeaders(req);
  if (req.method === "OPTIONS") return new Response(null, { headers: cors });

  const json = (body: unknown, status = 200) =>
    new Response(JSON.stringify(body), {
      status,
      headers: { ...cors, "Content-Type": "application/json" },
    });

  // Auth
  const authHeader = req.headers.get("Authorization");
  if (!authHeader) return json({ error: "unauthorized" }, 401);

  const supabaseUser = createClient(
    Deno.env.get("SUPABASE_URL")!,
    Deno.env.get("SUPABASE_ANON_KEY")!,
    { global: { headers: { Authorization: authHeader } } },
  );
  const { data: { user }, error: authErr } = await supabaseUser.auth.getUser();
  if (authErr || !user) return json({ error: "unauthorized" }, 401);

  const supabase = createClient(
    Deno.env.get("SUPABASE_URL")!,
    Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!,
  );

  try {
    const body = await req.json();
    const { display_name, pix_key, pix_key_type, whatsapp } = body;

    // Find affiliate by user_id
    const { data: affiliate, error: findErr } = await supabase
      .from("affiliates")
      .select("id")
      .eq("user_id", user.id)
      .maybeSingle();
    if (findErr) throw findErr;
    if (!affiliate) return json({ error: "not_found" }, 404);

    // Build update with only allowed fields
    const update: Record<string, unknown> = { updated_at: new Date().toISOString() };
    if (display_name !== undefined) {
      if (!display_name?.trim()) return json({ error: "invalid_display_name" }, 400);
      update.display_name = display_name.trim();
    }
    if (pix_key !== undefined) update.pix_key = pix_key ?? null;
    if (pix_key_type !== undefined) {
      if (pix_key_type && !PIX_TYPES.has(pix_key_type)) return json({ error: "invalid_pix_key_type" }, 400);
      update.pix_key_type = pix_key_type ?? null;
    }
    if (whatsapp !== undefined) {
      update.whatsapp = typeof whatsapp === "string" ? whatsapp.replace(/\D/g, "").slice(0, 15) || null : null;
    }

    const { error: updateErr } = await supabase
      .from("affiliates")
      .update(update)
      .eq("id", affiliate.id);
    if (updateErr) throw updateErr;

    return json({ success: true });

  } catch (err) {
    console.error("affiliate-self error:", err);
    return json({ error: "internal" }, 500);
  }
});

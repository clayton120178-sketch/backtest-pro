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

// Simple in-memory rate limiter: 20 requests/min per IP
const ipWindow = new Map<string, { count: number; reset: number }>();
function checkRateLimit(ip: string): boolean {
  const now = Date.now();
  const entry = ipWindow.get(ip);
  if (!entry || now > entry.reset) {
    ipWindow.set(ip, { count: 1, reset: now + 60_000 });
    return true;
  }
  if (entry.count >= 20) return false;
  entry.count++;
  return true;
}

serve(async (req) => {
  const cors = corsHeaders(req);
  if (req.method === "OPTIONS") return new Response(null, { headers: cors });

  const ip = req.headers.get("x-forwarded-for")?.split(",")[0]?.trim() ?? "unknown";
  if (!checkRateLimit(ip)) {
    return new Response(JSON.stringify({ error: "rate_limit" }), {
      status: 429, headers: { ...cors, "Content-Type": "application/json" },
    });
  }

  try {
    const body = await req.json();
    const code = (body?.code ?? "").toString().trim();
    if (!code) {
      return new Response(JSON.stringify({ valid: false }), {
        headers: { ...cors, "Content-Type": "application/json" },
      });
    }

    const supabase = createClient(
      Deno.env.get("SUPABASE_URL")!,
      Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!,
    );

    const { data, error } = await supabase.rpc("validate_coupon", { p_code: code });
    if (error) throw error;

    const row = data?.[0];
    if (!row || !row.valid) {
      return new Response(JSON.stringify({ valid: false }), {
        headers: { ...cors, "Content-Type": "application/json" },
      });
    }

    return new Response(JSON.stringify({
      valid: true,
      discount_type: row.discount_type,
      discount_value: row.discount_value,
      applies_to: row.applies_to,
    }), { headers: { ...cors, "Content-Type": "application/json" } });

  } catch (err) {
    console.error("validate-coupon error:", err);
    return new Response(JSON.stringify({ error: "internal" }), {
      status: 500, headers: { ...cors, "Content-Type": "application/json" },
    });
  }
});

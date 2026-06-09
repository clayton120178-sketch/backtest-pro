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

const COUPON_RE = /^[A-Z0-9]{4,20}$/;
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
    const { display_name, pix_key, pix_key_type, coupon_code, terms_accepted } = body;

    if (!terms_accepted) return json({ error: "terms_required" }, 400);
    if (!display_name?.trim()) return json({ error: "display_name_required" }, 400);
    if (pix_key_type && !PIX_TYPES.has(pix_key_type)) return json({ error: "invalid_pix_key_type" }, 400);

    const normalizedCoupon = coupon_code?.toString().toUpperCase().trim();
    if (!normalizedCoupon || !COUPON_RE.test(normalizedCoupon)) {
      return json({ error: "invalid_coupon_code" }, 400);
    }

    // Check if user already is an affiliate
    const { data: existing } = await supabase
      .from("affiliates")
      .select("id")
      .eq("user_id", user.id)
      .maybeSingle();
    if (existing) return json({ error: "already_affiliate" }, 409);

    // Check coupon code uniqueness
    const { data: dupCoupon } = await supabase
      .from("coupons")
      .select("id")
      .eq("code", normalizedCoupon)
      .maybeSingle();
    if (dupCoupon) return json({ error: "coupon_code_taken" }, 409);

    // Read settings for require_approval
    const { data: settings } = await supabase
      .from("affiliate_settings")
      .select("require_approval")
      .eq("id", true)
      .single();
    const status = settings?.require_approval ? "pending" : "active";

    // Insert affiliate
    const { data: affiliate, error: affErr } = await supabase
      .from("affiliates")
      .insert({
        user_id: user.id,
        display_name: display_name.trim(),
        pix_key: pix_key ?? null,
        pix_key_type: pix_key_type ?? null,
        signup_source: "self",
        terms_accepted_at: new Date().toISOString(),
        status,
      })
      .select("id")
      .single();
    if (affErr) throw affErr;

    // Insert coupon linked to affiliate
    const { error: couponErr } = await supabase
      .from("coupons")
      .insert({
        code: normalizedCoupon,
        affiliate_id: affiliate.id,
        discount_type: "percent",
        discount_value: 10,
        applies_to: "all_purchases",
        status: "active",
      });
    if (couponErr) throw couponErr;

    return json({ success: true, affiliate_id: affiliate.id, coupon_code: normalizedCoupon, status });

  } catch (err) {
    console.error("affiliate-signup error:", err);
    return json({ error: "internal" }, 500);
  }
});

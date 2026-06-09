import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

// Internal function — only callable by payment-webhook via service_role key.
// No CORS needed (server-to-server only).

serve(async (req) => {
  if (req.method !== "POST") return new Response("Method Not Allowed", { status: 405 });

  // Verify caller is internal (service_role key in Authorization header)
  const authHeader = req.headers.get("Authorization") ?? "";
  const serviceKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
  if (!authHeader.includes(serviceKey)) {
    return new Response("Forbidden", { status: 403 });
  }

  const supabase = createClient(
    Deno.env.get("SUPABASE_URL")!,
    serviceKey,
  );

  try {
    const input = await req.json() as {
      mp_payment_ref: string;
      user_id: string;
      subscription_id: string | null;
      plan: string;
      cycle: string;
      gross_amount: number;
      discount_amount: number;
      net_amount: number;
      coupon_code?: string | null;
    };

    const {
      mp_payment_ref, user_id, subscription_id,
      plan, cycle, gross_amount, discount_amount, net_amount,
      coupon_code,
    } = input;

    // ── 1. Idempotência ──────────────────────────────────────────────────────
    const { data: existing } = await supabase
      .from("affiliate_commissions")
      .select("id")
      .eq("mp_payment_ref", mp_payment_ref)
      .maybeSingle();
    if (existing) {
      return new Response(JSON.stringify({ commission_created: false }), {
        headers: { "Content-Type": "application/json" },
      });
    }

    // ── 2. Resolver atribuição ───────────────────────────────────────────────
    let affiliate_id: string | null = null;
    let referral_id: string | null = null;
    let coupon_id: string | null = null;

    // 2a. Vínculo já existente (first-touch permanente)
    const { data: existingReferral } = await supabase
      .from("affiliate_referrals")
      .select("id, affiliate_id")
      .eq("referred_user_id", user_id)
      .eq("status", "active")
      .maybeSingle();

    if (existingReferral) {
      affiliate_id = existingReferral.affiliate_id;
      referral_id  = existingReferral.id;
    } else if (coupon_code) {
      // 2b. Novo vínculo via cupom
      const normalizedCode = coupon_code.toString().toUpperCase().trim();

      const { data: coupon } = await supabase
        .from("coupons")
        .select("id, affiliate_id, redemptions_count, max_redemptions, valid_until, valid_from, status")
        .eq("code", normalizedCode)
        .maybeSingle();

      if (!coupon || coupon.status !== "active") {
        console.log("[COMMISSION] Cupom inválido ou inativo:", normalizedCode);
        return new Response(JSON.stringify({ commission_created: false }), {
          headers: { "Content-Type": "application/json" },
        });
      }

      const now = new Date();
      if (coupon.valid_from && new Date(coupon.valid_from) > now) {
        return new Response(JSON.stringify({ commission_created: false }), {
          headers: { "Content-Type": "application/json" },
        });
      }
      if (coupon.valid_until && new Date(coupon.valid_until) < now) {
        return new Response(JSON.stringify({ commission_created: false }), {
          headers: { "Content-Type": "application/json" },
        });
      }
      if (coupon.max_redemptions !== null && coupon.redemptions_count >= coupon.max_redemptions) {
        return new Response(JSON.stringify({ commission_created: false }), {
          headers: { "Content-Type": "application/json" },
        });
      }

      if (!coupon.affiliate_id) {
        // Cupom promocional sem afiliado — sem comissão
        return new Response(JSON.stringify({ commission_created: false }), {
          headers: { "Content-Type": "application/json" },
        });
      }

      // Verificar afiliado ativo
      const { data: aff } = await supabase
        .from("affiliates")
        .select("id, user_id, status")
        .eq("id", coupon.affiliate_id)
        .maybeSingle();

      if (!aff || aff.status !== "active") {
        return new Response(JSON.stringify({ commission_created: false }), {
          headers: { "Content-Type": "application/json" },
        });
      }

      // Self-referral check
      if (aff.user_id === user_id) {
        console.warn("[COMMISSION] Self-referral bloqueado — user:", user_id);
        return new Response(JSON.stringify({ commission_created: false }), {
          headers: { "Content-Type": "application/json" },
        });
      }

      affiliate_id = aff.id;
      coupon_id    = coupon.id;

      // Criar vínculo first-touch
      const { data: newReferral, error: refErr } = await supabase
        .from("affiliate_referrals")
        .insert({
          affiliate_id,
          referred_user_id: user_id,
          coupon_id,
          status: "active",
        })
        .select("id")
        .single();

      if (refErr) {
        // Pode ser race condition (unique constraint em referred_user_id)
        console.error("[COMMISSION] Erro ao criar referral:", refErr);
        return new Response(JSON.stringify({ commission_created: false }), {
          headers: { "Content-Type": "application/json" },
        });
      }
      referral_id = newReferral.id;

      // Incrementar redemptions_count
      await supabase
        .from("coupons")
        .update({ redemptions_count: coupon.redemptions_count + 1 })
        .eq("id", coupon.id);
    }

    if (!affiliate_id || !referral_id) {
      // Sem atribuição — compra sem cupom/vínculo
      return new Response(JSON.stringify({ commission_created: false }), {
        headers: { "Content-Type": "application/json" },
      });
    }

    // ── 3. Resolver tier (já inclui o cliente desta venda, pois subscription
    //       já foi criada com status='active' antes desta chamada) ──────────
    const { data: tierRows, error: tierErr } = await supabase
      .rpc("resolve_affiliate_tier", { p_affiliate: affiliate_id });
    if (tierErr) throw tierErr;

    const tier = tierRows?.[0];
    if (!tier) throw new Error("resolve_affiliate_tier retornou vazio");

    const { tier_name, active_clients, commission_percent } = tier;

    // ── 4. Calcular comissão ────────────────────────────────────────────────
    const commission_amount = Math.round(net_amount * commission_percent / 100 * 100) / 100;

    // ── 5. INSERT comissão ──────────────────────────────────────────────────
    const { error: comErr } = await supabase
      .from("affiliate_commissions")
      .insert({
        affiliate_id,
        referral_id,
        referred_user_id: user_id,
        subscription_id:  subscription_id ?? null,
        plan,
        cycle,
        gross_amount,
        discount_amount,
        net_amount,
        tier_name,
        active_clients,
        commission_rate:   commission_percent,
        commission_amount,
        status:            "pending",
        mp_payment_ref,
      });
    if (comErr) throw comErr;

    console.log(`[COMMISSION] Criada — afiliado: ${affiliate_id} tier: ${tier_name} valor: ${commission_amount}`);

    return new Response(JSON.stringify({
      commission_created: true,
      tier_name,
      commission_amount,
    }), { headers: { "Content-Type": "application/json" } });

  } catch (err) {
    console.error("[COMMISSION] Erro interno:", err);
    return new Response(JSON.stringify({ error: "internal" }), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    });
  }
});

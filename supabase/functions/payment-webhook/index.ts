import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

serve(async (req) => {
  try {
    const body = await req.json();
    console.log("Webhook MP:", JSON.stringify(body));

    if (body.type !== "payment") {
      return new Response("ok", { status: 200 });
    }

    const paymentId = body.data?.id;
    if (!paymentId) return new Response("ok", { status: 200 });

    const MP_TOKEN = Deno.env.get("MP_ACCESS_TOKEN")!;
    const mpRes = await fetch(`https://api.mercadopago.com/v1/payments/${paymentId}`, {
      headers: { "Authorization": `Bearer ${MP_TOKEN}` },
    });
    const payment = await mpRes.json();

    console.log("Payment status:", payment.status, "| ID:", paymentId);

    if (payment.status !== "approved") {
      return new Response("ok", { status: 200 });
    }

    const { user_id, plan, cycle, days } = payment.metadata || {};
    if (!user_id || !plan || !cycle || !days) {
      console.error("Metadata incompleta:", payment.metadata);
      return new Response("ok", { status: 200 });
    }

    const supabase = createClient(
      Deno.env.get("SUPABASE_URL")!,
      Deno.env.get("SERVICE_ROLE_KEY")!
    );

    const { data: existing } = await supabase
      .from("subscriptions")
      .select("id")
      .eq("payment_ref", String(paymentId))
      .single();

    if (existing) {
      console.log("Assinatura já criada para payment_id:", paymentId);
      return new Response("ok", { status: 200 });
    }

    const expiresAt = new Date();
    expiresAt.setDate(expiresAt.getDate() + Number(days));

    const paymentMethod = payment.payment_type_id === "bank_transfer" ? "pix" : "cartao";

    const { error } = await supabase.from("subscriptions").insert({
      user_id,
      plan,
      cycle,
      expires_at: expiresAt.toISOString(),
      status: "active",
      payment_method: paymentMethod,
      payment_ref: String(paymentId),
    });

    if (error) {
      console.error("Erro ao criar assinatura:", error);
      return new Response("error", { status: 500 });
    }

    console.log("Assinatura criada para user:", user_id);
    return new Response("ok", { status: 200 });

  } catch (err) {
    console.error("Webhook error:", err);
    return new Response("error", { status: 500 });
  }
});

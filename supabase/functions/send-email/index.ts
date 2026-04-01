/**
 * send-email — Edge Function central de envio transacional
 *
 * Única função que fala com o Resend. Todas as outras funções
 * e triggers chamam esta. Isso centraliza log, idempotência e
 * substituição futura do provider.
 *
 * Payload esperado:
 * {
 *   user_id:    string (uuid)
 *   email_type: 'welcome' | 'subscription_confirmed' | 'trial_exhausted' | 'subscription_expired'
 *   metadata?:  object  (dados extras dependendo do tipo)
 * }
 *
 * NOTA SOBRE RESEND:
 * Esta função está preparada para o Resend mas usa um stub de log
 * enquanto a conta não estiver ativa. Quando tiver a API key,
 * basta definir o secret RESEND_API_KEY no Supabase e remover
 * o flag RESEND_ENABLED abaixo.
 */

import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

// ─── TIPOS ────────────────────────────────────────────────────────────────────

type EmailType =
  | "welcome"
  | "subscription_confirmed"
  | "trial_exhausted"
  | "subscription_expired";

interface SendEmailPayload {
  user_id:    string;
  email_type: EmailType;
  metadata?:  Record<string, unknown>;
}

interface UserRow {
  email: string;
  name:  string | null;
}

// ─── TEMPLATES ────────────────────────────────────────────────────────────────
// Cada template retorna { subject, html }
// O HTML usa inline styles para máxima compatibilidade com clientes de e-mail.
// Quando tiver identidade visual definida, substituir aqui.

function templateWelcome(name: string): { subject: string; html: string } {
  const firstName = name.split(" ")[0];
  return {
    subject: "Sua conta no Backtest Pro está pronta",
    html: `
<!DOCTYPE html>
<html lang="pt-BR">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#0A0A0F;font-family:'DM Sans',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#0A0A0F;padding:40px 20px;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0" style="background:#12121A;border-radius:12px;border:1px solid #2A2A3C;overflow:hidden;max-width:600px;">

        <!-- Header -->
        <tr><td style="padding:32px 40px 24px;border-bottom:1px solid #2A2A3C;">
          <span style="font-size:22px;font-weight:700;color:#F59E0B;">Backtest</span>
          <span style="font-size:22px;font-weight:700;color:#00D4AA;">·Pro</span>
        </td></tr>

        <!-- Body -->
        <tr><td style="padding:40px 40px 32px;">
          <p style="margin:0 0 16px;font-size:24px;font-weight:700;color:#E8E8ED;">
            Olá, ${firstName}.
          </p>
          <p style="margin:0 0 24px;font-size:16px;line-height:1.7;color:#8888A0;">
            Sua conta no Backtest Pro está criada e pronta para uso.
          </p>
          <p style="margin:0 0 24px;font-size:16px;line-height:1.7;color:#8888A0;">
            Você tem <strong style="color:#E8E8ED;">3 backtests gratuitos</strong> para usar agora.
            Teste os setups que você aprendeu — e descubra, com dados reais, se eles realmente funcionam.
          </p>
          <p style="margin:0 0 32px;font-size:16px;line-height:1.7;color:#8888A0;">
            Sem custo. Sem cartão. Só resultados.
          </p>
          <table cellpadding="0" cellspacing="0">
            <tr><td style="background:#00D4AA;border-radius:8px;">
              <a href="https://backtestpro-app.vercel.app"
                 style="display:inline-block;padding:14px 32px;font-size:15px;font-weight:600;color:#0A0A0F;text-decoration:none;">
                Rodar meu primeiro backtest
              </a>
            </td></tr>
          </table>
        </td></tr>

        <!-- Footer -->
        <tr><td style="padding:24px 40px;border-top:1px solid #2A2A3C;">
          <p style="margin:0;font-size:13px;color:#4A4A5A;line-height:1.6;">
            alphaQuant · Backtest Pro<br>
            Você recebeu este e-mail porque criou uma conta em backtestpro-app.vercel.app
          </p>
        </td></tr>

      </table>
    </td></tr>
  </table>
</body>
</html>`,
  };
}

function templateSubscriptionConfirmed(
  name: string,
  meta: Record<string, unknown>
): { subject: string; html: string } {
  const firstName = name.split(" ")[0];
  const plan      = meta.plan  === "pro" ? "Pro" : "Essencial";
  const cycle     = meta.cycle === "mensal"    ? "mensal"
                  : meta.cycle === "semestral" ? "semestral"
                  : "anual";
  const expiresAt = meta.expires_at
    ? new Date(meta.expires_at as string).toLocaleDateString("pt-BR", {
        day: "2-digit", month: "long", year: "numeric",
      })
    : "—";

  return {
    subject: `Assinatura ${plan} confirmada — bem-vindo ao Backtest Pro`,
    html: `
<!DOCTYPE html>
<html lang="pt-BR">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#0A0A0F;font-family:'DM Sans',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#0A0A0F;padding:40px 20px;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0" style="background:#12121A;border-radius:12px;border:1px solid #2A2A3C;overflow:hidden;max-width:600px;">

        <tr><td style="padding:32px 40px 24px;border-bottom:1px solid #2A2A3C;">
          <span style="font-size:22px;font-weight:700;color:#F59E0B;">Backtest</span>
          <span style="font-size:22px;font-weight:700;color:#00D4AA;">·Pro</span>
        </td></tr>

        <tr><td style="padding:40px 40px 32px;">
          <p style="margin:0 0 8px;font-size:13px;font-weight:600;color:#10B981;letter-spacing:0.08em;text-transform:uppercase;">
            Pagamento confirmado
          </p>
          <p style="margin:0 0 24px;font-size:24px;font-weight:700;color:#E8E8ED;">
            Assinatura ativa, ${firstName}.
          </p>
          <p style="margin:0 0 32px;font-size:16px;line-height:1.7;color:#8888A0;">
            Seu plano <strong style="color:#E8E8ED;">${plan}</strong> (${cycle}) está ativo
            e válido até <strong style="color:#E8E8ED;">${expiresAt}</strong>.
          </p>

          <!-- Card de resumo -->
          <table width="100%" cellpadding="0" cellspacing="0" style="background:#1A1A28;border-radius:8px;border:1px solid #2A2A3C;margin-bottom:32px;">
            <tr>
              <td style="padding:20px 24px;border-right:1px solid #2A2A3C;width:50%;">
                <p style="margin:0 0 4px;font-size:12px;color:#8888A0;text-transform:uppercase;letter-spacing:0.06em;">Plano</p>
                <p style="margin:0;font-size:18px;font-weight:700;color:#00D4AA;">${plan}</p>
              </td>
              <td style="padding:20px 24px;width:50%;">
                <p style="margin:0 0 4px;font-size:12px;color:#8888A0;text-transform:uppercase;letter-spacing:0.06em;">Válido até</p>
                <p style="margin:0;font-size:18px;font-weight:700;color:#E8E8ED;">${expiresAt}</p>
              </td>
            </tr>
          </table>

          <table cellpadding="0" cellspacing="0">
            <tr><td style="background:#00D4AA;border-radius:8px;">
              <a href="https://backtestpro-app.vercel.app"
                 style="display:inline-block;padding:14px 32px;font-size:15px;font-weight:600;color:#0A0A0F;text-decoration:none;">
                Acessar o Backtest Pro
              </a>
            </td></tr>
          </table>
        </td></tr>

        <tr><td style="padding:24px 40px;border-top:1px solid #2A2A3C;">
          <p style="margin:0;font-size:13px;color:#4A4A5A;line-height:1.6;">
            alphaQuant · Backtest Pro<br>
            Guarde este e-mail como comprovante da sua assinatura.
          </p>
        </td></tr>

      </table>
    </td></tr>
  </table>
</body>
</html>`,
  };
}

function templateTrialExhausted(name: string): { subject: string; html: string } {
  const firstName = name.split(" ")[0];
  return {
    subject: "Seus 3 backtests gratuitos acabaram",
    html: `
<!DOCTYPE html>
<html lang="pt-BR">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#0A0A0F;font-family:'DM Sans',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#0A0A0F;padding:40px 20px;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0" style="background:#12121A;border-radius:12px;border:1px solid #2A2A3C;overflow:hidden;max-width:600px;">

        <tr><td style="padding:32px 40px 24px;border-bottom:1px solid #2A2A3C;">
          <span style="font-size:22px;font-weight:700;color:#F59E0B;">Backtest</span>
          <span style="font-size:22px;font-weight:700;color:#00D4AA;">·Pro</span>
        </td></tr>

        <tr><td style="padding:40px 40px 32px;">
          <p style="margin:0 0 24px;font-size:24px;font-weight:700;color:#E8E8ED;">
            ${firstName}, você usou os 3 backtests gratuitos.
          </p>
          <p style="margin:0 0 24px;font-size:16px;line-height:1.7;color:#8888A0;">
            O que você viu até aqui é só o começo. Para continuar testando — e encontrar
            uma estratégia que realmente funcione — você precisa de acesso completo.
          </p>
          <p style="margin:0 0 32px;font-size:16px;line-height:1.7;color:#8888A0;">
            O plano Essencial dá acesso ilimitado a todos os indicadores, ativos e timeframes.
            Por menos do que uma perda no mini índice.
          </p>
          <table cellpadding="0" cellspacing="0">
            <tr><td style="background:#00D4AA;border-radius:8px;">
              <a href="https://backtestpro-app.vercel.app/#pricing"
                 style="display:inline-block;padding:14px 32px;font-size:15px;font-weight:600;color:#0A0A0F;text-decoration:none;">
                Ver planos e assinar
              </a>
            </td></tr>
          </table>
        </td></tr>

        <tr><td style="padding:24px 40px;border-top:1px solid #2A2A3C;">
          <p style="margin:0;font-size:13px;color:#4A4A5A;line-height:1.6;">
            alphaQuant · Backtest Pro
          </p>
        </td></tr>

      </table>
    </td></tr>
  </table>
</body>
</html>`,
  };
}

function templateSubscriptionExpired(
  name: string,
  meta: Record<string, unknown>
): { subject: string; html: string } {
  const firstName = name.split(" ")[0];
  const plan      = meta.plan === "pro" ? "Pro" : "Essencial";
  return {
    subject: "Seu acesso ao Backtest Pro expirou",
    html: `
<!DOCTYPE html>
<html lang="pt-BR">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#0A0A0F;font-family:'DM Sans',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#0A0A0F;padding:40px 20px;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0" style="background:#12121A;border-radius:12px;border:1px solid #2A2A3C;overflow:hidden;max-width:600px;">

        <tr><td style="padding:32px 40px 24px;border-bottom:1px solid #2A2A3C;">
          <span style="font-size:22px;font-weight:700;color:#F59E0B;">Backtest</span>
          <span style="font-size:22px;font-weight:700;color:#00D4AA;">·Pro</span>
        </td></tr>

        <tr><td style="padding:40px 40px 32px;">
          <p style="margin:0 0 24px;font-size:24px;font-weight:700;color:#E8E8ED;">
            Seu plano ${plan} expirou, ${firstName}.
          </p>
          <p style="margin:0 0 24px;font-size:16px;line-height:1.7;color:#8888A0;">
            Seu acesso ao Backtest Pro está suspenso. As suas estratégias salvas e
            o histórico de backtests estão preservados — basta renovar para continuar de onde parou.
          </p>
          <p style="margin:0 0 32px;font-size:16px;line-height:1.7;color:#8888A0;">
            O mercado não para. Suas estratégias precisam ser validadas antes do próximo trade.
          </p>
          <table cellpadding="0" cellspacing="0">
            <tr><td style="background:#00D4AA;border-radius:8px;">
              <a href="https://backtestpro-app.vercel.app/#pricing"
                 style="display:inline-block;padding:14px 32px;font-size:15px;font-weight:600;color:#0A0A0F;text-decoration:none;">
                Renovar acesso
              </a>
            </td></tr>
          </table>
        </td></tr>

        <tr><td style="padding:24px 40px;border-top:1px solid #2A2A3C;">
          <p style="margin:0;font-size:13px;color:#4A4A5A;line-height:1.6;">
            alphaQuant · Backtest Pro
          </p>
        </td></tr>

      </table>
    </td></tr>
  </table>
</body>
</html>`,
  };
}

// ─── DISPATCHER ───────────────────────────────────────────────────────────────

function buildEmail(
  emailType: EmailType,
  user: UserRow,
  metadata: Record<string, unknown>
): { subject: string; html: string } | null {
  const name = user.name ?? user.email.split("@")[0];
  switch (emailType) {
    case "welcome":
      return templateWelcome(name);
    case "subscription_confirmed":
      return templateSubscriptionConfirmed(name, metadata);
    case "trial_exhausted":
      return templateTrialExhausted(name);
    case "subscription_expired":
      return templateSubscriptionExpired(name, metadata);
    default:
      return null;
  }
}

// ─── ENVIO VIA RESEND ─────────────────────────────────────────────────────────

async function sendViaResend(
  to: string,
  subject: string,
  html: string,
  resendKey: string
): Promise<{ id: string } | null> {
  const res = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: {
      "Content-Type":  "application/json",
      "Authorization": `Bearer ${resendKey}`,
    },
    body: JSON.stringify({
      from:    "Backtest Pro <onboarding@resend.dev>",
      to:      [to],
      subject,
      html,
    }),
  });

  if (!res.ok) {
    const err = await res.text();
    console.error("[RESEND] Erro ao enviar:", res.status, err);
    return null;
  }

  return await res.json() as { id: string };
}

// ─── HANDLER PRINCIPAL ────────────────────────────────────────────────────────

serve(async (req) => {
  if (req.method !== "POST") {
    return new Response("Method Not Allowed", { status: 405 });
  }

  // Valida que a chamada veio de dentro do Supabase (service_role)
  const authHeader = req.headers.get("Authorization") ?? "";
  const serviceKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? "";
  if (!authHeader.includes(serviceKey)) {
    console.error("[SECURITY] Chamada não autorizada para send-email");
    return new Response("Unauthorized", { status: 401 });
  }

  let payload: SendEmailPayload;
  try {
    payload = await req.json() as SendEmailPayload;
  } catch {
    return new Response("Bad Request", { status: 400 });
  }

  const { user_id, email_type, metadata = {} } = payload;

  const VALID_TYPES: EmailType[] = [
    "welcome",
    "subscription_confirmed",
    "trial_exhausted",
    "subscription_expired",
  ];

  const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
  if (!user_id || !UUID_RE.test(user_id) || !VALID_TYPES.includes(email_type)) {
    console.error("[SEND-EMAIL] Payload inválido:", payload);
    return new Response("Bad Request", { status: 400 });
  }

  const supabase = createClient(
    Deno.env.get("SUPABASE_URL")!,
    Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!
  );

  // ── Idempotência: já enviamos este tipo para este usuário? ──
  const { data: existingLog } = await supabase
    .from("email_logs")
    .select("id")
    .eq("user_id", user_id)
    .eq("email_type", email_type)
    .eq("status", "sent")
    .maybeSingle();

  if (existingLog) {
    console.log(`[SEND-EMAIL] Já enviado — user:${user_id} type:${email_type} — ignorando`);
    return new Response("ok", { status: 200 });
  }

  // ── Buscar dados do usuário ──
  const { data: user, error: userError } = await supabase
    .from("users")
    .select("email, name")
    .eq("id", user_id)
    .maybeSingle();

  if (userError || !user) {
    console.error("[SEND-EMAIL] Usuário não encontrado:", user_id);
    return new Response("ok", { status: 200 });
  }

  // ── Montar e-mail ──
  const email = buildEmail(email_type, user as UserRow, metadata);
  if (!email) {
    console.error("[SEND-EMAIL] Tipo de e-mail desconhecido:", email_type);
    return new Response("Bad Request", { status: 400 });
  }

  // ── Enviar ou logar (modo stub sem RESEND_API_KEY) ──
  const resendKey = Deno.env.get("RESEND_API_KEY");
  let resendId: string | null = null;
  let status: "sent" | "failed" = "sent";

  if (resendKey) {
    const result = await sendViaResend(user.email, email.subject, email.html, resendKey);
    if (result) {
      resendId = result.id;
      console.log(`[SEND-EMAIL] Enviado via Resend — id:${resendId} user:${user_id} type:${email_type}`);
    } else {
      status = "failed";
      console.error(`[SEND-EMAIL] Falha no envio — user:${user_id} type:${email_type}`);
    }
  } else {
    // Modo stub: loga o e-mail completo para inspeção no Supabase Logs
    console.log(`[SEND-EMAIL][STUB] RESEND_API_KEY não configurada.`);
    console.log(`[SEND-EMAIL][STUB] Para: ${user.email}`);
    console.log(`[SEND-EMAIL][STUB] Assunto: ${email.subject}`);
    console.log(`[SEND-EMAIL][STUB] Tipo: ${email_type}`);
    console.log(`[SEND-EMAIL][STUB] Metadata:`, JSON.stringify(metadata));
    resendId = "stub-" + crypto.randomUUID();
  }

  // ── Registrar no email_logs (mesmo em modo stub) ──
  const { error: logError } = await supabase.from("email_logs").insert({
    user_id,
    email_type,
    status,
    resend_id: resendId,
    metadata:  Object.keys(metadata).length > 0 ? metadata : null,
  });

  if (logError) {
    console.error("[SEND-EMAIL] Erro ao registrar log:", logError);
  }

  return new Response("ok", { status: 200 });
});

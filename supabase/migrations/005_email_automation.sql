-- ═══════════════════════════════════════════════════════════
-- MIGRATION 005 — Email Automation
-- Tabela de log + triggers para disparar e-mails automáticos
-- ═══════════════════════════════════════════════════════════

-- ─── TABELA: email_logs ──────────────────────────────────────────────────────
-- Controla o que já foi enviado para evitar duplicatas em qualquer cenário

CREATE TABLE public.email_logs (
  id          uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id     uuid NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
  email_type  text NOT NULL CHECK (email_type IN (
                 'welcome',
                 'subscription_confirmed',
                 'trial_exhausted',
                 'subscription_expired'
               )),
  sent_at     timestamptz DEFAULT now(),
  status      text NOT NULL DEFAULT 'sent' CHECK (status IN ('sent', 'failed')),
  resend_id   text,
  metadata    jsonb
);

-- Índice composto: a consulta de idempotência sempre filtra por estes dois campos
CREATE UNIQUE INDEX email_logs_user_type_unique
  ON public.email_logs (user_id, email_type)
  WHERE status = 'sent';

-- Índice para queries de auditoria por tipo
CREATE INDEX email_logs_type_idx ON public.email_logs (email_type);

-- RLS: apenas service_role acessa (Edge Functions usam service_role)
ALTER TABLE public.email_logs ENABLE ROW LEVEL SECURITY;

-- Usuário pode ver seu próprio histórico de e-mails (útil para debugging futuro)
CREATE POLICY "Usuário vê seus próprios email_logs"
  ON public.email_logs FOR SELECT USING (auth.uid() = user_id);

-- Apenas service_role pode inserir (as Edge Functions)
GRANT SELECT ON public.email_logs TO authenticated;
GRANT ALL ON public.email_logs TO service_role;


-- ─── TRIGGER: welcome ao criar usuário ──────────────────────────────────────
-- Dispara quando handle_new_user() insere em public.users
-- (que já é disparado pelo trigger on_auth_user_created em auth.users)

CREATE OR REPLACE FUNCTION notify_user_created()
RETURNS trigger AS $$
BEGIN
  PERFORM net.http_post(
    url    := current_setting('app.supabase_url') || '/functions/v1/send-email',
    body   := jsonb_build_object(
                'user_id',    NEW.id,
                'email_type', 'welcome'
              )::text,
    headers := jsonb_build_object(
                 'Content-Type',  'application/json',
                 'Authorization', 'Bearer ' || current_setting('app.service_role_key')
               )
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_user_created_send_email
  AFTER INSERT ON public.users
  FOR EACH ROW EXECUTE FUNCTION notify_user_created();


-- ─── TRIGGER: subscription_confirmed ao criar assinatura ────────────────────
-- Dispara quando payment-webhook insere em public.subscriptions

CREATE OR REPLACE FUNCTION notify_subscription_created()
RETURNS trigger AS $$
BEGIN
  -- Só dispara para assinaturas novas e ativas (não para renovações via UPDATE)
  IF NEW.status = 'active' THEN
    PERFORM net.http_post(
      url    := current_setting('app.supabase_url') || '/functions/v1/send-email',
      body   := jsonb_build_object(
                  'user_id',    NEW.user_id,
                  'email_type', 'subscription_confirmed',
                  'metadata',   jsonb_build_object(
                                  'plan',       NEW.plan,
                                  'cycle',      NEW.cycle,
                                  'expires_at', NEW.expires_at
                                )
                )::text,
      headers := jsonb_build_object(
                   'Content-Type',  'application/json',
                   'Authorization', 'Bearer ' || current_setting('app.service_role_key')
                 )
    );
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_subscription_created_send_email
  AFTER INSERT ON public.subscriptions
  FOR EACH ROW EXECUTE FUNCTION notify_subscription_created();


-- ─── NOTA sobre o trigger de trial_exhausted ────────────────────────────────
-- Não usamos trigger de DB aqui porque requer lógica de contagem + join
-- (verificar se usuário tem assinatura ativa). Isso fica na Edge Function
-- on-backtest-created que é chamada via Database Webhook no Supabase Dashboard.
-- Ver: supabase/functions/on-backtest-created/index.ts


-- ─── CRON: check-expired-subscriptions ──────────────────────────────────────
-- Roda todo dia às 09:00 horário de Brasília (12:00 UTC)
-- Habilitar pg_cron: Extensions > pg_cron no Dashboard do Supabase

SELECT cron.schedule(
  'check-expired-subscriptions',
  '0 12 * * *',
  $$
    SELECT net.http_post(
      url     := current_setting('app.supabase_url') || '/functions/v1/check-expired-subscriptions',
      body    := '{}',
      headers := jsonb_build_object(
                   'Content-Type',  'application/json',
                   'Authorization', 'Bearer ' || current_setting('app.service_role_key')
                 )
    );
  $$
);

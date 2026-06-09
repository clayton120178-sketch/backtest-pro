-- ═══════════════════════════════════════════════════════════
-- MIGRATION 009 — Fix email/cron: substituir GUCs por Vault
-- Causa raiz de P0-1 e P0-2:
--   current_setting('app.supabase_url') e ('app.service_role_key')
--   não ficam disponíveis para pg_cron nem para triggers em todos
--   os contextos. Solução: URL literal (não é segredo) + service key
--   lida do Vault (vault.decrypted_secrets).
-- ═══════════════════════════════════════════════════════════

-- ─── notify_user_created ─────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION notify_user_created()
RETURNS trigger AS $$
DECLARE
  svc text;
BEGIN
  SELECT decrypted_secret INTO svc
  FROM vault.decrypted_secrets WHERE name = 'service_role_key' LIMIT 1;

  IF svc IS NULL THEN
    RAISE WARNING '[notify_user_created] service_role_key ausente no Vault — email não enviado';
    RETURN NEW;
  END IF;

  PERFORM net.http_post(
    url     := 'https://lmrpxtshdiwufbfkaymg.supabase.co/functions/v1/send-email',
    body    := jsonb_build_object('user_id', NEW.id, 'email_type', 'welcome')::text,
    headers := jsonb_build_object(
                 'Content-Type',  'application/json',
                 'Authorization', 'Bearer ' || svc
               )
  );
  RETURN NEW;
EXCEPTION WHEN OTHERS THEN
  RAISE WARNING '[notify_user_created] falha não-fatal: %', SQLERRM;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ─── notify_subscription_created ─────────────────────────────────────────────
CREATE OR REPLACE FUNCTION notify_subscription_created()
RETURNS trigger AS $$
DECLARE
  svc text;
BEGIN
  IF NEW.status != 'active' THEN
    RETURN NEW;
  END IF;

  SELECT decrypted_secret INTO svc
  FROM vault.decrypted_secrets WHERE name = 'service_role_key' LIMIT 1;

  IF svc IS NULL THEN
    RAISE WARNING '[notify_subscription_created] service_role_key ausente no Vault — email não enviado';
    RETURN NEW;
  END IF;

  PERFORM net.http_post(
    url     := 'https://lmrpxtshdiwufbfkaymg.supabase.co/functions/v1/send-email',
    body    := jsonb_build_object(
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
                 'Authorization', 'Bearer ' || svc
               )
  );
  RETURN NEW;
EXCEPTION WHEN OTHERS THEN
  RAISE WARNING '[notify_subscription_created] falha não-fatal: %', SQLERRM;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ─── Reagendar cron com mesmo padrão ─────────────────────────────────────────
SELECT cron.unschedule('check-expired-subscriptions');

SELECT cron.schedule(
  'check-expired-subscriptions',
  '0 12 * * *',
  $$
    SELECT net.http_post(
      url     := 'https://lmrpxtshdiwufbfkaymg.supabase.co/functions/v1/check-expired-subscriptions',
      body    := '{}',
      headers := jsonb_build_object(
                   'Content-Type',  'application/json',
                   'Authorization', 'Bearer ' || (
                     SELECT decrypted_secret FROM vault.decrypted_secrets
                     WHERE name = 'service_role_key' LIMIT 1
                   )
                 )
    );
  $$
);

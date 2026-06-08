-- ═══════════════════════════════════════════════════════════
-- MIGRATION 011 — Agendar cron de reconciliação de pagamentos
-- Roda a cada 15 minutos para fechar Pix aprovados que o
-- webhook não entregou.
-- ═══════════════════════════════════════════════════════════

SELECT cron.schedule(
  'reconcile-payments',
  '*/15 * * * *',
  $$
    SELECT net.http_post(
      url     := 'https://lmrpxtshdiwufbfkaymg.supabase.co/functions/v1/reconcile-payments',
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

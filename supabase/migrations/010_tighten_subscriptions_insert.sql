-- ═══════════════════════════════════════════════════════════
-- MIGRATION 010 — Remover policy INSERT permissiva em subscriptions
-- A policy "Usuário insere suas assinaturas" não tem WITH CHECK e
-- seria re-ativada se o GRANT INSERT fosse concedido a authenticated.
-- service_role já tem GRANT ALL — não precisamos de policy de INSERT
-- para usuários.
-- ═══════════════════════════════════════════════════════════

DROP POLICY IF EXISTS "Usuário insere suas assinaturas" ON public.subscriptions;

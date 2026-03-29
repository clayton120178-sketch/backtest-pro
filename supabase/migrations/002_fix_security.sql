-- ═══════════════════════════════════════════════════════════
-- MIGRAÇÃO 002 — Correções de Segurança
-- Executar via SQL Editor do Supabase Dashboard
-- ═══════════════════════════════════════════════════════════

-- ───────────────────────────────────────────────────────────
-- 1. REVOGAR GRANTS ABERTOS EM SUBSCRIPTIONS
--    (criados na migração 001 como workaround do RLS off)
-- ───────────────────────────────────────────────────────────
REVOKE INSERT, UPDATE ON public.subscriptions FROM anon;
REVOKE INSERT, UPDATE ON public.subscriptions FROM authenticated;
-- SELECT mantido para authenticated (via RLS abaixo)
-- anon não deve ler subscriptions
REVOKE SELECT ON public.subscriptions FROM anon;

-- ───────────────────────────────────────────────────────────
-- 2. HABILITAR RLS EM SUBSCRIPTIONS
-- ───────────────────────────────────────────────────────────
ALTER TABLE public.subscriptions ENABLE ROW LEVEL SECURITY;

-- Usuário autenticado só lê suas próprias assinaturas
CREATE POLICY "sub_select_own"
  ON public.subscriptions
  FOR SELECT
  USING (auth.uid() = user_id);

-- INSERT e UPDATE APENAS via service_role (Edge Functions)
-- Usuários comuns nunca inserem nem alteram assinaturas diretamente
-- (sem policy de INSERT/UPDATE para authenticated = bloqueado por RLS)

-- ───────────────────────────────────────────────────────────
-- 3. CORRIGIR CONSTRAINT payment_method
--    O código inseria 'cartao_debito' mas a constraint só aceitava
--    'pix' e 'cartao' — causava falha silenciosa
-- ───────────────────────────────────────────────────────────
ALTER TABLE public.subscriptions
  DROP CONSTRAINT IF EXISTS subscriptions_payment_method_check;

ALTER TABLE public.subscriptions
  ADD CONSTRAINT subscriptions_payment_method_check
  CHECK (payment_method IN ('pix', 'cartao', 'cartao_debito'));

-- ───────────────────────────────────────────────────────────
-- 4. ÍNDICE EM payment_ref (idempotência no webhook)
--    Garante que o webhook não cria duas assinaturas pro mesmo
--    payment_id mesmo em race conditions
-- ───────────────────────────────────────────────────────────
CREATE UNIQUE INDEX IF NOT EXISTS idx_subscriptions_payment_ref
  ON public.subscriptions (payment_ref)
  WHERE payment_ref IS NOT NULL;

-- ───────────────────────────────────────────────────────────
-- 5. ÍNDICE EM user_id + status + expires_at
--    Para a query de verificação de assinatura ativa ser rápida
-- ───────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_subscriptions_user_active
  ON public.subscriptions (user_id, status, expires_at DESC)
  WHERE status = 'active';

-- ───────────────────────────────────────────────────────────
-- 6. BACKTESTS — ADICIONAR POLICY DE DELETE (usuário apaga os seus)
--    e bloquear UPDATE (resultado só é gravado pelo backend)
-- ───────────────────────────────────────────────────────────
CREATE POLICY "bt_delete_own"
  ON public.backtests
  FOR DELETE
  USING (auth.uid() = user_id);

-- ───────────────────────────────────────────────────────────
-- 7. USERS — BLOQUEAR DELETE por usuário comum
--    (deleção de conta deve ser feita via Edge Function)
-- ───────────────────────────────────────────────────────────
-- Já existe: SELECT e UPDATE. Sem policy de DELETE = bloqueado. OK.

-- ───────────────────────────────────────────────────────────
-- VERIFICAÇÃO FINAL — deve listar as policies criadas
-- ───────────────────────────────────────────────────────────
-- SELECT tablename, policyname, cmd, qual
-- FROM pg_policies
-- WHERE schemaname = 'public'
-- ORDER BY tablename, cmd;

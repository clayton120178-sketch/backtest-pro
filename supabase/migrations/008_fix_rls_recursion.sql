-- ═══════════════════════════════════════════════════════════
-- MIGRATION 008 — Corrige RLS recursivo + view acesso_status
-- Executar via Supabase Dashboard > SQL Editor
-- ═══════════════════════════════════════════════════════════

-- ───────────────────────────────────────────────────────────
-- 1. Função is_admin() com SECURITY DEFINER
--    Bypassa o RLS para verificar role sem recursão infinita.
-- ───────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION public.is_admin()
RETURNS boolean AS $$
  SELECT EXISTS (
    SELECT 1 FROM public.users
    WHERE id = auth.uid() AND role = 'admin'
  );
$$ LANGUAGE sql SECURITY DEFINER STABLE;

GRANT EXECUTE ON FUNCTION public.is_admin() TO authenticated;
GRANT EXECUTE ON FUNCTION public.is_admin() TO anon;

-- ───────────────────────────────────────────────────────────
-- 2. Corrigir policy recursiva em USERS
--    A policy anterior consultava public.users dentro de si mesma
-- ───────────────────────────────────────────────────────────
DROP POLICY IF EXISTS "admin_select_all_users"   ON public.users;
DROP POLICY IF EXISTS "Usuário vê apenas seus próprios dados" ON public.users;
DROP POLICY IF EXISTS "user_or_admin_select"     ON public.users;

CREATE POLICY "user_select"
  ON public.users FOR SELECT
  USING (auth.uid() = id OR public.is_admin());

-- ───────────────────────────────────────────────────────────
-- 3. Corrigir policy recursiva em SUBSCRIPTIONS
-- ───────────────────────────────────────────────────────────
DROP POLICY IF EXISTS "admin_select_all_subscriptions" ON public.subscriptions;
DROP POLICY IF EXISTS "sub_select_own" ON public.subscriptions;

CREATE POLICY "sub_select"
  ON public.subscriptions FOR SELECT
  USING (auth.uid() = user_id OR public.is_admin());

-- ───────────────────────────────────────────────────────────
-- 4. Corrigir policy recursiva em BACKTESTS
-- ───────────────────────────────────────────────────────────
DROP POLICY IF EXISTS "admin_select_all_backtests" ON public.backtests;
DROP POLICY IF EXISTS "Usuário vê apenas seus backtests" ON public.backtests;

CREATE POLICY "bt_select"
  ON public.backtests FOR SELECT
  USING (auth.uid() = user_id OR public.is_admin());

-- ───────────────────────────────────────────────────────────
-- 5. VIEW acesso_status
--    Unifica users + subscriptions numa view consultável
--    pelo frontend via db.from('acesso_status')
-- ───────────────────────────────────────────────────────────
DROP VIEW IF EXISTS public.acesso_status;

CREATE OR REPLACE VIEW public.acesso_status
WITH (security_invoker = true)
AS
SELECT
  u.id,
  u.email,
  u.name,
  u.role,
  u.whatsapp,
  CASE
    WHEN u.role = 'admin'     THEN 'admin'
    WHEN s.id IS NOT NULL     THEN s.plan
    ELSE NULL
  END AS tipo_acesso,
  CASE
    WHEN u.role = 'admin'     THEN 'ativo'
    WHEN s.id IS NOT NULL     THEN 'ativo'
    ELSE 'trial'
  END AS status,
  s.expires_at   AS acesso_anual_fim,
  NULL::timestamptz AS trial_fim
FROM public.users u
LEFT JOIN public.subscriptions s
  ON  s.user_id   = u.id
  AND s.status    = 'active'
  AND s.expires_at > now()
ORDER BY s.expires_at DESC NULLS LAST;

-- A view usa security_invoker, então o acesso é controlado
-- pelas policies das tabelas subjacentes (já corrigidas acima).
-- Garante que cada user só enxerga o próprio row.
GRANT SELECT ON public.acesso_status TO authenticated;

-- ───────────────────────────────────────────────────────────
-- VERIFICAÇÃO
-- ───────────────────────────────────────────────────────────
-- SELECT * FROM public.acesso_status WHERE id = auth.uid();
-- SELECT id, rolname FROM pg_roles WHERE rolname IN ('anon','authenticated');

-- ═══════════════════════════════════════════════════════════
-- MIGRATION 006 — Admin Role + Policies + Dashboard Functions
-- Executar via Supabase Dashboard > SQL Editor
-- ═══════════════════════════════════════════════════════════

-- 1. Adicionar coluna role na tabela users
ALTER TABLE public.users
  ADD COLUMN IF NOT EXISTS role text DEFAULT 'user'
  CHECK (role IN ('user', 'admin'));

-- 2. Setar admins (substituir pelos emails reais do Auth > Users)
-- UPDATE public.users SET role = 'admin' WHERE email IN ('clayton@...', 'ivan@...');

-- ───────────────────────────────────────────────────────────
-- POLICIES RLS — users
-- ───────────────────────────────────────────────────────────

-- Dropar policy antiga que só permitia SELECT próprio
DROP POLICY IF EXISTS "Usuário vê apenas seus próprios dados" ON public.users;

-- Nova policy: user vê só ele mesmo; admin vê todos
CREATE POLICY "admin_select_all_users"
  ON public.users FOR SELECT
  USING (
    auth.uid() = id
    OR EXISTS (
      SELECT 1 FROM public.users u2
      WHERE u2.id = auth.uid() AND u2.role = 'admin'
    )
  );

-- ───────────────────────────────────────────────────────────
-- POLICIES RLS — backtests
-- ───────────────────────────────────────────────────────────

DROP POLICY IF EXISTS "Usuário vê apenas seus backtests" ON public.backtests;

CREATE POLICY "admin_select_all_backtests"
  ON public.backtests FOR SELECT
  USING (
    auth.uid() = user_id
    OR EXISTS (
      SELECT 1 FROM public.users u
      WHERE u.id = auth.uid() AND u.role = 'admin'
    )
  );

-- ───────────────────────────────────────────────────────────
-- POLICIES RLS — subscriptions
-- ───────────────────────────────────────────────────────────

DROP POLICY IF EXISTS "sub_select_own" ON public.subscriptions;

CREATE POLICY "admin_select_all_subscriptions"
  ON public.subscriptions FOR SELECT
  USING (
    auth.uid() = user_id
    OR EXISTS (
      SELECT 1 FROM public.users u
      WHERE u.id = auth.uid() AND u.role = 'admin'
    )
  );

-- ═══════════════════════════════════════════════════════════
-- FUNÇÕES SQL — Dashboard admin (SECURITY DEFINER)
-- ═══════════════════════════════════════════════════════════

CREATE OR REPLACE FUNCTION admin_ranking_assets(
  p_date_from timestamptz DEFAULT now() - interval '30 days',
  p_date_to   timestamptz DEFAULT now()
)
RETURNS TABLE(asset text, count bigint) AS $$
BEGIN
  RETURN QUERY
  SELECT config->>'asset', COUNT(*)
  FROM public.backtests
  WHERE status = 'completed'
    AND created_at BETWEEN p_date_from AND p_date_to
    AND config->>'asset' IS NOT NULL
  GROUP BY config->>'asset'
  ORDER BY count DESC;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE FUNCTION admin_ranking_timeframes(
  p_date_from timestamptz DEFAULT now() - interval '30 days',
  p_date_to   timestamptz DEFAULT now()
)
RETURNS TABLE(tf text, count bigint) AS $$
BEGIN
  RETURN QUERY
  SELECT config->>'tf', COUNT(*)
  FROM public.backtests
  WHERE status = 'completed'
    AND created_at BETWEEN p_date_from AND p_date_to
    AND config->>'tf' IS NOT NULL
  GROUP BY config->>'tf'
  ORDER BY count DESC;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE FUNCTION admin_ranking_indicators(
  p_date_from timestamptz DEFAULT now() - interval '30 days',
  p_date_to   timestamptz DEFAULT now()
)
RETURNS TABLE(indicator text, count bigint) AS $$
BEGIN
  RETURN QUERY
  SELECT cond->>'indicator', COUNT(*)
  FROM public.backtests,
    jsonb_array_elements(config->'conditions') AS cond
  WHERE status = 'completed'
    AND created_at BETWEEN p_date_from AND p_date_to
    AND jsonb_array_length(config->'conditions') > 0
  GROUP BY cond->>'indicator'
  ORDER BY count DESC;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE FUNCTION admin_ranking_entry_types(
  p_date_from timestamptz DEFAULT now() - interval '30 days',
  p_date_to   timestamptz DEFAULT now()
)
RETURNS TABLE(entry_type text, count bigint) AS $$
BEGIN
  RETURN QUERY
  SELECT config->>'entryType', COUNT(*)
  FROM public.backtests
  WHERE status = 'completed'
    AND created_at BETWEEN p_date_from AND p_date_to
    AND config->>'entryType' IS NOT NULL
  GROUP BY config->>'entryType'
  ORDER BY count DESC;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE FUNCTION admin_ranking_stop_types(
  p_date_from timestamptz DEFAULT now() - interval '30 days',
  p_date_to   timestamptz DEFAULT now()
)
RETURNS TABLE(stop_type text, count bigint) AS $$
BEGIN
  RETURN QUERY
  SELECT config->>'stopType', COUNT(*)
  FROM public.backtests
  WHERE status = 'completed'
    AND created_at BETWEEN p_date_from AND p_date_to
    AND config->>'stopType' IS NOT NULL
  GROUP BY config->>'stopType'
  ORDER BY count DESC;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE FUNCTION admin_ranking_tp_types(
  p_date_from timestamptz DEFAULT now() - interval '30 days',
  p_date_to   timestamptz DEFAULT now()
)
RETURNS TABLE(tp_type text, count bigint) AS $$
BEGIN
  RETURN QUERY
  SELECT config->>'tpType', COUNT(*)
  FROM public.backtests
  WHERE status = 'completed'
    AND created_at BETWEEN p_date_from AND p_date_to
    AND config->>'tpType' IS NOT NULL
  GROUP BY config->>'tpType'
  ORDER BY count DESC;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE FUNCTION admin_ranking_directions(
  p_date_from timestamptz DEFAULT now() - interval '30 days',
  p_date_to   timestamptz DEFAULT now()
)
RETURNS TABLE(direction text, count bigint) AS $$
BEGIN
  RETURN QUERY
  SELECT config->>'direction', COUNT(*)
  FROM public.backtests
  WHERE status = 'completed'
    AND created_at BETWEEN p_date_from AND p_date_to
    AND config->>'direction' IS NOT NULL
  GROUP BY config->>'direction'
  ORDER BY count DESC;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE FUNCTION admin_ranking_trade_windows(
  p_date_from timestamptz DEFAULT now() - interval '30 days',
  p_date_to   timestamptz DEFAULT now()
)
RETURNS TABLE(window_start text, window_end text, count bigint) AS $$
BEGIN
  RETURN QUERY
  SELECT config->>'tStart', config->>'tEnd', COUNT(*)
  FROM public.backtests
  WHERE status = 'completed'
    AND created_at BETWEEN p_date_from AND p_date_to
    AND config->>'tStart' IS NOT NULL
  GROUP BY config->>'tStart', config->>'tEnd'
  ORDER BY count DESC
  LIMIT 20;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE FUNCTION admin_ranking_trailing(
  p_date_from timestamptz DEFAULT now() - interval '30 days',
  p_date_to   timestamptz DEFAULT now()
)
RETURNS TABLE(trailing_used boolean, count bigint) AS $$
BEGIN
  RETURN QUERY
  SELECT (config->>'trailing')::boolean, COUNT(*)
  FROM public.backtests
  WHERE status = 'completed'
    AND created_at BETWEEN p_date_from AND p_date_to
  GROUP BY (config->>'trailing')::boolean
  ORDER BY count DESC;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE FUNCTION admin_user_activity(
  p_date_from timestamptz DEFAULT now() - interval '30 days',
  p_date_to   timestamptz DEFAULT now()
)
RETURNS TABLE(
  user_id uuid, email text, name text,
  backtest_count bigint, last_backtest timestamptz
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    u.id, u.email, u.name,
    COUNT(b.id) AS backtest_count,
    MAX(b.completed_at) AS last_backtest
  FROM public.users u
  LEFT JOIN public.backtests b
    ON b.user_id = u.id
    AND b.status = 'completed'
    AND b.created_at BETWEEN p_date_from AND p_date_to
  GROUP BY u.id, u.email, u.name
  ORDER BY backtest_count DESC;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- GRANTs para authenticated poder chamar via RPC
GRANT EXECUTE ON FUNCTION admin_ranking_assets TO authenticated;
GRANT EXECUTE ON FUNCTION admin_ranking_timeframes TO authenticated;
GRANT EXECUTE ON FUNCTION admin_ranking_indicators TO authenticated;
GRANT EXECUTE ON FUNCTION admin_ranking_entry_types TO authenticated;
GRANT EXECUTE ON FUNCTION admin_ranking_stop_types TO authenticated;
GRANT EXECUTE ON FUNCTION admin_ranking_tp_types TO authenticated;
GRANT EXECUTE ON FUNCTION admin_ranking_directions TO authenticated;
GRANT EXECUTE ON FUNCTION admin_ranking_trade_windows TO authenticated;
GRANT EXECUTE ON FUNCTION admin_ranking_trailing TO authenticated;
GRANT EXECUTE ON FUNCTION admin_user_activity TO authenticated;

-- ═══════════════════════════════════════════════════════════
-- VERIFICAÇÃO
-- ═══════════════════════════════════════════════════════════
-- SELECT tablename, policyname, cmd FROM pg_policies WHERE schemaname = 'public' ORDER BY tablename, cmd;
-- SELECT routine_name FROM information_schema.routines WHERE routine_schema = 'public' AND routine_name LIKE 'admin_%';

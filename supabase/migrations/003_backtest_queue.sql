-- =====================================================================
-- MIGRACAO 003 - Backtest Queue (worker VPS)
-- Executar via SQL Editor do Supabase Dashboard
-- =====================================================================

-- 1. Adicionar checksum para cache lookup (evita re-rodar backtests identicos)
ALTER TABLE public.backtests
  ADD COLUMN IF NOT EXISTS checksum text;

-- 2. Adicionar campos do worker
ALTER TABLE public.backtests
  ADD COLUMN IF NOT EXISTS worker_id text,           -- ID da VPS que pegou o job
  ADD COLUMN IF NOT EXISTS started_at timestamptz,   -- Quando o worker comecou
  ADD COLUMN IF NOT EXISTS error text,               -- Mensagem de erro se failed
  ADD COLUMN IF NOT EXISTS elapsed_ms integer;        -- Tempo de execucao em ms

-- 3. Indice no checksum para cache lookup rapido
CREATE INDEX IF NOT EXISTS idx_backtests_checksum
  ON public.backtests (checksum)
  WHERE checksum IS NOT NULL AND status = 'completed';

-- 4. Indice para o worker buscar jobs pendentes
CREATE INDEX IF NOT EXISTS idx_backtests_queued
  ON public.backtests (created_at ASC)
  WHERE status = 'queued';

-- 5. Policy para service_role atualizar backtests (worker usa service_role key)
-- O worker precisa UPDATE em status, result, completed_at, worker_id, started_at, error, elapsed_ms
-- service_role ja tem bypass de RLS, entao nao precisa de policy adicional.

-- 6. Funcao para claim de job (atomica, evita race condition entre workers)
CREATE OR REPLACE FUNCTION claim_backtest_job(p_worker_id text)
RETURNS uuid AS $$
DECLARE
  v_id uuid;
BEGIN
  SELECT id INTO v_id
  FROM public.backtests
  WHERE status = 'queued'
  ORDER BY created_at ASC
  LIMIT 1
  FOR UPDATE SKIP LOCKED;

  IF v_id IS NULL THEN
    RETURN NULL;
  END IF;

  UPDATE public.backtests
  SET status = 'running',
      worker_id = p_worker_id,
      started_at = now()
  WHERE id = v_id;

  RETURN v_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 7. Funcao para cache lookup por checksum
-- Retorna o result mais recente de um backtest completado com mesmo checksum
CREATE OR REPLACE FUNCTION lookup_backtest_cache(p_checksum text)
RETURNS jsonb AS $$
DECLARE
  v_result jsonb;
BEGIN
  SELECT result INTO v_result
  FROM public.backtests
  WHERE checksum = p_checksum
    AND status = 'completed'
    AND result IS NOT NULL
  ORDER BY completed_at DESC
  LIMIT 1;

  RETURN v_result;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Backtest Pro — Schema Inicial
-- Executado via SQL Editor do Supabase (não via CLI migrations)

-- ═══════════════════════════════════════════════════════════
-- EXTENSÕES
-- ═══════════════════════════════════════════════════════════
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ═══════════════════════════════════════════════════════════
-- TABELAS
-- ═══════════════════════════════════════════════════════════

CREATE TABLE public.users (
  id         uuid PRIMARY KEY REFERENCES auth.users(id),
  email      text NOT NULL,
  name       text,
  created_at timestamptz DEFAULT now()
);

CREATE TABLE public.subscriptions (
  id              uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id         uuid NOT NULL REFERENCES public.users(id),
  plan            text NOT NULL CHECK (plan IN ('essencial', 'pro')),
  cycle           text NOT NULL CHECK (cycle IN ('mensal', 'semestral', 'anual')),
  started_at      timestamptz DEFAULT now(),
  expires_at      timestamptz NOT NULL,
  status          text NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'expired', 'cancelled')),
  payment_method  text CHECK (payment_method IN ('pix', 'cartao')),
  payment_ref     text,
  created_at      timestamptz DEFAULT now()
);

CREATE TABLE public.backtests (
  id           uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id      uuid NOT NULL REFERENCES public.users(id),
  config       jsonb NOT NULL,
  status       text NOT NULL DEFAULT 'queued' CHECK (status IN ('queued', 'running', 'completed', 'failed')),
  result       jsonb,
  created_at   timestamptz DEFAULT now(),
  completed_at timestamptz
);

-- ═══════════════════════════════════════════════════════════
-- TRIGGER: Auto-criar user na tabela public ao signup
-- ═══════════════════════════════════════════════════════════

CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS trigger AS $$
BEGIN
  INSERT INTO public.users (id, email, name)
  VALUES (
    new.id,
    new.email,
    coalesce(new.raw_user_meta_data->>'full_name', split_part(new.email, '@', 1))
  );
  RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION handle_new_user();

-- ═══════════════════════════════════════════════════════════
-- RLS POLICIES
-- ═══════════════════════════════════════════════════════════

-- users: RLS habilitado
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Usuário vê apenas seus próprios dados"
  ON public.users FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Usuário atualiza apenas seus próprios dados"
  ON public.users FOR UPDATE USING (auth.uid() = id);

-- subscriptions: RLS desabilitado (acesso via GRANTs)
ALTER TABLE public.subscriptions DISABLE ROW LEVEL SECURITY;

-- backtests: RLS habilitado
ALTER TABLE public.backtests ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Usuário vê apenas seus backtests"
  ON public.backtests FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Usuário insere seus backtests"
  ON public.backtests FOR INSERT WITH CHECK (auth.uid() = user_id);

-- ═══════════════════════════════════════════════════════════
-- GRANTS (necessários para subscriptions com RLS off)
-- ═══════════════════════════════════════════════════════════

GRANT SELECT, INSERT, UPDATE ON public.subscriptions TO anon;
GRANT SELECT, INSERT, UPDATE ON public.subscriptions TO authenticated;
GRANT SELECT, INSERT, UPDATE ON public.subscriptions TO service_role;

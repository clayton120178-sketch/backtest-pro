-- Backtest Pro — Migration 004: adiciona WhatsApp ao perfil do usuário

-- Adiciona coluna whatsapp na tabela users
ALTER TABLE public.users
  ADD COLUMN IF NOT EXISTS whatsapp text;

-- Atualiza trigger de novo usuário para capturar whatsapp dos metadados
-- (passado via options.data no signUp)
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS trigger AS $$
BEGIN
  INSERT INTO public.users (id, email, name, whatsapp)
  VALUES (
    new.id,
    new.email,
    coalesce(new.raw_user_meta_data->>'full_name', split_part(new.email, '@', 1)),
    new.raw_user_meta_data->>'whatsapp'
  )
  ON CONFLICT (id) DO UPDATE
    SET
      email    = EXCLUDED.email,
      name     = EXCLUDED.name,
      whatsapp = COALESCE(EXCLUDED.whatsapp, public.users.whatsapp);
  RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Policy para permitir UPDATE do próprio whatsapp (já existe policy de UPDATE geral)
-- A policy existente "Usuário atualiza apenas seus próprios dados" já cobre isso.

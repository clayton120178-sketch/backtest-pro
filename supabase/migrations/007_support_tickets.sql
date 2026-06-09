-- ── 007_support_tickets.sql ────────────────────────────────────────────────
-- Tabela de tickets de suporte com RLS e Realtime

CREATE TABLE public.support_tickets (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id       uuid REFERENCES public.users(id) ON DELETE SET NULL,
  user_name     text,
  user_email    text,
  user_plan     text,
  user_whatsapp text NOT NULL,
  category      text NOT NULL,
  conversation  jsonb NOT NULL DEFAULT '[]',
  admin_notes   text,
  status        text NOT NULL DEFAULT 'pending'
                CHECK (status IN ('pending', 'resolved')),
  created_at    timestamptz NOT NULL DEFAULT now(),
  resolved_at   timestamptz,
  resolved_by   uuid REFERENCES public.users(id) ON DELETE SET NULL
);

-- RLS
ALTER TABLE public.support_tickets ENABLE ROW LEVEL SECURITY;

-- Admin visualiza todos os tickets
CREATE POLICY "admin_select_tickets" ON public.support_tickets
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM public.users
      WHERE id = auth.uid() AND role = 'admin'
    )
  );

-- Admin atualiza (notas, status)
CREATE POLICY "admin_update_tickets" ON public.support_tickets
  FOR UPDATE USING (
    EXISTS (
      SELECT 1 FROM public.users
      WHERE id = auth.uid() AND role = 'admin'
    )
  );

-- Inserção apenas via service_role (Edge Function chat-support-escalate)
-- Sem policy de INSERT para anon/authenticated — a Edge Function usa service_role

-- Realtime
ALTER PUBLICATION supabase_realtime ADD TABLE public.support_tickets;

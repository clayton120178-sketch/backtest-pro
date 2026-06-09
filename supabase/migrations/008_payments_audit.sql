-- ═══════════════════════════════════════════════════════════
-- MIGRATION 008 — Tabela payments (auditoria e reconciliação)
-- Fonte de verdade para intenções de pagamento. Permite
-- reconciliar Pix mesmo se o webhook falhar ou não chegar.
-- ═══════════════════════════════════════════════════════════

CREATE TABLE public.payments (
  id              uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id         uuid NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
  mp_payment_id   text UNIQUE,
  plan            text NOT NULL,
  cycle           text NOT NULL,
  amount          numeric(10,2) NOT NULL,
  method          text NOT NULL,
  status          text NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending','approved','rejected','refunded','cancelled','charged_back')),
  subscription_id uuid REFERENCES public.subscriptions(id),
  created_at      timestamptz DEFAULT now(),
  updated_at      timestamptz DEFAULT now()
);

CREATE INDEX idx_payments_user   ON public.payments(user_id);
CREATE INDEX idx_payments_status ON public.payments(status, created_at DESC);

ALTER TABLE public.payments ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Usuário vê seus pagamentos"
  ON public.payments FOR SELECT
  USING (auth.uid() = user_id);

GRANT SELECT ON public.payments TO authenticated;
GRANT ALL    ON public.payments TO service_role;

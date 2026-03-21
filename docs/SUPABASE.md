# Supabase — Infraestrutura do Backtest Pro

## Projeto

- **URL:** `https://lmrpxtshdiwufbfkaymg.supabase.co`
- **Região:** us-east-1
- **Postgres:** 17.6.1
- **Org:** `pjaqsegbmogbetfkwuhm`

## Schema (public)

### Tabela `users`

| Coluna | Tipo | Default | Notas |
|---|---|---|---|
| `id` | uuid | — | PK, FK → auth.users.id |
| `email` | text | — | |
| `name` | text | — | nullable |
| `created_at` | timestamptz | `now()` | nullable |

### Tabela `subscriptions`

| Coluna | Tipo | Default | Constraints |
|---|---|---|---|
| `id` | uuid | `uuid_generate_v4()` | PK |
| `user_id` | uuid | — | FK → users.id |
| `plan` | text | — | CHECK: `essencial`, `pro` |
| `cycle` | text | — | CHECK: `mensal`, `semestral`, `anual` |
| `started_at` | timestamptz | `now()` | nullable |
| `expires_at` | timestamptz | — | |
| `status` | text | `'active'` | CHECK: `active`, `expired`, `cancelled` |
| `payment_method` | text | — | nullable, CHECK: `pix`, `cartao` |
| `payment_ref` | text | — | nullable (ID do pagamento no MP) |
| `created_at` | timestamptz | `now()` | nullable |

**RLS:** Desabilitado (acesso controlado via GRANTs)

### Tabela `backtests`

| Coluna | Tipo | Default | Notas |
|---|---|---|---|
| `id` | uuid | `uuid_generate_v4()` | PK |
| `user_id` | uuid | — | FK → users.id |
| `config` | jsonb | — | Configuração completa da estratégia |
| `status` | text | `'queued'` | CHECK: `queued`, `running`, `completed`, `failed` |
| `result` | jsonb | — | nullable (métricas, equity, trades) |
| `created_at` | timestamptz | `now()` | nullable |
| `completed_at` | timestamptz | — | nullable |

## Trigger

### `on_auth_user_created`

Dispara em INSERT na tabela `auth.users`. Cria automaticamente um registro na tabela `public.users`.

```sql
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
```

## RLS Policies

### `users`
- **RLS:** Habilitado
- `Usuário vê apenas seus próprios dados` — SELECT onde `auth.uid() = id`
- `Usuário atualiza apenas seus próprios dados` — UPDATE onde `auth.uid() = id`

### `subscriptions`
- **RLS:** Desabilitado (GRANTs diretos)
- Policies existem mas RLS está OFF:
  - `Usuário vê apenas suas assinaturas` — SELECT onde `auth.uid() = user_id`
  - `Usuário insere suas assinaturas` — INSERT onde `auth.uid() = user_id`

### `backtests`
- **RLS:** Habilitado
- `Usuário vê apenas seus backtests` — SELECT onde `auth.uid() = user_id`
- `Usuário insere seus backtests` — INSERT onde `auth.uid() = user_id`

## GRANTs

### `subscriptions` (RLS off, acesso via GRANTs)
- `anon`: SELECT, INSERT, UPDATE
- `authenticated`: SELECT, INSERT, UPDATE
- `service_role`: SELECT, INSERT, UPDATE

### `users` e `backtests`
- Acesso via RLS policies (GRANTs padrão do Supabase)

## Edge Functions

### `create-payment`
- **Slug:** `create-payment`
- **JWT Verify:** Desabilitado no gateway (auth feita internamente via `supabase.auth.getUser()`)
- **Função:** Recebe plano/ciclo/método, cria pagamento no Mercado Pago, retorna QR Pix ou status do cartão
- **Código:** [`supabase/functions/create-payment/index.ts`](../supabase/functions/create-payment/index.ts)

### `payment-webhook`
- **Slug:** `payment-webhook`
- **JWT Verify:** Desabilitado (chamado pelo Mercado Pago sem token)
- **Função:** Recebe notificação do MP, verifica pagamento, cria assinatura na tabela `subscriptions`
- **Código:** [`supabase/functions/payment-webhook/index.ts`](../supabase/functions/payment-webhook/index.ts)

## Secrets (Edge Functions)

| Nome | Descrição |
|---|---|
| `SUPABASE_URL` | URL do projeto (automático) |
| `SUPABASE_ANON_KEY` | Chave anon (automático) |
| `SERVICE_ROLE_KEY` | Chave service_role (nome customizado — Supabase bloqueia prefixo `SUPABASE_`) |
| `MP_ACCESS_TOKEN` | Access Token do Mercado Pago (produção) |

## Autenticação

- **Email/senha:** Ativo
- **Google OAuth:** Ativo (configurado via Google Cloud Console)
- **Redirect URI:** `https://lmrpxtshdiwufbfkaymg.supabase.co/auth/v1/callback`

## Nota sobre `subscriptions` RLS

A tabela `subscriptions` tem RLS **desabilitado** intencionalmente. Isso foi necessário porque o frontend faz query direta via REST API com o token do usuário, e a Edge Function `payment-webhook` precisa inserir com `service_role`. Os GRANTs garantem que `anon` e `authenticated` podem SELECT/INSERT/UPDATE.

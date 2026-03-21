# Backtest Pro

**Prove antes de arriscar seu dinheiro.**

Backtest Pro é um produto da [alphaQuant](https://alphaquant.com.br) que permite traders de varejo — sem nenhum conhecimento de programação — testarem se os setups de análise técnica que aprenderam realmente funcionam, usando dados históricos reais.

## Stack

| Componente | Tecnologia | URL |
|---|---|---|
| Frontend | HTML + CSS + JS (single-file) | [backtestpro-app.vercel.app](https://backtestpro-app.vercel.app) |
| Hospedagem | Vercel (deploy automático via GitHub) | — |
| Banco de Dados | Supabase (Postgres 17) | `lmrpxtshdiwufbfkaymg.supabase.co` |
| Autenticação | Supabase Auth (email + Google OAuth) | — |
| Pagamentos | Mercado Pago (Pix + Cartão crédito/débito) | — |
| Motor de Backtest | MT5 Headless (a definir) | — |

## Estrutura do Repositório

```
├── index.html                          # Landing page (marketing, pricing, FAQ)
├── app.html                            # App do backtester (wizard 5 passos, auth, pagamento)
├── README.md                           # Este arquivo
├── .env.example                        # Template de variáveis de ambiente
├── docs/
│   ├── SUPABASE.md                     # Infra Supabase: schema, RLS, edge functions, secrets
│   ├── ARQUITETURA.md                  # Decisões técnicas e arquitetura
│   └── MODELO-NEGOCIO.md              # Planos, pricing, funil
└── supabase/
    ├── migrations/
    │   └── 001_initial_schema.sql      # Schema completo do banco (DDL)
    └── functions/
        ├── create-payment/
        │   └── index.ts                # Edge Function: criar pagamento MP
        └── payment-webhook/
            └── index.ts                # Edge Function: webhook MP
```

## Setup Local

1. Clone o repositório
2. Abra `index.html` ou `app.html` no navegador
3. `app.html` requer conexão com Supabase para auth/pagamento

## Deploy

Automático via Vercel a cada push no `main`.

- **URL de produção:** [backtestpro-app.vercel.app](https://backtestpro-app.vercel.app)
- **Landing page:** `/` → `index.html`
- **Backtester:** `/app.html`
- **Repositório:** [github.com/clayton120178-sketch/backtest-pro](https://github.com/clayton120178-sketch/backtest-pro)
- **Branch:** `main`

Pastas `docs/` e `supabase/` não afetam o deploy — Vercel serve apenas os arquivos estáticos da raiz.

## Documentação

- **[docs/SUPABASE.md](docs/SUPABASE.md)** — Schema, RLS policies, Edge Functions, secrets
- **[docs/ARQUITETURA.md](docs/ARQUITETURA.md)** — Decisões técnicas, stack, fluxos
- **[docs/MODELO-NEGOCIO.md](docs/MODELO-NEGOCIO.md)** — Planos, pricing, gateway de pagamento

# Arquitetura e Decisões Técnicas

## Decisão Fundamental: EA Universal Parametrizado

O Backtest Pro **não gera código**. Usa um EA universal pré-compilado (.ex5) que contém todos os módulos de indicadores, condições e gestão de risco. A interface web gera apenas parâmetros de configuração (JSON) que ativam módulos específicos do EA.

**Zero geração de código. Zero compilação em runtime. Zero ambiguidade.**

## Três Camadas

### Frontend (Vercel)
- `index.html` — Landing page (marketing, pricing, FAQ)
- `app.html` — Aplicação (wizard 5 passos, auth, pagamento, resultado)
- HTML + CSS + JS vanilla, single-file
- Deploy automático via GitHub → Vercel

### Backend / Banco (Supabase)
- Postgres para dados (users, subscriptions, backtests)
- Auth embutido (email + Google OAuth)
- Edge Functions para pagamento (Mercado Pago)
- REST API automática via SDK

### Motor de Backtest (MT5 Headless — a definir)
- MetaTrader 5 em servidor sem interface
- Recebe parâmetros via backend
- Roda Strategy Tester com EA universal
- Retorna resultado estruturado

## Fluxo Completo

```
Login (Supabase Auth)
  → Verifica assinatura (subscriptions)
  → Wizard 5 passos (monta estratégia)
  → JSON de parâmetros
  → Backend configura MT5 + EA universal
  → Strategy Tester roda backtest
  → Resultado → Frontend (equity, métricas, trades)
  → Salvo no Supabase (backtests)
```

## Decisões Tomadas

| Decisão | Motivo |
|---|---|
| EA universal (não geração de código) | Elimina erros de compilação e ambiguidade |
| Supabase (não SQLite) | Vercel é serverless, sem filesystem persistente |
| Cobranças avulsas (não recorrentes) | Simplifica — sem retry, régua de cobrança |
| Mercado Pago (não Hotmart) | Já tem conta, Pix nativo, taxa menor |
| Pix como método principal | 100% aprovação, sem antifraude bloqueando |
| JWT verify desabilitado nas Edge Functions | Auth interna via getUser() + webhook sem token |

## Dependências Críticas Pendentes

1. **MT5 Headless** — VPS Windows, licenciamento MetaQuotes, alternativa com engine Python
2. **EA Universal** — Refatorar bibliotecas MQL5 existentes
3. **Dados históricos** — WIN, WDO, 5+ anos, múltiplos timeframes
4. **API intermediária** — Bridge frontend → MT5 (Node.js ou Edge Functions)

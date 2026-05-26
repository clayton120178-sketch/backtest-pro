# Painel Administrativo — Backtest Pro

> **Arquivo:** `admin.html` (root do projeto)  
> **Acesso:** exclusivo para usuários com `role = 'admin'` no banco de dados  
> **Stack:** HTML + CSS + JS vanilla · Supabase JS v2 · Lightweight Charts v4.1.3

---

## Sumário

1. [Visão Geral](#1-visão-geral)
2. [Controle de Acesso](#2-controle-de-acesso)
3. [Layout e Navegação](#3-layout-e-navegação)
4. [Seletor de Período](#4-seletor-de-período)
5. [Seção — Visão Geral](#5-seção--visão-geral)
6. [Seção — Usuários](#6-seção--usuários)
7. [Seção — Backtests](#7-seção--backtests)
8. [Seção — Rankings](#8-seção--rankings)
9. [Seção — Atividade](#9-seção--atividade)
10. [Cache e Performance](#10-cache-e-performance)
11. [Realtime](#11-realtime)
12. [Banco de Dados](#12-banco-de-dados)
13. [Design System](#13-design-system)
14. [Administradores Cadastrados](#14-administradores-cadastrados)

---

## 1. Visão Geral

O painel admin é uma **single-page application** embutida em `admin.html`. Ele permite monitorar toda a operação do Backtest Pro em tempo real: usuários, backtests, receita estimada e padrões de uso (via curva ABC).

**Fluxo de acesso:**

```
app.html  →  login do usuário
          →  verificarAcesso() consulta acesso_status view
          →  se role = 'admin', exibe botão "Painel Admin" no menu do avatar
          →  clique abre admin.html em nova aba
          →  admin.html verifica sessão + role novamente (double-check)
          →  redireciona para /app.html silenciosamente se não for admin
```

---

## 2. Controle de Acesso

### Função `initAdmin()` — executada no `DOMContentLoaded`

```js
async function initAdmin() {
  const { data: { session } } = await db.auth.getSession();
  if (!session) { window.location.href = '/app.html'; return; }

  const { data: user } = await db.from('users')
    .select('id,email,name,role')
    .eq('id', session.user.id)
    .maybeSingle();

  if (!user || user.role !== 'admin') {
    window.location.href = '/app.html'; return;
  }
  // ... inicializa painel
}
```

| Condição | Comportamento |
|---|---|
| Sem sessão ativa | Redireciona para `/app.html` |
| Usuário sem `role = 'admin'` | Redireciona para `/app.html` |
| Admin válido | Exibe o painel, carrega Visão Geral |

### Botão "Painel Admin" no `app.html`

```html
<!-- Visível apenas quando currentUsuario?.role === 'admin' -->
<button id="avatar-admin-btn" style="display:none"
  onclick="window.open('/admin.html','_blank')">
  Painel Admin
</button>
```

A exibição é controlada em `updateAvatarUI()`:

```js
const adminBtn = document.getElementById('avatar-admin-btn');
if (adminBtn) adminBtn.style.display =
  currentUsuario?.role === 'admin' ? 'flex' : 'none';
```

### Policies RLS relevantes (migration `006_admin_role.sql`)

| Policy | Tabela | Regra |
|---|---|---|
| `admin_select_all_users` | `users` | Admin vê todos; user vê só o próprio |
| `admin_select_all_backtests` | `backtests` | Admin vê todos; user vê só os próprios |
| `admin_select_all_subscriptions` | `subscriptions` | Admin vê todas; user vê só as próprias |

---

## 3. Layout e Navegação

```
┌─────────────────────────────────────────────────────────────┐
│  Header (52px)  —  Backtest Pro [ADMIN]        email / Sair │
├──────────────┬──────────────────────────────────────────────┤
│  Sidebar     │  Content (scrollável)                        │
│  (188px)     │                                              │
│  • Visão     │  [Seletor de Período]                        │
│  • Usuários  │                                              │
│  • Backtests │  <section id="s-overview">                   │
│  • Rankings  │  <section id="s-users">                      │
│  • Atividade │  <section id="s-backtests">                  │
│              │  <section id="s-rankings">                   │
│              │  <section id="s-activity">                   │
└──────────────┴──────────────────────────────────────────────┘
```

### Função `navTo(section)`

- Destroça gráficos da seção anterior (`destroyCharts()`)
- Para o canal realtime se ativo (`stopRealtime()`)
- Oculta todas as `<section>` e exibe a alvo
- Adiciona a classe `section-visible` para fade-in
- Chama `loadSection(name)` que despacha para o loader correto

---

## 4. Seletor de Período

Presente em **todas as seções** via a `.period-bar` fixada no topo do content.

### Presets disponíveis

| Botão | Intervalo |
|---|---|
| Hoje | `new Date(now.toDateString())` até agora |
| 7 dias | últimos 7 dias |
| 30 dias | últimos 30 dias *(padrão ao carregar)* |
| 90 dias | últimos 90 dias |
| Tudo | A partir de `2024-01-01` |

### Range customizado

Dois `<input type="date">` (`#date-from` / `#date-to`) + botão "Aplicar".  
Ao aplicar, há um debounce de **300ms** antes de disparar `onPeriodChange()`.

### `onPeriodChange()`

```js
function onPeriodChange() {
  clearCache();                               // invalida todos os dados em cache
  state.rankingsLoaded = { strategy: false, market: false };
  loadSection(state.activeSection);           // recarrega a seção ativa
}
```

---

## 5. Seção — Visão Geral

**ID:** `s-overview` | **Loader:** `loadOverview()`

### KPIs

| ID | Métrica | Fonte |
|---|---|---|
| `kpi-total` | Total de Usuários | `users` (todos os registros) |
| `kpi-active` | Usuários Ativos | `subscriptions` com `status='active'` e `expires_at > now` |
| `kpi-bts` | Backtests no Período | `backtests` com `status='completed'` no range |
| `kpi-rev` | Receita Estimada | Soma de `PLAN_PRICES[plan]` para todas as assinaturas ativas |

**Preços usados para cálculo de receita:**

```js
const PLAN_PRICES = {
  essencial: 109.9,
  pro:       139.9,
  starter:   109.9,
  advanced:  139.9,
  elite:     159.9
};
```

### Gráficos (Lightweight Charts v4.1.3)

| ID | Dado | Cor |
|---|---|---|
| `chart-signups` | Novos cadastros / dia | `#00D4AA` |
| `chart-bts` | Backtests completados / dia | `#00D4AA` |

Ambos são área (`addAreaSeries`). Série gerada por `aggregateByDay()` que agrupa por `toISODate(created_at)`.

### Tabela de Distribuição por Plano

Exibida abaixo dos gráficos. Para cada plano com ao menos 1 usuário, mostra:
- Badge colorido do plano
- Contagem absoluta
- Barra de progresso proporcional + percentual

Ordem de exibição: `trial → essencial → pro → starter → advanced → elite`

---

## 6. Seção — Usuários

**ID:** `s-users` | **Loader:** `loadUsers(page)`

### Dados carregados (paralelo)

| Query | Cache key | Dado |
|---|---|---|
| `users` | `usr-users` | `id, email, name, created_at` (todos, ordenados por created_at DESC) |
| `subscriptions` | `usr-subs` | `user_id, plan, cycle, expires_at, status` |
| `backtests` | `usr-btcount` | `user_id` onde `status = 'completed'` |

Os três são cruzados em memória para montar o array `state.usersAll`.

### Tabela

| Coluna | Campo |
|---|---|
| Email | `users.email` |
| Nome | `users.name` |
| Cadastro | `users.created_at` (formato `dd/mm/aa`) |
| Plano | Badge derivado de `subscriptions.plan` ou `'trial'` |
| Ciclo | `subscriptions.cycle` (mensal/anual) |
| Expira em | `subscriptions.expires_at` |
| Backtests | Contagem de backtests completados |

### Busca e Paginação

- Campo `#user-search` filtra por email ou nome (case-insensitive, client-side)
- Paginação: **20 registros por página**
- Botões Anterior / Próximo com estado desabilitado quando nos limites
- Filtro atualiza `state.usersFiltered` e reseta para page 0

---

## 7. Seção — Backtests

**ID:** `s-backtests` | **Loader:** `loadBacktests()`

### KPIs

| ID | Métrica |
|---|---|
| `kpi-bt-total` | Total completados no período |
| `kpi-bt-running` | Em andamento (status `queued` ou `running`) |
| `kpi-bt-fail` | Taxa de falha (`failed / total * 100`) |
| `kpi-bt-avg` | Tempo médio de execução (`elapsed_ms`) dos completados |

### Gráfico

- `chart-bt-vol`: Área — volume de backtests completados por dia no período (full-width)

### Feed ao Vivo (últimos 50)

Tabela com os 50 backtests mais recentes (todos os status). Colunas:
- Usuário (email via join `users(email)`)
- Ativo / Timeframe (`config.asset` / `config.tf`)
- Status (badge colorido)
- Tempo de execução (`elapsed_ms`)
- Criado em (data + hora)

Esta tabela é atualizada em tempo real via Supabase Realtime (ver seção 11).

---

## 8. Seção — Rankings

**ID:** `s-rankings` | **Loader:** `loadRankings(tab)`

### Tabs

| Tab | Conteúdo |
|---|---|
| **Estratégia** | Indicadores, Direção, Entrada, Stop Loss, Take Profit, Trailing |
| **Mercado** | Ativos, Timeframes, Janelas Operacionais |

### Componente Curva ABC — `renderRankingABC()`

Implementação da **Análise ABC de Pareto**:

- **A** (verde `#00D4AA`): acumulado ≤ 80% do volume → itens críticos
- **B** (amarelo `#F59E0B`): acumulado 80–95% → itens secundários
- **C** (cinza `#8888A0`): acumulado > 95% → itens residuais

Cada linha exibe:
```
[A/B/C]  [label]  [contagem]  [████░░░░ barra]  [%]
```

### RPC Functions chamadas (tab Estratégia)

| Função | Retorno |
|---|---|
| `admin_ranking_indicators` | `{ indicator, count }` |
| `admin_ranking_directions` | `{ direction, count }` |
| `admin_ranking_entry_types` | `{ entry_type, count }` |
| `admin_ranking_stop_types` | `{ stop_type, count }` |
| `admin_ranking_tp_types` | `{ tp_type, count }` |
| `admin_ranking_trailing` | `{ trailing_used (bool), count }` |

### RPC Functions chamadas (tab Mercado)

| Função | Retorno |
|---|---|
| `admin_ranking_assets` | `{ asset, count }` |
| `admin_ranking_timeframes` | `{ tf, count }` |
| `admin_ranking_trade_windows` | `{ window_start, window_end, count }` — top 20 |

### Mapa de Labels (`LABEL_MAP`)

Traduz chaves internas para labels legíveis na UI:

```js
const LABEL_MAP = {
  RSI: 'RSI / IFR', SMA: 'SMA (Média Simples)', EMA: 'EMA (Média Exp.)',
  MACD: 'MACD', Stoch: 'Estocástico', CCI: 'CCI',
  Bollinger: 'Bandas de Bollinger', VWAP: 'VWAP',
  'WIN$N': 'Mini Índice', 'WDO$N': 'Mini Dólar',
  'breakout': 'Rompimento', 'next_open': 'Abertura do candle',
  'fixed': 'Stop Fixo', 'candle': 'Stop no Candle',
  'rr': 'Ratio R:R', 'fibo': 'Fibonacci',
  'long': 'Long', 'short': 'Short', 'both': 'Long e Short',
  // ... (ver fonte completo)
};
```

### Cache de tabs

`state.rankingsLoaded = { strategy: false, market: false }` — cada tab é carregada apenas uma vez por período. Mudança de período reseta ambas para `false`.

---

## 9. Seção — Atividade

**ID:** `s-activity` | **Loader:** `loadActivity()`

### Fonte de dados

RPC `admin_user_activity(p_date_from, p_date_to)` — retorna:
```
{ user_id, email, name, backtest_count, last_backtest }
```
Ordenado por `backtest_count DESC`.

### KPIs de Ativação

| ID | Métrica |
|---|---|
| `act-k1` | Usuários que rodaram ≥ 1 backtest |
| `act-k2` | Média de backtests por usuário ativo |
| `act-k3` | Taxa de ativação (`usersWithBt / totalUsers`) |
| `act-k4` | Usuários sem nenhum backtest |

### Tabela Ranking de Uso

Top 100 usuários ordenados por volume. Colunas:
- Posição (#)
- Usuário (email)
- Backtests no período
- Último backtest (`fmtRelative`: "há Xmin / Xh / Xd")
- Status (ponto verde "ativo" ou cinza "sem uso")

### Histograma de Distribuição

Buckets de uso agrupados por faixa:

| Faixa | Significado |
|---|---|
| 0 | Nunca usou |
| 1–5 | Uso baixo |
| 6–20 | Uso médio |
| 21–50 | Uso alto |
| 50+ | Power users |

Barras verticais proporcionais ao maior bucket. Renderizado em HTML puro (sem biblioteca de charts).

---

## 10. Cache e Performance

```js
const cache = {};

async function cachedFetch(key, fn, ttl = 60000) {
  const now = Date.now();
  if (cache[key] && now - cache[key].ts < ttl) return cache[key].data;
  const data = await fn();
  cache[key] = { data, ts: now };
  return data;
}

function clearCache() {
  Object.keys(cache).forEach(k => delete cache[k]);
}
```

- **TTL padrão:** 60 segundos
- **Invalidação:** automática ao mudar período (`onPeriodChange()`)
- **Chaves com range no nome** (ex: `bt-period-${from}`) evitam colisões entre períodos distintos

### Queries paralelas

Todas as seções usam `Promise.all([...])` para disparar múltiplas queries simultaneamente, minimizando o tempo de carregamento percebido.

---

## 11. Realtime

Ativo **somente na seção Backtests**. Gerenciado pelo ciclo de vida da navegação.

```js
// Liga ao entrar na seção backtests
function startRealtime() {
  if (state.realtimeChannel) return;
  state.realtimeChannel = db.channel('admin-backtests-live')
    .on('postgres_changes', { event: '*', schema: 'public', table: 'backtests' }, payload => {
      // Atualiza linha existente (UPDATE) ou insere nova linha no topo (INSERT)
    })
    .subscribe();
}

// Desliga ao navegar para outra seção
function stopRealtime() {
  if (state.realtimeChannel) {
    db.removeChannel(state.realtimeChannel);
    state.realtimeChannel = null;
  }
}
```

### Comportamento

| Evento | Ação |
|---|---|
| `UPDATE` | Atualiza badge de status e tempo de execução da linha existente |
| `INSERT` | Adiciona nova linha no topo com animação `row-new`; remove a 51ª linha se ultrapassar 50 |

Um indicador `●` pulsante (`.live-dot`) na tabela sinaliza que o realtime está ativo.

---

## 12. Banco de Dados

### Tabelas consultadas diretamente

| Tabela | Campos usados |
|---|---|
| `public.users` | `id, email, name, role, created_at` |
| `public.backtests` | `id, user_id, config (JSONB), status, elapsed_ms, created_at, completed_at, error` |
| `public.subscriptions` | `id, user_id, plan, cycle, status, expires_at, started_at` |

### Funções RPC (SECURITY DEFINER)

Todas em `public`, com `GRANT EXECUTE TO authenticated`:

| Função | Parâmetros | Descrição |
|---|---|---|
| `admin_ranking_assets` | `p_date_from, p_date_to` | Ativos mais testados |
| `admin_ranking_timeframes` | `p_date_from, p_date_to` | Timeframes mais usados |
| `admin_ranking_indicators` | `p_date_from, p_date_to` | Indicadores mais configurados |
| `admin_ranking_entry_types` | `p_date_from, p_date_to` | Tipos de entrada |
| `admin_ranking_stop_types` | `p_date_from, p_date_to` | Tipos de stop loss |
| `admin_ranking_tp_types` | `p_date_from, p_date_to` | Tipos de take profit |
| `admin_ranking_directions` | `p_date_from, p_date_to` | Direções (long/short/both) |
| `admin_ranking_trade_windows` | `p_date_from, p_date_to` | Janelas operacionais (top 20) |
| `admin_ranking_trailing` | `p_date_from, p_date_to` | Uso de trailing stop |
| `admin_user_activity` | `p_date_from, p_date_to` | Atividade por usuário |

> Todas as funções filtram `status = 'completed'` e usam `created_at BETWEEN p_date_from AND p_date_to`.

### View `acesso_status`

Usada pelo `app.html` para determinar nível de acesso. O campo `role` é retornado e utilizado para exibir/ocultar o botão "Painel Admin".

```sql
SELECT u.id, u.email, u.name,
  CASE WHEN u.role = 'admin' THEN 'admin' ELSE COALESCE(s.plan, 'trial') END AS tipo_acesso,
  u.role,
  CASE
    WHEN u.role = 'admin' THEN 'ativo'
    WHEN s.status = 'active' AND s.expires_at > now() THEN 'ativo'
    ELSE 'trial'
  END AS status
FROM public.users u
LEFT JOIN public.subscriptions s ON ...
```

### Migration aplicada

`supabase/migrations/006_admin_role.sql`:
- `ALTER TABLE public.users ADD COLUMN role text DEFAULT 'user' CHECK (role IN ('user', 'admin'))`
- Drop/Create de 3 policies RLS
- Create/Replace de 10 funções RPC
- GRANTs

---

## 13. Design System

O admin herda os tokens CSS do `app.html` e adiciona a cor de acento `--adm`.

### Tokens exclusivos do admin

```css
--adm:  #00D4AA   /* cor principal do admin (teal) */
--admd: rgba(0,212,170,0.1)  /* background suave */
```

### Tokens compartilhados com app.html

```css
--bg0: #08080B  --bg1: #0F0F14  --bg2: #151519  --bg3: #1C1C22
--bd:  rgba(255,255,255,0.07)
--tx:  #F2F2F6  --txs: #72728A  --txm: #6B6B82
--ac:  #F0A020  (warning/amber)
--pr:  #00BB80  (positivo/verde)
--dg:  #EE3A3A  (negativo/vermelho)
--in:  #7878EE  (info/roxo)
```

### Tipografia

| Fonte | Uso |
|---|---|
| `Syne` (700/800) | Títulos de seção, logo |
| `DM Sans` (300–700) | Corpo, labels, botões |
| `JetBrains Mono` (400–600) | Valores numéricos, KPIs, badges de label |

### Classes de componentes

| Classe | Componente |
|---|---|
| `.kpi-card` | Card de KPI (16×18px padding, border-radius 12px) |
| `.chart-card` | Card de gráfico (height 160px por padrão) |
| `.table-card` | Tabela com header + pagination |
| `.ranking-card` | Card de ranking ABC |
| `.abc-row` | Linha do ranking (grid 5 colunas) |
| `.badge` | Badge de status/plano (inline-flex, 10px, font-weight 800) |
| `.period-btn` | Botão de período preset |
| `.nav-item` | Item da sidebar |

---

## 14. Administradores Cadastrados

| Email | Status |
|---|---|
| `clayton120178@gmail.com` | `role = 'admin'` ✓ |
| `ivans.lins@gmail.com` | `role = 'admin'` ✓ |

Para adicionar novos admins, executar no SQL Editor do Supabase:

```sql
UPDATE public.users
SET role = 'admin'
WHERE email = 'novo-admin@exemplo.com';
```

Para remover um admin:

```sql
UPDATE public.users
SET role = 'user'
WHERE email = 'ex-admin@exemplo.com';
```

---

## Apêndice — Estrutura de Arquivos Relacionados

```
backtest-pro/
├── admin.html                          ← painel admin (este documento)
├── app.html                            ← app principal (contém botão Painel Admin)
├── vercel.json                         ← CSP header para /admin.html
└── supabase/
    └── migrations/
        └── 006_admin_role.sql          ← role column + RLS policies + 10 RPC functions
```

---

*Documento gerado em 26/05/2026. Atualizar sempre que novas seções ou funções RPC forem adicionadas ao painel.*

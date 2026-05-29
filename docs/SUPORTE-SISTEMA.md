# Sistema de Suporte — Backtest Pro

> Documentação técnica do chat de suporte com IA, escalation flow e painel de administração de tickets.

---

## Índice

1. [Visão Geral](#visão-geral)
2. [Arquitetura](#arquitetura)
3. [Banco de Dados](#banco-de-dados)
4. [Edge Functions](#edge-functions)
5. [Chat Widget (app.html)](#chat-widget-apphtml)
6. [Painel Admin (admin.html)](#painel-admin-adminhtml)
7. [Fluxo de Dados](#fluxo-de-dados)
8. [Segurança](#segurança)
9. [Deploy](#deploy)

---

## Visão Geral

O sistema de suporte é composto por três camadas integradas:

| Camada | Descrição |
|--------|-----------|
| **Chat Widget** | Botão fixo no `app.html` com janela flutuante de atendimento |
| **IA (Claude Haiku)** | Responde dúvidas automaticamente usando contexto do usuário e do produto |
| **Escalation Flow** | Quando a IA detecta que o caso exige humano, coleta WhatsApp e salva ticket |
| **Painel Admin** | Seção "Suporte" no `admin.html` com KPIs, tabela de tickets e drawer de atendimento |

---

## Arquitetura

```
app.html (usuário)
  │
  ├─ POST /chat-support          → Claude Haiku (resposta + flag [ESCALONAR])
  │
  └─ POST /chat-support-escalate → INSERT support_tickets (service_role)
                                        │
                                        └─ Realtime → admin.html (badge + tabela ao vivo)
```

**Arquivos envolvidos:**

```
backtest-pro/
├── supabase/
│   ├── functions/
│   │   ├── chat-support/index.ts          ← Edge Function: IA de suporte
│   │   └── chat-support-escalate/index.ts ← Edge Function: salva ticket
│   └── migrations/
│       └── 007_support_tickets.sql        ← Tabela + RLS + Realtime
├── app.html                               ← Chat widget (linhas ~9371–9690)
└── admin.html                             ← Seção Suporte (linhas ~1149–1410)
```

---

## Banco de Dados

### Tabela `support_tickets`

**Migration:** `supabase/migrations/007_support_tickets.sql`

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `id` | `uuid` PK | Gerado automaticamente |
| `user_id` | `uuid` FK → `users.id` | Usuário que abriu o ticket (SET NULL se deletado) |
| `user_name` | `text` | Nome do usuário no momento da abertura |
| `user_email` | `text` | E-mail do usuário |
| `user_plan` | `text` | Plano ativo no momento |
| `user_whatsapp` | `text` NOT NULL | WhatsApp coletado no escalation flow |
| `category` | `text` NOT NULL | Categoria selecionada no chat |
| `conversation` | `jsonb` | Array do histórico completo da conversa |
| `admin_notes` | `text` | Anotações internas do admin |
| `status` | `text` | `pending` \| `resolved` (default: `pending`) |
| `created_at` | `timestamptz` | Data/hora de criação |
| `resolved_at` | `timestamptz` | Data/hora de resolução |
| `resolved_by` | `uuid` FK → `users.id` | Admin que resolveu |

### RLS (Row Level Security)

| Policy | Role | Operação |
|--------|------|----------|
| `admin_select_tickets` | `authenticated` (role = admin) | SELECT |
| `admin_update_tickets` | `authenticated` (role = admin) | UPDATE |
| *(sem policy de INSERT)* | — | INSERT via `service_role` (Edge Function) |

> A inserção é feita exclusivamente pela Edge Function `chat-support-escalate` usando a chave `service_role`, que bypassa RLS.

### Realtime

```sql
ALTER PUBLICATION supabase_realtime ADD TABLE public.support_tickets;
```

Eventos escutados no `admin.html`: `INSERT` (novo ticket) e `UPDATE` (ticket resolvido).

### Grants necessários

Aplicados manualmente após a criação da tabela (grants não são automáticos para tabelas criadas por migration):

```sql
GRANT USAGE ON SCHEMA public TO service_role, authenticated, anon;
GRANT ALL ON TABLE public.support_tickets TO service_role;
GRANT SELECT, UPDATE ON TABLE public.support_tickets TO authenticated;
```

---

## Edge Functions

### `chat-support`

**Arquivo:** `supabase/functions/chat-support/index.ts`
**JWT:** não requerido (`--no-verify-jwt`)
**Autenticação:** via `Authorization` header → `supabase.auth.getUser()`

#### Payload (POST)

```typescript
{
  user_id: string;
  user_name: string;
  user_email: string;
  user_plan: string;
  user_backtests_used: number;
  user_backtests_limit: number;
  category: string;
  message: string;
  conversation_history: Array<{ role: "user" | "assistant"; content: string }>;
}
```

#### Response

```typescript
{
  message: string;    // Resposta da IA (sem o marcador [ESCALONAR])
  escalate: boolean;  // true quando a IA decidiu escalonar
}
```

#### Modelo de IA

- **Modelo:** `claude-haiku-4-5-20251001`
- **max_tokens:** 512
- **System prompt:** inclui contexto do produto, planos, indicadores, glossário de métricas e protocolos de atendimento
- **Detecção de escalation:** a IA inclui `[ESCALONAR]` ao final da resposta quando decide escalonar; a string é removida antes de retornar ao cliente

#### Categorias disponíveis no chat

- Problema técnico / backtest travado
- Dúvida sobre o produto
- Pagamento e planos
- Solicitar reembolso ou estorno
- Outro assunto

#### Quando escalonar imediatamente (sem protocolo)

- Pagamento realizado mas acesso não liberado
- Solicitação de reembolso ou estorno
- Usuário claramente insatisfeito
- Dúvida jurídica ou contratual

#### Protocolo para backtest travado (5 passos)

1. Perguntar se houve erro ou timeout
2. Verificar histórico (pode ter sido problema de exibição)
3. Testar em aba anônima
4. Simplificar a estratégia
5. Escalonar apenas após todos os passos falharem

---

### `chat-support-escalate`

**Arquivo:** `supabase/functions/chat-support-escalate/index.ts`
**JWT:** não requerido (`--no-verify-jwt`)
**Autenticação:** via `Authorization` header → `supabase.auth.getUser()`

#### Payload (POST)

```typescript
{
  user_id: string;
  user_name: string;
  user_email: string;
  user_plan: string;
  user_whatsapp: string;
  category: string;
  conversation_history: Array<{ role: string; content: string }>;
}
```

#### Response (sucesso)

```json
{ "success": true }
```

#### Lógica

1. Valida `Authorization` header
2. Faz parse do payload
3. Autentica sessão via `supabaseAnon.auth.getUser()`
4. Verifica que `body.user_id === user.id` (evita spoofing)
5. Valida campos obrigatórios (`user_whatsapp`, `category`)
6. Insere em `support_tickets` usando cliente `service_role` (bypassa RLS)

---

## Chat Widget (app.html)

**Localização:** linhas ~9371–9690 (HTML + IIFE script) + linhas ~561–597 (CSS)

### HTML

```html
<!-- Botão flutuante -->
<button id="chat-btn" onclick="chatToggle()">...</button>

<!-- Janela do chat -->
<div id="chat-window">
  <div class="chat-header">
    <span class="chat-header-title">Suporte Backtest Pro</span>
    <button id="chat-new-btn" onclick="chatReset()" style="display:none">↺ Nova conversa</button>
    <button onclick="chatToggle()">✕</button>
  </div>
  <div class="chat-msgs" id="chat-msgs"></div>
  <div class="chat-footer" id="chat-footer">
    <textarea id="chat-input" ...></textarea>
    <button id="chat-send" onclick="chatSend()">...</button>
  </div>
</div>
```

### Funções JavaScript (IIFE)

| Função | Descrição |
|--------|-----------|
| `chatReveal()` | Exibe o botão `#chat-btn` (chamada após login bem-sucedido em `verificarAcesso()`) |
| `chatToggle()` | Abre/fecha a janela; chama `chatInit()` na primeira abertura |
| `chatInit()` | Exibe saudação e lista de categorias |
| `chatShowCategories()` | Renderiza botões de categoria na área de mensagens |
| `chatSelectCategory(cat)` | Registra categoria, exibe botão "Nova conversa" e envia à API |
| `chatSend()` | Lê o input, adiciona bubble do usuário e chama `chatSendToAPI()` |
| `chatSendToAPI(message)` | POST para `/chat-support`; se `escalate: true` → `chatShowEscalateFlow()` |
| `chatShowEscalateFlow()` | Exibe campo de WhatsApp; oculta o input de texto |
| `chatConfirmWhatsApp()` | POST para `/chat-support-escalate`; exibe mensagem de confirmação ou erro |
| `chatAddBubble(role, text)` | Adiciona bolha de mensagem (`user` ou `agent`) |
| `chatAddTyping()` | Exibe indicador de digitação animado |
| `chatReset()` | Limpa histórico, estado e reinicia o chat do zero |

### Estado interno

```javascript
let chatOpen = false;
let chatCategory = null;
let chatHistory = [];      // Array de { role, content } para a API
let chatEscalated = false;
```

### CSS customizado

Variáveis usadas: `--adm` (#00D4AA), `--admd` (rgba(0,212,170,0.1)), `--bg0..3`, `--bd`, `--tx`, `--txs`, `--txm`, `--dg`

Classes principais: `#chat-btn`, `#chat-window`, `.chat-header`, `.chat-msgs`, `.chat-bubble.user`, `.chat-bubble.agent`, `.chat-typing`, `.chat-cats`, `.chat-cat-btn`, `.chat-footer`, `.chat-input`, `.chat-send`, `.chat-wa-row`

---

## Painel Admin (admin.html)

**Localização:** seção `#s-support` + drawer + funções a partir da linha ~1149

### Navegação

Item "Suporte" na sidebar com badge de contagem de tickets pendentes:

```html
<span id="support-badge" class="support-badge" style="display:none">0</span>
```

O badge é atualizado em tempo real via canal separado `admin-pending-count`.

### KPIs

| KPI | Descrição |
|-----|-----------|
| Total | Todos os tickets |
| Pendentes | `status = 'pending'` |
| Resolvidos | `status = 'resolved'` |
| Hoje | `created_at` no dia atual |

### Filtros

- **Todos** / **Pendentes** / **Resolvidos** (botões de filtro)
- **Busca textual** (nome, e-mail, WhatsApp, categoria)

### Tabela de tickets

Colunas: Data, Nome, E-mail, WhatsApp, Plano, Categoria, Status, Ação

### Drawer lateral

Exibido ao clicar "Ver / Responder" — mostra:

- Dados do usuário (nome, e-mail, plano, WhatsApp, categoria)
- Status e data de abertura
- Histórico completo da conversa (alternando user/agente)
- Textarea para anotações internas do admin (`admin_notes`)
- Botão "Marcar como resolvido"

### Funções

| Função | Descrição |
|--------|-----------|
| `loadSupport()` | Carrega todos os tickets, renderiza KPIs e tabela, inicia Realtime |
| `renderSupKPIs()` | Atualiza os 4 cards de métricas |
| `renderSupTable()` | Re-renderiza a tabela com filtro + busca aplicados |
| `supFilteredTickets()` | Filtra `state.supTickets` por status e busca textual |
| `openTicketDrawer(id)` | Abre drawer com dados do ticket selecionado |
| `closeTicketDrawer()` | Fecha o drawer e limpa `state.openTicket` |
| `saveAdminNotes()` | UPDATE `admin_notes` no ticket aberto |
| `resolveTicket()` | UPDATE `status = 'resolved'`, `resolved_at`, `resolved_by` |
| `startSupportRealtime()` | Escuta INSERT e UPDATE em `support_tickets` via Supabase Realtime |
| `watchPendingCount()` | Canal separado para atualizar o badge da sidebar em tempo real |
| `refreshPendingBadge()` | Query `count` de tickets `pending` e atualiza o badge |

### Estado global (admin)

```javascript
state.supportChannel = null;  // Canal Realtime da seção de suporte
state.openTicket = null;       // Ticket aberto no drawer
state.supTickets = [];         // Array local de tickets
state.supFilter = 'all';       // Filtro de status ativo
state.supSearch = '';          // Texto de busca ativo
```

---

## Fluxo de Dados

```
1. Usuário faz login
   └─ verificarAcesso() → chatReveal() [botão #chat-btn aparece]

2. Usuário abre o chat
   └─ chatToggle() → chatInit() → saudação + categorias

3. Usuário seleciona categoria e envia mensagem
   └─ chatSendToAPI()
      └─ POST /chat-support
         ├─ Autenticação via Authorization header
         ├─ Claude Haiku processa com system prompt + histórico
         └─ Retorna { message, escalate }

4a. escalate = false → exibe resposta, continua conversa

4b. escalate = true
   └─ chatShowEscalateFlow() → exibe campo de WhatsApp
      └─ chatConfirmWhatsApp()
         └─ POST /chat-support-escalate
            ├─ Autentica sessão
            ├─ INSERT support_tickets (service_role)
            └─ Retorna { success: true }

5. INSERT dispara evento Realtime
   └─ admin.html recebe → atualiza badge, tabela e KPIs em tempo real

6. Admin abre o ticket
   └─ openTicketDrawer() → lê histórico da conversa
      ├─ saveAdminNotes() → UPDATE admin_notes
      └─ resolveTicket() → UPDATE status = 'resolved'
```

---

## Segurança

| Camada | Mecanismo |
|--------|-----------|
| **Autenticação** | Bearer token JWT validado em ambas as Edge Functions via `auth.getUser()` |
| **Autorização** | `user_id` do payload é comparado com o `user.id` da sessão (evita spoofing) |
| **RLS** | Admin visualiza/atualiza via políticas; sem policy de INSERT para usuários comuns |
| **service_role** | Usado apenas dentro da Edge Function; nunca exposto ao cliente |
| **Dados sensíveis** | `user_whatsapp` armazenado apenas no DB; nunca em localStorage |

---

## Deploy

### Edge Functions

```bash
# Autenticar
export SUPABASE_ACCESS_TOKEN=<token>

# Deploy
supabase functions deploy chat-support --project-ref lmrpxtshdiwufbfkaymg --no-verify-jwt
supabase functions deploy chat-support-escalate --project-ref lmrpxtshdiwufbfkaymg --no-verify-jwt
```

> **Importante:** as funções devem ser deployadas com `--no-verify-jwt` pois a validação de autenticação é feita manualmente dentro do código.

### Migration

A migration `007_support_tickets.sql` foi aplicada diretamente via Supabase Management API (sem `supabase db push`) por incompatibilidade de histórico de migrations no ambiente.

Após a migration, os seguintes grants precisam ser aplicados manualmente:

```sql
GRANT USAGE ON SCHEMA public TO service_role, authenticated, anon;
GRANT ALL ON TABLE public.support_tickets TO service_role;
GRANT SELECT, UPDATE ON TABLE public.support_tickets TO authenticated;
```

### Variáveis de ambiente (Edge Functions)

As variáveis abaixo são injetadas automaticamente pelo Supabase em todas as Edge Functions:

- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`

A variável `ANTHROPIC_API_KEY` deve ser definida via:

```bash
supabase secrets set ANTHROPIC_API_KEY=<chave> --project-ref lmrpxtshdiwufbfkaymg
```

---

*Última atualização: maio/2026*

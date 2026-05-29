# CLAUDE.md — Backtest Pro / alphaQuant

> Leia este arquivo no início de cada sessão antes de qualquer ação no projeto.

---

## IDENTIDADE DO PROJETO

**Produto:** Backtest Pro — plataforma web no-code de backtesting para traders varejo brasileiros  
**Empresa:** alphaQuant | **Founder:** Clayton Barros (29 anos mercado financeiro, ex-Citibank/HSBC)  
**Posicionamento:** Anti-guru, anti-hype, pro-dado. Premissas, não promessas.  
**ICP:** Homem, 35–60 anos, opera mini índice/mini dólar (B3), não programa, nunca fez backtest.

---

## STATUS (maio/2026) — PRODUTO EM PRODUÇÃO

| Componente | Status |
|---|---|
| Frontend (app.html — wizard 5 passos + relatório) | ✅ Produção |
| Motor backtest (Python worker + pipeline) | ✅ Operacional |
| MT5 Headless | ✅ VPS Windows dedicada |
| EA Universal (`BacktestPro_Universal_EA.mq5`) | ✅ Produção |
| Dados históricos (WIN + WDO + 193+ ativos, 5 anos) | ✅ Pré-carregados |
| Auth + controle de acesso (Supabase) | ✅ Operacional |
| Pagamentos (Mercado Pago — Pix + cartão) | ✅ Operacional |
| Free trial (5 backtests gratuitos, salvos automaticamente) | ✅ Implementado |
| Emails transacionais (Resend — 4 triggers) | ✅ Operacional |
| Tela home pós-login | ✅ Implementada |
| Motor de diagnóstico e sugestões (23 nós) | ✅ Implementado |
| Compartilhamento de resultado (share card PNG) | ✅ Implementado |

**Não há bloqueadores técnicos. Foco atual: go-to-market.**

---

## URLS E INFRA

| Item | Valor |
|---|---|
| Produção | `https://www.backtestpro.com.br/` |
| App (Vercel) | `https://backtestpro-app.vercel.app` |
| Supabase ref | `lmrpxtshdiwufbfkaymg` |
| Repo | `github.com/clayton120178-sketch/backtest-pro` |
| Token GitHub | (ver cofre de senhas — não armazenar em texto plano) |
| Git identity | `user.email=dev@alphaquant.com.br` / `user.name=alphaQuant Dev` |

---

## GIT WORKFLOW (OBRIGATÓRIO)

```
1. Início de sessão: sync main → dev
2. Todo desenvolvimento no branch dev
3. Clayton valida no dev antes de merge
4. NUNCA push direto para main sem validação de Clayton
5. Claude executa as operações git (não instrui Clayton a fazer)
```

---

## ARQUITETURA DO PRODUTO

**Frontend:** `app.html` (single-file, ~10k+ linhas, HTML+CSS+JS vanilla)  
**Landing:** `index.html`  
**Deploy:** Vercel auto-deploy no push para `main`

**Wizard 5 passos:**
1. Mercado — Ativo, Timeframe, Janela horária
2. Condições — Indicadores com lógica AND
3. Gatilho — Direção, tipo de entrada, validade
4. Risco — Stop loss, Take profit
5. Gestão — Trailing stop, parcial, saída por condição

**Fluxo de backtest:**
`state.cfg (frontend)` → `submit-backtest (Edge Function)` → `fila Supabase` → `Python worker` → `MT5 headless` → `resultado em backtests.result` → `polling frontend` → `tela de resultados`

---

## TELA HOME PÓS-LOGIN

Implementada. Dois estados:
- **Estado A (com histórico):** painel de impacto (aprovadas/reprovadas em R$), CTA strip, lista de estratégias com tabs e cards clicáveis
- **Estado B (novo usuário):** banner de ativação com dots de trial

Cards da lista: `ativo · TF · direção`, badge verdict, data, condições, métricas, botão **Compartilhar**.

---

## MOTOR DE DIAGNÓSTICO

23 nós implementados. Documentação completa em `docs/motor-diagnostico.md`.

Resumo da árvore:
- **Sem edge:** Taxa de acerto crítica (4 sub-sugestões) → Payoff baixo (4 sub-sugestões) → Expectância negativa (4 sub-sugestões)
- **Com edge:** Drawdown elevado → Tempo sob água → Retorno abaixo de 200% CDI → Estratégia aprovada

**Importante:** diagnóstico calculado 100% no cliente em tempo real — não é persistido no banco. Atualiza automaticamente todos os históricos quando a lógica evolui.

---

## COMPARTILHAMENTO

- Botão "Compartilhar" em cada card da lista de backtests (home e history)
- `shareFromHistory(bt, btn)`: carrega dados do backtest, gera share card 1080×1080px, compartilha sem navegar para o resultado
- Link no texto compartilhado: `https://www.backtestpro.com.br/`

---

## BUGS CORRIGIDOS RECENTEMENTE (maio/2026)

| Bug | Fix |
|---|---|
| `TOKEN_REFRESHED` do Supabase sobrescrevia tela de loading/resultado | Guard `state?.screen === 'loading' \|\| 'results'` em `verificarAcesso()` |
| Texto "acerta mais da metade das vezes" com WR < 50% | Removida assunção de WR no bloco Payoff baixo |
| Payoff baixo sem sugestão quando !trailing e janela ≥ 3h | Adicionados 2 branches: ATR já ativo → aumentar mult; outros tipos → trocar para ATR |

---

## MODELO DE NEGÓCIO

| | Starter | Advanced | Elite |
|---|---|---|---|
| Backtests/mês | 100 | 150 | 200 |
| Estratégias salvas | 20 | 40 | 60 |
| **Mensal** | R$ 109,90 | R$ 139,90 | R$ 159,90 |
| **Semestral** (total) | R$ 599,40 | R$ 779,40 | R$ 899,40 |
| **Anual** (total) | R$ 1.044,00 | R$ 1.318,80 | R$ 1.558,80 |

Cobranças avulsas (não recorrentes). Free trial: 5 backtests gratuitos.

---

## ESCOPO DE DESENVOLVIMENTO

**Clayton (frontend):** `app.html`, `index.html`, decisões de produto, QA  
**Ivan (backend — NÃO TOCAR):** `worker.py`, `pipeline.py`, `cfg_to_json.py`, `mappings.py`, `backtest_runner.py`

---

## PENDÊNCIAS COMERCIAIS

- [ ] Sender de email próprio (sair do `onboarding@resend.dev`)
- [ ] Z-API WhatsApp (captura pós-cadastro + pós-3º backtest)
- [ ] Monitoring/alertas de produção (VPS + pipeline)

---

## FEATURES DE PRODUTO PENDENTES (BACKLOG)

- Score badge (0–100) por card na home — depende de algoritmo de scoring
- Version chain (v1→v2→v3) — depende de `parent_id` na query
- Sugestão ativa como pill clicável — depende de persistir `result.suggestion`
- Nome rico da estratégia (indicadores no título do card)

---

## ARQUIVOS DE DOCUMENTAÇÃO

| Arquivo | Conteúdo |
|---|---|
| `00-INSTRUCOES-PROJETO.md` | Instruções comportamentais para o Claude |
| `01-CONTEXTO-GERAL.md` | Visão geral, problema, público |
| `02-ARQUITETURA-DECISOES.md` | Stack e decisões arquiteturais |
| `03-MODELO-NEGOCIO.md` | Tiers, pricing, funil |
| `04-SPEC-INTERFACE-UX.md` | Especificação da interface |
| `05-EA-UNIVERSAL.md` | EA, módulos MQL5, parâmetros |
| `06-ROADMAP-STATUS.md` | Roadmap e status atualizado |
| `07-GIT-WORKFLOW.md` | Fluxo Git |
| `docs/motor-diagnostico.md` | Motor de diagnóstico — 23 nós documentados |
| `docs/SUPORTE-SISTEMA.md` | Spec do sistema de suporte |

---

## COMPORTAMENTO ESPERADO

- Diagnóstico de causa-raiz antes de propor solução — sem preâmbulos
- Executar, não rediscutir decisões já tomadas
- Análise crítica independente — não validar reflexivamente
- Português direto em todas as interações
- JS: validar com `node -e "new Function(code)"` antes de qualquer commit
- CSS: exclusivamente via custom properties — sem hex hardcoded

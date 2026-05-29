# Motor de Diagnóstico e Sugestões de Backtest

Documentação técnica da feature implementada em `app.html` — seção de análise automática de resultados com sugestões acionáveis de novos testes.

---

## 1. Visão Geral

Após cada backtest executado com sucesso (resultado real do MT5/backend), a tela de resultados exibe uma seção chamada **"O que os dados mostram"**. Essa seção:

1. Analisa as métricas retornadas pelo backend.
2. Classifica o resultado em um dos nós da árvore de diagnóstico.
3. Exibe **um único bloco** de diagnóstico (a causa raiz mais relevante).
4. Dentro desse bloco, oferece **uma sugestão concreta e parametrizável** com controles interativos.
5. Um botão **"Testar agora →"** aplica a mudança sugerida diretamente na configuração atual e dispara um novo backtest automaticamente.

A seção **não aparece** ao visualizar itens do histórico mock (apenas backtests reais têm métricas de backend).

---

## 2. Fonte de Dados

### `CURRENT_BACKEND_METRICS` (variável global)

Populada quando o backtest real conclui (`result.metrics`). Contém os campos retornados pelo parser MT5:

| Campo | Tipo | Uso no diagnóstico |
|---|---|---|
| `total_trades` | `number` | Guarda contra diagnóstico com 0 trades |
| `win_rate` | `number` (0–100) | Taxa de acerto em % |
| `total_net_profit` | `number` | Determina se há edge (positivo/negativo) |
| `profit_factor` | `number` | Fator de lucro |
| `max_drawdown_pct` | `number` (0–100) | MDD como % do capital |
| `payoff` | `number` | Payoff médio real (ganho médio / perda média) |
| `initial_deposit` | `number` | Depósito inicial para cálculo de retorno % |

### `EQ_ANALYSIS` (variável global)

Calculada pelo `computeAnalysis()` a partir da curva de equity. Usada como fallback para demos/histórico mock, e também para calcular `uwPeriods` (períodos "underwater").

### `state.cfg` (configuração atual)

Lida durante o diagnóstico para entender o que já está configurado (condições, tipo de stop, tipo de take profit, janela horária, etc.) e determinar qual sugestão faz sentido.

---

## 3. Ponto de Entrada

```javascript
function renderDiagnosticSection()
```

Localização: `app.html`, linha ~8025.

Chamada dentro de `renderResults()` após os cartões de métricas. O retorno é um elemento DOM (`<div class="diag-section">`) que é anexado ao container de resultados, ou `null` se não houver diagnóstico aplicável.

**Condições para retornar `null` (sem diagnóstico):**
- Está visualizando histórico (`viewingHistoryItem !== null`)
- `CURRENT_BACKEND_METRICS` é `null`
- `state.cfg` é `null`
- `total_trades === 0`

---

## 4. Variáveis Computadas

Antes de entrar na árvore, a função calcula:

| Variável | Cálculo | Significado |
|---|---|---|
| `winRate` | `win_rate / 100` | Taxa de acerto em fração (0–1) |
| `netProfit` | `total_net_profit` | Lucro/prejuízo líquido |
| `mddPct` | `max_drawdown_pct / 100` | MDD em fração |
| `avgPayoff` | `payoff` | Payoff médio real |
| `totalReturnPct` | `(netProfit / deposit) * 100` | Retorno total % sobre depósito |
| `tuwPct` | períodos abaixo do pico / total trades | Fração do tempo "underwater" |
| `cdiPct` | `diagComputeCDI(start, end)` | CDI acumulado no período testado |
| `trPerMonth` | `totalTrades / periodMonths` | Trades por mês |
| `hasEdge` | `netProfit > 0` | Se a estratégia é lucrativa |
| `mddStatus` | `≤25% → green`, `≤40% → yellow`, `>40% → red` | Classificação do drawdown |
| `tuwStatus` | `≤20% → green`, `≤35% → yellow`, `>35% → red` | Classificação do tempo underwater |
| `rentOk` | `(totalReturnPct / cdiPct) >= 2.0` | Se retorna ≥ 200% do CDI |
| `rrConfigured` | calculado do tipo de TP configurado | R:R implícito da config |
| `hasMA` | condição SMA ou EMA presente | Filtro de tendência ativo |
| `hasOsc` | condição RSI/Stoch/CCI/Williams/MACD presente | Oscilador ativo |
| `hasVolume` | condição volume/OBV/VWAP presente | Filtro de volume ativo |
| `showDisclosure` | `trPerMonth < 8` | Aviso de amostra pequena |

---

## 5. Árvore de Diagnóstico

O motor segue uma árvore determinística. Para cada execução, **apenas um bloco é exibido** — o que representa o problema mais relevante a resolver naquele momento.

```
raiz
├── SEM EDGE (netProfit ≤ 0)
│   ├── winRate < 33%  →  [DANGER] Taxa de acerto crítica
│   │   ├── sem MA        →  sugerir Média Móvel como filtro
│   │   ├── tem MA, sem Osc →  sugerir IFR (RSI) como oscilador
│   │   ├── tLastEntry ≥ 12h →  sugerir restringir entradas até 12:00
│   │   └── direção = 'both' →  sugerir testar 1 direção (long ou short)
│   │
│   ├── avgPayoff < rrConfigured × 0.85  →  [DANGER] Payoff baixo
│   │   ├── trailing ativo   →  sugerir remover trailing + alvo fixo
│   │   └── janela < 3h      →  sugerir ampliar horário de encerramento
│   │
│   └── catch-all (WR ok mas expectância negativa)  →  [DANGER] Expectância negativa
│       ├── tpType = 'rr'    →  stepper de R:R
│       ├── tpType = 'fixed' →  stepper de alvo em pontos
│       ├── tpType = 'atr'   →  stepper de multiplicador ATR
│       └── outro            →  nota genérica
│
└── COM EDGE (netProfit > 0)
    ├── mddStatus ≠ 'green'  →  [WARNING] Drawdown elevado
    │   ├── stopType = 'fixed'  →  sugerir stop por ATR
    │   └── stop não fixo (reutiliza árvore WR crítico):
    │       ├── sem MA          →  sugerir Média Móvel
    │       ├── tem MA, sem Osc →  sugerir IFR (RSI)
    │       ├── tLastEntry ≥ 12h →  restringir entradas até 12:00
    │       └── direção = 'both' →  testar 1 direção
    │
    ├── tuwStatus ≠ 'green'  →  [WARNING] Tempo sob água elevado
    │   ├── sem Volume          →  sugerir volume acima da média
    │   ├── sem maxDailyTrades  →  sugerir max 2 operações/dia
    │   └── partial ativo       →  sugerir desativar saída parcial
    │
    ├── !rentOk              →  [WARNING] Retorno abaixo do esperado
    │   ├── tpType = 'fixed'  →  sugerir trocar para alvo por ATR
    │   ├── tpType = 'rr'     →  stepper para aumentar multiplicador
    │   └── tpType = 'atr'    →  stepper para aumentar multiplicador
    │
    └── tudo ok              →  [SUCCESS] Estratégia aprovada
        └── cards de próximos testes sugeridos (timeframe maior + ativo diferente)
```

---

## 6. Componentes de UI

### 6.1 Bloco de diagnóstico (`.diag-block`)

Container visual principal. Recebe um modificador de cor:

| Modificador | Uso |
|---|---|
| `.danger` | Resultado negativo (sem edge) — fundo vermelho sutil, borda esquerda vermelha |
| `.warning` | Resultado positivo mas com problema — fundo âmbar sutil, borda esquerda âmbar |
| `.success` | Todos os critérios atendidos — fundo teal/índigo sutil, borda esquerda gradiente |

A borda lateral colorida é implementada via `::before` com `position:absolute; pointer-events:none; z-index:0` (importante para não bloquear interações).

### 6.2 Tag de diagnóstico (`.diag-tag`)

Label de identificação do problema, exibido no topo do bloco. Ex: `"Taxa de acerto crítica"`, `"Drawdown elevado"`, `"✓ Estratégia aprovada"`.

### 6.3 Texto explicativo (`.diag-text`)

Parágrafo em prosa que explica **por que** o problema existe em linguagem acessível ao trader. Usa `<strong>` para destacar os valores numéricos relevantes.

### 6.4 Separador (`.diag-sep`)

Linha horizontal sutil que separa o diagnóstico da seção de sugestão.

### 6.5 Cabeçalho de sugestão (`.sugg-hdr`)

Label fixo `"Vale a pena testar:"` com linha decorativa à direita.

### 6.6 Nota de sugestão (`.sugg-note`)

Caixa explicativa que detalha **o que** a sugestão faz e **por que** pode ajudar. Fundo `var(--bg2)` com borda sutil.

### 6.7 Disclaimer de sugestão (`.sugg-disc`)

Texto menor com aviso de trade-off. Ex: `"Atenção: alvos maiores tendem a reduzir a taxa de acerto."` Aparece quando a sugestão tem consequências ambíguas.

### 6.8 Linha de controles (`.sugg-row`)

Container flexível que agrupa os controles interativos horizontalmente (chips, steppers, selects, botão).

### 6.9 Chips de operação (`.op-chip`)

Representação visual da mudança que será aplicada. Três tipos:

| Classe | Visual | Uso |
|---|---|---|
| `.add` | fundo verde | Adiciona algo (nova condição) |
| `.remove` | fundo vermelho | Remove algo (trailing, parcial) |
| `.repl` | fundo teal | Substitui algo (fixed → ATR) |

### 6.10 Stepper numérico (`diagMakeStepper`)

Controle `−` / valor / `+` para parâmetros numéricos. Função:

```javascript
diagMakeStepper(label, initVal, min, max, step, unit, ref)
```

- `ref` é um objeto `{val}` passado por referência — mantém o valor atual sem re-renderizar.
- Respeita min/max nos cliques.
- Exibe unidade (ex: `"×"`, `"pts"`, `"× ATR"`) após o valor.

Usado para: R:R, alvo em pontos, multiplicador ATR, multiplicador stop ATR, valor de RSI.

### 6.11 Select de parâmetro (`diagMakeSelect`)

Dropdown estilizado para opções discretas. Função:

```javascript
diagMakeSelect(label, options, ref)
```

- `options`: array de `[value, label]`.
- `ref` é um objeto `{val}` atualizado pelo `onchange`.

Usado para: tipo de MA, período, condição, horário de encerramento.

### 6.12 Botão "Testar agora →" (`diagTestBtn`)

```javascript
diagTestBtn(onClick)
```

Botão com estilo `btn-test` (fundo teal, hover com glow). O `onClick` recebe uma arrow function que é chamada quando clicado.

### 6.13 Seta de fluxo (`chipArr`)

Seta `→` simples entre chips para indicar a transformação. Ex: `[Stop fixo · 200 pts] → [Stop por ATR]`.

---

## 7. Fluxo "Testar Agora"

```javascript
function diagApplyAndTest(fn) {
  fn();        // aplica a mudança em state.cfg
  startLoading(); // dispara novo backtest com a config modificada
}
```

O botão "Testar agora →" chama `diagApplyAndTest` passando uma closure que modifica `state.cfg` com os valores atuais dos controles (lidos via `ref.val`). Em seguida, `startLoading()` reenvia o backtest para o backend com a nova configuração — o ciclo completo do backtest é reexecutado.

Isso permite que o usuário:
1. Leia o diagnóstico.
2. Ajuste os parâmetros nos steppers/selects.
3. Clique em "Testar agora →" para ver o impacto imediato.

---

## 8. Caminho de Sucesso (Estratégia Aprovada)

Quando `hasEdge && mddStatus === 'green' && tuwStatus === 'green' && rentOk`, o bloco `.success` é exibido com:

- **Mensagem motivacional**: reconhece que o trader está entre menos de 5% que conseguem estratégias consistentes.
- **Cards de próximos testes sugeridos**: dois cards clicáveis gerados a partir de tabelas de lookup:
  - `DIAG_TF_NEXT`: mapeamento de timeframe atual → timeframe maior sugerido.
  - `DIAG_ASSET_PAIR`: mapeamento de ativo atual → ativo correlato sugerido.
  - Card 1: mesmo ativo, timeframe maior.
  - Card 2: ativo diferente, mesmo timeframe.
  - Clicar em qualquer card aplica a mudança e dispara novo backtest via `diagApplyAndTest`.

---

## 9. Aviso de Amostra Pequena

Se `trPerMonth < 8` (menos de 8 trades por mês em média), um banner amarelo é exibido acima do bloco:

> ⚠ Poucos trades no período — interprete os resultados com cautela.

Isso não impede o diagnóstico — apenas contextualiza a confiabilidade estatística.

---

## 10. Integração CDI

```javascript
function diagComputeCDI(start, end)
```

Calcula o CDI acumulado no período testado usando a tabela `DIAG_CDI` (taxas anuais de 2015 a 2025). O resultado é usado no critério `rentOk` para comparar o retorno da estratégia com a renda fixa — o padrão mínimo exigido é **200% do CDI** no período.

---

## 11. Estrutura de Arquivos

Toda a implementação está em um único arquivo:

```
backtest-pro/
└── app.html
    ├── CSS: linhas ~599–650  (classes .diag-*, .sugg-*, .btn-test, .op-chip, .chip-arr)
    ├── JS — globals: linha ~1902  (CURRENT_BACKEND_METRICS)
    ├── JS — getMetrics(): linha ~7895
    ├── JS — diagMakeStepper(): linha ~7979
    ├── JS — diagMakeSelect(): linha ~8000
    ├── JS — diagTestBtn(): linha ~8013
    ├── JS — diagApplyAndTest(): linha ~8020
    └── JS — renderDiagnosticSection(): linha ~8025
```

---

## 12. Resumo dos Diagnósticos Implementados

| # | Condição de Ativação | Tag | Tipo | Sugestões |
|---|---|---|---|---|
| 1 | Sem edge + WR < 33% + sem MA | Taxa de acerto crítica | danger | + Média Móvel (SMA/EMA) com período e condição |
| 2 | Sem edge + WR < 33% + tem MA, sem oscilador | Taxa de acerto crítica | danger | + IFR (RSI) com período, condição e valor |
| 3 | Sem edge + WR < 33% + tem MA+Osc + tLastEntry ≥ 12h | Taxa de acerto crítica | danger | Restringir entradas até 12:00 |
| 4 | Sem edge + WR < 33% + tem MA+Osc + tLastEntry < 12h + direção ambos | Taxa de acerto crítica | danger | Testar apenas compra ou apenas venda |
| 5 | Sem edge + payoff < RR × 0.85 + trailing ativo | Payoff baixo | danger | Remover trailing + alvo fixo (stepper de pontos) |
| 6 | Sem edge + payoff < RR × 0.85 + janela < 3h | Payoff baixo | danger | Ampliar horário de encerramento (select) |
| 7 | Sem edge + WR ≥ 33% + expectância negativa + tpType=rr | Expectância negativa | danger | Aumentar R:R (stepper ×) |
| 8 | Sem edge + WR ≥ 33% + expectância negativa + tpType=fixed | Expectância negativa | danger | Aumentar alvo em pontos (stepper pts) |
| 9 | Sem edge + WR ≥ 33% + expectância negativa + tpType=atr | Expectância negativa | danger | Aumentar multiplicador ATR (stepper ×ATR) |
| 10 | Com edge + MDD > 25% + stopType=fixed | Drawdown elevado | warning | Stop por ATR (select período + stepper mult) |
| 11 | Com edge + MDD > 25% + stop não fixo + sem MA | Drawdown elevado | warning | + Média Móvel |
| 12 | Com edge + MDD > 25% + stop não fixo + tem MA, sem Osc | Drawdown elevado | warning | + IFR (RSI) |
| 13 | Com edge + MDD > 25% + stop não fixo + tLastEntry ≥ 12h | Drawdown elevado | warning | Restringir entradas até 12:00 |
| 14 | Com edge + MDD > 25% + stop não fixo + direção ambos | Drawdown elevado | warning | Testar apenas compra ou apenas venda |
| 15 | Com edge + MDD ok + TUW > 20% + sem volume | Tempo sob água elevado | warning | + Volume acima da média |
| 16 | Com edge + MDD ok + TUW > 20% + sem maxDailyTrades | Tempo sob água elevado | warning | Máximo 2 operações por dia |
| 17 | Com edge + MDD ok + TUW > 20% + saída parcial ativa | Tempo sob água elevado | warning | Desativar saída parcial |
| 18 | Com edge + MDD ok + TUW ok + retorno < 200% CDI + tpType=fixed | Retorno abaixo do esperado | warning | Trocar para alvo por ATR (select + stepper) |
| 19 | Com edge + MDD ok + TUW ok + retorno < 200% CDI + tpType=rr | Retorno abaixo do esperado | warning | Aumentar R:R (stepper) |
| 20 | Com edge + MDD ok + TUW ok + retorno < 200% CDI + tpType=atr | Retorno abaixo do esperado | warning | Aumentar multiplicador ATR (stepper) |
| 21 | Com edge + MDD ok + TUW ok + retorno ≥ 200% CDI | Estratégia aprovada | success | Cards: timeframe maior + ativo correlato |

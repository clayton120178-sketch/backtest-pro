# Bug Report — EA Universal BacktestPro
**Data:** 29/04/2026  
**Testado por:** Clayton Barros  
**Ambiente:** WIN$N · M5 · 01/01/2021–31/03/2026 · Broker XPMT5-PRD · Depósito R$100.000  
**EA:** BacktestPro_Universal_EA v1.0  
**Suíte de testes:** H (Smart Money Concepts)

---

## Sumário Executivo

A bateria completa da Suíte H (65 casos, P1 + P2) foi executada. Dois módulos Smart Money produziram **zero operações em todos os seus casos de teste**, incluindo os casos mais básicos com parâmetros padrão e 5 anos de dados históricos. Os demais módulos SMC (FVG, BoS, CHoCH) apresentaram operações normais.

| # | Módulo | Casos testados | Casos com zero operações | Diagnóstico |
|---|---|---|---|---|
| 1 | Liquidity Grab | 9 | 9 (100%) | Bug — módulo não detecta nenhum padrão |
| 2 | Liquidity Sweep | 6 | 6 (100%) | Bug — módulo não detecta nenhum padrão |

---

## Bug #1 — Liquidity Grab: zero operações em todos os cenários

### Descrição

O módulo `BP_SMC_GRAB` (GRAB_BULL = índice 7, GRAB_BEAR = índice 8) não produziu nenhuma operação em nenhum dos 9 casos testados, incluindo o caso de referência mais básico (H-044: GRAB_BULL, BUY_ONLY, NEXT_OPEN, parâmetros padrão, 5 anos de dados).

### Casos afetados

| Case ID | Configuração | Operações |
|---|---|---|
| H-041 | GRAB_BULL · BUY_ONLY · NEXT_OPEN | 0 |
| H-042 | GRAB_BEAR · SELL_ONLY · NEXT_OPEN | 0 |
| H-043 | GRAB_BULL · BOTH · NEXT_OPEN | 0 |
| H-044 | GRAB_BULL · BUY_ONLY · NEXT_OPEN *(referência)* | 0 |
| H-045 | GRAB_BULL · BUY_ONLY · BREAKOUT · validade 3 barras | 0 |
| H-046 | GRAB_BULL · BUY_ONLY · CLOSE | 0 |
| H-047 | GRAB_BULL · BUY_ONLY · comparação com Sweep | 0 |
| H-058 | GRAB_BULL · BUY_ONLY · saída por condição RSI>70 | 0 |
| H-064 | GRAB_BULL · BUY_ONLY · SL mínimo forçado | 0 |

### Parâmetros do caso de referência (H-044)

```
InpUseSmartMoney    = true
InpSMCEntry         = 7||BP_SMC_GRAB_BULL
InpFVGEntryMode     = 0||FVG_ENTRY_AGGRESSIVE
InpBOS_Leg1Min      = 2
InpBOS_Leg1Max      = 5
InpBOS_CorrectionMax= 3
InpBOS_Leg2Max      = 3
InpDirection        = 1||TRADING_BUY_ONLY
InpEntryType        = 1||BP_ENTRY_NEXT_OPEN
InpSLType           = 2||BP_SL_CANDLE (N=1, buffer=5)
InpTPType           = 1||BP_TP_RR (RR=2.0)
Janela              = 09:00–17:30
```

### Investigação com log DEBUG (H-041)

O caso H-041 foi rodado manualmente com `InpLogLevel=5` (DEBUG). O Journal exibiu a cada candle a mensagem `Operacoes hoje: 0 (sem limite)` — confirmando que o EA inicializou, executou o diagnóstico por candle e nunca atingiu a linha de sinal. Nenhuma mensagem relacionada ao padrão Grab foi encontrada no Journal durante o período inteiro.

### Hipóteses de causa raiz

**Hipótese A (mais provável) — Mapeamento de enum incorreto:** Os valores `BP_SMC_GRAB_BULL=7` e `BP_SMC_GRAB_BEAR=8` usados nos arquivos `.set` podem não corresponder aos índices reais da enum `ENUM_BP_SMC_CONCEPT` na versão compilada atual. Se os índices foram alterados em alguma revisão e o mapeamento não foi atualizado, o EA recebe um conceito diferente do esperado (ou nenhum).

**Hipótese B — Módulo não implementado na versão atual:** A função `BP_SmartMoney_GetGrab` (ou equivalente) pode não estar implementada no `BP_SmartMoney.mqh` da versão compilada, fazendo com que `BP_SignalEngine_Evaluate` ignore o conceito Grab e nunca gere sinal.

**Hipótese C — Condição de detecção nunca satisfeita:** A lógica de detecção do Grab pode ter restrições internas tão rígidas que nenhum candle do WIN$N M5 nos últimos 5 anos satisfaz o padrão. Improvável dado o volume de dados (≈340.000 candles), mas não pode ser descartado sem ver o código.

### Como confirmar

1. Confirmar os índices reais da enum `ENUM_BP_SMC_CONCEPT` no fonte `BP_Constants.mqh`
2. Verificar se `BP_SignalEngine_Evaluate` tem um branch para `BP_SMC_GRAB_BULL` e `BP_SMC_GRAB_BEAR`
3. Adicionar um log explícito dentro da função de detecção do Grab para confirmar que está sendo chamada

---

## Bug #2 — Liquidity Sweep: zero operações em todos os cenários

### Descrição

O módulo `BP_SMC_SWEEP` (SWEEP_BULL = índice 9, SWEEP_BEAR = índice 10) não produziu nenhuma operação em nenhum dos 6 casos testados, incluindo o caso de referência mais básico (H-049: SWEEP_BULL, BUY_ONLY, NEXT_OPEN, parâmetros padrão, 5 anos de dados). Isso inclui o caso H-052 com parâmetros de confirmação propositalmente permissivos (Leg1=1–3 candles, CorrMax=2).

### Casos afetados

| Case ID | Configuração | Operações |
|---|---|---|
| H-048 | SWEEP_BULL · BUY_ONLY · comparação com Grab | 0 |
| H-049 | SWEEP_BULL · BUY_ONLY · NEXT_OPEN *(referência)* | 0 |
| H-050 | SWEEP_BEAR · SELL_ONLY · NEXT_OPEN | 0 |
| H-052 | SWEEP_BULL · BUY_ONLY · confirmação rápida (Leg1=1–3, CorrMax=2) | 0 |
| H-053 | SWEEP_BULL · BUY_ONLY · confirmação rigorosa (Leg1=5–15, CorrMax=5) | 0 |
| H-059 | SWEEP_BULL · BUY_ONLY · Trailing BAR + Parcial 50% | 0 |

### Parâmetros do caso de referência (H-049)

```
InpUseSmartMoney    = true
InpSMCEntry         = 9||BP_SMC_SWEEP_BULL
InpFVGEntryMode     = 0||FVG_ENTRY_AGGRESSIVE
InpBOS_Leg1Min      = 2
InpBOS_Leg1Max      = 5
InpBOS_CorrectionMax= 3
InpBOS_Leg2Max      = 3
InpDirection        = 1||TRADING_BUY_ONLY
InpEntryType        = 1||BP_ENTRY_NEXT_OPEN
InpSLType           = 2||BP_SL_CANDLE (N=1, buffer=5)
InpTPType           = 1||BP_TP_RR (RR=2.0)
Janela              = 09:00–17:30
```

### Observação relevante — caso H-052

O caso H-052 foi configurado com parâmetros intencionalmente permissivos (Leg1=1–3 candles, CorrMax=2) para maximizar o número de sinais. Ainda assim: zero operações. Isso praticamente descarta a hipótese de que a lógica de detecção está funcionando mas com critérios muito restritivos — o módulo simplesmente não está gerando sinal em nenhuma condição.

### Hipóteses de causa raiz

As mesmas hipóteses do Bug #1 se aplicam: mapeamento de enum incorreto (índices 9 e 10) ou módulo não implementado na versão compilada. Dado que ambos os bugs afetam os dois módulos mais recentes adicionados ao EA (Grab e Sweep foram separados na última revisão), a **Hipótese A é a mais provável para ambos**: a enum `ENUM_BP_SMC_CONCEPT` pode ter sido reordenada ou os novos conceitos não foram incluídos na versão compilada que está sendo testada.

---

## Contexto — O que funcionou corretamente

Para referência, os seguintes módulos SMC produziram operações normais na mesma bateria de testes, confirmando que a infraestrutura de SMC está funcionando:

| Módulo | Casos testados | Resultado |
|---|---|---|
| FVG Bullish / Bearish (Agressivo) | 4 | ✅ Operações normais |
| FVG Bullish (Mitigation/Limite) | 4 | ✅ Ordens LIMIT registradas |
| BoS Bullish / Bearish | 11 | ✅ Operações normais |
| CHoCH Bullish / Bearish | 11 | ✅ Operações normais |
| OB Mitigation (filtro sobre BoS e CHoCH) | 6 | ✅ Filtro aplicado corretamente |

---

## Casos com zero operações esperados (não são bugs)

Os casos abaixo também produziram zero operações mas estavam marcados como resultado esperado no roteiro de testes. Confirmados como **aprovados**:

| Case ID | Motivo |
|---|---|
| H-031 | CHoCH TrendMin=15–30 candles no M5 — condição raríssima, zero sinais em 5 anos é normal |
| H-040 | CHoCH com três restrições simultâneas (Leg longa + Trend longa + Amp=60%) |
| H-054 | Sweep CorrMax=1 — marcado como [BORDA] no roteiro |
| H-062 | BoS Leg1Min=10 > Leg1Max=5 — parâmetro inválido intencional, zero trades esperado |
| H-063 | CHoCH TrendMin=20 > TrendMax=10 — parâmetro inválido intencional |
| H-065 | Janela operacional invertida (início 17h > fim 9h) — zero trades esperado |

---

## Ação solicitada

1. Verificar os índices reais de `BP_SMC_GRAB_BULL`, `BP_SMC_GRAB_BEAR`, `BP_SMC_SWEEP_BULL` e `BP_SMC_SWEEP_BEAR` na enum `ENUM_BP_SMC_CONCEPT` do fonte atual
2. Confirmar se há implementação ativa desses conceitos em `BP_SignalEngine_Evaluate` na versão compilada em teste
3. Se os índices estiverem corretos e o código implementado, adicionar log DEBUG explícito dentro das funções de detecção para rastrear por que nenhum candle satisfaz a condição
4. Após correção, recompilar e reenviar o `.ex5` para nova bateria nos casos H-041 a H-050, H-052, H-053, H-058, H-059 e H-064

---

*Relatório gerado com base na execução automatizada via `backtest_runner.py` + análise manual do caso H-041 com LogLevel=DEBUG.*

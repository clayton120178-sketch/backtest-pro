# Backtest Pro — Análise & Planejamento
 
**Data:** 26 de março de 2026
**Status:** v1.0 — Arquitetura Definida, Pronto para Desenvolvimento
 
---
 
## 1. VISÃO GERAL DO PROJETO
 
### Problema
Traders varejistas precisam testar setups de análise técnica usando dados históricos reais antes de arriscar dinheiro.
 
### Solução
**Backtest Pro**: Plataforma que permite usuários montar estratégias via interface web, executa backtests no MT5 e retorna resultados completos.
 
### Stack Tecnológico
 
| Camada | Tecnologia |
|--------|-----------|
| **Frontend** | HTML + CSS + JS (single-file) — Vercel |
| **Banco** | Supabase (Postgres 17) |
| **Auth** | Supabase Auth (email + Google OAuth) |
| **Pagamento** | Mercado Pago (Pix + Cartão) |
| **Motor Backtest** | MT5 Headless (a infraestruturar) |
| **Backend** | Node.js / Edge Functions (a desenvolver) |
 
### Fluxo Completo
 
```
Usuário (Interface Web)
  ? (Dados + Parâmetros JSON)
Backend MT5 (Seu trabalho)
  +- Validação + Padronização
  +- Geração .ini e .set
  +- Orquestração MT5
  ?
MT5 Strategy Tester
  +- Carrega EA Universal
  +- Ativa módulos conforme JSON
  +- Executa backtest
  ?
Resultados (Equity, Métricas, Trades)
  ? (Salvo em Supabase)
Usuário (Vê relatório completo)
```
 
---
 
## 2. ARQUITETURA DE EAS — DECISÃO PRINCIPAL
 
### Proposta: 1 EA Universal + Módulos Dinâmicos
 
**Vs. 4 EAs Separados** (proposta inicial)
 
| Aspecto | 1 EA + Módulos | 4 EAs Separados | Vencedor |
|---------|---|---|---|
| **Compilação** | 1x | 4x | 1 EA ? |
| **Manutenção** | Código centralizado | Duplicação | 1 EA ? |
| **Flexibilidade** | Ativa módulos via JSON | Troca EA inteira | 1 EA ? |
| **Tamanho** | 1 .ex5 moderado | 4 .ex5 grandes | 1 EA ? |
 
### Arquitetura Proposta
 
```
+------------------------------------------------+
¦   BacktestPro-Universal-EA.mq5                 ¦
¦   (Cópia de ModularEA_Template.mq5)            ¦
+------------------------------------------------¦
¦                                                ¦
¦  FRAMEWORK alphaQuant (sempre ativo)           ¦
¦  +- Logger                                     ¦
¦  +- License                                    ¦
¦  +- OrderManager                               ¦
¦  +- RiskManager                                ¦
¦  +- PositionTracker                            ¦
¦  +- StopLoss/TakeProfit/Trailing               ¦
¦  +- Gestão Universal                           ¦
¦                                                ¦
¦  +------------------------------------------+  ¦
¦  ¦ MÓDULOS DINÂMICOS (via FLAGS do JSON)    ¦  ¦
¦  +------------------------------------------¦  ¦
¦  ¦                                          ¦  ¦
¦  ¦ [FLAG] BP_Indicators.mqh                 ¦  ¦
¦  ¦ +- RSI, Estocástico, CCI, Williams, MACD¦  ¦
¦  ¦ +- SMA, EMA, ADX, SAR, Bollinger, VWAP  ¦  ¦
¦  ¦ +- Volume, OBV, ATR                      ¦  ¦
¦  ¦ +- Cálculos genéricos de preço           ¦  ¦
¦  ¦                                          ¦  ¦
¦  ¦ [FLAG] BP_Oscillators.mqh                ¦  ¦
¦  ¦ +- Detecta cruzamentos de osciladores   ¦  ¦
¦  ¦ +- Aplica filtros (tendência, volume)   ¦  ¦
¦  ¦ +- Lógica de zonas (overbought/sold)    ¦  ¦
¦  ¦ +- Validações R01-R32                   ¦  ¦
¦  ¦                                          ¦  ¦
¦  ¦ [FLAG] BP_CandlePatterns.mqh             ¦  ¦
¦  ¦ +- Detecção padrões (Martelo, Engolfo) ¦  ¦
¦  ¦ +- Spinning Top, Harami, Hammer        ¦  ¦
¦  ¦ +- Confirmação com preço/padrões       ¦  ¦
¦  ¦                                          ¦  ¦
¦  ¦ [FLAG] BP_SmartMoney.mqh                 ¦  ¦
¦  ¦ +- Fair Value Gap (FVG)                  ¦  ¦
¦  ¦ +- Break of Structure (BoS)              ¦  ¦
¦  ¦ +- Change of Character (CHoCH)          ¦  ¦
¦  ¦ +- Order Block (OB)                      ¦  ¦
¦  ¦ +- Liquidity Sweep (Sweep)               ¦  ¦
¦  ¦                                          ¦  ¦
¦  +------------------------------------------+  ¦
¦                                                ¦
¦  BP_SignalEngine.mqh                           ¦
¦  +- Orquestra condições ? gera sinal          ¦
¦                                                ¦
¦  EXECUTION                                     ¦
¦  +- Calcula Stop/TP (universal)               ¦
¦  +- Executa ordem via OrderManager            ¦
¦  +- Gerencia risco (RiskManager)              ¦
¦                                                ¦
+------------------------------------------------+
```
 
---
 
## 3. ESTRUTURA MQL5 NO REPOSITÓRIO
 
```
mql5/
+-- Experts/
¦   +-- BacktestPro_Universal_EA.mq5      ? EA Principal
+-- Include/
¦   +-- Framework/
¦   ¦   +-- FrameworkCore.mqh              ? Seu framework alphaQuant
¦   +-- BacktestPro/
¦       +-- BP_Constants.mqh               ? Enums, FLAGS, tipos
¦       +-- BP_Indicators.mqh              ? Cálculos indicadores
¦       +-- BP_Oscillators.mqh             ? Lógica osciladores
¦       +-- BP_CandlePatterns.mqh          ? Detecção padrões
¦       +-- BP_SmartMoney.mqh              ? Lógica SMC
¦       +-- BP_SignalEngine.mqh            ? Orquestração sinais
+-- Libraries/
    +-- AlphaQuant_*.ex5                  ? Framework compilado
```
 
---
 
## 4. ANÁLISE: EAs EXISTENTES
 
Você tem 3 EAs prontos com lógica reutilizável:
 
### BT_TT.mq5 (100KB)
- **Padrões:** Bottom Tail, Top Tail, TTTO, BTTO
- **Estrutura:** Classe `LocalizacaoEventoEA`
- **Reutilizável:** Métodos `IsBT()`, `IsTT()`, `IsPattern()`
- **Para:** BP_CandlePatterns.mqh
 
### dB_dT_finder.mq5 (141KB)
- **Padrões:** Double Bottom, Double Top, Bullish Pivot, Bearish Pivot
- **Estrutura:** Análise de swings (máximas/mínimas de N períodos)
- **Reutilizável:** Métodos `GetMove()`, `GetNextMove()`, análise estrutural
- **Para:** BP_CandlePatterns.mqh
 
### 12padraoes_exe_v2.mq5 (264KB)
- **Padrões:** Repositório consolidado dos 12 padrões
- **Reutilizável:** Código de detecção pronto
- **Para:** BP_CandlePatterns.mqh (consolidar com os 2 anteriores)
 
### Estratégia de Reuso
1. Extrair métodos de detecção de padrões dos 3 EAs
2. Consolidar em `BP_CandlePatterns.mqh`
3. Deixar padrões antigos em `/mql5/PastEAs/` como referência
 
---
 
## 5. FRAMEWORK alphaQuant — Integração
 
### O Que É
- **Padrão handle-based** (object pool)
- **20 módulos especializados** como .ex5 libraries
- **API headers (.mqh)** para cada módulo
- **FrameworkCore.mqh** como master include
 
### Módulos Disponíveis (11 principais)
1. **Logger** — Logging centralizado
2. **PositionTracker** — Rastreia posições abertas
3. **RiskManager** — Gestão de risco + lote
4. **StopLossManager** — Cálculo de stops (ATR, fixo, gráfico)
5. **TakeProfitManager** — Cálculo de TP (fixo, RR, ZigZag, ATR)
6. **OCOSystem** — One-Cancels-Other pairs
7. **PostExecutionManager** — Ajusta stops após abertura
8. **TrailingStopManager** — Trailing stops automáticos
9. **MultiIndicatorAnalyzer** — RSI, Stochastic, ZigZag
10. **OrderManager** — Executa todas as operações
11. E 9 mais (internos ou especializados)
 
### Como Integrar com BacktestPro
- ? EA universal usa FrameworkCore.mqh
- ? Declara handles dos módulos conforme necessário
- ? Ativa/desativa via FLAGS do JSON
- ? Exemplo: Se JSON não tiver SMC, `BP_SmartMoney` não é compilado
 
---
 
## 6. FLUXO JSON ? EA ? Resultados
 
### JSON de Entrada (Frontend ? Backend)
```json
{
  "strategist": "BacktestPro v2.0",
  "modules": {
    "indicators": { "enabled": true },
    "oscillators": { "enabled": true },
    "candlePatterns": { "enabled": false },
    "smartMoney": { "enabled": false }
  },
  "conditions": [
    {
      "id": "rsi",
      "module": "oscillators",
      "params": { "period": 14, "cond": "cruza_acima_de", "value": 30 }
    },
    {
      "id": "sma",
      "module": "oscillators",
      "params": { "period": 200, "cond": "acima_de_preco" }
    }
  ],
  "entryType": "next_open",
  "stopLoss": { "type": "candle", "candles": 1 },
  "takeProfit": { "type": "rr", "ratio": 2.0 }
}
```
 
### Processamento Backend
1. **Validação** — Verifica bloqueios (R01-R33)
2. **Padronização** — Normaliza parâmetros
3. **Geração .ini/.set** — Cria arquivos para MT5
4. **Orquestração** — Executa no MT5 Headless
 
### MT5 Strategy Tester
1. Carrega EA Universal
2. Ativa módulos conforme `modules.enabled`
3. Injeta parâmetros do JSON
4. Executa backtest com dados históricos
 
### Resultado para Usuário
```json
{
  "status": "completed",
  "metrics": {
    "totalTrades": 45,
    "winRate": 62.5,
    "profitFactor": 2.1,
    "maxDrawdown": -8.3,
    "netProfit": 2540.50
  },
  "equity": [...],
  "trades": [...]
}
```
 
---
 
## 7. PLANO DE DESENVOLVIMENTO — 3 FASES
 
### FASE 1: Arquitetura + Módulos Base (Semana 1-2)
 
**Objetivo:** Estrutura pronta e compilável
 
**Tarefas:**
- [ ] Criar estrutura MQL5 (pastas, includes)
- [ ] `BP_Constants.mqh` — Enums, FLAGS, tipos
- [ ] `BP_Indicators.mqh` — Cálculos RSI, MACD, SMA, ATR, etc
- [ ] `BP_Oscillators.mqh` — Lógica cruzamentos + filtros + bloqueios R01-R32
- [ ] `BP_CandlePatterns.mqh` — Consolidar padrões dos 3 EAs existentes
- [ ] `BP_SignalEngine.mqh` — Orquestração de condições ? sinal
- [ ] Compilação teste (0 errors, 0 warnings)
 
**Entrega:** Módulos compiláveis + testes básicos
 
---
 
### FASE 2: EA Universal + Smart Money (Semana 2-3)
 
**Objetivo:** EA funcional com 3 módulos
 
**Tarefas:**
- [ ] `BacktestPro_Universal_EA.mq5` — Estrutura principal + OnInit/OnTick
- [ ] Integração FrameworkCore.mqh (Logger, RiskManager, OrderManager)
- [ ] `BP_SmartMoney.mqh` — Lógica FVG, BoS, CHoCH, OB, Sweep
- [ ] Signal generator ativo (Oscillators + CandlePatterns)
- [ ] Testes manuais no MT5 Strategy Tester
- [ ] Validações de bloqueios (R33: SMC isolado)
 
**Entrega:** EA compilado, testado em 5 estratégias diferentes
 
---
 
### FASE 3: Integração Python + MT5 (Semana 3-4)
 
**Objetivo:** Fluxo completo frontend ? backend ? MT5 ? usuário
 
**Tarefas:**
- [ ] Backend: Parser JSON ? validação ? geração .ini/.set
- [ ] Python: Automação MT5 (carregar EA, injetar parâmetros, rodar teste)
- [ ] Python: Extração de resultados (equity curve, trades, métricas)
- [ ] Supabase: Salvar resultados do backtest
- [ ] Testes end-to-end (5 estratégias completas)
 
**Entrega:** Fluxo completo funcionando
 
---
 
## 8. DECISÕES TÉCNICAS CONFIRMADAS
 
| Decisão | Confirmado |
|---------|-----------|
| 1 EA Universal + Módulos Dinâmicos | ? |
| `#include` files (padrão framework) | ? |
| Indicadores em BP_Indicators.mqh | ? |
| Osciladores em BP_Oscillators.mqh | ? |
| Framework alphaQuant para gestão | ? |
| Padrões consolidados de 3 EAs | ? |
 
---
 
## 9. PRÓXIMOS PASSOS IMEDIATOS
 
1. **Clone local** — Você clonar backtest-pro em ~/backtest-pro/
2. **Estrutura MQL5** — Criar pastas e arquivos base
3. **BP_Constants.mqh** — Começar com enums e tipos
4. **BP_Indicators.mqh** — Implementar cálculos de indicadores
5. **Testes** — Compilação sem erros
 
---
 
## 10. REFERÊNCIAS
 
- **EA_BUILDING_GUIDE.md** — Framework alphaQuant completo
- **EA-ARCHITECTURE-EXEC-SUMMARY.md** — Visão executiva dos 4 EAs
- **ESTUDO-ARQUITETURA-EAS.md** — Análise completa de indicadores
- **PastEAs/** — BT_TT.mq5, dB_dT_finder.mq5, 12padraoes_exe_v2.mq5
 
---
 
**Status Final:** ? Análise completa, arquitetura definida, pronto para desenvolvimento.
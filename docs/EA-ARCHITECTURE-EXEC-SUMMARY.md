# BACKTEST PRO — Arquitetura de EAs
## Executive Summary para Revisão

**Preparado por:** Claude (análise técnica)  
**Data:** 26 de março de 2026  
**Status:** v1.0-draft (Aguardando aprovação de Clayton)  
**Documento completo:** `docs/EA-ARCHITECTURE.md`

---

## 🎯 PROPOSTA EXECUTIVA

**Problema:** Usuários conseguem combinar até 28 indicadores diferentes em múltiplas condições. Precisamos de uma quantidade eficiente de EAs (Expert Advisors) que cubra 95%+ das combinações possíveis.

**Solução:** 4 EAs principais + 1 gestão universal de stop/TP/trailing

| EA | Responsabilidade | Cobertura |
|---|---|---|
| **#1: Oscillators Core** | Osciladores + Filtros | ~65% |
| **#2: Price Action Core** | Estrutura de preço + Padrões | ~25% |
| **#3: Smart Money** | Conceitos institucionais (isolados) | ~5-10% |
| **#4: Volume & Volatility** | Volume, OBV, ATR como contexto | ~5% |

**Total de cobertura:** 100% (com R33: bloqueio SMC)

---

## 📊 MATRIZ RÁPIDA: O QUE COMBINA COM O QUÊ

```
                    Osc  Tend  Vol  Preço  Vol*  Padrão  SMC
Osciladores         ✓    ✓    ✓    ✓      ✓     ✓      ❌
Tendência           ✓    ✓    ✓    ✓      ✓     ✓      ❌
Volume              ✓    ✓    ✓    ✓      ✓     ✓      ❌
Preço               ✓    ✓    ✓    ✓      ✓     ✓      ❌
Volatilidade        ✓    ✓    ✓    ✓      ✓     ✓      ❌
Padrões Gráficos    ✓    ✓    ✓    ✓      ✓     ✓      ❌
Smart Money (SMC)   ❌   ❌   ❌   ❌      ❌    ❌      ✓*

Legenda: ✓ = Pode combinar | ❌ = Não pode combinar | ✓* = SMC isolado
```

**Lógica:**
- Osciladores funcionam bem como entrada com outros como filtro
- Preço + Padrões = lógica de estrutura natural
- SMC é abordagem completamente diferente → isolado

---

## 🔧 CADA EA PROCESSA

### EA #1: Oscillators Core (~65% dos backtests)

**Entrada (pode uma de cada):**
- RSI, Estocástico, CCI, Williams %R, MACD

**Filtros (qualquer combinação):**
- SMA/EMA (médias móveis com períodos customizáveis)
- Preço (OHLC simples, Range, Máx/Mín N períodos)
- Volume (absoluto e média móvel)
- Padrões de candle (Martelo, Engolfo, etc.)
- ATR (como filtro de volatilidade)

**Exemplos de estratégias:**
- "RSI(14) cruza 30" → Long
- "RSI(14) cruza 30 E SMA(200) acima" → Long com filtro
- "MACD cruza sinal E volume > média" → Entrada com confirmação
- "Estocástico cruza 20 E martelo forma" → Padrão + oscilador

---

### EA #2: Price Action Core (~25% dos backtests)

**Entrada (estrutura de preço):**
- Preço rompe máxima/mínima de N períodos
- Preço retesta nível anterior
- Fibonacci (retrações em swing)
- Gap (diferença entre fechamento anterior e abertura)

**Padrões visuais:**
- Martelo, Engolfo, Doji, Spinning Top, etc.

**Filtros de tendência (opcional):**
- SMA/EMA (confirma direção)
- SAR (confirmação de reversão)

**Exemplos:**
- "Martelo em zona de resistência" → Padrão + nível
- "Preço rompe máxima de 20 períodos com volume" → Breakout
- "Fibonacci 61.8% retesta E SMA(200) acima" → Nível + tendência

---

### EA #3: Smart Money Concepts (~5-10% dos backtests)

**Isolado de outras condições:**
- Fair Value Gap (FVG) — gap de preço
- Break of Structure (BoS) — rompimento de topo/fundo
- Change of Character (CHoCH) — possível reversão
- Order Block (OB) — zona institucional
- Liquidity Sweep (Sweep) — falso rompimento

**Entrada:** Quando preço retesta/penetra essas zonas

**Bloqueio:** Não pode combinar com Osciladores/Tendência/Volume/Preço simples

---

### EA #4: Volume & Volatility (~5% dos backtests)

**Entrada/Filtro:**
- Volume absoluto (> ou < threshold)
- OBV (On-Balance Volume subindo/caindo)
- ATR como contexto ambiental

**Gestão dinâmica:**
- Stop em múltiplo de ATR (ex: -2×ATR)
- TP em múltiplo de ATR (ex: +3×ATR)

---

## 🚦 BLOQUEIOS CRÍTICOS JÁ IMPLEMENTADOS

### Bloqueios Lógicos (32 regras R01-R32)
- ✅ Osciladores não podem estar acima E abaixo simultaneamente
- ✅ MACD não pode cruzar sinal para cima E para baixo no mesmo candle
- ✅ Preço não pode estar acima E abaixo de um nível simultaneamente
- ✅ Valores fora de faixa válida (RSI deve ser 0-100, Williams -100 a 0, etc.)
- ✅ Condição de saída não pode ser idêntica à de entrada

### ⚠️ BLOQUEIO FALTANDO: R33 (Smart Money Isolado)
**Atual:** Não há validação
**Proposto:**
- Se usuário adicionar qualquer SMC → Não pode adicionar não-SMC
- Se há não-SMC → Não pode adicionar SMC
- **Exceção possível:** Múltiplos SMC podem coexistir (v2.5+)

**Código necessário:**
```javascript
// Na função validateNewCondition()
const hasSMC = existingConds.some(c => SMC_IDS.includes(c.id));
const isSMC = SMC_IDS.includes(newCond.id);

if (hasSMC && !isSMC) {
  issues.push({type:'block',rule:'R33',msg:'Smart Money Concepts não podem ser combinados com outras condições.'});
}
if (!hasSMC && existingConds.length > 0 && isSMC) {
  issues.push({type:'block',rule:'R33',msg:'Smart Money Concepts não podem ser combinados com outras condições.'});
}
```

---

## 🗓️ ROADMAP DE IMPLEMENTAÇÃO

### FASE 1 — MVP (Imediato)
- ✅ EA #1: Oscillators Core (RSI, Estocástico, CCI, Williams)
  - Suporta 1-4 condições simultâneas
  - Filtros básicos (SMA/EMA)
  - ~65% de cobertura

- ✅ EA #2: Price Action Core (Preço, Padrões, Estrutura)
  - Rompimentos, padrões de candle, Fibonacci
  - ~25% de cobertura

- ✅ Implementar R33 (bloqueio SMC isolado)

### FASE 2 — v2.5 (Próximas semanas)
- ✅ EA #3: Smart Money Concepts (FVG, BoS, CHoCH, OB, Sweep)
  - Lógica diferente (não baseada em valores numéricos)
  - ~5-10% de cobertura

- ✅ Expandir EA #1:
  - Adicionar MACD, ADX, SAR, HiLo
  - Suportar até 6 condições
  - Melhorar filtros

### FASE 3 — v3.0 (Otimização)
- ✅ EA #4: Volume & Volatility Profile (se demanda existir)
- ✅ Combinações SMC inter-grupo (SMC + SMC com validações)
- ✅ Cruzamentos duplos avançados (SMA(50) × SMA(200), EMA(9) × EMA(21))
- ✅ Gestão dinâmica por ATR (stops e TP automáticos)

---

## 🔴 DECISÕES PENDENTES (CLAYTON)

1. **Onde MACD deve ficar?**
   - Opção A: Em "Oscillators Core" (atual proposta) ✓
   - Opção B: Em EA separado (complexa demais)

2. **ATR é entrada ou gestão?**
   - Atual: Considerado filtro ambiental
   - Decisão: Fica em EA #4 (Volume) ou em EA universal de gestão?

3. **Qual é o limite máximo de condições?**
   - Atual: Aviso em 4+ (R26)
   - Decisão: Bloquear em 5? 6? 8?

4. **SMC + SMC são permitidas?**
   - FVG + OB = Confluência de zonas (SIM?)
   - BoS + CHoCH = Lógica oposta (NÃO?)
   - Decisão: Mapa completo necessário para v2.5

5. **Quantos anos de dados históricos?**
   - Impacto: performance do backtest
   - Sugerido: 5-10 anos (2014-2024)

---

## 📈 ESTIMATIVA DE ESFORÇO POR EA

| EA | Indicadores | Validações | Complexidade | Dias |
|---|---|---|---|---|
| #1: Oscillators | 5 principais + 6 filtros | Zona-based | Média | 8-10 |
| #2: Price Action | 6 estruturais + padrões | Nível-based | Alta | 12-15 |
| #3: Smart Money | 5 conceitos | Zona-based | Muito alta | 15-20 |
| **TOTAL MVP** | | | | **35-45 dias** |

*(Estimativa para desenvolvimento MQL5, testing, debugging)*

---

## ✅ RESULTADO FINAL

**Resposta à pergunta original:**

> "Quantas EAs precisamos e o que cada EA deve executar?"

**Resposta:**
- **4 EAs necessárias** para MVP (Phases 1-2)
- **EA #1** processa 65% (Osciladores + Filtros)
- **EA #2** processa 25% (Price Action + Padrões)
- **EA #3** processa 5-10% (Smart Money isolado)
- **EA #4** processa 5% (Volume/Volatility - nice-to-have)
- **Gestão universal** (Stop/TP/Trailing) compartilhada por todos

---

## 📋 PRÓXIMOS PASSOS

1. **Clayton revisa proposta** ← VOCÊ ESTÁ AQUI
2. Clayton aprova ou solicita mudanças
3. Implementar R33 no app.html
4. Corrigir constantes (OSC_IDS inclua MACD)
5. Atualizar `docs/EA-ARCHITECTURE.md` com feedback
6. Fazer commit no GitHub
7. Iniciar desenvolvimento de EA #1

---

## 📞 PERGUNTAS?

Este documento é um **draft para revisão**. Toda a análise está em `docs/EA-ARCHITECTURE.md` com detalhes completos de:
- Parâmetros específicos de cada indicador
- Validações por indicador
- Exemplos de estratégias
- Código sugerido para R33

**Status:** ✅ Aguardando aprovação para GitHub

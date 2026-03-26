# BACKTEST PRO — Estudo Completo de Arquitetura de EAs
## Mapeamento de Combinações Paramétricas e Proposição de Arquitetura

**Data:** 26 de março de 2026  
**Scope:** MVP v2.0+ (estado atual do GitHub)  
**Objetivo:** Determinar quantos EAs são necessários e quais combinações cada um deve processar

---

## 1. INVENTÁRIO COMPLETO DE INDICADORES/CONDIÇÕES

### 1.1 Grupos de Indicadores Implementados

| Grupo | Indicadores | Qtd | Observações |
|---|---|---|---|
| **Osciladores** | RSI, Estocástico, MACD, CCI, Williams %R | 5 | Operam em zonas definidas (0-100, -100-0) |
| **Tendência** | SMA, EMA, ADX, SAR, HiLo Activator, Bollinger Bands, VWAP | 7 | Indicadores de direção/momento |
| **Volume** | Volume absoluto, Volume Médio, OBV | 3 | Medem pressão de compra/venda |
| **Preço** | Preço (OHLC), Range, Máx/Mín N períodos, Gap, Máx/Mín dia anterior, Fibonacci | 6 | Padrões estruturais de preço |
| **Volatilidade** | ATR | 1 | Mede oscilação média |
| **Padrões Gráficos** | Padrões de Candle (Martelo, Engolfo, Doji, etc.) | 1 | Formações visuais de candlestick |
| **Smart Money Concepts** | FVG, BoS, CHoCH, Order Block, Liquidity Sweep | 5 | Conceitos institucionais — **NÃO COMBINAM com nada** |
| **TOTAL** | | **28** | |

---

## 2. MAPEAMENTO DE RESTRIÇÕES LÓGICAS JÁ IMPLEMENTADAS

### 2.1 Bloqueios Absolutos (type:'block')

| Regra | Descrição | Aplica a | Permite combinação? |
|---|---|---|---|
| **R01** | Condição idêntica repetida | Todas | ❌ Bloqueio total |
| **R02-R04** | Osciladores com valores contraditórios | Osciladores (mesmo ID) | ❌ Bloqueio intra-grupo |
| **R05-R07** | Médias móveis com direções contraditórias | Médias (mesmo período) | ❌ Bloqueio intra-grupo |
| **R08-R10** | VWAP com direções contraditórias | VWAP duplicado | ❌ Bloqueio intra-grupo |
| **R11** | MACD com cruzamentos opostos | MACD duplicado | ❌ Bloqueio intra-grupo |
| **R12** | OBV subindo e caindo simultaneamente | OBV duplicado | ❌ Bloqueio intra-grupo |
| **R13-R14** | Volume com valores contraditórios | Volume (mesmo tipo) | ❌ Bloqueio intra-grupo |
| **R15-R17** | Preço com valores contraditórios | Preço duplicado | ❌ Bloqueio intra-grupo |
| **R18** | Bollinger bandas sup. e inf. simultâneas | BB duplicado | ❌ Bloqueio intra-grupo |
| **R27-R31** | Valores fora de faixa válida | Osciladores, Volume, Range | ❌ Bloqueio total |
| **R32** | Saída idêntica a entrada | Saída por condição | ❌ Bloqueio total |
| **R34** | Janela operacional inválida | Horários | ❌ Bloqueio total |

### 2.2 Avisos (type:'warn')

| Regra | Descrição | Recomendação | Permite? |
|---|---|---|---|
| **R19** | SMA e EMA mesmo período | Use apenas uma | ⚠️ Alerta |
| **R22** | SMA/EMA períodos muito próximos | Escolha períodos mais distintos | ⚠️ Alerta |
| **R23** | Volume + Volume Médio redundância | Use apenas Volume Médio | ⚠️ Alerta |
| **R26** | 4+ condições simultâneas | Pode haver sinais insuficientes | ⚠️ Alerta |
| **R30** | CCI fora de faixa normal | Sinais podem ser raros | ⚠️ Alerta |
| **R35** | Janela operacional < timeframe | Nenhum candle completo cabe | ⚠️ Alerta |

### 2.3 Restrições Não-Explícitas (Observadas no Código)

❌ **Smart Money Concepts NÃO COMBINAM com nada:**
- Se usuário tenta adicionar qualquer SMC enquanto há condições não-SMC → Deve ser bloqueado
- Se usuário tenta adicionar não-SMC enquanto há condições SMC → Deve ser bloqueado
- **Status atual:** Não há validação R33 implementada explicitamente no `app.html`
- **Recomendação:** Implementar bloqueio antes de prosseguir com EAs

---

## 3. ANÁLISE DE COMBINABILIDADE INTER-GRUPOS

### 3.1 Matriz de Compatibilidade

```
                    Osc  Tend  Vol  Preço  Vol*  Padrão  SMC
Osciladores (Osc)    ✓    ✓    ✓    ✓      ✓     ✓      ❌
Tendência (Tend)     ✓    ✓    ✓    ✓      ✓     ✓      ❌
Volume (Vol)         ✓    ✓    ✓    ✓      ✓     ✓      ❌
Preço (Preço)        ✓    ✓    ✓    ✓      ✓     ✓      ❌
Volatilidade (Vol*)  ✓    ✓    ✓    ✓      ✓     ✓      ❌
Padrões Gráficos     ✓    ✓    ✓    ✓      ✓     ✓      ❌
Smart Money (SMC)    ❌   ❌   ❌   ❌      ❌    ❌      ✓*

* SMC com SMC (múltiplos conceitos SMC) requer análise específica
```

### 3.2 Justificativa de Compatibilidades

#### ✓ **Osciladores + Tendência** (COMPATÍVEL)
**Exemplo real:** "Compra quando RSI cruzar 30 E preço está acima de SMA(200)"
- Oscilador: Entrada
- Tendência: Filtro

#### ✓ **Osciladores + Volume** (COMPATÍVEL)
**Exemplo:** "Compra quando RSI cruza 30 E volume > média"
- Oscilador: Entrada
- Volume: Confirmação

#### ✓ **Osciladores + Preço** (COMPATÍVEL)
**Exemplo:** "Compra quando RSI cruza 30 E preço rompe máxima de 20 períodos"
- Oscilador: Gatilho
- Preço: Estrutura

#### ✓ **Osciladores + Volatilidade** (COMPATÍVEL)
**Exemplo:** "Compra quando RSI cruza 30 E ATR > 100"
- Oscilador: Entrada
- Volatilidade: Filtro de ambiente

#### ✓ **Osciladores + Padrões Gráficos** (COMPATÍVEL)
**Exemplo:** "Compra quando RSI cruza 30 E formação é martelo"
- Oscilador: Entrada
- Padrão: Confirmação visual

#### ✓ **Tendência + Tendência** (COMPATÍVEL)
**Exemplo:** "Compra quando preço cruza acima de SMA(50) E SMA(50) está acima de SMA(200)"
- Dupla validação de tendência

#### ✓ **Tendência + Volume** (COMPATÍVEL)
**Exemplo:** "Compra quando preço rompe máxima E volume > média"
- Estrutura de preço + Pressão

#### ✓ **Tendência + Preço** (COMPATÍVEL)
**Exemplo:** "Compra quando SMA(50) cruza acima de SMA(200) E preço rompe resistência anterior"
- Cruzamento de médias + Nível estrutural

#### ✓ **Tendência + Volatilidade** (COMPATÍVEL)
**Exemplo:** "Compra quando preço cruza SMA E ATR está elevado"
- Entrada + Contexto de volatilidade

#### ✓ **Tendência + Padrões Gráficos** (COMPATÍVEL)
**Exemplo:** "Compra quando martelo forma E preço está acima de SMA(200)"
- Padrão + Tendência de fundo

#### ✓ **Volume + Preço** (COMPATÍVEL)
**Exemplo:** "Compra quando volume sobe E preço rompe resistência"
- Pressão + Estrutura

#### ✓ **Volume + Volatilidade** (COMPATÍVEL)
**Exemplo:** "Compra quando volume > média E ATR elevado"
- Pressão + Ambiente volátil

#### ✓ **Volume + Padrões Gráficos** (COMPATÍVEL)
**Exemplo:** "Compra quando martelo forma com volume elevado"
- Padrão com pressão confirmada

#### ✓ **Preço + Volatilidade** (COMPATÍVEL)
**Exemplo:** "Compra quando rompe máxima de 20 períodos E ATR > 100"
- Estrutura + Contexto volátil

#### ✓ **Preço + Padrões Gráficos** (COMPATÍVEL)
**Exemplo:** "Compra quando martelo forma na resistência anterior"
- Padrão em nível estrutural

#### ✓ **Volatilidade + Padrões Gráficos** (COMPATÍVEL)
**Exemplo:** "Compra quando martelo forma com ATR elevado"
- Padrão + Contexto de volatilidade

#### ❌ **Smart Money + Qualquer Outro** (INCOMPATÍVEL)
**Razão:** SMC é abordagem diferente — trabalha com conceitos institucionais (FVG, BoS, CHoCH, OB, Sweep) e já encapsula lógica de entrada/confirmação completa. Misturar com osciladores/tendência adiciona ruído.

**Exceção possível (SMC + SMC):**
- FVG + BoS? → Talvez (ambos estruturais)
- FVG + Order Block? → Possível (buscam zonas)
- BoS + CHoCH? → Não (lógica oposta)
- Múltiplos SMC exigem validação específica (escopo v3+)

---

## 4. COMBINAÇÕES POSSÍVEIS POR CATEGORIA

### 4.1 Combinações Permitidas (Resumo)

**Total de grupos não-SMC:** 6 (Osciladores, Tendência, Volume, Preço, Volatilidade, Padrões)

**Número máximo de combinações inter-grupos:**
- C(6,1) = 6 (um grupo apenas)
- C(6,2) = 15 (dois grupos)
- C(6,3) = 20 (três grupos)
- C(6,4) = 15 (quatro grupos)
- C(6,5) = 6 (cinco grupos)
- C(6,6) = 1 (todos os seis grupos)
- **TOTAL TEÓRICO: 63 combinações inter-grupos**

Mas nem todas fazem sentido operacionalmente. Exemplo:
- "Apenas volatilidade (ATR)" como entrada? Fraco.
- "Apenas volume" como entrada? Raramente.

### 4.2 Combinações com Relevância Operacional

**Tier 1 — Altamente Relevantes (Provavelmente usadas em >5% dos backtests):**
1. Osciladores isolados
2. Osciladores + Tendência
3. Osciladores + Preço
4. Osciladores + Padrões Gráficos
5. Tendência isolada
6. Tendência + Preço
7. Tendência + Padrões Gráficos
8. Padrões Gráficos + Tendência (como filtro)

**Tier 2 — Relevantes (Niche, 1-5% dos backtests):**
9. Osciladores + Volume
10. Osciladores + Volatilidade
11. Tendência + Volume
12. Preço + Padrões Gráficos
13. Volume como filtro

**Tier 3 — Raras (0.1-1%):**
14. Volatilidade isolada
15. Combinações complexas com 4+ grupos

**Not-Relevant — Praticamente impossível:**
- "Apenas Volume" como sinal de entrada
- Combinações que caem em bloqueios (R02-R32)

---

## 5. ARQUITETURA PROPOSTA: ESTRUTURA DE EAs

### 5.1 Princípios de Design

1. **Cada EA processa um "universo de entrada coerente"**
   - Osciladores, tendência, preço e padrões que fazem sentido juntos
   - Não criar EAs para combinações raras

2. **Gestão (Stop/TP/Trailing) é UNIVERSAL**
   - Todos os EAs suportam: stop fixo, stop candle, stop N candles
   - Take profit: fixo, múltiplo R:R, sem alvo
   - Trailing, parcial, saída por condição são separáveis

3. **Dado que Smart Money é isolado, criar EA dedicado**
   - SMC requer lógica diferente (não baseada em valores numéricos simples)

4. **Priorizar EAs que cubrem 80% da demanda**
   - Não criar EA para cada combinação possível (matrix explosion)

### 5.2 Proposta de Arquitetura: 4 EAs principais

#### **EA #1: "Oscillators Core" — Osciladores Puros + Filtros**

**Processa:**
- Osciladores isolados (RSI, Estocástico, CCI, Williams %R, MACD)
- Osciladores + Tendência (qualquer uma: SMA, EMA, ADX, SAR, HiLo, BB, VWAP)
- Osciladores + Volume (filtro)
- Osciladores + Preço (filtro estrutural)
- Osciladores + Padrões Gráficos
- Osciladores + Volatilidade (filtro ATR)

**Características:**
- Processamento direto de valores numéricos
- Suporta até 4 condições simultâneas (osciladores que não se bloqueiam)
- Lógica de inferência de direção a partir de osciladores
- Compatível com todas as gestões

**Exemplos de estratégias:**
- "RSI(14) cruza 30 em compra" → Long
- "RSI(14) cruza 30 E SMA(200) acima" → Long + filtro
- "RSI(14) cruza 30 E volume > média E preço > SMA(50)" → Long com 3 condições

**Indicadores processados internamente:**
- RSI (período customizável)
- Estocástico (K, D, slowing customizável)
- CCI (período customizável)
- Williams %R (período customizável)
- MACD (fast, slow, signal customizáveis)
- SMA, EMA (períodos customizáveis)
- ADX (período customizável)
- SAR (aceleração customizável)
- HiLo (período customizável)
- Bollinger Bands (período, desvio customizáveis)
- VWAP
- Volume (absoluto e média móvel)
- Price levels (OHLC)
- ATR (período customizável)

---

#### **EA #2: "Price Action Core" — Estrutura de Preço + Padrões**

**Processa:**
- Preço isolado (suporte/resistência, ranges, gaps, fibonacci)
- Preço + Tendência (SMA, EMA, SAR, HiLo como estrutura)
- Preço + Padrões Gráficos (Martelo na resistência, Engolfo em fundo, etc.)
- Preço + Volume
- Padrões Gráficos isolados
- Padrões Gráficos + Tendência como filtro

**Características:**
- Lógica estrutural (não apenas valores)
- Detecção de padrões de candle
- Suporte a swings (máximas/mínimas de N períodos)
- Rompimentos e retests
- Fibonacci e Golden ratios

**Exemplos:**
- "Preço rompe máxima de 20 períodos" → Breakout
- "Martelo em zona de resistência" → Pattern + Level
- "Engolfo E preço acima de SMA(200)" → Pattern + Trend filter
- "Preço retesta Fibonacci 61.8%" → Fib level

**Indicadores processados:**
- Suportes/resistências (máximas/mínimas)
- Ranges
- Gaps
- Máx/Mín dia anterior
- Fibonacci (retrações, extensões)
- Padrões de candle (detecção visual)

---

#### **EA #3: "Smart Money Concepts" — Conceitos Institucionais**

**Processa:**
- Fair Value Gap (FVG) isolado ou + outro SMC?
- Break of Structure (BoS) isolado ou + outro SMC?
- Change of Character (CHoCH) isolado ou + outro SMC?
- Order Block (OB) isolado ou + outro SMC?
- Liquidity Sweep (Sweep) isolado ou + outro SMC?

**Características:**
- Lógica diferente (análise estrutural institucional)
- Zonas de confluência
- Reconhecimento de padrões SMC
- **NÃO permite** mistura com Osciladores/Tendência/Volume/Preço simples

**Exemplos:**
- "Preço retorna ao FVG (zona crítica)" → Compra no pull-back
- "BoS + CHoCH" → Confirmação de reversão estrutural (se Tier 1)
- "Order Block + reteste" → Entrada em zona institucional

**Indicadores processados:**
- Fair Value Gap detection
- Structure breaks
- Order blocks
- Liquidity sweeps
- Change of character

---

#### **EA #4: "Volume & Volatility Profile" — Volume + Volatilidade + Filtros**

**Processa:**
- Volume isolado (raro, mas suportado)
- Volume + Tendência (volume na confirmação)
- Volume + Preço (volume em rompimentos)
- Volume + Padrões (volume no padrão)
- Volatilidade (ATR) + Qualquer coisa
- Volatilidade isolada (filtro ambiental)

**Características:**
- Profile de volume (POC, VAH, VAL)
- On-Balance Volume (OBV)
- Volume Médio
- ATR como contexto
- Gestão de risco dinâmica (stop baseado em ATR)

**Exemplos:**
- "Volume > média E preço rompe" → Breakout com força
- "ATR > 100 E SMA(50) com tendência" → Trade em ambiente volátil
- "OBV subindo E padrão de compra" → Pressão + Pattern

---

### 5.3 Proposta Alternativa: 5 EAs (mais granular)

Se preferir mais especialização:

1. **"Pure Oscillators"** → Apenas osciladores isolados
2. **"Oscillators + Filters"** → Osciladores + Tendência/Preço/Padrões
3. **"Price Action"** → Preço + Padrões + Tendência como filtro
4. **"Smart Money"** → SMC isolado
5. **"Volume & Risk"** → Volume, Volatilidade, Gestão dinâmica

**Trade-off:** Mais EAs = mais especialização, mas duplicação de código de gestão.

---

## 6. MAPEAMENTO DETALHADO DE PARÂMETROS POR EA

### 6.1 Estrutura Universal de Parâmetros (Todos os EAs)

**Entrada (Conditions):**
```json
{
  "conditions": [
    {
      "id": "rsi",
      "name": "IFR (RSI)",
      "params": {
        "per": 14,
        "cond": "cruza acima de",
        "val": 30
      }
    },
    // ... mais condições
  ],
  "direction": "long", // long | short | both
  "entryType": "breakout", // breakout | next_open | sig_close
  "validityCandles": 3
}
```

**Stop Loss:**
```json
{
  "stopType": "fixed", // fixed | hl_candle | n_candles
  "stopPts": 200,          // para 'fixed'
  "stopOffset": 10,        // para 'hl_candle' ou 'n_candles'
  "stopCandles": 5         // para 'n_candles'
}
```

**Take Profit:**
```json
{
  "tpType": "fixed", // fixed | rr | none
  "tpPts": 400,    // para 'fixed'
  "tpRR": 2        // para 'rr' (múltiplo do risco)
}
```

**Gestão:**
```json
{
  "trailing": {
    "enabled": true,
    "activation": 100,  // pontos de lucro
    "distance": 100,    // distância do trailing
    "step": 50          // step do movimento
  },
  "partial": {
    "enabled": true,
    "pct": 50,          // % da posição
    "at": 200,          // pontos de lucro
    "moveStop": true    // mover stop para entrada
  },
  "exitCondition": {
    "enabled": true,
    "condition": { /* estrutura igual a 'conditions' */ }
  }
}
```

**Contexto:**
```json
{
  "asset": "WIN",    // WIN | WDO | IND | DOL
  "timeframe": "5m", // 1m | 5m | 15m | 60m | D
  "windowStart": "09:00",
  "windowEnd": "17:30",
  "closeOnWindowEnd": true
}
```

### 6.2 Parâmetros Específicos por EA

#### **EA #1: Oscillators Core**

**Osciladores suportados:**
```
RSI (IFR)
├─ per: 5-50 (default 14)
├─ cond: "cruza acima de", "cruza abaixo de", "está acima de", "está abaixo de"
└─ val: 0-100 (default 30 para compra, 70 para venda)

Estocástico
├─ per: 5-50 (K period, default 14)
├─ per2: 3-10 (D period, default 3)
├─ per3: 1-3 (slowing, default 1)
├─ cond: "cruza acima de", "cruza abaixo de", "está acima de", "está abaixo de"
└─ val: 0-100 (default 20/80)

MACD
├─ per: 12 (fast, não customizável agora)
├─ per2: 26 (slow, não customizável agora)
├─ per3: 9 (signal, não customizável agora)
├─ cond: "MACD cruza acima do sinal", "MACD cruza abaixo", "acima de zero", "abaixo de zero"
└─ val: N/A

CCI
├─ per: 5-50 (default 20)
├─ cond: "cruza acima de", "cruza abaixo de", "está acima de", "está abaixo de"
└─ val: -300 a +300 (default -100/+100)

Williams %R
├─ per: 5-50 (default 14)
├─ cond: "cruza acima de", "cruza abaixo de", "está acima de", "está abaixo de"
└─ val: -100 a 0 (default -80/-20)
```

**Filtros suportados (opcionais):**
```
SMA
├─ per: 5-500 (default 200)
├─ cond: "Preço cruza acima", "Preço cruza abaixo", "Preço está acima", "Preço está abaixo"
└─ Combinável com cruzamentos duplos

EMA
├─ per: 5-500 (default 200)
└─ Mesmas condições que SMA

Bollinger Bands
├─ per: 5-50 (default 20)
├─ dev: 1.5-3 (desvio, default 2)
└─ cond: "toca banda sup.", "cruza banda sup.", "sai da banda inf."

VWAP
├─ Sem parâmetros customizáveis
└─ cond: "está acima do VWAP", "está abaixo", "cruza acima", "cruza abaixo"

ADX
├─ per: 5-50 (default 14)
├─ cond: "está acima de", "está abaixo de", "cruza acima de", "cruza abaixo de"
└─ val: 0-100 (default 25 = tendência forte)

SAR Parabólico
├─ accel: 0.01-0.2 (default 0.02)
├─ max: 0.2 (default)
└─ cond: "está acima do SAR", "está abaixo do SAR", "cruza acima", "cruza abaixo"

HiLo Activator
├─ per: 3-50 (default 6)
└─ cond: "HiLo virou compra", "HiLo virou venda"

Volume
├─ val: > 0 (threshold em número de contratos/volume)
└─ cond: "é maior que", "é menor que"

Volume Médio
├─ per: 5-50 (default 20)
├─ val: > 0
└─ cond: "é maior que", "é menor que"

Preço (OHLC)
├─ tipo: Open, High, Low, Close
├─ cond: "está acima de", "está abaixo de", "cruza acima de", "cruza abaixo de"
└─ val: preço em pontos

Range (Máx-Mín)
├─ cond: "é maior que", "é menor que"
└─ val: > 0 (em pontos)

ATR (Volatilidade)
├─ per: 5-50 (default 14)
├─ cond: "está acima de", "está abaixo de"
└─ val: > 0 (em pontos)

Padrões de Candle
├─ padrão: "Martelo", "Engolfo", "Doji", "Spinning Top", "Morning Star", "Evening Star", etc.
└─ dir: "compra", "venda", "ambos"
```

---

#### **EA #2: Price Action Core**

```
Preço (OHLC)
├─ Conforme acima

Range (Máx-Mín)
├─ Conforme acima

Máx/Mín N períodos
├─ per: 5-100 (default 20)
├─ cond: "Preço rompe máxima", "Preço rompe mínima", "Preço retesta"
└─ tipo: "rompimento", "reteste", "confluência"

Gap
├─ cond: "Gap de alta", "Gap de baixa"
├─ val: > 0 (tamanho mínimo em pontos)
└─ tipo: "volume", "fechamento anterior"

Máx/Mín Dia Anterior
├─ cond: "Preço está acima da máxima", "está abaixo da mínima", "cruza"
└─ aplica-se apenas a timeframes intraday

Fibonacci
├─ per: 5-500 (default 50, swing de quantos candles)
├─ niveis: 23.6%, 38.2%, 50%, 61.8%, 78.6%, 100%, 127.2%, 161.8%
├─ cond: "Preço toca nível X", "Preço sai de", "retesta"
└─ tipo: "retração", "extensão"

Padrões de Candle
├─ padrão: Martelo, Engolfo, Doji, Spinning Top, Morning Star, Evening Star, Three White Soldiers, etc.
├─ confirmação: "em zona de resistência", "em zona de suporte", "sem confirmação"
└─ combinável com: SMA/EMA como filtro de tendência

Suporte/Resistência
├─ per: 5-100 (últimos N períodos para identificar SR)
├─ cond: "Preço está acima", "está abaixo", "cruza"
└─ tipo: "automático", "manual"

Estrutura (HiLo Activator)
├─ per: 3-50 (default 6)
└─ cond: "Rompimento de topo", "Rompimento de fundo"
```

---

#### **EA #3: Smart Money Concepts**

```
Fair Value Gap (FVG)
├─ type: "bullish", "bearish"
├─ cond: "Preço retorna ao FVG", "Preço chega perto", "Preço penetra"
├─ val: tolerância em pontos (default 50)
└─ per: períodos para buscar FVG (default 50)

Break of Structure (BoS)
├─ type: "bullish", "bearish"
├─ per: períodos para análise (default 10)
├─ cond: "BoS detectado e confirmado", "BoS detectado (sem conf.)"
└─ confirmação: volume? velocidade? impulso?

Change of Character (CHoCH)
├─ type: "bullish", "bearish"
├─ per: períodos para análise (default 10)
├─ cond: "CHoCH detectado"
└─ implicação: reversão potencial

Order Block (OB)
├─ type: "bullish", "bearish" (último candle oposto antes do impulso)
├─ cond: "Preço retesta Order Block", "Preço se aproxima"
├─ val: tolerância em pontos (default 150)
└─ per: períodos para buscar (default N/A)

Liquidity Sweep
├─ type: "bullish", "bearish"
├─ per: períodos para análise (default 20)
├─ cond: "Sweep detectado"
├─ val: tolerância (default 10 pontos)
└─ implicação: falso rompimento antes de reversão

Combinações SMC (v3+)
├─ FVG + OB: confluência de zonas?
├─ BoS + OB: estrutura + zona?
├─ FVG + BoS: gap + rompimento?
└─ Outras combinações exigem análise específica
```

---

#### **EA #4: Volume & Volatility Profile**

```
Volume Absoluto
├─ cond: "é maior que", "é menor que"
├─ val: threshold em contratos/volume
└─ combinável com: preço, padrões, tendência

Volume Médio
├─ per: 5-50 (default 20)
├─ cond: "é maior que", "é menor que"
└─ val: threshold

On-Balance Volume (OBV)
├─ cond: "está subindo", "está caindo", "cruza acima de", "cruza abaixo de nível"
└─ val: nível numérico (para cruzamento)

ATR (Average True Range)
├─ per: 5-50 (default 14)
├─ cond: "está acima de", "está abaixo de"
├─ val: threshold em pontos
└─ uso: filtro ambiental, stop dinâmico

Profile de Volume (POC, VAH, VAL)
├─ per: períodos para calcular perfil
├─ cond: "Preço toca POC", "Preço sai de VAL-VAH", "está acima de VAH"
└─ tipo: "profile diário", "profile intraday", "profile customizado"

Gestão Dinâmica por ATR
├─ stopTipo: "atr_multiple" (ex: 2× ATR)
├─ tpTipo: "atr_multiple" (ex: 3× ATR)
└─ Exemplo: Stop = -2×ATR, TP = +3×ATR
```

---

## 7. TABELA RESUMO: QUAIS INDICADORES EM CADA EA

| Indicador | EA #1 | EA #2 | EA #3 | EA #4 | Notas |
|---|---|---|---|---|---|
| RSI | ✓ | ✗ | ✗ | ✗ | Core oscilador |
| Estocástico | ✓ | ✗ | ✗ | ✗ | Core oscilador |
| MACD | ✓ | ✗ | ✗ | ✗ | Core oscilador |
| CCI | ✓ | ✗ | ✗ | ✗ | Core oscilador |
| Williams %R | ✓ | ✗ | ✗ | ✗ | Core oscilador |
| SMA/EMA | ✓ | ✓* | ✗ | ✗ | *Filtro em EA #2 |
| Bollinger | ✓ | ✓* | ✗ | ✗ | *Filtro em EA #2 |
| VWAP | ✓ | ✓* | ✗ | ✗ | *Filtro em EA #2 |
| ADX | ✓ | ✗ | ✗ | ✗ | Força de tendência |
| SAR | ✓ | ✓* | ✗ | ✗ | *Estrutura em EA #2 |
| HiLo Activator | ✓ | ✓ | ✗ | ✗ | Estrutura |
| Preço (OHLC) | ✓ | ✓ | ✗ | ✗ | Ambos suportam |
| Range | ✓ | ✓ | ✗ | ✗ | Ambos suportam |
| Máx/Mín N períodos | ✓ | ✓ | ✗ | ✗ | Ambos suportam |
| Gap | ✗ | ✓ | ✗ | ✗ | Price Action |
| Máx/Mín Dia Anterior | ✗ | ✓ | ✗ | ✗ | Price Action |
| Fibonacci | ✗ | ✓ | ✗ | ✗ | Price Action |
| Padrões de Candle | ✓ | ✓ | ✗ | ✗ | Ambos suportam |
| ATR | ✓ | ✗ | ✗ | ✓ | Volatilidade |
| Volume Absoluto | ✓ | ✗ | ✗ | ✓ | Ambos |
| Volume Médio | ✓ | ✗ | ✗ | ✓ | Ambos |
| OBV | ✓ | ✗ | ✗ | ✓ | Ambos |
| FVG | ✗ | ✗ | ✓ | ✗ | SMC only |
| BoS | ✗ | ✗ | ✓ | ✗ | SMC only |
| CHoCH | ✗ | ✗ | ✓ | ✗ | SMC only |
| Order Block | ✗ | ✗ | ✓ | ✗ | SMC only |
| Liquidity Sweep | ✗ | ✗ | ✓ | ✗ | SMC only |

---

## 8. RECOMENDAÇÃO FINAL: ROADMAP DE IMPLEMENTAÇÃO

### **FASE 1 (MVP — Essencial para v2.0):**
- ✓ **EA #1: Oscillators Core** (RSI, Estocástico, MACD, CCI, Williams)
  - Suporta 1-4 condições simultâneas
  - Suporta filtros básicos (SMA/EMA)
  - ~60-70% dos backtests cai nesta categoria

- ✓ **EA #2: Price Action Core** (Preço, Padrões, Estrutura)
  - Suporta rompimentos, padrões, Fibonacci
  - ~20-25% dos backtests

- ✓ **Implementar bloqueio R33** (Smart Money isolado)
  - Ainda não tem validação explícita no app.html

### **FASE 2 (v2.5 — Complementar):**
- ✓ **EA #3: Smart Money Concepts** (FVG, BoS, CHoCH, OB, Sweep)
  - ~5-10% dos backtests (mercado nicho)

- ✓ **Expandir EA #1** com ADX, SAR, HiLo, ATR, Volume, OBV
  - Suportar até 6 condições
  - Combinações mais complexas

### **FASE 3 (v3.0 — Otimização):**
- ✓ **EA #4: Volume & Volatility Profile** (se demanda existir)
- ✓ **Combinações SMC inter-grupo** (SMC + SMC validação)
- ✓ **Cruzamentos duplos avançados** (SMA(50) × SMA(200), EMA(9) × EMA(21))
- ✓ **Gestão dinâmica** (stop/TP baseado em ATR)

---

## 9. DIRETRIZES TÉCNICAS PARA IMPLEMENTAÇÃO

### 9.1 Padrão Arquitetural por EA

```
EA_Oscillators_Core.mq5
├─ OnInit() → carregar períodos de osciladores
├─ OnTick() → calcular RSI, Estocástico, MACD, CCI, Williams
├─ OnTick() → carregar parâmetros via extern (JSON parser)
├─ validateConditions() → verificar se todas as condições atendidas
├─ executeEntry() → if all conditions && !already_in_trade
├─ manage Position() → aplicar trailing, parcial, saída por condição
├─ OnDeinit() → cleanup
└─ main trade logic (Buy/Sell/Close)

EA_PriceAction_Core.mq5
├─ Focado em: níveis (suporte/resistência), padrões, estrutura
├─ onTick() → detectar padrões de candle
├─ onTick() → calcular Fibonacci, gaps, máximas/mínimas de N períodos
├─ validateConditions() → estrutura semelhante
└─ Trade logic (Price action signals)

EA_SmartMoney_Concepts.mq5
├─ Lógica totalmente diferente
├─ FVG detection, BoS detection, CHoCH detection, OB detection, Sweep detection
├─ Zone management (onde múltiplas zonas se sobrepõem)
├─ validateConditions() → adaptada para SMC (não valores numéricos)
└─ Trade logic (Smart money signals)

EA_Volume_Volatility.mq5
├─ Focado em volume, OBV, ATR, profile
├─ Dynamic stop/TP calculation
└─ Environmental filters
```

### 9.2 Abstração de Parâmetros

Cada EA recebe configuração JSON convertida de:

```json
{
  "ea_type": "oscillators",  // oscillators | price_action | smart_money | volume_volatility
  "conditions": [ ... ],
  "stop_loss": { ... },
  "take_profit": { ... },
  "management": { ... },
  "asset": "WIN",
  "timeframe": "5m"
}
```

### 9.3 Tratamento de Overlaps

Se usuário pedir combinação que cai em múltiplos EAs → **Primeira condição determina EA**

Exemplo: "RSI(14) cruza 30 E preço rompe máxima de 50" 
- RSI = Oscillators Core
- Preço = Price Action Core
- **Decisão:** Usar EA #1 (Oscillators) como primário, usar EA #2 como suporte?
- **OU**: Bloquear combinação?
- **Recomendação:** Permitir em EA #1 (Oscillators Core suporta filtros de preço)

---

## 10. QUESTÕES ABERTAS PARA CLAYTON

1. **Bloqueio R33:** Deseja bloquear SMC + não-SMC antes de prosseguir com EAs?
   - Simples: bloqueio total (SMC isolado)
   - Complexo: análise por combinação SMC

2. **Combinações SMC inter-grupo:** Quantos SMC diferentes podem coexistir?
   - FVG + BoS (estrutural + estrutural) = OK?
   - FVG + OB (gap + zona) = OK?
   - BoS + CHoCH (opostos lógicos) = Bloquear?

3. **Prioridade de EAs:** Qual ordem de implementação?
   - Sugerido: #1 (Osciladores) → #2 (Price Action) → #3 (SMC) → #4 (Volume)

4. **Limite de condições:** Máximo de quantas condições simultâneas?
   - Atualmente: aviso em 4+
   - Recomendação: permitir até 6, bloquear em 7+

5. **Escopo de ativos:** Todos os EAs suportam WIN, WDO, IND, DOL?
   - Simples: sim
   - Complexo: padrões de candle funcionam melhor em alguns ativos?

6. **Dados históricos:** Quantos anos de dados pré-carregados no servidor MT5?
   - Simples: 5-10 anos (2014-2024)
   - Impacta: performance do backtest

---

## RESUMO EXECUTIVO

| Critério | Resposta |
|---|---|
| **Quantas combinações possíveis?** | ~63 inter-grupos (em teoria), mas ~40-50 operacionalmente relevantes |
| **Quantas EAs necessárias?** | **4 principais** (ou 5 com granularidade extra) |
| **EA #1 cobertura?** | ~65% dos backtests (Osciladores + Filtros) |
| **EA #2 cobertura?** | ~25% dos backtests (Price Action) |
| **EA #3 cobertura?** | ~5-10% dos backtests (Smart Money) |
| **EA #4 cobertura?** | ~5% dos backtests (Volume/Volatility) |
| **Bloqueios críticos?** | SMC isolado (R33) — não implementado, deve ser adicionado |
| **Roadmap sugerido?** | EA #1 MVP, EA #2 v2.5, EA #3 v2.5, EA #4 v3.0 |
| **Gestão universal?** | SIM — stop/TP/trailing idêntico em todos os EAs |


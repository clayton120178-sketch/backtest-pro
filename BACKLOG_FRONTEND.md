# BacktestPro - Backlog de Alteracoes Frontend

## [2026-04-17] BoS: Inputs de limites das pernas

### Contexto
A logica do Break of Structure (BoS) foi reescrita com 3 fases bem definidas
e limites configuraveis para filtrar sinais de qualidade. Os inputs ja foram
adicionados no backend (BP_SmartMoney.mqh + EA). Quando o frontend for
atualizado, adicionar os seguintes inputs no grupo Smart Money.

### Inputs a adicionar (grupo [11] Smart Money)

```mql5
input int    InpBOS_Leg1Min       = 2;  // [BoS] Min candles 1a perna
input int    InpBOS_Leg1Max       = 5;  // [BoS] Max candles 1a perna
input int    InpBOS_CorrectionMax = 3;  // [BoS] Max candles correcao
input int    InpBOS_Leg2Max       = 3;  // [BoS] Max candles 2a perna
```

### Chamada no OnInit (apos BP_SmartMoney_Create)

```mql5
BP_SmartMoney_SetBOSLimits(g_hBPSmartMoney,
                           InpBOS_Leg1Min, InpBOS_Leg1Max,
                           InpBOS_CorrectionMax, InpBOS_Leg2Max);
```

### Descricao dos parametros

| Input | Default | Min | Descricao |
|---|---|---|---|
| InpBOS_Leg1Min | 2 | 2 | Minimo de candles consecutivos na 1a perna de tendencia |
| InpBOS_Leg1Max | 5 | >= Leg1Min | Maximo de candles na 1a perna (acima = esticado) |
| InpBOS_CorrectionMax | 3 | 1 | Maximo de candles na correcao (acima = consolidacao) |
| InpBOS_Leg2Max | 3 | 1 | Maximo de candles na 2a perna para romper (acima = sem forca) |

### Regra adicional (implementada no backend)
A correcao nao pode ter mais candles que a 1a perna.
Ex: se a 1a perna tem 2 candles, a correcao aceita no maximo 2.

---

## [2026-04-17] CHoCH: Inputs de tendencia previa e amplitude

### Contexto
O Change of Character (CHoCH) foi reescrito com a seguinte estrutura:
- **Tendencia previa** (oposta a reversao desejada) com limites de candles
- **1a perna de reversao** (reutiliza limites do BoS) com regras de forca
- **Correcao + 2a perna** (reutiliza mecanica do BoS para o rompimento)

O CHoCH detecta reversoes: CHoCH Bull = tendencia de baixa previa + BoS de alta.
CHoCH Bear = tendencia de alta previa + BoS de baixa.

### Inputs a adicionar (grupo [11] Smart Money)

```mql5
input int    InpCHoCH_TrendMin          = 5;   // [CHoCH] Min candles tendencia previa
input int    InpCHoCH_TrendMax          = 15;  // [CHoCH] Max candles tendencia previa
input int    InpCHoCH_MinAmplitudeRatio = 40;  // [CHoCH] Min % amplitude 1a perna vs previa
```

### Chamada no OnInit (apos BP_SmartMoney_SetBOSLimits)

```mql5
BP_SmartMoney_SetCHoCHLimits(g_hBPSmartMoney,
                             InpCHoCH_TrendMin, InpCHoCH_TrendMax,
                             InpCHoCH_MinAmplitudeRatio);
```

### Descricao dos parametros

| Input | Default | Min | Descricao |
|---|---|---|---|
| InpCHoCH_TrendMin | 5 | 2 | Minimo de candles consecutivos na tendencia previa (oposta). Garante que ha uma tendencia estabelecida antes da reversao. |
| InpCHoCH_TrendMax | 15 | >= TrendMin | Maximo de candles na tendencia previa. Acima disso a tendencia e muito longa e o padrao perde relevancia temporal. |
| InpCHoCH_MinAmplitudeRatio | 40 | 1 | Porcentagem minima da amplitude da tendencia previa que a 1a perna de reversao deve cobrir (em pontos, nao candles). Ex: se a tendencia previa tem 1000 pontos e o ratio e 40%, a 1a perna deve ter pelo menos 400 pontos. |

### Logica completa do CHoCH (implementada no backend)

**CHoCH Bullish (reversao de baixa para alta):**

1. **Tendencia previa de BAIXA**: sequencia de candles bearish consecutivos
   - Quantidade entre TrendMin e TrendMax
   - Amplitude = High do candle mais antigo - Low do candle mais recente da tendencia

2. **1a perna de ALTA (impulso de reversao)**:
   - Candles bullish consecutivos (usa limites do BoS: Leg1Min/Leg1Max)
   - **Regra de forca (candles)**: quantidade de candles da 1a perna <= quantidade de candles da tendencia previa
   - **Regra de forca (amplitude)**: amplitude da 1a perna >= MinAmplitudeRatio% da amplitude da tendencia previa
   - Exemplo: tendencia com 7 candles e 1000 pontos -> 1a perna com 3 candles e 450 pontos (45% >= 40%) = VALIDO
   - Exemplo: tendencia com 7 candles e 1000 pontos -> 1a perna com 8 candles e 420 pontos = INVALIDO (mais candles que a tendencia, sem forca)

3. **Correcao**: candles bearish consecutivos (usa limites do BoS: CorrectionMax)
   - Nao pode ter mais candles que a 1a perna
   - Pullback nao pode romper o inicio da 1a perna

4. **2a perna de ALTA (rompimento)**: candles bullish consecutivos (usa limite do BoS: Leg2Max)
   - Close acima do high da 1a perna = **CHoCH confirmado**
   - Candle bearish antes do rompimento = invalido (topo mais baixo)

**CHoCH Bearish**: logica espelhada (tendencia previa de alta + BoS de baixa)

### Nota importante
Os limites do BoS (Leg1Min, Leg1Max, CorrectionMax, Leg2Max) sao reutilizados
automaticamente pelo CHoCH nas etapas de 1a perna, correcao e 2a perna.
Alterar os limites do BoS afeta tambem o comportamento do CHoCH.

---

## [2026-04-23] Liquidity Grab & Sweep: Reestruturacao baseada em BoS

### Contexto
As deteccoes de Liquidity Sweep foram reescritas reaproveitando a logica do BoS.
Foram separados dois conceitos distintos que antes estavam consolidados:
- **Liquidity Grab** = BoS falhado com rejeicao imediata
- **Liquidity Sweep** = BoS confirmado + consolidacao + reversao

Foram adicionados 4 enumeradores no `ENUM_BP_SMC_CONCEPT`:

```mql5
BP_SMC_SWEEP_HIGH   = 9,   // Liquidity Sweep de maximas -> venda
BP_SMC_SWEEP_LOW    = 10,  // Liquidity Sweep de minimas -> compra
BP_SMC_GRAB_HIGH    = 11,  // Liquidity Grab de maximas -> venda
BP_SMC_GRAB_LOW     = 12   // Liquidity Grab de minimas -> compra
```

### Nao exposto no frontend (inputs hardcoded)
Os parametros de qualificacao do Grab sao internos e NAO devem ser expostos
como inputs. Estao fixados no backend via `#define`:

```
BP_GRAB_WICK_RATIO     = 0.5   // Pavio superior/inferior >= 50% do range do candle
BP_GRAB_CLOSE_IN_LOWER = 0.5   // Close na metade inferior (grab high) / superior (grab low)
```

Caso no futuro queira-se expor, basta substituir os `#define` por variaveis
globais e adicionar um `BP_SmartMoney_SetGrabParams()`.

### Definicao do [BSL] (Buy-Side Liquidity)
Regiao no topo do padrao BoS_Bull que funciona como zona de liquidez.

**Passo 1 - Candle pivo:** maior high entre:
- (a) ultimo candle bullish da 1a perna de alta
- (b) 1o candle bearish da correcao

Motivo: o 1o candle da correcao pode ter violado o high pra cima (pavio superior
acima do fechamento do candle anterior) antes de virar bearish. Esse pavio e o
verdadeiro topo.

**Passo 2 - Bordas do [BSL]:**
- Borda superior = high do candle pivo
- Borda inferior = max(open, close) do candle pivo
  - Se pivo e bullish: borda inferior = close (base do pavio superior)
  - Se pivo e bearish: borda inferior = open (base do pavio superior)

### Definicao do [SSL] (Sell-Side Liquidity)
Espelhada: regiao no fundo do padrao BoS_Bear.
- Candle pivo = menor low entre (ultimo bearish da 1a perna, 1o bullish da correcao)
- Borda inferior = low do candle pivo
- Borda superior = min(open, close) do candle pivo

### Liquidity Grab High (BoS falhado)
1. Detecta 1a perna de alta + correcao (fases 1 e 2 do BoS_Bull)
2. Na 2a perna, candle viola `bslTop` (high > borda superior)
3. **MAS close < bslTop** -> BoS falhado (rejeicao imediata)
4. **Qualificacao**:
   - Pavio superior >= 50% do range do candle
   - Close na metade inferior do range
5. Sinal: **venda** (preco deve cair apos rejeicao)

### Liquidity Sweep High (BoS confirmado + consolidacao + reversao)
1. Detecta 1a perna de alta + correcao
2. **Rompimento**: candle rompe com close > `bslTop` (BoS_Bull confirmado)
3. **Consolidacao**: candles seguintes devem tocar a zona [BSL]
   - Criterio: `low <= bslTop` (o low do candle toca ou entra na zona)
4. **Anulacao**: primeiro candle com `low > bslTop` cancela o setup
5. **Confirmacao da reversao**: candle fecha abaixo da borda inferior
   - Criterio: `close < bslBottom`
6. Sinal: **venda** (reversao apos sweep)

### Liquidity Grab Low e Sweep Low
Logica espelhada para o lado de venda usando [SSL].
- Grab Low: rompe fundo, close fica acima, qualificacao de pavio -> compra
- Sweep Low: BoS_Bear confirmado, consolida tocando zona, fecha acima -> compra

### Por que Grab e Sweep nao se confundem com BoS puro
- Usuario seleciona **qual sinal operar** via input `InpSMCEntry`
- Se selecionar `BP_SMC_BOS_BULL` -> sinal assim que BoS confirma
- Se selecionar `BP_SMC_SWEEP_HIGH` -> espera consolidacao + reversao (nao dispara BoS puro)
- Se selecionar `BP_SMC_GRAB_HIGH` -> so dispara quando ha rejeicao no candle

### Direcao dos sinais
| Conceito | Direcao | Logica |
|---|---|---|
| SWEEP_HIGH | SELL | BoS de alta confirmado mas revertido |
| SWEEP_LOW | BUY | BoS de baixa confirmado mas revertido |
| GRAB_HIGH | SELL | Rejeicao no topo do padrao de alta |
| GRAB_LOW | BUY | Rejeicao no fundo do padrao de baixa |

### Frontend: atualizacao necessaria
O input `InpSMCEntry` (tipo `ENUM_BP_SMC_CONCEPT`) agora exibe automaticamente
os 4 novos conceitos no dropdown do MT5:
- `BP_SMC_SWEEP_HIGH`
- `BP_SMC_SWEEP_LOW`
- `BP_SMC_GRAB_HIGH`
- `BP_SMC_GRAB_LOW`

Se o frontend externo (planilha, interface web) listar os conceitos SMC, adicionar
esses 4 novos valores como opcoes selecionaveis.

---

## [2026-04-23] Order Block: Removido como padrao isolado, transformado em filtro de BoS/CHoCH

### Contexto
O Order Block (OB) deixou de ser um conceito SMC isolado e passou a ser um
**filtro de mitigacao** aplicado dentro de BoS e CHoCH. A razao e que OB sem
contexto estrutural (BoS/CHoCH) nao tem valor institucional -- e apenas "um
candle qualquer". Com o filtro, so confirmam BoS/CHoCH quando a correcao
interage adequadamente com a zona de origem do movimento.

### Remocoes
- `BP_SMC_OB_BULL` e `BP_SMC_OB_BEAR` **removidos** do enum `ENUM_BP_SMC_CONCEPT`
- Funcoes `_OB_Bull` e `_OB_Bear` removidas de `BP_SmartMoney.mqh`
- Valores 7 e 8 do enum reservados (nao reutilizar)

### Novo enum: `ENUM_BP_OB_MITIGATION`

```mql5
enum ENUM_BP_OB_MITIGATION
{
   OB_MITIGATION_NONE       = 0,  // Sem filtro (BoS/CHoCH puros como antes)
   OB_MITIGATION_TOUCH      = 1,  // Pavio da correcao toca a zona OB
   OB_MITIGATION_VALIDATION = 2   // Algum candle da correcao fecha dentro da zona OB
};
```

### Novo input (grupo [11] Smart Money)

```mql5
input ENUM_BP_OB_MITIGATION InpOB_Mitigation = OB_MITIGATION_NONE; // [OB] Filtro de mitigacao (BoS/CHoCH)
```

### Chamada no OnInit (apos SetCHoCHLimits)

```mql5
BP_SmartMoney_SetOBMitigation(g_hBPSmartMoney, InpOB_Mitigation);
```

### Zonas do OB

**BoS_Bull:**
- Candle pivo = 1o candle bullish da 1a perna (`legStart`)
- Zona = `[low, close]` do candle pivo (corpo inferior + pavio inferior)

**BoS_Bear:**
- Candle pivo = 1o candle bearish da 1a perna (`legStart`)
- Zona = `[close, high]` do candle pivo (corpo superior + pavio superior)

**CHoCH_Bull:**
- Candle pivo = aquele com **menor low** entre:
  - (a) Ultimo candle bearish da tendencia previa (`trendEnd`): zona `[low, open]`
  - (b) 1o candle bullish da 1a perna de reversao (`legStart`): zona `[low, close]`

**CHoCH_Bear:**
- Candle pivo = aquele com **maior high** entre:
  - (a) Ultimo candle bullish da tendencia previa (`trendEnd`): zona `[open, high]`
  - (b) 1o candle bearish da 1a perna de reversao (`legStart`): zona `[close, high]`

### Modos de mitigacao

| Modo | Criterio (Bull) | Criterio (Bear) |
|---|---|---|
| NONE | sem filtro | sem filtro |
| TOUCH | `pullbackLow <= borda_superior` | `pullbackHigh >= borda_inferior` |
| VALIDATION | existe candle da correcao com `close` em `(bordaInf, bordaSup)` | idem espelhado |

### Aplicacao
O filtro e aplicado **dentro** da fase de correcao do BoS e CHoCH, apos as
regras existentes (limites de candles, pullbackLow/High nao romper inicio da perna).
Quando o filtro reprova, o padrao e invalidado -- nenhum BoS/CHoCH e detectado.

### Frontend: atualizacao necessaria
1. **Remover** as opcoes `BP_SMC_OB_BULL` e `BP_SMC_OB_BEAR` do dropdown
   `InpSMCEntry`. Qualquer estrategia salva que referencie esses valores
   precisa ser migrada para usar `InpOB_Mitigation`.
2. **Adicionar** novo controle para `InpOB_Mitigation` com 3 opcoes:
   - None (padrao)
   - Touch
   - Validation
3. **Traducao de estrategias antigas**: uma estrategia que usava OB isolado
   deve migrar para BoS ou CHoCH (escolher qual faz sentido) + `InpOB_Mitigation`
   no modo desejado.

### Python: atualizacao pendente
Os arquivos `python/backtest_runner.py` e `python/mappings.py` ainda listam
`BP_SMC_OB_BULL`/`BP_SMC_OB_BEAR`. Precisam ser atualizados para:
- Remover entradas que apontam para valores 7 e 8
- Adicionar mapeamento para `InpOB_Mitigation` (novo input)

---

## [2026-04-24] Fibonacci: Novo modulo de gatilho + SL + TP

### Contexto
Novo modulo `BP_Fibonacci.mqh` que detecta a perna de impulso mais recente
via ZigZag (iCustom local em `Examples\ZigZag`) e expoe os niveis de retracao
(23.6%, 38.2%, 50%, 61.8%, 78.6%, 100%) e projecao (127.2%, 161.8%, 200%,
261.8%) para uso como:
- **Gatilho de entrada** (substitui Cond1/2/3 + SMC quando ativo)
- **Preco de Stop Loss** (novo tipo `BP_SL_FIBO`)
- **Preco de Take Profit** (novo tipo `BP_TP_FIBO`)

A perna e definida pelos 2 pivos alternados (um topo + um fundo) mais recentes
do ZigZag. Direcao:
- Pivo recente = topo -> impulso de ALTA -> setup de COMPRA
- Pivo recente = fundo -> impulso de BAIXA -> setup de VENDA

Os niveis SL/TP sao calculados no instante da entrada e enviados como precos
absolutos (sem alteracao no framework - Opcao B). O modulo continua atualizando
a perna para a proxima operacao, permitindo posicoes simultaneas com niveis
distintos (cada posicao carrega o SL/TP congelado no momento do trigger).

### Enums novos em `BP_Constants.mqh`

```mql5
// Adicionado em ENUM_BP_SL_TYPE
BP_SL_FIBO = 10  // Nivel de retracao Fibonacci (calculado pelo modulo BP_Fibonacci)

// Adicionado em ENUM_BP_TP_TYPE
BP_TP_FIBO = 10  // Nivel de projecao Fibonacci

// Novo enum: niveis de Fibonacci (retracao + projecao)
enum ENUM_BP_FIBO_LEVEL
{
   BP_FIBO_236   = 0,  // Retracao 23.6%
   BP_FIBO_382   = 1,  // Retracao 38.2%
   BP_FIBO_500   = 2,  // Retracao 50.0%
   BP_FIBO_618   = 3,  // Retracao 61.8%
   BP_FIBO_786   = 4,  // Retracao 78.6%
   BP_FIBO_100   = 5,  // 100% = fim da perna de impulso
   BP_FIBO_1272  = 6,  // Projecao 127.2%
   BP_FIBO_1618  = 7,  // Projecao 161.8%
   BP_FIBO_200   = 8,  // Projecao 200%
   BP_FIBO_2618  = 9   // Projecao 261.8%
};

// Novo enum: modo de gatilho
enum ENUM_BP_FIBO_TRIGGER_MODE
{
   BP_FIBO_TRIG_TOUCH      = 0,  // Pavio toca o nivel
   BP_FIBO_TRIG_VALIDATION = 1   // Candle fecha confirmando rejeicao
};
```

### Inputs adicionados no EA

**No grupo [1] Modulos Ativos (1 input novo):**

```mql5
input bool   InpUseFibonacci = false;  // Usar modulo Fibonacci (substitui Cond1/2/3 como gatilho)
```

**Alteracao de tipo dos inputs existentes de SL/TP (grupos [6] e [7]):**

Os tipos dos enums foram trocados dos enums do framework para os enums BP
(compativeis 1:1 com cast nos valores 0-3). Isso permite expor os novos
valores `BP_SL_FIBO` e `BP_TP_FIBO` no dropdown do MT5.

```mql5
// ANTES: input ENUM_STOP_LOSS_TYPE InpSLType = SL_GRAPHIC;
input ENUM_BP_SL_TYPE InpSLType = BP_SL_CANDLE; // Tipo de SL (0=ATR, 1=FIXED, 2=CANDLE, 10=FIBO)

// ANTES: input ENUM_TAKE_PROFIT_TYPE InpTPType = TP_RR_MULTIPLIER;
input ENUM_BP_TP_TYPE InpTPType = BP_TP_RR;     // Tipo de TP (0=FIXED, 1=RR, 2=ZIGZAG, 3=ATR, 10=FIBO)
```

**Novo grupo [15] Fibonacci (7 inputs):**

```mql5
input group "=== [15] Fibonacci ==="
input int                       InpFibo_ZZDepth      = 12;                        // ZigZag Depth
input int                       InpFibo_ZZDeviation  = 5;                         // ZigZag Deviation
input int                       InpFibo_ZZBackstep   = 3;                         // ZigZag Backstep
input ENUM_BP_FIBO_LEVEL        InpFibo_TriggerLevel = BP_FIBO_618;               // Nivel de retracao p/ monitorar trigger
input ENUM_BP_FIBO_TRIGGER_MODE InpFibo_TriggerMode  = BP_FIBO_TRIG_VALIDATION;   // Modo de trigger (TOQUE ou VALIDACAO)
input ENUM_BP_FIBO_LEVEL        InpFibo_SLLevel      = BP_FIBO_100;               // Nivel Fibo usado como SL (se InpSLType = BP_SL_FIBO)
input ENUM_BP_FIBO_LEVEL        InpFibo_TPLevel      = BP_FIBO_1618;              // Nivel Fibo usado como TP (se InpTPType = BP_TP_FIBO)
```

### Descricao dos parametros

| Input | Default | Descricao |
|---|---|---|
| InpUseFibonacci | false | Ativa modulo. Quando true, Fibonacci vira gatilho principal e substitui Cond1/2/3 + SMC |
| InpFibo_ZZDepth | 12 | ZigZag Depth (quantidade min de barras entre pivos) |
| InpFibo_ZZDeviation | 5 | ZigZag Deviation (distancia min em pontos para confirmar pivo) |
| InpFibo_ZZBackstep | 3 | ZigZag Backstep (barras a ignorar apos pivo detectado) |
| InpFibo_TriggerLevel | BP_FIBO_618 | Nivel de retracao onde o gatilho e monitorado |
| InpFibo_TriggerMode | VALIDATION | TOQUE: low/high toca o nivel; VALIDATION: candle fecha confirmando rejeicao |
| InpFibo_SLLevel | BP_FIBO_100 | Nivel Fibo usado para calcular SL (so se InpSLType = BP_SL_FIBO) |
| InpFibo_TPLevel | BP_FIBO_1618 | Nivel Fibo usado para calcular TP (so se InpTPType = BP_TP_FIBO) |

### Regras de gatilho (implementadas no backend)

**Compra (impulso de alta, preco recuando):**
- TOQUE: `low[1] <= precoNivel`
- VALIDATION: `low[1] <= precoNivel` E `close[1] > precoNivel` (rejeitou a retracao)

**Venda (impulso de baixa, preco subindo):**
- TOQUE: `high[1] >= precoNivel`
- VALIDATION: `high[1] >= precoNivel` E `close[1] < precoNivel`

Apos confirmado o trigger, a entrada segue o `InpEntryType` existente
(NEXT_OPEN = mercado na abertura do proximo candle; STOP_ORDER = pendente
na max/min do candle trigger).

### Relacao com outros modulos (exclusividade)

- Quando `InpUseFibonacci = true`, o gatilho vem do Fibonacci e **substitui**
  Cond1/2/3 + SmartMoney. As condicoes tradicionais e SMC sao ignoradas.
- Filtro de direcao (`InpDirection`) continua ativo: bloqueia sinal contrario
  ao permitido.
- Modulo pode tambem ser usado **so** como fonte de SL/TP (sem ser gatilho):
  basta deixar `InpUseFibonacci = true` e selecionar `BP_SL_FIBO`/`BP_TP_FIBO`
  nos inputs de SL/TP. Neste caso o gatilho ainda vem de Cond1/2/3 ou SMC.

### Frontend: atualizacao necessaria

1. **Grupo "Modulos Ativos"**: adicionar toggle `InpUseFibonacci` (default off).
2. **Dropdown de Tipo de SL** (`InpSLType`): adicionar opcao "Fibonacci" (valor 10).
3. **Dropdown de Tipo de TP** (`InpTPType`): adicionar opcao "Fibonacci" (valor 10).
4. **Novo grupo "Fibonacci"** com 7 controles:
   - Depth / Deviation / Backstep (inteiros)
   - TriggerLevel (dropdown dos 10 niveis Fibo) -- idealmente so mostrar
     retracoes (23.6% a 100%) pois projecao nao faz sentido como trigger
   - TriggerMode (dropdown: Toque / Validacao)
   - SLLevel (dropdown dos 10 niveis) -- tipicamente 78.6% ou 100%
   - TPLevel (dropdown dos 10 niveis) -- tipicamente projecoes 127.2%+
5. **Regra de visibilidade sugerida**: o grupo Fibonacci so fica ativo no
   frontend se `InpUseFibonacci = true` OU se `InpSLType = BP_SL_FIBO` OU
   se `InpTPType = BP_TP_FIBO`.
6. **Exclusividade com SMC**: se o frontend ja trata `InpUseSmartMoney` como
   exclusivo com `InpUseOscillators`/`InpUseIndicators`, tratar
   `InpUseFibonacci` da mesma forma (gatilho unico).

### Python: atualizacao pendente

Os arquivos `python/backtest_runner.py` e `python/mappings.py` precisam ser
atualizados para:
- Incluir mapeamento dos novos inputs (`InpUseFibonacci`, grupo `[15]`).
- Adicionar valores `BP_SL_FIBO=10` e `BP_TP_FIBO=10` nos mapeamentos de
  `ENUM_BP_SL_TYPE` e `ENUM_BP_TP_TYPE`.
- Adicionar mapeamentos para `ENUM_BP_FIBO_LEVEL` e `ENUM_BP_FIBO_TRIGGER_MODE`.

### Arquivos afetados
- **Novo**: `mql5/Include/BacktestPro/BP_Fibonacci.mqh`
- **Modificado**: `mql5/Include/BacktestPro/BP_Constants.mqh` (novos enums + valores 10)
- **Modificado**: `mql5/Experts/BacktestPro_Universal_EA.mq5` (inputs + integracao)
- **Modificado**: `.claude/deploy-backtest-pro.ps1` (BP_Fibonacci.mqh adicionado ao copy)

---

## [2026-04-24] FVG: Modo de Entrada (Imediata vs Correcao Limite)

### Status no backend
**Implementado** desde versao anterior. Backend MQL5 esta completo e validado:

- Enum em `BP_Constants.mqh`:
```mql5
enum ENUM_BP_FVG_ENTRY_MODE
{
   FVG_ENTRY_AGGRESSIVE = 0,  // Entrada imediata (abertura proximo candle)
   FVG_ENTRY_MITIGATION = 1   // Ordem limite na zona do FVG (aguarda correcao)
};
```

- Input no EA (grupo `[11] Smart Money`):
```mql5
input ENUM_BP_FVG_ENTRY_MODE InpFVGEntryMode = FVG_ENTRY_AGGRESSIVE; // [FVG] Modo de entrada
```

- Roteamento no OnTick: quando `InpUseSmartMoney=true`, `InpFVGEntryMode=FVG_ENTRY_MITIGATION`
  e conceito SMC e `BP_SMC_FVG_BULL`/`BP_SMC_FVG_BEAR`, o EA chama `PlaceFVGLimitEntry`
  que coloca uma ordem **LIMIT** na borda da zona FVG (BUY_LIMIT no topo, SELL_LIMIT no
  fundo) e registra no `TriggerMonitor` para expirar em `InpStopOrderExpBars` candles.

- No modo `FVG_ENTRY_AGGRESSIVE`, o fluxo segue o padrao (mercado no proximo candle,
  ou stop order conforme `InpEntryType`).

### Problema atual
O input existe no EA mas **nao e populado pela cadeia frontend -> Python worker**.
- `app.html` nao tem controle para `entryMode` nos params do FVG.
- `python/cfg_to_json.py` e `python/backtest_runner.py` nao mapeiam `InpFVGEntryMode`.
- Resultado: toda estrategia com FVG roda hoje no default `FVG_ENTRY_AGGRESSIVE`
  (entrada imediata), mesmo que o usuario queira aguardar mitigacao.

### Frontend: atualizacao necessaria (app.html)

**1. Adicionar pills "Modo de Entrada" no bloco FVG config** (~linha 2495, dentro do
`if(smcId==='fvg')`), apos o stepper "Tamanho minimo do gap":

```javascript
frag.appendChild(pills('Modo de Entrada',
   'Imediata = entra no proximo candle apos detectar o FVG. ' +
   'Correcao (Limite) = coloca ordem limite na borda do gap e aguarda o preco retornar.',
   ['Imediata','Correcao (Limite)'],
   ms.params.entryMode==='mitigation' ? 'Correcao (Limite)' : 'Imediata',
   v=>{ms.params.entryMode = (v==='Correcao (Limite)') ? 'mitigation' : 'aggressive';}));
```

**2. Campo condicional "Validade do sinal em candles"** — so visivel quando
`entryMode='mitigation'`. Reusa a logica existente do input global `InpStopOrderExpBars`
(que ja e compartilhado: o backend usa o mesmo input para controlar expiracao de
ordens stop e ordens limite FVG). Duas opcoes de UX:

- **Opcao A (recomendada)**: nao duplicar o input no FVG. Mostrar um aviso/texto
  informativo: "A validade usa o campo 'Validade em candles' do grupo Entrada".
- **Opcao B**: adicionar stepper proprio do FVG que sobrescreve o global so quando
  FVG mitigation esta ativo. Requer novo input backend (`InpFVGExpBars`), o que
  NAO foi implementado. Nao usar a menos que autorizado.

**3. Adicionar `entryMode` no objeto params do FVG** (~linha 2378):

```javascript
// ANTES
if(ind.id==='fvg')  ms.params={dir:'Compra',val:50,cond:FVG_CONDS[1]};

// DEPOIS
if(ind.id==='fvg')  ms.params={dir:'Compra',val:50,cond:FVG_CONDS[1],entryMode:'aggressive'};
```

**4. BoS config nao precisa de novos inputs**: a logica de 3 fases (Leg1/Correcao/
Leg2) ja foi documentada em `[2026-04-17] BoS` e os limites sao passados via
`InpBOS_Leg1Min/Max/CorrectionMax/Leg2Max` — nao ha relacao com `entryMode` do FVG.
O bloco `if(smcId==='bos')` (~linha 2523) pode receber ajustes independentes
conforme `[2026-04-17] BoS`, mas NAO neste item.

### Geracao do payload (app.html + Python worker)

O app.html envia `state.cfg` para `submit-backtest` Edge Function. O Python worker
(`python/cfg_to_json.py` e `python/backtest_runner.py`) traduz a cfg em params do
`.set` para o EA. **Ambos precisam ser atualizados**:

**`python/cfg_to_json.py`** (proximo ao `params["InpSMCEntry"] = smc_entry`, linha ~388):

```python
# Mapear entryMode do FVG para o enum MQL5
if smc_entry in ("BP_SMC_FVG_BULL", "BP_SMC_FVG_BEAR"):
    entry_mode = ms_params.get("entryMode", "aggressive")
    params["InpFVGEntryMode"] = (
        "FVG_ENTRY_MITIGATION" if entry_mode == "mitigation"
        else "FVG_ENTRY_AGGRESSIVE"
    )
else:
    params["InpFVGEntryMode"] = "FVG_ENTRY_AGGRESSIVE"  # default
```

**`python/backtest_runner.py`** (proximo ao `"InpSMCEntry": "BP_SMC_NONE"`, linha ~456):
adicionar `"InpFVGEntryMode": "FVG_ENTRY_AGGRESSIVE"` ao dicionario de defaults.

**`python/example_config.json`**: adicionar `"InpFVGEntryMode": "FVG_ENTRY_AGGRESSIVE"`
no bloco de defaults.

**`python/mappings.py`**: adicionar entrada para `ENUM_BP_FVG_ENTRY_MODE` com valores
`FVG_ENTRY_AGGRESSIVE=0` e `FVG_ENTRY_MITIGATION=1`.

### Checklist de entrega

- [ ] app.html: adicionar pills "Modo de Entrada" em `if(smcId==='fvg')` (~L2495)
- [ ] app.html: adicionar `entryMode:'aggressive'` no default dos params (~L2378)
- [ ] app.html: aviso visual quando modo=mitigation explicando que validade usa `InpStopOrderExpBars` global
- [ ] cfg_to_json.py: traduzir `ms.params.entryMode` para `InpFVGEntryMode`
- [ ] backtest_runner.py: incluir `InpFVGEntryMode` nos defaults
- [ ] example_config.json: adicionar `InpFVGEntryMode` no exemplo
- [ ] mappings.py: mapear enum `ENUM_BP_FVG_ENTRY_MODE`
- [ ] Teste end-to-end: estrategia FVG com modo mitigation deve gerar ordem limite (BUY_LIMIT/SELL_LIMIT), nao ordem a mercado

### Arquivos afetados
- **Ja modificado (backend)**: `mql5/Include/BacktestPro/BP_Constants.mqh`, `mql5/Experts/BacktestPro_Universal_EA.mq5`, `mql5/Include/BacktestPro/BP_SmartMoney.mqh`
- **Pendente (frontend)**: `app.html`
- **Pendente (worker)**: `python/cfg_to_json.py`, `python/backtest_runner.py`, `python/example_config.json`, `python/mappings.py`

---

## [2026-04-24] Fibonacci: Debug visual + Bloqueio de reentrada + Fixes

### Contexto
Pacote de ajustes no modulo Fibonacci apos analise de operacoes reais no
backtest. Tres mudancas tecnicas (uma de comportamento, uma UX opcional,
um bug fix critico) e dois fixes internos sem impacto externo.

### Mudanca 1 - Bloqueio de reentrada (Rigor B)

**Problema**: apos uma operacao ser aberta na perna atual, o EA continuava
avaliando o mesmo nivel de retracao a cada novo candle e disparava
**reentradas sequenciais** enquanto o preco estivesse no nivel. Cenario
concreto: compra na retracao 61.8% de perna F0->T1, SL atingido, preco
continua caindo, ZZ mantem T1 como topo, e o EA dispara compra novamente.

**Solucao implementada no backend**: apos uma posicao ser efetivamente
aberta (confirmada em `OnTradeTransaction`), o modulo Fibo guarda o
time do pivo da perna. Novos triggers do mesmo lado ficam bloqueados
ate o ZigZag reportar um pivo diferente:

- **COMPRA**: bloqueado enquanto `legHighTime == lastEnteredHighTime_BUY`
  (libera quando forma-se um novo topo)
- **VENDA**: bloqueado enquanto `legLowTime == lastEnteredLowTime_SELL`
  (libera quando forma-se um novo fundo)

Bloqueio e independente por lado (em `TRADING_BOTH`, uma entrada comprada
nao bloqueia vendas). Pendentes que expiram sem virar posicao **nao**
bloqueiam. Nao ha desbloqueio manual.

### Mudanca 2 - Debug visual (opt-in)

Novo modulo `BP_DebugViz.mqh` com API consolidada para debug visual
(HLine, VLine, TrendLine, Rectangle, Arrow, Text, Label, Channel,
HighlightCandle). Usado pelo Fibo para desenhar no chart: perna
(trend line), topo/fundo, nivel de trigger, SL, TP, e destaque do
candle que disparou (seta + retangulo).

**Novos inputs no EA (grupo [15] Fibonacci):**
```mql5
input bool                      InpFibo_Debug          = false;      // Desenha linhas Fibo no chart
input ENUM_BP_TRIGGER_HIGHLIGHT InpFibo_DebugHighlight = BP_HL_BOTH; // Como destacar candle trigger
```

**Novo enum:**
```mql5
enum ENUM_BP_TRIGGER_HIGHLIGHT
{
   BP_HL_NONE      = 0,  // Sem destaque
   BP_HL_ARROW     = 1,  // Apenas seta
   BP_HL_RECTANGLE = 2,  // Apenas retangulo
   BP_HL_BOTH      = 3   // Seta + retangulo
};
```

**Ativacao**: debug viz so fica ativo se `InpFibo_Debug=true` **E**
`Logger` em nivel `DEBUG` (5). Em producao, custo e zero (early-return
no master-switch).

### Mudanca 3 - Bug fix: shift >= 2

**Problema (critico)**: `BP_Fibonacci_Update` aceitava o pivo mais
recente do ZigZag mesmo quando ele estava no **bar[1]** (candle que
acabou de fechar, mesmo candle avaliado no trigger). Isso fazia o
ZZ marcar um "topo" no high do candle atual, e no mesmo candle o low
ja estava alem da retracao 23.6% - trigger disparava na perna **antes
dela existir**.

**Fix**: pivo recente so e aceito se estiver em bar >= 2. Perna
precisa estar fechada antes de ser avaliada.

### Fixes internos (sem impacto no frontend/Python)

- **Comentario do enum `BP_FIBO_100`**: corrigido de "fim da perna de
  impulso (topo na compra, fundo na venda)" para o correto "100% da
  retracao = inicio da perna = fundo (compra) / topo (venda)". Valor
  numerico e comportamento **nao mudaram**.
- **Log detalhado em `CheckTrigger`**: agora em nivel DEBUG mostra
  direcao, nivel, preco do nivel, OHLC do candle, modo de trigger e
  resultado (DISPAROU / penetrou mas nao validou / nivel nao atingido /
  BLOQUEADO por reentrada).
- **`DescribeState`**: inclui time dos pivos e range da perna.
- **Normalizacao de preco no OrderManager (framework)**: `OrderManagerImpl.mqh`
  foi alterado para usar `CSymbolInfo::NormalizePrice` em `request.sl/tp/price`
  de `ExecuteMarketOrder`, `ExecutePendingOrder`, `CalculatePendingPrice` e
  `ModifyOrder`. Resolve `Invalid stops` (10016) quando precos fracionarios
  de Fibonacci sao enviados em simbolos com tick_size > point (ex: WIN
  tick=5). `OrderManager.ex5` foi recompilado. **Zero mudanca na API publica**.

### Frontend: atualizacao necessaria (app.html)

**Inputs de debug** - sao de uso interno para analise/suporte. Duas opcoes:

**Opcao A (recomendada)**: **NAO expor** `InpFibo_Debug` e
`InpFibo_DebugHighlight` no frontend publico. Clientes finais nao precisam
ver. O Python worker envia os defaults (`false` / `BP_HL_BOTH`) e pronto.

**Opcao B**: expor como seccao "Avancado/Debug" escondida atras de um
toggle, acessivel apenas em modo suporte. Requer:
- Checkbox `InpFibo_Debug` (default off)
- Dropdown `InpFibo_DebugHighlight` (None/Arrow/Rectangle/Both, default Both)
- So ativa quando `InpUseFibonacci = true` OU `InpSLType=BP_SL_FIBO` OU
  `InpTPType=BP_TP_FIBO`

**Bloqueio de reentrada** - **NAO tem input novo**, mas muda
comportamento visivel ao usuario. Duas consequencias de UX:

1. Usuario pode notar operacoes "faltando" em relacao a versoes antigas
   (onde o EA reentrava na mesma perna). Documentar na FAQ/help: "Apos
   uma entrada na mesma estrutura, o EA aguarda formacao de nova perna
   antes de novo sinal do mesmo lado."
2. Se houver visualizacao de log ou estatisticas de sinais, a mensagem
   `Fibo trigger bloqueado: COMPRA/VENDA (pivo @ TIMESTAMP ja usado)`
   pode aparecer em nivel DEBUG - nao e erro.

### Python: atualizacao necessaria

**`python/cfg_to_json.py`** - adicionar mapeamento dos novos inputs Fibo:

```python
# Defaults de debug visual (nao exposto ao cliente)
if cfg.get("useFibonacci", False):
    params["InpFibo_Debug"]          = "false"
    params["InpFibo_DebugHighlight"] = "BP_HL_BOTH"
```

**`python/backtest_runner.py`** - incluir nos defaults do dicionario:
```python
"InpFibo_Debug":          "false",
"InpFibo_DebugHighlight": "BP_HL_BOTH",
```

**`python/example_config.json`** - adicionar os 2 inputs no exemplo.

**`python/mappings.py`** - adicionar `ENUM_BP_TRIGGER_HIGHLIGHT`:
```python
{
    "BP_HL_NONE":      0,
    "BP_HL_ARROW":     1,
    "BP_HL_RECTANGLE": 2,
    "BP_HL_BOTH":      3,
}
```

### Checklist de entrega

- [ ] **Decidir**: expor `InpFibo_Debug` no frontend (Opcao A ou B)?
- [ ] Se B: implementar secao "Debug" no grupo Fibonacci com os 2 controles
- [ ] FAQ/help: adicionar explicacao do bloqueio de reentrada (rigor B)
- [ ] cfg_to_json.py: enviar defaults de `InpFibo_Debug`/`InpFibo_DebugHighlight`
- [ ] backtest_runner.py: incluir defaults
- [ ] example_config.json: incluir exemplo
- [ ] mappings.py: mapear `ENUM_BP_TRIGGER_HIGHLIGHT`
- [ ] Teste end-to-end: rodar estrategia Fibo e verificar que nao ha reentradas sequenciais na mesma perna
- [ ] Teste debug viz: rodar com `InpFibo_Debug=true, LogLevel=DEBUG` e confirmar linhas desenhadas no chart

### Arquivos afetados
- **Novo (backend)**: `mql5/Include/BacktestPro/BP_DebugViz.mqh`
- **Modificado (backend)**: `mql5/Include/BacktestPro/BP_Fibonacci.mqh` (fix shift, bloqueio reentrada, debug viz, log melhorado), `mql5/Include/BacktestPro/BP_Constants.mqh` (novo enum + fix comentario), `mql5/Experts/BacktestPro_Universal_EA.mq5` (novos inputs + OnTradeTransaction)
- **Modificado (framework)**: `MQL5_Framework/Source/Internal/Trading/OrderManagerImpl.mqh` (normalizacao de preco) - `OrderManager.ex5` recompilado
- **Modificado (deploy)**: `.claude/deploy-backtest-pro.ps1` (BP_DebugViz.mqh adicionado)
- **Pendente (frontend)**: `app.html` (decisao sobre expor inputs debug + FAQ reentrada)
- **Pendente (worker)**: `python/cfg_to_json.py`, `python/backtest_runner.py`, `python/example_config.json`, `python/mappings.py`

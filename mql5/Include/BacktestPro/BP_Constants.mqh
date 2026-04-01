//+------------------------------------------------------------------+
//|                                              BP_Constants.mqh    |
//|                                             BacktestPro v1.0     |
//| Enums, FLAGS e tipos compartilhados por todos os modulos BP      |
//+------------------------------------------------------------------+
#ifndef __BP_CONSTANTS_MQH__
#define __BP_CONSTANTS_MQH__

//+------------------------------------------------------------------+
//| FLAGS de modulos ativos (passados via inputs do EA)              |
//+------------------------------------------------------------------+
enum ENUM_BP_MODULE_FLAG
{
   BP_MODULE_NONE          = 0,
   BP_MODULE_INDICATORS    = 1,   // Indicadores tecnicos (tendencia, volume, preco)
   BP_MODULE_OSCILLATORS   = 2,   // Osciladores com cruzamentos e zonas
   BP_MODULE_CANDLE        = 4,   // Padroes de candle
   BP_MODULE_SMARTMONEY    = 8    // Smart Money Concepts (isolado - nao combina)
};

//+------------------------------------------------------------------+
//| Sinal de entrada                                                  |
//+------------------------------------------------------------------+
enum ENUM_BP_SIGNAL
{
   BP_SIGNAL_NONE  =  0,
   BP_SIGNAL_BUY   =  1,
   BP_SIGNAL_SELL  = -1
};

//+------------------------------------------------------------------+
//| Tipo de entrada                                                  |
//+------------------------------------------------------------------+
enum ENUM_BP_ENTRY_TYPE
{
   BP_ENTRY_NEXT_OPEN  = 0,  // Mercado na abertura do proximo candle
   BP_ENTRY_STOP_ORDER = 1   // Ordem stop: BUY_STOP acima da maxima / SELL_STOP abaixo da minima do candle trigger
};

//+------------------------------------------------------------------+
//| Tipo de Stop Loss                                                 |
// ATENCAO: InpSLType usa ENUM_STOP_LOSS_TYPE do Framework (CommonTypes.mqh)
//          SL_ATR=0, SL_FIXED=1, SL_GRAPHIC=2 (max/min candle + buffer)
enum ENUM_BP_SL_TYPE
{
   BP_SL_ATR       = 0,  // Baseado em ATR (= SL_ATR do Framework)
   BP_SL_FIXED_PTS = 1,  // Pontos fixos   (= SL_FIXED do Framework)
   BP_SL_CANDLE    = 2   // Maxima/minima do candle sinal (= SL_GRAPHIC do Framework)
};

//+------------------------------------------------------------------+
//| Tipo de Take Profit                                               |
//+------------------------------------------------------------------+
// ATENCAO: InpTPType usa ENUM_TAKE_PROFIT_TYPE do Framework (CommonTypes.mqh)
//          TP_FIXED_POINTS=0, TP_RR_MULTIPLIER=1, TP_ZIGZAG_LEVEL=2, TP_ATR=3
enum ENUM_BP_TP_TYPE
{
   BP_TP_FIXED_PTS = 0,  // Pontos fixos           (= TP_FIXED_POINTS do Framework)
   BP_TP_RR        = 1,  // Risk/Reward ratio      (= TP_RR_MULTIPLIER do Framework)
   BP_TP_ZIGZAG    = 2,  // Ultimo pico/vale ZigZag(= TP_ZIGZAG_LEVEL do Framework)
   BP_TP_ATR       = 3   // Baseado em ATR         (= TP_ATR do Framework)
};

//+------------------------------------------------------------------+
//| Indicadores suportados                                            |
//+------------------------------------------------------------------+
enum ENUM_BP_INDICATOR
{
   BP_IND_NONE      =  0,
   // Osciladores
   BP_IND_RSI       =  1,
   BP_IND_STOCH     =  2,
   BP_IND_CCI       =  3,
   BP_IND_WILLIAMS  =  4,
   BP_IND_MACD      =  5,
   // Tendencia
   BP_IND_SMA       = 10,
   BP_IND_EMA       = 11,
   BP_IND_ADX       = 12,
   BP_IND_SAR       = 13,
   BP_IND_BOLLINGER = 14,
   BP_IND_VWAP      = 15,
   // Volume
   BP_IND_VOLUME    = 20,
   BP_IND_VOLUME_MA = 21,
   BP_IND_OBV       = 22,
   // Volatilidade
   BP_IND_ATR       = 30,
   // HiLo
   BP_IND_HILO          = 16,  // HiLo Activator
   // Preco
   BP_IND_PRICE_HIGH_N  = 40,  // Maxima de N periodos
   BP_IND_PRICE_LOW_N   = 41,  // Minima de N periodos
   BP_IND_PREV_HIGH     = 42,  // Maxima do dia anterior
   BP_IND_PREV_LOW      = 43,  // Minima do dia anterior
   BP_IND_FIBONACCI     = 44,
   BP_IND_GAP           = 45
};

//+------------------------------------------------------------------+
//| Condicoes de entrada para osciladores                            |
//+------------------------------------------------------------------+
enum ENUM_BP_CONDITION
{
   BP_COND_NONE              = 0,
   BP_COND_CROSS_ABOVE       = 1,  // Cruza acima de (cruzamento ascendente)
   BP_COND_CROSS_BELOW       = 2,  // Cruza abaixo de (cruzamento descendente)
   BP_COND_ABOVE             = 3,  // Esta acima de
   BP_COND_BELOW             = 4,  // Esta abaixo de
   BP_COND_IN_ZONE_OB        = 5,  // Em zona de sobrecompra (overbought)
   BP_COND_IN_ZONE_OS        = 6,  // Em zona de sobrevenda (oversold)
   BP_COND_CROSS_ABOVE_PRICE = 7,  // Indicador cruza acima do preco
   BP_COND_CROSS_BELOW_PRICE = 8,  // Indicador cruza abaixo do preco
   // MACD especifico
   BP_COND_MACD_CROSS_UP     = 9,  // MACD cruza sinal para cima
   BP_COND_MACD_CROSS_DOWN   = 10, // MACD cruza sinal para baixo
   BP_COND_MACD_ABOVE_ZERO   = 11, // MACD acima da linha zero
   BP_COND_MACD_BELOW_ZERO   = 12, // MACD abaixo da linha zero
   // Cruzamento MA vs MA (period=rapida, period2=lenta)
   BP_COND_MA_CROSS_ABOVE    = 13, // MA rapida cruza acima da MA lenta -> BUY
   BP_COND_MA_CROSS_BELOW    = 14, // MA rapida cruza abaixo da MA lenta -> SELL
   // HiLo Activator
   BP_COND_HILO_BUY          = 15, // HiLo virou compra (preco acima da media das minimas)
   BP_COND_HILO_SELL         = 16, // HiLo virou venda (preco abaixo da media das maximas)
   BP_COND_HILO_CHANGED      = 17  // HiLo mudou de direcao (qualquer)
};

//+------------------------------------------------------------------+
//| Condicoes para medias moveis                                     |
//+------------------------------------------------------------------+
enum ENUM_BP_MA_CONDITION
{
   BP_MA_PRICE_ABOVE = 0,  // Preco acima da media
   BP_MA_PRICE_BELOW = 1,  // Preco abaixo da media
   BP_MA_CROSS_UP    = 2,  // Media rapida cruza acima da lenta
   BP_MA_CROSS_DOWN  = 3,  // Media rapida cruza abaixo da lenta
   BP_MA_SLOPE_UP    = 4,  // Media inclinada para cima
   BP_MA_SLOPE_DOWN  = 5   // Media inclinada para baixo
};

//+------------------------------------------------------------------+
//| Padroes de candle suportados                                     |
//+------------------------------------------------------------------+
enum ENUM_BP_CANDLE_PATTERN
{
   BP_CANDLE_NONE          =  0,
   // Padroes de reversao de alta (bullish)
   BP_CANDLE_HAMMER        =  1,  // Martelo
   BP_CANDLE_BULL_ENGULF   =  2,  // Engolfo de alta
   BP_CANDLE_MORNING_STAR  =  3,  // Estrela da manha
   BP_CANDLE_BULL_HARAMI   =  4,  // Harami de alta
   BP_CANDLE_BOTTOM_TAIL   =  5,  // Bottom Tail (BT) - cauda inferior
   BP_CANDLE_DOUBLE_BOTTOM =  6,  // Fundo duplo
   BP_CANDLE_BULL_PIVOT    =  7,  // Pivot de alta
   // Padroes de reversao de baixa (bearish)
   BP_CANDLE_SHOOTING_STAR =  10, // Estrela cadente
   BP_CANDLE_BEAR_ENGULF   =  11, // Engolfo de baixa
   BP_CANDLE_EVENING_STAR  =  12, // Estrela da noite
   BP_CANDLE_BEAR_HARAMI   =  13, // Harami de baixa
   BP_CANDLE_TOP_TAIL      =  14, // Top Tail (TT) - cauda superior
   BP_CANDLE_DOUBLE_TOP    =  15, // Topo duplo
   BP_CANDLE_BEAR_PIVOT    =  16, // Pivot de baixa
   // Neutros/doji
   BP_CANDLE_DOJI          =  20, // Doji
   BP_CANDLE_SPINNING_TOP  =  21  // Spinning Top
};

//+------------------------------------------------------------------+
//| Conceitos Smart Money suportados                                 |
//+------------------------------------------------------------------+
enum ENUM_BP_SMC_CONCEPT
{
   BP_SMC_NONE         = 0,
   BP_SMC_FVG_BULL     = 1,  // Fair Value Gap de alta
   BP_SMC_FVG_BEAR     = 2,  // Fair Value Gap de baixa
   BP_SMC_BOS_BULL     = 3,  // Break of Structure de alta
   BP_SMC_BOS_BEAR     = 4,  // Break of Structure de baixa
   BP_SMC_CHOCH_BULL   = 5,  // Change of Character para alta
   BP_SMC_CHOCH_BEAR   = 6,  // Change of Character para baixa
   BP_SMC_OB_BULL      = 7,  // Order Block de alta
   BP_SMC_OB_BEAR      = 8,  // Order Block de baixa
   BP_SMC_SWEEP_HIGH   = 9,  // Liquidity Sweep de maximas
   BP_SMC_SWEEP_LOW    = 10  // Liquidity Sweep de minimas
};

//+------------------------------------------------------------------+
//| Tipo de Trailing Stop (mapeia 1:1 com Framework ENUM_TRAILING_TYPE)|
//+------------------------------------------------------------------+
enum ENUM_BP_TRAILING_TYPE
{
   BP_TRAIL_NONE        = 0,  // Sem trailing
   BP_TRAIL_RR_RATIO    = 1,  // Baseado em Risk/Reward
   BP_TRAIL_BAR_BY_BAR  = 2,  // High/Low da barra anterior
   BP_TRAIL_ATR         = 3   // Distancia dinamica ATR
};

//+------------------------------------------------------------------+
//| Modo de ativacao do Trailing (mapeia 1:1 com Framework)          |
//+------------------------------------------------------------------+
enum ENUM_BP_ACTIVATION_MODE
{
   BP_ACT_IMMEDIATE       = 0,  // Desde a entrada
   BP_ACT_AFTER_PROFIT    = 1,  // Apos lucro minimo
   BP_ACT_AFTER_BREAKEVEN = 2   // Apos breakeven
};

//+------------------------------------------------------------------+
//| Estrutura de uma condicao de entrada                             |
//+------------------------------------------------------------------+
struct BPCondition
{
   ENUM_BP_INDICATOR   indicator;    // Qual indicador
   ENUM_BP_CONDITION   condition;    // Qual condicao
   int                 period;       // Periodo do indicador
   int                 period2;      // Segundo periodo (MA cruzamento, MACD sinal)
   double              value;        // Valor de referencia (ex: RSI cruza acima de 30)
   double              value2;       // Segundo valor (ex: faixa: entre 40 e 60)
};

//+------------------------------------------------------------------+
//| Estrutura de parametros de risco                                 |
//+------------------------------------------------------------------+
struct BPRiskParams
{
   ENUM_BP_SL_TYPE  slType;
   int              slCandlesBack;  // Candles para buscar max/min (SL_CANDLE)
   double           slAtrMult;      // Multiplicador ATR (SL_ATR)
   double           slFixedPts;     // Pontos fixos (SL_FIXED_PTS)

   ENUM_BP_TP_TYPE  tpType;
   double           tpRR;           // Ratio R:R (TP_RR)
   double           tpAtrMult;      // Multiplicador ATR (TP_ATR)
   double           tpFixedPts;     // Pontos fixos (TP_FIXED_PTS)
};

//+------------------------------------------------------------------+
//| Constantes gerais                                                 |
//+------------------------------------------------------------------+
#define BP_MAX_CONDITIONS     8     // Maximo de condicoes por estrategia
#define BP_MAGIC_NUMBER       20260326  // Magic number do BacktestPro
#define BP_VERSION            "1.0"

#endif // __BP_CONSTANTS_MQH__

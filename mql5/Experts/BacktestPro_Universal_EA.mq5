//+------------------------------------------------------------------+
//|                               BacktestPro_Universal_EA.mq5      |
//|                                           BacktestPro v1.0       |
//| EA Universal para execucao de backtests do BacktestPro           |
//| Recebe parametros via inputs (.set file) gerado pelo backend     |
//+------------------------------------------------------------------+
#property copyright "BacktestPro"
#property version   "1.00"
#property strict

//--- Framework alphaQuant (instalado no MT5)
#include <AlphaQuant/FrameworkCore.mqh>

//--- Modulos BacktestPro
#include <BacktestPro/BP_Constants.mqh>
#include <BacktestPro/BP_Indicators.mqh>
#include <BacktestPro/BP_Oscillators.mqh>
#include <BacktestPro/BP_CandlePatterns.mqh>
#include <BacktestPro/BP_SmartMoney.mqh>
#include <BacktestPro/BP_Fibonacci.mqh>
#include <BacktestPro/BP_SignalEngine.mqh>

//+------------------------------------------------------------------+
//| INPUTS: Logger                                                   |
//+------------------------------------------------------------------+
input group "=== [0] Logger ==="
input ENUM_LOG_LEVEL  InpLogLevel  = LOG_LEVEL_INFO;   // Nivel de log (3=INFO, 5=DEBUG)
input ENUM_LOG_OUTPUT InpLogOutput = LOG_TO_PRINT;     // Saida (1=PRINT, 2=FILE, 3=AMBOS)

//+------------------------------------------------------------------+
//| INPUTS: Modulos Ativos                                           |
//+------------------------------------------------------------------+
input group "=== [1] Modulos Ativos ==="
input bool   InpUseOscillators   = true;   // Usar modulo de osciladores
input bool   InpUseIndicators    = true;   // Usar modulo de indicadores de tendencia/volume
input bool   InpUseCandlePatterns= false;  // Usar modulo de padroes de candle
input bool   InpUseSmartMoney    = false;  // Usar modulo Smart Money Concepts
input bool   InpUseFibonacci     = false;  // Usar modulo Fibonacci (substitui Cond1/2/3 como gatilho)

//+------------------------------------------------------------------+
//| INPUTS: Condicao 1 (Oscilador Principal)                        |
//+------------------------------------------------------------------+
input group "=== [2] Condicao 1 - Oscilador ==="
input ENUM_BP_INDICATOR InpInd1      = BP_IND_RSI;          // Indicador
input ENUM_BP_CONDITION InpCond1     = BP_COND_CROSS_ABOVE;  // Condicao
input int               InpPeriod1   = 14;                   // Periodo (MA rapida se MA_CROSS)
input int               InpPeriod1b  = 0;                    // Periodo 2 (MA lenta se MA_CROSS, 0=nao usado)
input double            InpValue1    = 30.0;                 // Valor de referencia

//+------------------------------------------------------------------+
//| INPUTS: Condicao 2 (Filtro de Tendencia)                        |
//+------------------------------------------------------------------+
input group "=== [3] Condicao 2 - Tendencia ==="
input bool              InpUseCond2  = false;                // Ativar condicao 2
input ENUM_BP_INDICATOR InpInd2      = BP_IND_SMA;           // Indicador
input ENUM_BP_CONDITION InpCond2     = BP_COND_ABOVE;        // Condicao
input int               InpPeriod2   = 200;                  // Periodo (MA rapida se MA_CROSS)
input int               InpPeriod2b  = 0;                    // Periodo 2 (MA lenta se MA_CROSS, 0=nao usado)
input double            InpValue2    = 0.0;                  // Valor (0 = usa preco)

//+------------------------------------------------------------------+
//| INPUTS: Condicao 3                                               |
//+------------------------------------------------------------------+
input group "=== [4] Condicao 3 ==="
input bool              InpUseCond3  = false;
input ENUM_BP_INDICATOR InpInd3      = BP_IND_NONE;
input ENUM_BP_CONDITION InpCond3     = BP_COND_NONE;
input int               InpPeriod3   = 14;
input int               InpPeriod3b  = 0;                    // Periodo 2 (MA lenta se MA_CROSS, 0=nao usado)
input double            InpValue3    = 0.0;

//+------------------------------------------------------------------+
//| INPUTS: Tipo de Entrada e Direcao                               |
//+------------------------------------------------------------------+
input group "=== [5] Entrada ==="
input ENUM_BP_ENTRY_TYPE      InpEntryType        = BP_ENTRY_NEXT_OPEN;  // Tipo de entrada
input int                     InpStopOrderBuffer  = 1;                   // [STOP_ORDER] Ticks acima/abaixo da max/min do candle trigger
input int                     InpStopOrderExpBars = 1;                   // [STOP_ORDER] Validade do sinal em candles (1=expira no candle seguinte ao trigger)
input ENUM_TRADING_DIRECTION  InpDirection        = TRADING_BOTH;        // Direcao permitida (0=AMBAS, 1=SO_COMPRA, -1=SO_VENDA)

//+------------------------------------------------------------------+
//| INPUTS: Stop Loss                                                |
//+------------------------------------------------------------------+
input group "=== [6] Stop Loss ==="
input ENUM_BP_SL_TYPE InpSLType        = BP_SL_CANDLE; // Tipo de SL (0=ATR, 1=FIXED, 2=CANDLE, 10=FIBO)
input int    InpSL_ATRPeriod           = 14;           // Periodo ATR
input double InpSL_ATRMult             = 1.5;          // Multiplicador ATR
input int    InpSL_FixedPts            = 100;          // Pontos fixos
input int    InpSL_Buffer              = 5;            // Buffer grafico (ticks)
input int    InpSL_CandlesBack         = 1;            // [CANDLE] Buscar max/min dos ultimos N candles
input int    InpSL_Min                 = 10;           // Stop minimo (pontos)
input int    InpSL_Max                 = 5000;         // Stop maximo (pontos, 0=sem limite)

//+------------------------------------------------------------------+
//| INPUTS: Take Profit                                              |
//+------------------------------------------------------------------+
input group "=== [7] Take Profit ==="
input ENUM_BP_TP_TYPE InpTPType        = BP_TP_RR;    // Tipo de TP (0=FIXED, 1=RR, 2=ZIGZAG, 3=ATR, 10=FIBO)
input int    InpTP_FixedPts            = 200;                // Pontos fixos
input double InpTP_RR                  = 2.0;                // Ratio R:R
input int    InpTP_ZZDepth             = 12;                 // ZigZag Depth
input int    InpTP_ZZDeviation         = 5;                  // ZigZag Deviation
input int    InpTP_ZZBackstep          = 3;                  // ZigZag Backstep
input int    InpTP_ZZBuffer            = 2;                  // ZigZag Buffer (ticks)
input int    InpTP_Min                 = 10;                 // TP minimo (pontos)
input int    InpTP_Max                 = 0;                  // TP maximo (pontos, 0=sem limite)
input int    InpTP_ATRPeriod           = 14;                 // ATR Period (para TP_ATR)
input double InpTP_ATRPercent          = 100.0;              // ATR Percentual (para TP_ATR)
input ENUM_TIMEFRAMES InpTP_ATRTF      = PERIOD_D1;          // ATR Timeframe (para TP_ATR)

//+------------------------------------------------------------------+
//| INPUTS: Gestao de Risco                                          |
//+------------------------------------------------------------------+
input group "=== [8] Risco ==="
input ENUM_RISK_TYPE InpRiskType  = RISK_FIXED;  // Tipo de risco (0=FIXED, 1=PERCENT, 2=PROGRESSION)
input double InpRiskPercent       = 1.0;          // Risco por operacao (%)
input double InpFixedLots         = 0.1;          // Lote fixo
input double InpInitialAlloc      = 10000.0;      // Capital alocado

//+------------------------------------------------------------------+
//| INPUTS: Janela de Operacao                                       |
//+------------------------------------------------------------------+
input group "=== [9] Janela de Operacao ==="
input int InpStartHour      = 9;    // Hora inicio (novas entradas)
input int InpStartMin       = 0;    // Minuto inicio
input int InpEndHour        = 17;   // Hora fim (novas entradas)
input int InpEndMin         = 30;   // Minuto fim
input int InpCloseHour      = 17;   // Hora encerramento forcado de posicoes
input int InpCloseMin       = 45;   // Minuto encerramento forcado
input int InpMaxTradesPerDay= 0;    // Max operacoes por dia (0 = sem limite)

//+------------------------------------------------------------------+
//| INPUTS: Padroes de Candle (modulo opcional)                     |
//+------------------------------------------------------------------+
input group "=== [10] Padroes de Candle ==="
input ENUM_BP_CANDLE_PATTERN InpCandleBull = BP_CANDLE_NONE;  // Padrao de alta
input ENUM_BP_CANDLE_PATTERN InpCandleBear = BP_CANDLE_NONE;  // Padrao de baixa

//+------------------------------------------------------------------+
//| INPUTS: Smart Money (modulo isolado)                            |
//+------------------------------------------------------------------+
input group "=== [11] Smart Money ==="
input ENUM_BP_SMC_CONCEPT    InpSMCEntry      = BP_SMC_NONE;          // Conceito SMC de entrada
input ENUM_BP_FVG_ENTRY_MODE InpFVGEntryMode  = FVG_ENTRY_AGGRESSIVE; // [FVG] Modo de entrada (Imediata / Correcao Limite)
input int    InpBOS_Leg1Min       = 2;  // [BoS] Min candles 1a perna
input int    InpBOS_Leg1Max       = 5;  // [BoS] Max candles 1a perna
input int    InpBOS_CorrectionMax = 3;  // [BoS] Max candles correcao
input int    InpBOS_Leg2Max       = 3;  // [BoS] Max candles 2a perna
input int    InpCHoCH_TrendMin          = 5;   // [CHoCH] Min candles tendencia previa
input int    InpCHoCH_TrendMax          = 15;  // [CHoCH] Max candles tendencia previa
input int    InpCHoCH_MinAmplitudeRatio = 40;  // [CHoCH] Min % amplitude 1a perna vs previa
input ENUM_BP_OB_MITIGATION InpOB_Mitigation = OB_MITIGATION_NONE; // [OB] Filtro de mitigacao (BoS/CHoCH)

//+------------------------------------------------------------------+
//| INPUTS: Trailing Stop                                             |
//+------------------------------------------------------------------+
input group "=== [12] Trailing Stop ==="
input ENUM_BP_TRAILING_TYPE    InpTrailType        = BP_TRAIL_NONE;        // Tipo de trailing (0=OFF, 1=RR, 2=BAR, 3=ATR)
input ENUM_BP_ACTIVATION_MODE  InpTrailActMode     = BP_ACT_IMMEDIATE;     // Modo de ativacao
input double InpTrailRRBreakeven   = 1.0;    // [RR] RR para breakeven
input double InpTrailRRTrailing    = 1.5;    // [RR] RR para iniciar trailing
input int    InpTrailStepPts       = 10;     // Step minimo em pontos
input bool   InpTrailOnlyFavorable = false;  // So mover em barras favoraveis
input int    InpTrailBufferTicks   = 5;      // Buffer em ticks
input int    InpTrailATRPeriod     = 14;     // [ATR] Periodo ATR
input double InpTrailATRBreakMult  = 0.0;    // [ATR] Multiplicador ATR breakeven (0=off)
input double InpTrailATRMult       = 2.0;    // [ATR] Multiplicador ATR trailing
input int    InpTrailMinPoints     = 10;     // Distancia minima em pontos
input double InpTrailMinProfit     = 0.0;    // Lucro minimo para ativar (moeda)

//+------------------------------------------------------------------+
//| INPUTS: Saida Parcial                                             |
//+------------------------------------------------------------------+
input group "=== [13] Saida Parcial ==="
input bool   InpUsePartial       = false;   // Usar saida parcial
input int    InpPartialPct       = 50;      // % do volume a fechar (1-99)
input int    InpPartialTriggerPts= 100;     // Pontos de lucro para ativar
input bool   InpPartialMoveSL    = true;    // Mover SL para breakeven apos parcial

//+------------------------------------------------------------------+
//| INPUTS: Saida por Condicao                                        |
//+------------------------------------------------------------------+
input group "=== [14] Saida por Condicao ==="
input bool              InpUseExitCond  = false;         // Usar saida por condicao
input ENUM_BP_INDICATOR InpExitInd      = BP_IND_NONE;   // Indicador de saida
input ENUM_BP_CONDITION InpExitCond     = BP_COND_NONE;  // Condicao de saida
input int               InpExitPeriod   = 14;            // Periodo
input double            InpExitValue    = 0.0;           // Valor de referencia

//+------------------------------------------------------------------+
//| INPUTS: Fibonacci (modulo opcional, substitui Cond1/2/3)         |
//+------------------------------------------------------------------+
input group "=== [15] Fibonacci ==="
input int                       InpFibo_ZZDepth      = 12;                        // ZigZag Depth
input int                       InpFibo_ZZDeviation  = 5;                         // ZigZag Deviation
input int                       InpFibo_ZZBackstep   = 3;                         // ZigZag Backstep
input ENUM_BP_FIBO_LEVEL        InpFibo_TriggerLevel = BP_FIBO_618;               // Nivel de retracao p/ monitorar trigger
input ENUM_BP_FIBO_TRIGGER_MODE InpFibo_TriggerMode  = BP_FIBO_TRIG_VALIDATION;   // Modo de trigger (TOQUE ou VALIDACAO)
input ENUM_BP_FIBO_LEVEL        InpFibo_SLLevel      = BP_FIBO_100;               // Nivel Fibo usado como SL (se InpSLType = BP_SL_FIBO)
input ENUM_BP_FIBO_LEVEL        InpFibo_TPLevel      = BP_FIBO_1618;              // Nivel Fibo usado como TP (se InpTPType = BP_TP_FIBO)
input bool                      InpFibo_Debug        = false;                     // [DEBUG] Desenha linhas Fibo no chart (requer LogLevel=DEBUG)
input ENUM_BP_TRIGGER_HIGHLIGHT InpFibo_DebugHighlight = BP_HL_BOTH;               // [DEBUG] Como destacar o candle que disparou o trigger

//+------------------------------------------------------------------+
//| Handles do Framework alphaQuant                                  |
//+------------------------------------------------------------------+
int g_hLogger         = -1;
int g_hLicense        = -1;
int g_hRisk           = -1;
int g_hSL             = -1;
int g_hTP             = -1;
int g_hOrder          = -1;
int g_hTracker        = -1;
int g_hTrailing       = -1;
int g_hTriggerMonitor = -1;

//+------------------------------------------------------------------+
//| Handles dos indicadores BP                                       |
//+------------------------------------------------------------------+
int g_hBPIndicators = -1;
int g_hBPOscillators= -1;
int g_hBPCandles    = -1;
int g_hBPSmartMoney = -1;
int g_hBPFibonacci  = -1;
int g_hBPSignal     = -1;

//+------------------------------------------------------------------+
//| Estado interno                                                    |
//+------------------------------------------------------------------+
datetime g_lastBarTime        = 0;
datetime g_currentDay         = 0;   // Dia atual para reset do contador
bool     g_partialDone        = false;  // Saida parcial ja executada para posicao atual
datetime g_lastStopOrderBarTime = 0;   // Barra em que a ultima ordem STOP foi colocada (evita recolocar na mesma barra)

//+------------------------------------------------------------------+
//| Funcoes auxiliares                                               |
//+------------------------------------------------------------------+
bool IsNewBar()
{
   datetime current = iTime(_Symbol, PERIOD_CURRENT, 0);
   if(current != g_lastBarTime)
   {
      g_lastBarTime = current;
      return true;
   }
   return false;
}

bool IsInTradingWindow()
{
   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);
   int now = dt.hour * 60 + dt.min;
   int start = InpStartHour * 60 + InpStartMin;
   int end   = InpEndHour   * 60 + InpEndMin;
   return (now >= start && now < end);
}

bool HasOpenPosition()
{
   return PositionTracker_GetOpenCount(g_hTracker) > 0;
}

void ResetDailyCounterIfNeeded()
{
   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);
   datetime today = (datetime)(dt.year * 10000 + dt.mon * 100 + dt.day);
   if(today != g_currentDay)
   {
      g_currentDay = today;
      OrderManager_ResetExecutedPositionsCount(g_hOrder);
      PositionTracker_CleanupClosedPositions(g_hTracker);
      RiskManager_OnNewDay(g_hRisk);
   }
}

//+------------------------------------------------------------------+
//| Verifica horario de encerramento e fecha posicoes/pendentes      |
//+------------------------------------------------------------------+
void CheckForceClose()
{
   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);
   int now   = dt.hour * 60 + dt.min;
   int close = InpCloseHour * 60 + InpCloseMin;
   if(now < close) return;

   //--- Cancela ordens pendentes registradas no TriggerMonitor
   if(g_hTriggerMonitor >= 0 && TriggerMonitor_GetPendingOrderCount(g_hTriggerMonitor) > 0)
   {
      TriggerMonitor_CancelAllPendingOrders(g_hTriggerMonitor);
      Logger_Info(g_hLogger, "Encerramento forcado: ordens pendentes canceladas");
   }

   //--- Fecha posicoes abertas
   if(HasOpenPosition())
   {
      OrderManager_CloseAllPositions(g_hOrder);
      Logger_Info(g_hLogger, "Encerramento forcado: posicoes fechadas (" +
                  IntegerToString(InpCloseHour) + "h" + StringFormat("%02d", InpCloseMin) + ")");
   }
}

bool HasReachedDailyLimit()
{
   if(InpMaxTradesPerDay <= 0) return false;
   return OrderManager_GetExecutedPositionsCount(g_hOrder) >= InpMaxTradesPerDay;
}

//+------------------------------------------------------------------+
//| Monta lista de condicoes ativas                                  |
//+------------------------------------------------------------------+
int BuildConditions(BPCondition &conditions[])
{
   ArrayResize(conditions, BP_MAX_CONDITIONS);
   int count = 0;

   // Condicao 1 (sempre ativa)
   conditions[count].indicator = InpInd1;
   conditions[count].condition = InpCond1;
   conditions[count].period    = InpPeriod1;
   conditions[count].period2   = InpPeriod1b;
   conditions[count].value     = InpValue1;
   conditions[count].value2    = 0.0;
   count++;

   // Condicao 2
   if(InpUseCond2 && InpInd2 != BP_IND_NONE)
   {
      conditions[count].indicator = InpInd2;
      conditions[count].condition = InpCond2;
      conditions[count].period    = InpPeriod2;
      conditions[count].period2   = InpPeriod2b;
      conditions[count].value     = InpValue2;
      conditions[count].value2    = 0.0;
      count++;
   }

   // Condicao 3
   if(InpUseCond3 && InpInd3 != BP_IND_NONE)
   {
      conditions[count].indicator = InpInd3;
      conditions[count].condition = InpCond3;
      conditions[count].period    = InpPeriod3;
      conditions[count].period2   = InpPeriod3b;
      conditions[count].value     = InpValue3;
      conditions[count].value2    = 0.0;
      count++;
   }

   ArrayResize(conditions, count);
   return count;
}

//+------------------------------------------------------------------+
//| Retorna nome legivel do indicador                               |
//+------------------------------------------------------------------+
string IndicatorName(ENUM_BP_INDICATOR ind, int period, int period2 = 0)
{
   switch(ind)
   {
      case BP_IND_RSI:      return "RSI("     + IntegerToString(period) + ")";
      case BP_IND_STOCH:    return "Stoch("   + IntegerToString(period) + ")";
      case BP_IND_CCI:      return "CCI("     + IntegerToString(period) + ")";
      case BP_IND_WILLIAMS: return "Williams("+ IntegerToString(period) + ")";
      case BP_IND_MACD:     return "MACD("    + IntegerToString(period) + ")";
      case BP_IND_SMA:      return period2 > 0
                                   ? "SMA(" + IntegerToString(period) + "x" + IntegerToString(period2) + ")"
                                   : "SMA(" + IntegerToString(period) + ")";
      case BP_IND_EMA:      return period2 > 0
                                   ? "EMA(" + IntegerToString(period) + "x" + IntegerToString(period2) + ")"
                                   : "EMA(" + IntegerToString(period) + ")";
      case BP_IND_ADX:      return "ADX("     + IntegerToString(period) + ")";
      case BP_IND_HILO:     return "HiLo("    + IntegerToString(period) + ")";
      case BP_IND_VOLUME:   return "Volume";
      case BP_IND_OBV:      return "OBV";
      case BP_IND_BOLLINGER:return "BB(" + IntegerToString(period) + ")";
      default:              return "Ind(" + IntegerToString(ind) + ")";
   }
}

string ConditionName(ENUM_BP_CONDITION cond)
{
   switch(cond)
   {
      case BP_COND_CROSS_ABOVE:       return "cruzou ACIMA de";
      case BP_COND_CROSS_BELOW:       return "cruzou ABAIXO de";
      case BP_COND_ABOVE:             return "esta ACIMA de";
      case BP_COND_BELOW:             return "esta ABAIXO de";
      case BP_COND_IN_ZONE_OB:        return "em zona SOBRECOMPRA";
      case BP_COND_IN_ZONE_OS:        return "em zona SOBREVENDA";
      case BP_COND_CROSS_ABOVE_PRICE: return "cruzou ACIMA do preco";
      case BP_COND_CROSS_BELOW_PRICE: return "cruzou ABAIXO do preco";
      case BP_COND_MACD_CROSS_UP:     return "MACD cruzou sinal PARA CIMA";
      case BP_COND_MACD_CROSS_DOWN:   return "MACD cruzou sinal PARA BAIXO";
      case BP_COND_MACD_ABOVE_ZERO:   return "MACD acima de zero";
      case BP_COND_MACD_BELOW_ZERO:   return "MACD abaixo de zero";
      case BP_COND_MA_CROSS_ABOVE:    return "MA rapida cruza ACIMA da lenta";
      case BP_COND_MA_CROSS_BELOW:    return "MA rapida cruza ABAIXO da lenta";
      case BP_COND_HILO_BUY:          return "HiLo COMPRA";
      case BP_COND_HILO_SELL:         return "HiLo VENDA";
      case BP_COND_HILO_CHANGED:      return "HiLo MUDOU direcao";
      default:                        return "?";
   }
}

//+------------------------------------------------------------------+
//| Loga estado diagnostico de todas as condicoes ativas            |
//| Chamada a cada novo candle quando nivel >= DEBUG                 |
//+------------------------------------------------------------------+
void LogDiagnostic(const BPCondition &conditions[], int count)
{
   if(g_hLogger < 0) return;
   if(Logger_GetLevel(g_hLogger) < LOG_LEVEL_DEBUG) return;

   //--- Hora e preco de referencia: candle[1] (candle trigger)
   datetime barTime = iTime(_Symbol, PERIOD_CURRENT, 1);
   MqlDateTime dt;
   TimeToStruct(barTime, dt);
   string timeStr = StringFormat("%02d:%02d", dt.hour, dt.min);
   double closeRef = iClose(_Symbol, PERIOD_CURRENT, 1);
   double highRef  = iHigh(_Symbol,  PERIOD_CURRENT, 1);
   double lowRef   = iLow(_Symbol,   PERIOD_CURRENT, 1);

   Logger_Debug(g_hLogger, "");
   Logger_Debug(g_hLogger, "=== DIAGNOSTICO CANDLE " + timeStr +
                " | C=" + DoubleToString(closeRef, _Digits) +
                " H=" + DoubleToString(highRef, _Digits) +
                " L=" + DoubleToString(lowRef, _Digits) + " ===");

   //--- Janela de operacao
   string winStatus = IsInTradingWindow() ? "[DENTRO]" : "[FORA]";
   Logger_Debug(g_hLogger, "  Janela " + IntegerToString(InpStartHour) + "h" +
                StringFormat("%02d", InpStartMin) + "-" +
                IntegerToString(InpEndHour) + "h" +
                StringFormat("%02d", InpEndMin) + ": " + winStatus);

   //--- Posicao aberta
   int openCount = PositionTracker_GetOpenCount(g_hTracker);
   Logger_Debug(g_hLogger, "  Posicoes abertas: " + IntegerToString(openCount));

   //--- Direcao permitida
   string dirStr = (InpDirection == TRADING_BUY_ONLY)  ? "SO COMPRA" :
                   (InpDirection == TRADING_SELL_ONLY) ? "SO VENDA"  : "AMBAS";
   Logger_Debug(g_hLogger, "  Direcao: " + dirStr);

   //--- Contador diario (posicoes efetivamente executadas via OrderManager)
   int tradesHoje = OrderManager_GetExecutedPositionsCount(g_hOrder);
   string limitStr = (InpMaxTradesPerDay > 0)
      ? IntegerToString(tradesHoje) + "/" + IntegerToString(InpMaxTradesPerDay)
      : IntegerToString(tradesHoje) + " (sem limite)";
   Logger_Debug(g_hLogger, "  Operacoes hoje: " + limitStr);

   //--- Avalia cada condicao individualmente
   Logger_Debug(g_hLogger, "  --- Condicoes (" + IntegerToString(count) + " ativas) ---");
   for(int i = 0; i < count; i++)
   {
      ENUM_BP_INDICATOR cInd    = conditions[i].indicator;
      ENUM_BP_CONDITION cCond   = conditions[i].condition;
      int    cPeriod  = conditions[i].period;
      int    cPeriod2 = conditions[i].period2;
      double cValue   = conditions[i].value;

      string indName  = IndicatorName(cInd, cPeriod, cPeriod2);
      string condName = ConditionName(cCond);

      //--- Busca valores reais do indicador no candle[1] e candle[2]
      double v1 = 0, v2 = 0;
      bool hasValue = true;

      switch(cInd)
      {
         case BP_IND_RSI:
            v1 = BP_Indicators_RSI(g_hBPIndicators, cPeriod, 1);
            v2 = BP_Indicators_RSI(g_hBPIndicators, cPeriod, 2);
            break;
         case BP_IND_STOCH:
            v1 = BP_Indicators_StochK(g_hBPIndicators, cPeriod, 1);
            v2 = BP_Indicators_StochK(g_hBPIndicators, cPeriod, 2);
            break;
         case BP_IND_CCI:
            v1 = BP_Indicators_CCI(g_hBPIndicators, cPeriod, 1);
            v2 = BP_Indicators_CCI(g_hBPIndicators, cPeriod, 2);
            break;
         case BP_IND_WILLIAMS:
            v1 = BP_Indicators_Williams(g_hBPIndicators, cPeriod, 1);
            v2 = BP_Indicators_Williams(g_hBPIndicators, cPeriod, 2);
            break;
         case BP_IND_MACD:
            v1 = BP_Indicators_MACDMain(g_hBPIndicators, cPeriod, 1);
            v2 = BP_Indicators_MACDMain(g_hBPIndicators, cPeriod, 2);
            break;
         case BP_IND_SMA:
            v1 = BP_Indicators_SMA(g_hBPIndicators, cPeriod, 1);
            v2 = BP_Indicators_SMA(g_hBPIndicators, cPeriod, 2);
            break;
         case BP_IND_EMA:
            v1 = BP_Indicators_EMA(g_hBPIndicators, cPeriod, 1);
            v2 = BP_Indicators_EMA(g_hBPIndicators, cPeriod, 2);
            break;
         case BP_IND_ADX:
            v1 = BP_Indicators_ADX(g_hBPIndicators, cPeriod, 1);
            v2 = BP_Indicators_ADX(g_hBPIndicators, cPeriod, 2);
            break;
         case BP_IND_VOLUME:
            v1 = BP_Indicators_Volume(g_hBPIndicators, 1);
            v2 = BP_Indicators_Volume(g_hBPIndicators, 2);
            break;
         case BP_IND_OBV:
            v1 = BP_Indicators_OBV(g_hBPIndicators, 1);
            v2 = BP_Indicators_OBV(g_hBPIndicators, 2);
            break;
         case BP_IND_HILO:
            v1 = (double)BP_Indicators_HiLo(g_hBPIndicators, cPeriod, 1);
            v2 = (double)BP_Indicators_HiLo(g_hBPIndicators, cPeriod, 2);
            break;
         case BP_IND_BOLLINGER:
         {
            int banda = (int)cValue;
            if(banda == 2)      { v1 = BP_Indicators_BollUpper(g_hBPIndicators,  cPeriod, 1); v2 = BP_Indicators_BollUpper(g_hBPIndicators,  cPeriod, 2); }
            else if(banda == 1) { v1 = BP_Indicators_BollMiddle(g_hBPIndicators, cPeriod, 1); v2 = BP_Indicators_BollMiddle(g_hBPIndicators, cPeriod, 2); }
            else                { v1 = BP_Indicators_BollLower(g_hBPIndicators,  cPeriod, 1); v2 = BP_Indicators_BollLower(g_hBPIndicators,  cPeriod, 2); }
            break;
         }
         default:
            hasValue = false;
            break;
      }

      //--- Referencia: para Bollinger mostra qual banda; para outros: valor fixo ou "preco"
      string bandaNames[] = {"inferior", "media", "superior"};
      string refStr;
      if(cInd == BP_IND_BOLLINGER)
         refStr = "banda " + bandaNames[MathMin((int)cValue, 2)];
      else
         refStr = (cValue != 0.0) ? StringFormat("%.4f", cValue) : "preco";

      //--- Verifica se a condicao esta sendo satisfeita
      bool passed = false;
      if(hasValue && v1 != EMPTY_VALUE && v2 != EMPTY_VALUE)
      {
         //--- HiLo: v1/v2 sao +1(buy)/-1(sell)/0(indefinido)
         if(cInd == BP_IND_HILO)
         {
            switch(cCond)
            {
               case BP_COND_HILO_BUY:     passed = ((int)v1 == +1); break;
               case BP_COND_HILO_SELL:    passed = ((int)v1 == -1); break;
               case BP_COND_HILO_CHANGED: passed = ((int)v1 != (int)v2 && (int)v2 != 0); break;
               default: passed = false; break;
            }
         }
         //--- Bollinger: compara preco vs banda (v1/v2 ja sao a banda escolhida)
         else if(cInd == BP_IND_BOLLINGER)
         {
            switch(cCond)
            {
               case BP_COND_CROSS_ABOVE: passed = (iClose(_Symbol,PERIOD_CURRENT,2) < v2 && closeRef >= v1); break;
               case BP_COND_CROSS_BELOW: passed = (iClose(_Symbol,PERIOD_CURRENT,2) > v2 && closeRef <= v1); break;
               case BP_COND_ABOVE:       passed = (closeRef > v1); break;
               case BP_COND_BELOW:       passed = (closeRef < v1); break;
               default:                  passed = false; break;
            }
         }
         else switch(cCond)
         {
            case BP_COND_CROSS_ABOVE:
               passed = (v2 < cValue && v1 >= cValue);
               break;
            case BP_COND_CROSS_BELOW:
               passed = (v2 > cValue && v1 <= cValue);
               break;
            case BP_COND_ABOVE:
               passed = (cValue == 0.0) ? (closeRef > v1) : (v1 > cValue);
               break;
            case BP_COND_BELOW:
               passed = (cValue == 0.0) ? (closeRef < v1) : (v1 < cValue);
               break;
            case BP_COND_IN_ZONE_OB:
               if(cInd == BP_IND_RSI  || cInd == BP_IND_STOCH) passed = (v1 >= 70.0);
               else if(cInd == BP_IND_CCI)     passed = (v1 >= 100.0);
               else if(cInd == BP_IND_WILLIAMS)passed = (v1 >= -20.0);
               else passed = (v1 >= cValue);
               break;
            case BP_COND_IN_ZONE_OS:
               if(cInd == BP_IND_RSI  || cInd == BP_IND_STOCH) passed = (v1 <= 30.0);
               else if(cInd == BP_IND_CCI)     passed = (v1 <= -100.0);
               else if(cInd == BP_IND_WILLIAMS)passed = (v1 <= -80.0);
               else passed = (v1 <= cValue);
               break;
            case BP_COND_CROSS_ABOVE_PRICE:
               passed = (v2 <= iClose(_Symbol, PERIOD_CURRENT, 2) && v1 > closeRef);
               break;
            case BP_COND_CROSS_BELOW_PRICE:
               passed = (v2 >= iClose(_Symbol, PERIOD_CURRENT, 2) && v1 < closeRef);
               break;
            default:
               passed = false;
               break;
         }
      }

      string status = passed ? "[OK]" : "[--]";

      //--- Linha principal
      string line = StringFormat("  %s C%d %s | %s ref=%s | atual=%.4f prev=%.4f",
                                 status, i+1, indName, condName, refStr, v1, v2);

      //--- Para MA: detalhe extra com preco vs MA
      if(cInd == BP_IND_SMA || cInd == BP_IND_EMA)
      {
         string priceVsMA = (closeRef > v1) ? "preco ACIMA" : "preco ABAIXO";
         int diffPts = (int)MathRound(MathAbs(closeRef - v1) / SymbolInfoDouble(_Symbol, SYMBOL_POINT));
         line += StringFormat(" | %s (C=%.5f MA=%.5f dif=%dpts)", priceVsMA, closeRef, v1, diffPts);
      }
      //--- Para Bollinger: detalhe extra com preco vs banda
      else if(cInd == BP_IND_BOLLINGER)
      {
         string priceVsBand = (closeRef > v1) ? "preco ACIMA" : "preco ABAIXO";
         int diffPts = (int)MathRound(MathAbs(closeRef - v1) / SymbolInfoDouble(_Symbol, SYMBOL_POINT));
         line += StringFormat(" | %s banda (C=%.5f Banda=%.5f dif=%dpts)", priceVsBand, closeRef, v1, diffPts);
      }
      //--- Para MA_CROSS: detalhe com rapida vs lenta
      else if((cCond == BP_COND_MA_CROSS_ABOVE || cCond == BP_COND_MA_CROSS_BELOW) && cPeriod2 > 0)
      {
         double slow1 = (cInd == BP_IND_EMA) ? BP_Indicators_EMA(g_hBPIndicators, cPeriod2, 1)
                                              : BP_Indicators_SMA(g_hBPIndicators, cPeriod2, 1);
         double slow2 = (cInd == BP_IND_EMA) ? BP_Indicators_EMA(g_hBPIndicators, cPeriod2, 2)
                                              : BP_Indicators_SMA(g_hBPIndicators, cPeriod2, 2);
         string crossState = (v1 > slow1) ? "rapida ACIMA" : "rapida ABAIXO";
         int diffPts = (int)MathRound(MathAbs(v1 - slow1) / SymbolInfoDouble(_Symbol, SYMBOL_POINT));
         line += StringFormat(" | %s lenta (R=%.5f L=%.5f dif=%dpts)", crossState, v1, slow1, diffPts);
         // corrige o passed para MA_CROSS
         if(v1 != EMPTY_VALUE && v2 != EMPTY_VALUE && slow1 != EMPTY_VALUE && slow2 != EMPTY_VALUE)
            passed = (cCond == BP_COND_MA_CROSS_ABOVE) ? (v2 <= slow2 && v1 > slow1)
                                                       : (v2 >= slow2 && v1 < slow1);
         line = StringFormat("  %s C%d %s | %s", passed ? "[OK]" : "[--]", i+1, indName, condName)
              + StringFormat(" | rapida=%s lenta=%s", IntegerToString(cPeriod), IntegerToString(cPeriod2))
              + StringFormat(" | %s lenta (R=%.5f L=%.5f dif=%dpts)", crossState, v1, slow1, diffPts);
      }

      Logger_Debug(g_hLogger, line);
   }

   //--- Janela de candle
   if(InpUseCandlePatterns)
   {
      string bullName = EnumToString(InpCandleBull);
      string bearName = EnumToString(InpCandleBear);
      Logger_Debug(g_hLogger, "  --- Candle Patterns ---");
      Logger_Debug(g_hLogger, "  Bull: " + bullName + " | Bear: " + bearName);
   }

   //--- SMC
   if(InpUseSmartMoney)
   {
      Logger_Debug(g_hLogger, "  --- Smart Money ---");
      Logger_Debug(g_hLogger, "  Conceito: " + EnumToString(InpSMCEntry));
      if(InpSMCEntry == BP_SMC_FVG_BULL || InpSMCEntry == BP_SMC_FVG_BEAR)
         Logger_Debug(g_hLogger, "  FVG Modo: " + EnumToString(InpFVGEntryMode));
   }
}

//+------------------------------------------------------------------+
//| Executa ordem de entrada usando SL/TP do framework             |
//+------------------------------------------------------------------+
void ExecuteEntry(ENUM_BP_SIGNAL signal)
{
   if(HasOpenPosition()) return;

   int signalType = (signal == BP_SIGNAL_BUY) ? SIGNAL_BUY : SIGNAL_SELL;

   //--- Preco de entrada e referencia de candle trigger (candle[1] = candle que fechou)
   double entry = (signal == BP_SIGNAL_BUY) ? SymbolInfoDouble(_Symbol, SYMBOL_ASK)
                                             : SymbolInfoDouble(_Symbol, SYMBOL_BID);
   datetime triggerBarTime = iTime(_Symbol, PERIOD_CURRENT, 1);

   //--- Calcula SL: Fibo tem prioridade; SL_CANDLE com N>1 usa calculo proprio; senao framework
   double sl = 0.0;
   if(InpSLType == BP_SL_FIBO && g_hBPFibonacci >= 0)
      sl = BP_Fibonacci_CalculateSL(g_hBPFibonacci, signal, InpFibo_SLLevel, InpSL_Buffer);
   else if(InpSLType == BP_SL_CANDLE && InpSL_CandlesBack > 1)
      sl = CalculateGraphicSL_NCandles(signalType, entry, InpSL_CandlesBack);
   else
      sl = StopLoss_CalculateStopLoss(g_hSL, signalType, entry, triggerBarTime);
   if(sl <= 0.0)
   {
      Logger_Error(g_hLogger, "Falha ao calcular Stop Loss");
      return;
   }

   //--- Calcula TP: Fibo tem prioridade; senao framework
   double tp = 0.0;
   if(InpTPType == BP_TP_FIBO && g_hBPFibonacci >= 0)
      tp = BP_Fibonacci_CalculateTP(g_hBPFibonacci, signal, InpFibo_TPLevel);
   else
      tp = TakeProfit_Calculate(g_hTP, signalType, entry, sl);
   if(tp <= 0.0)
   {
      Logger_Error(g_hLogger, "Falha ao calcular Take Profit");
      return;
   }

   //--- Calcula lote via RiskManager
   double lots = RiskManager_CalculateLotSize(g_hRisk, entry, sl);
   if(lots <= 0.0)
   {
      Logger_Error(g_hLogger, "Tamanho de lote invalido: " + DoubleToString(lots, 2));
      return;
   }

   //--- Executa ordem
   ulong ticket = OrderManager_ExecuteMarketOrder(g_hOrder, signalType, lots, entry, sl, tp, "BP");

   if(ticket > 0)
   {
      // PositionTracker, RiskManager e contador: processados via OnTradeTransaction
      Logger_Info(g_hLogger, "Entrada executada: " + (signal == BP_SIGNAL_BUY ? "BUY" : "SELL") +
                  " lots=" + DoubleToString(lots, 2) +
                  " sl=" + DoubleToString(sl, _Digits) +
                  " tp=" + DoubleToString(tp, _Digits));
   }
   else
      Logger_Warning(g_hLogger, "Falha ao executar entrada: " + IntegerToString(GetLastError()));
}

//+------------------------------------------------------------------+
//| Coloca ordem STOP acima da maxima (BUY) ou abaixo da minima      |
//| (SELL) do candle trigger [1], com buffer em ticks               |
//+------------------------------------------------------------------+
void PlaceStopEntry(ENUM_BP_SIGNAL signal)
{
   if(HasOpenPosition()) return;
   if(TriggerMonitor_GetPendingOrderCount(g_hTriggerMonitor) > 0) return;

   //--- Evita recolocar ordem stop no mesmo candle em que ja foi colocada uma
   //--- (ocorre quando TriggerMonitor expira/cancela e o sinal ainda e valido)
   datetime triggerBarTime = iTime(_Symbol, PERIOD_CURRENT, 1);
   if(triggerBarTime == g_lastStopOrderBarTime) return;

   int signalType = (signal == BP_SIGNAL_BUY) ? SIGNAL_BUY : SIGNAL_SELL;

   //--- Preco de referencia: maxima do candle[1] para BUY, minima para SELL
   double refPrice = (signal == BP_SIGNAL_BUY)
                     ? iHigh(_Symbol, PERIOD_CURRENT, 1)
                     : iLow(_Symbol, PERIOD_CURRENT, 1);

   //--- Calcula SL: Fibo tem prioridade; SL_CANDLE com N>1 usa calculo proprio; senao framework
   double slEst = 0.0;
   if(InpSLType == BP_SL_FIBO && g_hBPFibonacci >= 0)
      slEst = BP_Fibonacci_CalculateSL(g_hBPFibonacci, signal, InpFibo_SLLevel, InpSL_Buffer);
   else if(InpSLType == BP_SL_CANDLE && InpSL_CandlesBack > 1)
      slEst = CalculateGraphicSL_NCandles(signalType, refPrice, InpSL_CandlesBack);
   else
      slEst = StopLoss_CalculateStopLoss(g_hSL, signalType, refPrice, triggerBarTime);
   if(slEst <= 0.0) { Logger_Error(g_hLogger, "PlaceStopEntry: falha ao calcular SL"); return; }

   //--- Calcula TP: Fibo tem prioridade; senao framework
   double tp = 0.0;
   if(InpTPType == BP_TP_FIBO && g_hBPFibonacci >= 0)
      tp = BP_Fibonacci_CalculateTP(g_hBPFibonacci, signal, InpFibo_TPLevel);
   else
      tp = TakeProfit_Calculate(g_hTP, signalType, refPrice, slEst);
   if(tp <= 0.0) { Logger_Error(g_hLogger, "PlaceStopEntry: falha ao calcular TP"); return; }

   double lots = RiskManager_CalculateLotSize(g_hRisk, refPrice, slEst);
   if(lots <= 0.0) { Logger_Error(g_hLogger, "PlaceStopEntry: lote invalido"); return; }

   //--- Coloca ordem stop via OrderManager (framework calcula entry = refPrice + buffer*tick)
   ulong ticket = OrderManager_PlacePendingOrder(
      g_hOrder, signalType, lots,
      refPrice,                    // max ou min do candle trigger
      (double)InpStopOrderBuffer,  // ticks acima/abaixo
      slEst, tp,
      0,                           // sem expiracao absoluta (TriggerMonitor controla por barras)
      "BP_STOP"
   );

   if(ticket > 0)
   {
      //--- Registra no TriggerMonitor: ele monitora, expira e cancela automaticamente
      TriggerMonitor_RegisterPendingOrder(g_hTriggerMonitor, (long)ticket);
      g_lastStopOrderBarTime = iTime(_Symbol, PERIOD_CURRENT, 1);  // marca barra para evitar recolocar
      // Nota: contador e RiskManager_OnNewOperation movidos para OnTradeTransaction
      Logger_Info(g_hLogger, "Ordem STOP registrada: " + (signal == BP_SIGNAL_BUY ? "BUY_STOP" : "SELL_STOP") +
                  " refPrice=" + DoubleToString(refPrice, _Digits) +
                  " buffer=" + IntegerToString(InpStopOrderBuffer) + " ticks" +
                  " sl=" + DoubleToString(slEst, _Digits) + " tp=" + DoubleToString(tp, _Digits));
   }
   else
      Logger_Warning(g_hLogger, "PlaceStopEntry: falha ao colocar ordem stop");
}

//+------------------------------------------------------------------+
//| Coloca ordem LIMIT na zona do FVG (modo mitigation)              |
//| BUY_LIMIT no topo da zona (zoneHigh) para FVG bullish            |
//| SELL_LIMIT no fundo da zona (zoneLow) para FVG bearish           |
//| Stop fixo na borda oposta do FVG                                 |
//| Expiracao controlada por InpStopOrderExpBars + TriggerMonitor    |
//+------------------------------------------------------------------+
void PlaceFVGLimitEntry(ENUM_BP_SIGNAL signal, double zoneHigh, double zoneLow)
{
   if(HasOpenPosition()) return;
   if(TriggerMonitor_GetPendingOrderCount(g_hTriggerMonitor) > 0) return;

   // Evita recolocar no mesmo candle
   datetime triggerBarTime = iTime(_Symbol, PERIOD_CURRENT, 1);
   if(triggerBarTime == g_lastStopOrderBarTime) return;

   double entryPrice = 0.0;
   double sl         = 0.0;
   int    signalType = 0;

   if(signal == BP_SIGNAL_BUY)
   {
      signalType = SIGNAL_BUY;
      entryPrice = zoneHigh;  // BUY_LIMIT: preco de entrada no topo da zona
      sl         = zoneLow;   // Stop fixo na borda oposta (fundo do FVG)
   }
   else
   {
      signalType = SIGNAL_SELL;
      entryPrice = zoneLow;   // SELL_LIMIT: preco de entrada no fundo da zona
      sl         = zoneHigh;  // Stop fixo na borda oposta (topo do FVG)
   }

   double tp = TakeProfit_Calculate(g_hTP, signalType, entryPrice, sl);
   if(tp <= 0.0) { Logger_Error(g_hLogger, "PlaceFVGLimitEntry: falha ao calcular TP"); return; }

   double lots = RiskManager_CalculateLotSize(g_hRisk, entryPrice, sl);
   if(lots <= 0.0) { Logger_Error(g_hLogger, "PlaceFVGLimitEntry: lote invalido"); return; }

   // Coloca ordem limite via OrderManager
   // signalType para limite: BUY_LIMIT = SIGNAL_BUY, SELL_LIMIT = SIGNAL_SELL
   // buffer = 0 (preco exato da zona)
   ulong ticket = OrderManager_PlacePendingOrder(
      g_hOrder, signalType, lots,
      entryPrice,       // preco de entrada na zona FVG
      0.0,              // sem buffer (preco exato)
      sl, tp,
      0,                // sem expiracao absoluta (TriggerMonitor controla por barras)
      "BP_FVG_LIMIT"
   );

   if(ticket > 0)
   {
      TriggerMonitor_RegisterPendingOrder(g_hTriggerMonitor, (long)ticket);
      g_lastStopOrderBarTime = iTime(_Symbol, PERIOD_CURRENT, 1);
      // Nota: contador e RiskManager_OnNewOperation movidos para OnTradeTransaction
      Logger_Info(g_hLogger, "Ordem FVG LIMIT registrada: " + (signal == BP_SIGNAL_BUY ? "BUY_LIMIT" : "SELL_LIMIT") +
                  " entry=" + DoubleToString(entryPrice, _Digits) +
                  " zoneHigh=" + DoubleToString(zoneHigh, _Digits) +
                  " zoneLow=" + DoubleToString(zoneLow, _Digits) +
                  " sl=" + DoubleToString(sl, _Digits) + " tp=" + DoubleToString(tp, _Digits));
   }
   else
      Logger_Warning(g_hLogger, "PlaceFVGLimitEntry: falha ao colocar ordem limite");
}

//+------------------------------------------------------------------+
//| OnInit                                                           |
//+------------------------------------------------------------------+
int OnInit()
{
   //--- 1. Logger
   g_hLogger = Logger_Create("BP_EA", InpLogLevel, InpLogOutput, true);
   if(g_hLogger < 0) return INIT_FAILED;
   Logger_Info(g_hLogger, "BacktestPro Universal EA v" + BP_VERSION + " iniciando...");

   //--- 2. License
   g_hLicense = License_Create(g_hLogger);
   if(g_hLicense < 0) { Logger_Error(g_hLogger, "License_Create falhou"); return INIT_FAILED; }
   if(!License_IsAuthorized(g_hLicense))
   { Logger_Error(g_hLogger, "Licenca nao autorizada"); return INIT_FAILED; }

   //--- 3. PositionTracker
   g_hTracker = PositionTracker_Create(_Symbol, BP_MAGIC_NUMBER, g_hLogger);
   if(g_hTracker < 0) { Logger_Error(g_hLogger, "PositionTracker_Create falhou"); return INIT_FAILED; }
   PositionTracker_RecoverStateAfterRestart(g_hTracker);

   //--- 4. RiskManager
   g_hRisk = RiskManager_Create(_Symbol, BP_MAGIC_NUMBER, g_hLogger,
                                 InpRiskType, InpFixedLots, InpInitialAlloc,
                                 InpRiskPercent, 1);
   if(g_hRisk < 0) { Logger_Error(g_hLogger, "RiskManager_Create falhou"); return INIT_FAILED; }

   //--- 5. StopLossManager
   //--- BP_SL_FIBO: nao existe no framework; usa SL_FIXED como placeholder,
   //--- o preco e calculado pelo modulo BP_Fibonacci no EA (ver ExecuteEntry).
   ENUM_STOP_LOSS_TYPE fwSLType = (InpSLType == BP_SL_FIBO)
      ? SL_FIXED
      : (ENUM_STOP_LOSS_TYPE)InpSLType;
   g_hSL = StopLoss_Create(_Symbol, PERIOD_CURRENT, g_hLogger,
                            fwSLType, InpSL_ATRPeriod, InpSL_ATRMult,
                            InpSL_FixedPts, InpSL_Buffer, InpSL_Min, InpSL_Max);
   if(g_hSL < 0) { Logger_Error(g_hLogger, "StopLoss_Create falhou"); return INIT_FAILED; }

   //--- 6. TakeProfitManager
   //--- BP_TP_FIBO: nao existe no framework; usa TP_FIXED_POINTS como placeholder.
   ENUM_TAKE_PROFIT_TYPE fwTPType = (InpTPType == BP_TP_FIBO)
      ? TP_FIXED_POINTS
      : (ENUM_TAKE_PROFIT_TYPE)InpTPType;
   g_hTP = TakeProfit_Create(_Symbol, PERIOD_CURRENT, g_hLogger,
                              fwTPType, InpTP_FixedPts, InpTP_RR,
                              InpTP_ZZDepth, InpTP_ZZDeviation, InpTP_ZZBackstep,
                              InpTP_ZZBuffer, InpTP_Min, InpTP_Max,
                              InpTP_ATRPeriod, InpTP_ATRPercent, InpTP_ATRTF);
   if(g_hTP < 0) { Logger_Error(g_hLogger, "TakeProfit_Create falhou"); return INIT_FAILED; }

   //--- 7. TrailingStopManager (configurado via inputs [12])
   g_hTrailing = TrailingStop_Create(_Symbol, PERIOD_CURRENT, g_hLogger, g_hTracker,
                                      (int)InpTrailType,       // TRAILING_NONE/RR/BAR/ATR
                                      (int)InpTrailActMode,    // ACTIVATION mode
                                      PRICE_BID_ASK,           // price source
                                      InpTrailRRBreakeven,     // RR breakeven
                                      InpTrailRRTrailing,      // RR trailing
                                      InpTrailStepPts,         // step points
                                      InpTrailOnlyFavorable,   // only favorable bars
                                      InpTrailBufferTicks,     // buffer ticks
                                      InpTrailATRPeriod,       // ATR period
                                      InpTrailATRBreakMult,    // ATR breakeven mult
                                      InpTrailATRMult,         // ATR trailing mult
                                      InpTrailMinPoints,       // min trail points
                                      InpTrailMinProfit);      // min profit activation
   if(g_hTrailing < 0) { Logger_Error(g_hLogger, "TrailingStop_Create falhou"); return INIT_FAILED; }

   //--- 8. OrderManager
   g_hOrder = OrderManager_Create(_Symbol, BP_MAGIC_NUMBER, g_hLogger);
   if(g_hOrder < 0) { Logger_Error(g_hLogger, "OrderManager_Create falhou"); return INIT_FAILED; }

   //--- 9. TriggerMonitor (gerencia ciclo de vida de ordens stop pendentes)
   //    EXPIRATION_BARS=1, expirationMinutes=60 (unused), expirationBars=InpStopOrderExpBars
   //    ADJUSTMENT_NONE=0, trailingStep=0, maxAdjustment=0
   g_hTriggerMonitor = TriggerMonitor_Create(_Symbol, PERIOD_CURRENT, BP_MAGIC_NUMBER,
                                              g_hLogger,
                                              1,                    // EXPIRATION_BARS
                                              60,                   // expirationMinutes (nao usado)
                                              InpStopOrderExpBars,  // expira apos N barras
                                              0,                    // ADJUSTMENT_NONE
                                              0, 0,                 // trailing/maxAdj (nao usado)
                                              false,                // sem OCO
                                              5,                    // checkIntervalSeconds
                                              true);                // log eventos
   if(g_hTriggerMonitor < 0) { Logger_Error(g_hLogger, "TriggerMonitor_Create falhou"); return INIT_FAILED; }
   TriggerMonitor_SetRiskManager(g_hTriggerMonitor, g_hRisk);
   TriggerMonitor_SetStopLossManager(g_hTriggerMonitor, g_hSL);
   TriggerMonitor_SetTakeProfitManager(g_hTriggerMonitor, g_hTP);

   //--- 10. Modulos BP
   //--- Indicadores (sempre criado — usado por outros modulos)
   g_hBPIndicators = BP_Indicators_Create(_Symbol, PERIOD_CURRENT, g_hLogger);
   if(g_hBPIndicators < 0) { Logger_Error(g_hLogger, "BP_Indicators_Create falhou"); return INIT_FAILED; }

   //--- Osciladores
   if(InpUseOscillators)
   {
      g_hBPOscillators = BP_Oscillators_Create(g_hBPIndicators, g_hLogger);
      if(g_hBPOscillators < 0) { Logger_Error(g_hLogger, "BP_Oscillators_Create falhou"); return INIT_FAILED; }
   }

   //--- Padroes de Candle
   if(InpUseCandlePatterns)
   {
      g_hBPCandles = BP_CandlePatterns_Create(_Symbol, PERIOD_CURRENT, g_hLogger);
      if(g_hBPCandles < 0) { Logger_Error(g_hLogger, "BP_CandlePatterns_Create falhou"); return INIT_FAILED; }
   }

   //--- Fibonacci
   if(InpUseFibonacci)
   {
      g_hBPFibonacci = BP_Fibonacci_Create(_Symbol, PERIOD_CURRENT, g_hLogger,
                                            InpFibo_ZZDepth, InpFibo_ZZDeviation, InpFibo_ZZBackstep);
      if(g_hBPFibonacci < 0) { Logger_Error(g_hLogger, "BP_Fibonacci_Create falhou"); return INIT_FAILED; }

      //--- Debug visual: so ativa se LogLevel=DEBUG E usuario marcou InpFibo_Debug
      bool vizEnabled = (InpFibo_Debug && Logger_GetLevel(g_hLogger) >= LOG_LEVEL_DEBUG);
      BP_Viz_SetEnabled(vizEnabled);
      if(vizEnabled)
      {
         BP_Fibonacci_SetDebugViz(g_hBPFibonacci, true,
                                   InpFibo_DebugHighlight,
                                   InpFibo_TriggerLevel,
                                   InpFibo_SLLevel,
                                   InpFibo_TPLevel);
         Logger_Info(g_hLogger, "Fibo debug visual ATIVADO");
      }
   }

   //--- Smart Money
   if(InpUseSmartMoney)
   {
      g_hBPSmartMoney = BP_SmartMoney_Create(_Symbol, PERIOD_CURRENT, g_hLogger);
      if(g_hBPSmartMoney < 0) { Logger_Error(g_hLogger, "BP_SmartMoney_Create falhou"); return INIT_FAILED; }

      // Configura limites do BoS (inputs do usuario)
      BP_SmartMoney_SetBOSLimits(g_hBPSmartMoney,
                                 InpBOS_Leg1Min, InpBOS_Leg1Max,
                                 InpBOS_CorrectionMax, InpBOS_Leg2Max);

      // Configura limites do CHoCH (inputs do usuario)
      BP_SmartMoney_SetCHoCHLimits(g_hBPSmartMoney,
                                   InpCHoCH_TrendMin, InpCHoCH_TrendMax,
                                   InpCHoCH_MinAmplitudeRatio);

      // Configura filtro de mitigacao do OB (aplicado em BoS e CHoCH)
      BP_SmartMoney_SetOBMitigation(g_hBPSmartMoney, InpOB_Mitigation);
   }

   //--- Signal Engine
   g_hBPSignal = BP_SignalEngine_Create(
      g_hBPIndicators, g_hBPOscillators, g_hBPCandles, g_hBPSmartMoney,
      g_hLogger
   );
   if(g_hBPSignal < 0) { Logger_Error(g_hLogger, "BP_SignalEngine_Create falhou"); return INIT_FAILED; }

   Logger_Info(g_hLogger, "EA inicializado com sucesso");
   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| OnDeinit                                                         |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   //--- Limpa objetos de debug visual (se ativos)
   if(BP_Viz_IsEnabled())
   {
      BP_Viz_Clear();
      BP_Viz_SetEnabled(false);
   }

   if(g_hBPSignal     >= 0) BP_SignalEngine_Destroy(g_hBPSignal);
   if(g_hBPFibonacci  >= 0) BP_Fibonacci_Destroy(g_hBPFibonacci);
   if(g_hBPSmartMoney >= 0) BP_SmartMoney_Destroy(g_hBPSmartMoney);
   if(g_hBPCandles    >= 0) BP_CandlePatterns_Destroy(g_hBPCandles);
   if(g_hBPOscillators>= 0) BP_Oscillators_Destroy(g_hBPOscillators);
   if(g_hBPIndicators >= 0) BP_Indicators_Destroy(g_hBPIndicators);

   if(g_hTriggerMonitor >= 0) TriggerMonitor_Destroy(g_hTriggerMonitor);
   if(g_hOrder          >= 0) OrderManager_Destroy(g_hOrder);
   if(g_hTrailing       >= 0) TrailingStop_Destroy(g_hTrailing);
   if(g_hTP       >= 0) TakeProfit_Destroy(g_hTP);
   if(g_hSL       >= 0) StopLoss_Destroy(g_hSL);
   if(g_hRisk     >= 0) RiskManager_Destroy(g_hRisk);
   if(g_hTracker  >= 0) PositionTracker_Destroy(g_hTracker);
   if(g_hLicense  >= 0) License_Destroy(g_hLicense);
   if(g_hLogger   >= 0) Logger_Destroy(g_hLogger);
}

//+------------------------------------------------------------------+
//| Calcula SL grafico usando N candles (iHighest/iLowest)           |
//| Retorna preco do SL ajustado, ou 0.0 se falhar                  |
//+------------------------------------------------------------------+
double CalculateGraphicSL_NCandles(int signalType, double entry, int candlesBack)
{
   if(candlesBack <= 0) candlesBack = 1;
   double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
   double sl = 0.0;

   if(signalType == SIGNAL_BUY)
   {
      // SL abaixo da minima dos ultimos N candles (a partir do candle[1])
      int lowestBar = iLowest(_Symbol, PERIOD_CURRENT, MODE_LOW, candlesBack, 1);
      if(lowestBar >= 0)
         sl = iLow(_Symbol, PERIOD_CURRENT, lowestBar) - InpSL_Buffer * point;
   }
   else
   {
      // SL acima da maxima dos ultimos N candles (a partir do candle[1])
      int highestBar = iHighest(_Symbol, PERIOD_CURRENT, MODE_HIGH, candlesBack, 1);
      if(highestBar >= 0)
         sl = iHigh(_Symbol, PERIOD_CURRENT, highestBar) + InpSL_Buffer * point;
   }

   // Validar limites min/max
   if(sl > 0.0)
   {
      double dist = MathAbs(entry - sl) / point;
      if(InpSL_Min > 0 && dist < InpSL_Min)
         sl = (signalType == SIGNAL_BUY) ? entry - InpSL_Min * point : entry + InpSL_Min * point;
      if(InpSL_Max > 0 && dist > InpSL_Max)
         sl = (signalType == SIGNAL_BUY) ? entry - InpSL_Max * point : entry + InpSL_Max * point;
   }

   return sl;
}

//+------------------------------------------------------------------+
//| Processa saida parcial: fecha % do volume quando lucro >= trigger|
//+------------------------------------------------------------------+
void ProcessPartialClose()
{
   if(!InpUsePartial || g_partialDone) return;
   if(!HasOpenPosition()) return;

   double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);

   // Percorre posicoes abertas com magic number do EA
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong ticket = PositionGetTicket(i);
      if(ticket == 0) continue;
      if(PositionGetString(POSITION_SYMBOL) != _Symbol) continue;
      if(PositionGetInteger(POSITION_MAGIC) != BP_MAGIC_NUMBER) continue;

      double openPrice = PositionGetDouble(POSITION_PRICE_OPEN);
      double curPrice   = PositionGetDouble(POSITION_PRICE_CURRENT);
      double volume     = PositionGetDouble(POSITION_VOLUME);
      long   posType    = PositionGetInteger(POSITION_TYPE);

      // Calcula lucro em pontos
      double profitPts = 0;
      if(posType == POSITION_TYPE_BUY)
         profitPts = (curPrice - openPrice) / point;
      else
         profitPts = (openPrice - curPrice) / point;

      if(profitPts < InpPartialTriggerPts) continue;

      // Calcula volume parcial
      double lotStep = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
      double minLot  = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
      double closeLots = MathFloor((volume * InpPartialPct / 100.0) / lotStep) * lotStep;
      if(closeLots < minLot) closeLots = minLot;
      if(closeLots >= volume) continue;  // Nao fechar 100%

      // Fecha parcial via OrderSend
      MqlTradeRequest req = {};
      MqlTradeResult  res = {};
      req.action    = TRADE_ACTION_DEAL;
      req.symbol    = _Symbol;
      req.position  = ticket;
      req.volume    = closeLots;
      req.type      = (posType == POSITION_TYPE_BUY) ? ORDER_TYPE_SELL : ORDER_TYPE_BUY;
      req.price     = (posType == POSITION_TYPE_BUY) ? SymbolInfoDouble(_Symbol, SYMBOL_BID)
                                                      : SymbolInfoDouble(_Symbol, SYMBOL_ASK);
      req.deviation = 10;
      req.magic     = BP_MAGIC_NUMBER;
      req.comment   = "BP_PARTIAL";

      if(OrderSend(req, res))
      {
         g_partialDone = true;
         Logger_Info(g_hLogger, "Saida parcial: " + DoubleToString(closeLots, 2) +
                     " lotes fechados (" + IntegerToString(InpPartialPct) + "%)");

         // Mover SL para breakeven se configurado
         if(InpPartialMoveSL)
         {
            MqlTradeRequest modReq = {};
            MqlTradeResult  modRes = {};
            modReq.action   = TRADE_ACTION_SLTP;
            modReq.symbol   = _Symbol;
            modReq.position = ticket;
            modReq.sl       = openPrice;
            modReq.tp       = PositionGetDouble(POSITION_TP);

            if(OrderSend(modReq, modRes))
               Logger_Info(g_hLogger, "SL movido para breakeven: " + DoubleToString(openPrice, _Digits));
            else
               Logger_Warning(g_hLogger, "Falha ao mover SL para breakeven: " + IntegerToString(GetLastError()));
         }
      }
      else
         Logger_Warning(g_hLogger, "Falha na saida parcial: " + IntegerToString(GetLastError()));
   }
}

//+------------------------------------------------------------------+
//| Avalia condicao de saida e fecha posicao se satisfeita           |
//+------------------------------------------------------------------+
void ProcessExitCondition()
{
   if(!InpUseExitCond || InpExitInd == BP_IND_NONE) return;
   if(!HasOpenPosition()) return;

   // Avalia indicador no candle[1] e candle[2]
   double v1 = 0, v2 = 0;
   bool hasValue = true;
   double closeRef = iClose(_Symbol, PERIOD_CURRENT, 1);

   switch(InpExitInd)
   {
      case BP_IND_RSI:      v1 = BP_Indicators_RSI(g_hBPIndicators, InpExitPeriod, 1);
                            v2 = BP_Indicators_RSI(g_hBPIndicators, InpExitPeriod, 2); break;
      case BP_IND_STOCH:    v1 = BP_Indicators_StochK(g_hBPIndicators, InpExitPeriod, 1);
                            v2 = BP_Indicators_StochK(g_hBPIndicators, InpExitPeriod, 2); break;
      case BP_IND_CCI:      v1 = BP_Indicators_CCI(g_hBPIndicators, InpExitPeriod, 1);
                            v2 = BP_Indicators_CCI(g_hBPIndicators, InpExitPeriod, 2); break;
      case BP_IND_SMA:      v1 = BP_Indicators_SMA(g_hBPIndicators, InpExitPeriod, 1);
                            v2 = BP_Indicators_SMA(g_hBPIndicators, InpExitPeriod, 2); break;
      case BP_IND_EMA:      v1 = BP_Indicators_EMA(g_hBPIndicators, InpExitPeriod, 1);
                            v2 = BP_Indicators_EMA(g_hBPIndicators, InpExitPeriod, 2); break;
      case BP_IND_MACD:     v1 = BP_Indicators_MACDMain(g_hBPIndicators, InpExitPeriod, 1);
                            v2 = BP_Indicators_MACDMain(g_hBPIndicators, InpExitPeriod, 2); break;
      case BP_IND_ADX:      v1 = BP_Indicators_ADX(g_hBPIndicators, InpExitPeriod, 1);
                            v2 = BP_Indicators_ADX(g_hBPIndicators, InpExitPeriod, 2); break;
      case BP_IND_WILLIAMS: v1 = BP_Indicators_Williams(g_hBPIndicators, InpExitPeriod, 1);
                            v2 = BP_Indicators_Williams(g_hBPIndicators, InpExitPeriod, 2); break;
      default: hasValue = false; break;
   }

   if(!hasValue || v1 == EMPTY_VALUE || v2 == EMPTY_VALUE) return;

   // Avalia condicao
   bool exitSignal = false;
   double val = InpExitValue;

   switch(InpExitCond)
   {
      case BP_COND_CROSS_ABOVE:       exitSignal = (v2 < val && v1 >= val); break;
      case BP_COND_CROSS_BELOW:       exitSignal = (v2 > val && v1 <= val); break;
      case BP_COND_ABOVE:             exitSignal = (val == 0.0) ? (closeRef > v1) : (v1 > val); break;
      case BP_COND_BELOW:             exitSignal = (val == 0.0) ? (closeRef < v1) : (v1 < val); break;
      case BP_COND_IN_ZONE_OB:        exitSignal = (v1 >= val); break;
      case BP_COND_IN_ZONE_OS:        exitSignal = (v1 <= val); break;
      case BP_COND_CROSS_ABOVE_PRICE: exitSignal = (v2 <= iClose(_Symbol,PERIOD_CURRENT,2) && v1 > closeRef); break;
      case BP_COND_CROSS_BELOW_PRICE: exitSignal = (v2 >= iClose(_Symbol,PERIOD_CURRENT,2) && v1 < closeRef); break;
      default: break;
   }

   if(exitSignal)
   {
      Logger_Info(g_hLogger, "Condicao de saida ativada: " +
                  IndicatorName(InpExitInd, InpExitPeriod) + " " + ConditionName(InpExitCond));
      OrderManager_CloseAllPositions(g_hOrder);
   }
}

//+------------------------------------------------------------------+
//| OnTick                                                           |
//+------------------------------------------------------------------+
void OnTick()
{
   //--- Reset diario do contador de operacoes
   ResetDailyCounterIfNeeded();

   //--- Sincroniza posicoes
   PositionTracker_SyncWithMT5Positions(g_hTracker);

   //--- Trailing stop em todas as posicoes abertas
   if(g_hTrailing >= 0)
      TrailingStop_ProcessTrailingStops(g_hTrailing);

   //--- Encerramento forcado no horario definido (a cada tick para precisao)
   CheckForceClose();

   //--- Saida parcial (avalia a cada tick para reagir rapido ao preco)
   ProcessPartialClose();

   //--- TriggerMonitor: monitora ordens pendentes, expira por barras, cancela automaticamente
   if(g_hTriggerMonitor >= 0)
      TriggerMonitor_ProcessPendingOrders(g_hTriggerMonitor);

   //--- Reset partial flag quando nao ha posicao aberta
   if(!HasOpenPosition())
      g_partialDone = false;

   //--- Detecta novo candle (candle[0] abriu = candle[1] acabou de fechar)
   if(!IsNewBar()) return;

   //--- Saida por condicao (avalia no novo candle, candle[1] fechado)
   ProcessExitCondition();

   //--- Notifica TriggerMonitor da nova barra (dispara contagem de expiracao por barras)
   if(g_hTriggerMonitor >= 0)
      TriggerMonitor_OnNewBar(g_hTriggerMonitor);

   //--- Monta condicoes (necessario para diagnostico mesmo fora da janela)
   BPCondition conditions[];
   int count = BuildConditions(conditions);

   //--- Atualiza perna do Fibonacci a cada nova barra (fora da janela tambem,
   //--- para manter o estado pronto para a proxima operacao; funciona tanto
   //--- quando Fibo e gatilho quanto quando e apenas fonte de SL/TP).
   if(g_hBPFibonacci >= 0)
   {
      BP_Fibonacci_Update(g_hBPFibonacci);
      BP_Fibonacci_DrawDebug(g_hBPFibonacci);  // no-op se debug viz desativado
   }

   //--- Log diagnostico a cada candle (so imprime em nivel DEBUG)
   LogDiagnostic(conditions, count);

   //--- Verifica condicoes para avaliar sinal
   if(!IsInTradingWindow()) return;
   if(HasOpenPosition()) return;
   if(HasReachedDailyLimit())
   {
      Logger_Verbose(g_hLogger, "  >> Limite diario atingido (" + IntegerToString(OrderManager_GetExecutedPositionsCount(g_hOrder)) + "/" + IntegerToString(InpMaxTradesPerDay) + ")");
      return;
   }
   if(count == 0) return;

   //--- Avalia sinal (indicadores usam shift=1 = candle[1] = candle trigger fechado)
   //--- InpDirection e passado diretamente: 0=BOTH, 1=BUY_ONLY, -1=SELL_ONLY
   ENUM_BP_SMC_CONCEPT smcConcept = InpUseSmartMoney ? InpSMCEntry : BP_SMC_NONE;
   ENUM_BP_CANDLE_PATTERN candleBull = InpUseCandlePatterns ? InpCandleBull : BP_CANDLE_NONE;
   ENUM_BP_CANDLE_PATTERN candleBear = InpUseCandlePatterns ? InpCandleBear : BP_CANDLE_NONE;

   ENUM_BP_SIGNAL signal = BP_SIGNAL_NONE;

   //--- Fibonacci como gatilho principal (substitui Cond1/2/3 + SMC quando ativo)
   //--- Nota: Update ja foi chamado acima, estado e comum a todas as operacoes.
   if(InpUseFibonacci && g_hBPFibonacci >= 0)
   {
      if(Logger_GetLevel(g_hLogger) >= LOG_LEVEL_DEBUG)
         Logger_Debug(g_hLogger, "  " + BP_Fibonacci_DescribeState(g_hBPFibonacci));

      ENUM_BP_SIGNAL fiboSig = BP_Fibonacci_CheckTrigger(g_hBPFibonacci,
                                                         InpFibo_TriggerLevel,
                                                         InpFibo_TriggerMode);
      // Filtro de direcao
      if(fiboSig != BP_SIGNAL_NONE)
      {
         if(InpDirection == TRADING_BUY_ONLY  && fiboSig != BP_SIGNAL_BUY)  fiboSig = BP_SIGNAL_NONE;
         if(InpDirection == TRADING_SELL_ONLY && fiboSig != BP_SIGNAL_SELL) fiboSig = BP_SIGNAL_NONE;
      }

      // Debug visual: destaca candle trigger quando efetivamente disparou
      if(fiboSig != BP_SIGNAL_NONE)
      {
         datetime triggerBar = iTime(_Symbol, PERIOD_CURRENT, 1);
         BP_Fibonacci_HighlightTriggerCandle(g_hBPFibonacci, fiboSig, triggerBar);
      }
      signal = fiboSig;
   }
   else
   {
      signal = BP_SignalEngine_Evaluate(
         g_hBPSignal,
         conditions, count,
         candleBull, candleBear,
         smcConcept,
         (int)InpDirection
      );
   }

   //--- Log resultado do sinal
   if(Logger_GetLevel(g_hLogger) >= LOG_LEVEL_VERBOSE)
   {
      if(signal == BP_SIGNAL_NONE)
         Logger_Verbose(g_hLogger, "  >> Sem sinal");
      else
         Logger_Verbose(g_hLogger, "  >> SINAL: " + (signal == BP_SIGNAL_BUY ? "BUY" : "SELL"));
   }

   if(signal == BP_SIGNAL_NONE) return;

   //--- FVG modo mitigation: coloca ordem limite na zona do FVG
   if(InpUseSmartMoney && InpFVGEntryMode == FVG_ENTRY_MITIGATION &&
      (smcConcept == BP_SMC_FVG_BULL || smcConcept == BP_SMC_FVG_BEAR))
   {
      double zoneHigh = 0.0, zoneLow = 0.0;
      if(BP_SmartMoney_GetFVGZone(g_hBPSmartMoney, smcConcept, zoneHigh, zoneLow, 1))
      {
         PlaceFVGLimitEntry(signal, zoneHigh, zoneLow);
         return;
      }
      Logger_Warning(g_hLogger, "FVG mitigation: zona nao encontrada, operacao ignorada");
      return;
   }

   //--- Executa conforme modo de entrada (normal ou BOS/outros SMC)
   if(InpEntryType == BP_ENTRY_NEXT_OPEN)
      ExecuteEntry(signal);       // Mercado no preco atual (abertura do candle[0])
   else
      PlaceStopEntry(signal);     // BUY_STOP/SELL_STOP na max/min do candle[1] + buffer
}

//+------------------------------------------------------------------+
//| OnTradeTransaction: processa abertura e fechamento de posicoes   |
//| - Abertura: OrderManager_ProcessDealEntry valida magic/symbol,   |
//|   registra posicao (anti-duplicata) e incrementa contador        |
//| - Fechamento: PositionTracker_ProcessDealExit com anti-duplicata,|
//|   acumulacao de profit (deals parciais) e suporte a INOUT        |
//+------------------------------------------------------------------+
void OnTradeTransaction(const MqlTradeTransaction &trans,
                        const MqlTradeRequest &request,
                        const MqlTradeResult &result)
{
   if(trans.type != TRADE_TRANSACTION_DEAL_ADD) return;
   if(trans.deal_type == DEAL_TYPE_BALANCE) return;

   //--- Abertura: OrderManager verifica magic/symbol/DEAL_ENTRY_IN + anti-duplicata
   if(OrderManager_ProcessDealEntry(g_hOrder, trans.deal, (int)trans.type))
   {
      RiskManager_OnNewOperation(g_hRisk);
      PositionTracker_RegisterPositionOpened(g_hTracker, trans.position, trans.position);
      Logger_Info(g_hLogger, StringFormat("Posicao confirmada #%I64d (total hoje: %d)",
                  trans.position, OrderManager_GetExecutedPositionsCount(g_hOrder)));

      //--- Fibo: registra a perna usada para bloquear reentrada do mesmo lado
      //--- (so quando a posicao e efetivamente aberta, nao em pendentes canceladas)
      if(InpUseFibonacci && g_hBPFibonacci >= 0 && PositionSelectByTicket(trans.position))
      {
         long posType = PositionGetInteger(POSITION_TYPE);
         ENUM_BP_SIGNAL sig = (posType == POSITION_TYPE_BUY) ? BP_SIGNAL_BUY : BP_SIGNAL_SELL;
         BP_Fibonacci_RegisterEntry(g_hBPFibonacci, sig);
      }
   }

   //--- Fechamento: PositionTracker verifica magic/symbol/DEAL_ENTRY_OUT|INOUT
   //--- Anti-duplicata interno, acumula profit de todos os deals parciais
   double closedProfit = 0.0;
   if(PositionTracker_ProcessDealExit(g_hTracker, trans.deal, (int)trans.type, closedProfit))
   {
      bool isWin = (closedProfit > 0.0);
      RiskManager_OnOperationResult(g_hRisk, isWin, closedProfit);
      Logger_Info(g_hLogger, StringFormat("Posicao #%I64d fechada | Profit total: %.2f",
                  trans.position, closedProfit));
   }
}

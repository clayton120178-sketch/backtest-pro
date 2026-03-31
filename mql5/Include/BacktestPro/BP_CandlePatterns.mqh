//+------------------------------------------------------------------+
//|                                          BP_CandlePatterns.mqh   |
//|                                             BacktestPro v1.0     |
//| Deteccao de padroes de candle consolidados dos 3 EAs:           |
//|   - BT_TT.mq5: Bottom Tail, Top Tail, BTTO, TTTO               |
//|   - dB_dT_finder.mq5: Double Bottom, Double Top, Pivots         |
//|   - 12padraoes_exe_v2.mq5: 12 padroes da biblioteca MT5         |
//+------------------------------------------------------------------+
#ifndef __BP_CANDLE_PATTERNS_MQH__
#define __BP_CANDLE_PATTERNS_MQH__
#include <BacktestPro/BP_Constants.mqh>

#define BP_CANDLE_MAX_INSTANCES 4

struct BPCandlePatternsInstance
{
   bool            active;
   string          symbol;
   ENUM_TIMEFRAMES tf;
   int             loggerHandle;
};

BPCandlePatternsInstance g_bp_cp[BP_CANDLE_MAX_INSTANCES];
bool                     g_bp_cp_init = false;

void _BP_CP_Init()
{
   if(g_bp_cp_init) return;
   for(int i = 0; i < BP_CANDLE_MAX_INSTANCES; i++) g_bp_cp[i].active = false;
   g_bp_cp_init = true;
}

int BP_CandlePatterns_Create(const string symbol, ENUM_TIMEFRAMES tf, int loggerHandle)
{
   _BP_CP_Init();
   for(int i = 0; i < BP_CANDLE_MAX_INSTANCES; i++)
   {
      if(!g_bp_cp[i].active)
      {
         g_bp_cp[i].active        = true;
         g_bp_cp[i].symbol        = symbol;
         g_bp_cp[i].tf            = tf;
         g_bp_cp[i].loggerHandle  = loggerHandle;
         return i;
      }
   }
   return -1;
}

bool BP_CandlePatterns_Destroy(int handle)
{
   if(handle < 0 || handle >= BP_CANDLE_MAX_INSTANCES || !g_bp_cp[handle].active)
      return false;
   g_bp_cp[handle].active = false;
   return true;
}

//+------------------------------------------------------------------+
//| Helpers internos                                                  |
//+------------------------------------------------------------------+

// Tamanho do corpo do candle
double _CandleBody(string sym, ENUM_TIMEFRAMES tf, int shift)
{
   return MathAbs(iClose(sym, tf, shift) - iOpen(sym, tf, shift));
}

// Tamanho total do candle (range)
double _CandleRange(string sym, ENUM_TIMEFRAMES tf, int shift)
{
   return iHigh(sym, tf, shift) - iLow(sym, tf, shift);
}

// Sombra inferior
double _LowerShadow(string sym, ENUM_TIMEFRAMES tf, int shift)
{
   double lo = iLow(sym, tf, shift);
   double open = iOpen(sym, tf, shift);
   double close = iClose(sym, tf, shift);
   return MathMin(open, close) - lo;
}

// Sombra superior
double _UpperShadow(string sym, ENUM_TIMEFRAMES tf, int shift)
{
   double hi = iHigh(sym, tf, shift);
   double open = iOpen(sym, tf, shift);
   double close = iClose(sym, tf, shift);
   return hi - MathMax(open, close);
}

// Candle de alta (close > open)
bool _IsBullish(string sym, ENUM_TIMEFRAMES tf, int shift)
{
   return iClose(sym, tf, shift) > iOpen(sym, tf, shift);
}

// Candle de baixa
bool _IsBearish(string sym, ENUM_TIMEFRAMES tf, int shift)
{
   return iClose(sym, tf, shift) < iOpen(sym, tf, shift);
}

//+------------------------------------------------------------------+
//| PADROES: Bottom Tail / Top Tail (de BT_TT.mq5)                  |
//| BT: sombra inferior longa, corpo pequeno no topo do range        |
//| TT: sombra superior longa, corpo pequeno na base do range        |
//+------------------------------------------------------------------+
bool _IsBT(string sym, ENUM_TIMEFRAMES tf, int shift)
{
   double range = _CandleRange(sym, tf, shift);
   if(range <= 0) return false;
   double body  = _CandleBody(sym, tf, shift);
   double lower = _LowerShadow(sym, tf, shift);
   double upper = _UpperShadow(sym, tf, shift);
   // BT: sombra inferior >= 60% do range, corpo <= 30% do range, sombra sup pequena
   return (lower / range >= 0.60 && body / range <= 0.30 && upper / range <= 0.20);
}

bool _IsTT(string sym, ENUM_TIMEFRAMES tf, int shift)
{
   double range = _CandleRange(sym, tf, shift);
   if(range <= 0) return false;
   double body  = _CandleBody(sym, tf, shift);
   double lower = _LowerShadow(sym, tf, shift);
   double upper = _UpperShadow(sym, tf, shift);
   // TT: sombra superior >= 60% do range, corpo <= 30%, sombra inf pequena
   return (upper / range >= 0.60 && body / range <= 0.30 && lower / range <= 0.20);
}

//+------------------------------------------------------------------+
//| PADROES: Double Bottom / Double Top (de dB_dT_finder.mq5)       |
//| Busca em janela de 20 candles (ajustavel)                        |
//+------------------------------------------------------------------+
bool _IsDoubleBottom(string sym, ENUM_TIMEFRAMES tf, int lookback = 20)
{
   // Encontra dois fundos proximos (tolerancia 0.3% do preco)
   double tol = iClose(sym, tf, 1) * 0.003;
   double low1 = iLow(sym, tf, 1);
   for(int i = 3; i <= lookback; i++)
   {
      double lowI = iLow(sym, tf, i);
      if(MathAbs(lowI - low1) <= tol)
      {
         // Verifica que entre os dois fundos ha um pico acima de ambos
         int startJ = 2;
         int endJ   = i - 1;
         double midHigh = -1;
         for(int j = startJ; j <= endJ; j++)
            midHigh = MathMax(midHigh, iHigh(sym, tf, j));
         double refHigh = MathMax(low1, lowI) * 1.005;
         if(midHigh > refHigh) return true;
      }
   }
   return false;
}

bool _IsDoubleTop(string sym, ENUM_TIMEFRAMES tf, int lookback = 20)
{
   double tol = iClose(sym, tf, 1) * 0.003;
   double high1 = iHigh(sym, tf, 1);
   for(int i = 3; i <= lookback; i++)
   {
      double highI = iHigh(sym, tf, i);
      if(MathAbs(highI - high1) <= tol)
      {
         double midLow = DBL_MAX;
         for(int j = 2; j <= i - 1; j++)
            midLow = MathMin(midLow, iLow(sym, tf, j));
         double refLow = MathMin(high1, highI) * 0.995;
         if(midLow < refLow) return true;
      }
   }
   return false;
}

//+------------------------------------------------------------------+
//| PADROES: Classicos da biblioteca MT5 (de 12padraoes_exe_v2.mq5) |
//+------------------------------------------------------------------+

// Martelo (Hammer): corpo no topo, sombra inferior longa
bool _IsHammer(string sym, ENUM_TIMEFRAMES tf, int shift)
{
   return _IsBT(sym, tf, shift);  // BT = Martelo
}

// Estrela cadente (Shooting Star): corpo na base, sombra superior longa
bool _IsShootingStar(string sym, ENUM_TIMEFRAMES tf, int shift)
{
   return _IsTT(sym, tf, shift);  // TT = Shooting Star
}

// Engolfo de alta
bool _IsBullishEngulfing(string sym, ENUM_TIMEFRAMES tf, int shift)
{
   if(!_IsBearish(sym, tf, shift + 1)) return false;
   if(!_IsBullish(sym, tf, shift))     return false;
   double open_now  = iOpen(sym, tf, shift);
   double close_now = iClose(sym, tf, shift);
   double open_prev = iOpen(sym, tf, shift + 1);
   double close_prev= iClose(sym, tf, shift + 1);
   return (open_now <= close_prev && close_now >= open_prev);
}

// Engolfo de baixa
bool _IsBearishEngulfing(string sym, ENUM_TIMEFRAMES tf, int shift)
{
   if(!_IsBullish(sym, tf, shift + 1)) return false;
   if(!_IsBearish(sym, tf, shift))     return false;
   double open_now  = iOpen(sym, tf, shift);
   double close_now = iClose(sym, tf, shift);
   double open_prev = iOpen(sym, tf, shift + 1);
   double close_prev= iClose(sym, tf, shift + 1);
   return (open_now >= close_prev && close_now <= open_prev);
}

// Doji: corpo < 10% do range
bool _IsDoji(string sym, ENUM_TIMEFRAMES tf, int shift)
{
   double range = _CandleRange(sym, tf, shift);
   if(range <= 0) return false;
   return (_CandleBody(sym, tf, shift) / range <= 0.10);
}

// Spinning Top: corpo medio, sombras de tamanho similar
bool _IsSpinningTop(string sym, ENUM_TIMEFRAMES tf, int shift)
{
   double range = _CandleRange(sym, tf, shift);
   if(range <= 0) return false;
   double body  = _CandleBody(sym, tf, shift);
   double lower = _LowerShadow(sym, tf, shift);
   double upper = _UpperShadow(sym, tf, shift);
   return (body / range >= 0.15 && body / range <= 0.40 &&
           lower / range >= 0.20 && upper / range >= 0.20);
}

// Harami de alta: candle bearish grande seguido de candle pequeno dentro
bool _IsBullishHarami(string sym, ENUM_TIMEFRAMES tf, int shift)
{
   if(!_IsBearish(sym, tf, shift + 1)) return false;
   double body_prev = _CandleBody(sym, tf, shift + 1);
   double body_now  = _CandleBody(sym, tf, shift);
   double high_now  = MathMax(iOpen(sym, tf, shift), iClose(sym, tf, shift));
   double low_now   = MathMin(iOpen(sym, tf, shift), iClose(sym, tf, shift));
   double high_prev = MathMax(iOpen(sym, tf, shift+1), iClose(sym, tf, shift+1));
   double low_prev  = MathMin(iOpen(sym, tf, shift+1), iClose(sym, tf, shift+1));
   return (body_now < body_prev * 0.50 &&
           high_now <= high_prev && low_now >= low_prev &&
           _IsBullish(sym, tf, shift));
}

// Harami de baixa
bool _IsBearishHarami(string sym, ENUM_TIMEFRAMES tf, int shift)
{
   if(!_IsBullish(sym, tf, shift + 1)) return false;
   double body_prev = _CandleBody(sym, tf, shift + 1);
   double body_now  = _CandleBody(sym, tf, shift);
   double high_now  = MathMax(iOpen(sym, tf, shift), iClose(sym, tf, shift));
   double low_now   = MathMin(iOpen(sym, tf, shift), iClose(sym, tf, shift));
   double high_prev = MathMax(iOpen(sym, tf, shift+1), iClose(sym, tf, shift+1));
   double low_prev  = MathMin(iOpen(sym, tf, shift+1), iClose(sym, tf, shift+1));
   return (body_now < body_prev * 0.50 &&
           high_now <= high_prev && low_now >= low_prev &&
           _IsBearish(sym, tf, shift));
}

// Pivot de alta (Bullish Pivot): minima local seguida de close acima da maxima anterior
bool _IsBullishPivot(string sym, ENUM_TIMEFRAMES tf, int shift)
{
   // Minima[1] < Minima[2] e Minima[1] < Minima[0] (fundo local)
   // e Close[0] > High[1]
   return (iLow(sym, tf, shift+1) < iLow(sym, tf, shift+2) &&
           iLow(sym, tf, shift+1) < iLow(sym, tf, shift) &&
           iClose(sym, tf, shift) > iHigh(sym, tf, shift+1));
}

// Pivot de baixa
bool _IsBearishPivot(string sym, ENUM_TIMEFRAMES tf, int shift)
{
   return (iHigh(sym, tf, shift+1) > iHigh(sym, tf, shift+2) &&
           iHigh(sym, tf, shift+1) > iHigh(sym, tf, shift) &&
           iClose(sym, tf, shift) < iLow(sym, tf, shift+1));
}

//+------------------------------------------------------------------+
//| API PUBLICA: detecta padrao especifico                          |
//| shift=1 por padrao (candle anterior fechado)                    |
//+------------------------------------------------------------------+
bool BP_CandlePatterns_Detect(int handle, ENUM_BP_CANDLE_PATTERN pattern, int shift = 1)
{
   if(handle < 0 || handle >= BP_CANDLE_MAX_INSTANCES || !g_bp_cp[handle].active)
      return false;

   string sym          = g_bp_cp[handle].symbol;
   ENUM_TIMEFRAMES tf  = g_bp_cp[handle].tf;

   switch(pattern)
   {
      case BP_CANDLE_HAMMER:        return _IsHammer(sym, tf, shift);
      case BP_CANDLE_SHOOTING_STAR: return _IsShootingStar(sym, tf, shift);
      case BP_CANDLE_BULL_ENGULF:   return _IsBullishEngulfing(sym, tf, shift);
      case BP_CANDLE_BEAR_ENGULF:   return _IsBearishEngulfing(sym, tf, shift);
      case BP_CANDLE_DOJI:          return _IsDoji(sym, tf, shift);
      case BP_CANDLE_SPINNING_TOP:  return _IsSpinningTop(sym, tf, shift);
      case BP_CANDLE_BULL_HARAMI:   return _IsBullishHarami(sym, tf, shift);
      case BP_CANDLE_BEAR_HARAMI:   return _IsBearishHarami(sym, tf, shift);
      case BP_CANDLE_BOTTOM_TAIL:   return _IsBT(sym, tf, shift);
      case BP_CANDLE_TOP_TAIL:      return _IsTT(sym, tf, shift);
      case BP_CANDLE_DOUBLE_BOTTOM: return _IsDoubleBottom(sym, tf, 20);
      case BP_CANDLE_DOUBLE_TOP:    return _IsDoubleTop(sym, tf, 20);
      case BP_CANDLE_BULL_PIVOT:    return _IsBullishPivot(sym, tf, shift);
      case BP_CANDLE_BEAR_PIVOT:    return _IsBearishPivot(sym, tf, shift);
      case BP_CANDLE_NONE:          return true;  // sem filtro = sempre passa
      default:                      return false;
   }
}

#endif // __BP_CANDLE_PATTERNS_MQH__

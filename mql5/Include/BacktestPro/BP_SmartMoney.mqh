//+------------------------------------------------------------------+
//|                                             BP_SmartMoney.mqh    |
//|                                             BacktestPro v1.0     |
//| Smart Money Concepts: FVG, BoS, CHoCH, Order Block, Sweep       |
//| IMPORTANTE: SMC nao combina com nenhum outro modulo (R33)       |
//+------------------------------------------------------------------+
#ifndef __BP_SMART_MONEY_MQH__
#define __BP_SMART_MONEY_MQH__
#include <BacktestPro/BP_Constants.mqh>

#define BP_SMC_MAX_INSTANCES 4

struct BPSmartMoneyInstance
{
   bool            active;
   string          symbol;
   ENUM_TIMEFRAMES tf;
   int             loggerHandle;
};

BPSmartMoneyInstance g_bp_smc[BP_SMC_MAX_INSTANCES];
bool                 g_bp_smc_init = false;

void _BP_SMC_Init()
{
   if(g_bp_smc_init) return;
   for(int i = 0; i < BP_SMC_MAX_INSTANCES; i++) g_bp_smc[i].active = false;
   g_bp_smc_init = true;
}

int BP_SmartMoney_Create(const string symbol, ENUM_TIMEFRAMES tf, int loggerHandle)
{
   _BP_SMC_Init();
   for(int i = 0; i < BP_SMC_MAX_INSTANCES; i++)
   {
      if(!g_bp_smc[i].active)
      {
         g_bp_smc[i].active       = true;
         g_bp_smc[i].symbol       = symbol;
         g_bp_smc[i].tf           = tf;
         g_bp_smc[i].loggerHandle = loggerHandle;
         return i;
      }
   }
   return -1;
}

bool BP_SmartMoney_Destroy(int handle)
{
   if(handle < 0 || handle >= BP_SMC_MAX_INSTANCES || !g_bp_smc[handle].active)
      return false;
   g_bp_smc[handle].active = false;
   return true;
}

//+------------------------------------------------------------------+
//| FAIR VALUE GAP (FVG)                                            |
//| Bullish FVG: Low[0] > High[2] — gap de alta entre candles      |
//|   Candle[2]: High  Candle[1]: impulso forte  Candle[0]: Low     |
//| Bearish FVG: High[0] < Low[2]                                   |
//+------------------------------------------------------------------+
bool _FVG_Bull(string sym, ENUM_TIMEFRAMES tf, int shift = 1)
{
   // shift=1: candle atual=1, check em [1],[2],[3]
   double low0  = iLow(sym, tf, shift);
   double high2 = iHigh(sym, tf, shift + 2);
   // Gap: espaco entre high[2] e low[0] nao foi preenchido
   return (low0 > high2);
}

bool _FVG_Bear(string sym, ENUM_TIMEFRAMES tf, int shift = 1)
{
   double high0 = iHigh(sym, tf, shift);
   double low2  = iLow(sym, tf, shift + 2);
   return (high0 < low2);
}

//+------------------------------------------------------------------+
//| BREAK OF STRUCTURE (BoS)                                        |
//| Bullish BoS: Close atual supera a maxima recente mais relevante  |
//| Bearish BoS: Close atual rompe a minima recente                  |
//+------------------------------------------------------------------+
bool _BoS_Bull(string sym, ENUM_TIMEFRAMES tf, int lookback = 20, int shift = 1)
{
   double closeNow = iClose(sym, tf, shift);
   // Encontra swing high recente (excluindo o candle atual)
   double swingHigh = -DBL_MAX;
   for(int i = shift + 1; i <= shift + lookback; i++)
      swingHigh = MathMax(swingHigh, iHigh(sym, tf, i));
   return (closeNow > swingHigh);
}

bool _BoS_Bear(string sym, ENUM_TIMEFRAMES tf, int lookback = 20, int shift = 1)
{
   double closeNow = iClose(sym, tf, shift);
   double swingLow = DBL_MAX;
   for(int i = shift + 1; i <= shift + lookback; i++)
      swingLow = MathMin(swingLow, iLow(sym, tf, i));
   return (closeNow < swingLow);
}

//+------------------------------------------------------------------+
//| CHANGE OF CHARACTER (CHoCH)                                     |
//| CHoCH de alta: mercado em downtrend (HH/HL decrescentes)        |
//|   quebra pela primeira vez uma maxima relevante                  |
//| CHoCH de baixa: mercado em uptrend que quebra uma minima        |
//+------------------------------------------------------------------+
bool _CHoCH_Bull(string sym, ENUM_TIMEFRAMES tf, int lookback = 30, int shift = 1)
{
   // Verifica tendencia de baixa previa (ultimas 2 maximas decrescentes)
   double high1 = -DBL_MAX, high2 = -DBL_MAX;
   int   idx1 = -1, idx2 = -1;
   for(int i = shift + 2; i <= shift + lookback; i++)
   {
      double h = iHigh(sym, tf, i);
      if(h > high1) { high2 = high1; idx2 = idx1; high1 = h; idx1 = i; }
      else if(h > high2 && i != idx1) { high2 = h; idx2 = i; }
   }
   if(idx1 < 0 || idx2 < 0 || idx1 <= idx2) return false;
   // high1 e o pico mais recente, high2 e o anterior
   bool downtrend = (high1 < high2);  // maximas decrescentes = downtrend
   // CHoCH: close atual supera o ultimo swing high (high1) no downtrend
   return (downtrend && iClose(sym, tf, shift) > high1);
}

bool _CHoCH_Bear(string sym, ENUM_TIMEFRAMES tf, int lookback = 30, int shift = 1)
{
   double low1 = DBL_MAX, low2 = DBL_MAX;
   int    idx1 = -1, idx2 = -1;
   for(int i = shift + 2; i <= shift + lookback; i++)
   {
      double l = iLow(sym, tf, i);
      if(l < low1) { low2 = low1; idx2 = idx1; low1 = l; idx1 = i; }
      else if(l < low2 && i != idx1) { low2 = l; idx2 = i; }
   }
   if(idx1 < 0 || idx2 < 0 || idx1 <= idx2) return false;
   bool uptrend = (low1 > low2);  // minimas crescentes = uptrend
   return (uptrend && iClose(sym, tf, shift) < low1);
}

//+------------------------------------------------------------------+
//| ORDER BLOCK (OB)                                                |
//| Bullish OB: ultimo candle bearish antes de forte movimento      |
//|   de alta. Preco retorna a essa zona para entrar comprado.      |
//| Bearish OB: ultimo candle bullish antes de forte queda         |
//+------------------------------------------------------------------+
bool _OB_Bull(string sym, ENUM_TIMEFRAMES tf, int lookback = 10, int shift = 1)
{
   // Procura: candle bearish[i+1], candle de impulso bullish[i], preco atual toca zona
   double closeNow = iClose(sym, tf, shift);
   double lowNow   = iLow(sym, tf, shift);
   for(int i = shift + 1; i <= shift + lookback; i++)
   {
      bool prevBearish  = iClose(sym, tf, i) < iOpen(sym, tf, i);
      bool impulso      = (iClose(sym, tf, i-1) - iOpen(sym, tf, i-1)) >
                          2.0 * MathAbs(iClose(sym, tf, i) - iOpen(sym, tf, i));
      if(prevBearish && impulso)
      {
         double obHigh = iHigh(sym, tf, i);
         double obLow  = iLow(sym, tf, i);
         // Preco atual toca o OB (reteste da zona)
         if(lowNow <= obHigh && closeNow >= obLow)
            return true;
      }
   }
   return false;
}

bool _OB_Bear(string sym, ENUM_TIMEFRAMES tf, int lookback = 10, int shift = 1)
{
   double closeNow = iClose(sym, tf, shift);
   double highNow  = iHigh(sym, tf, shift);
   for(int i = shift + 1; i <= shift + lookback; i++)
   {
      bool prevBullish  = iClose(sym, tf, i) > iOpen(sym, tf, i);
      bool impulso      = (iOpen(sym, tf, i-1) - iClose(sym, tf, i-1)) >
                          2.0 * MathAbs(iClose(sym, tf, i) - iOpen(sym, tf, i));
      if(prevBullish && impulso)
      {
         double obHigh = iHigh(sym, tf, i);
         double obLow  = iLow(sym, tf, i);
         if(highNow >= obLow && closeNow <= obHigh)
            return true;
      }
   }
   return false;
}

//+------------------------------------------------------------------+
//| LIQUIDITY SWEEP                                                  |
//| Sweep de maximas: preco rompe a maxima recente mas fecha abaixo  |
//|   (liquidez de stops de comprados varrida -> preco cai)         |
//| Sweep de minimas: rompe minima mas fecha acima                   |
//+------------------------------------------------------------------+
bool _Sweep_High(string sym, ENUM_TIMEFRAMES tf, int lookback = 20, int shift = 1)
{
   double highNow  = iHigh(sym, tf, shift);
   double closeNow = iClose(sym, tf, shift);
   double prevHigh = -DBL_MAX;
   for(int i = shift + 1; i <= shift + lookback; i++)
      prevHigh = MathMax(prevHigh, iHigh(sym, tf, i));
   // Rompeu a maxima mas fechou abaixo dela (sweep + rejeicao)
   return (highNow > prevHigh && closeNow < prevHigh);
}

bool _Sweep_Low(string sym, ENUM_TIMEFRAMES tf, int lookback = 20, int shift = 1)
{
   double lowNow   = iLow(sym, tf, shift);
   double closeNow = iClose(sym, tf, shift);
   double prevLow  = DBL_MAX;
   for(int i = shift + 1; i <= shift + lookback; i++)
      prevLow = MathMin(prevLow, iLow(sym, tf, i));
   return (lowNow < prevLow && closeNow > prevLow);
}

//+------------------------------------------------------------------+
//| API PUBLICA: detecta conceito SMC                               |
//+------------------------------------------------------------------+
bool BP_SmartMoney_Detect(int handle, ENUM_BP_SMC_CONCEPT concept, int shift = 1)
{
   if(handle < 0 || handle >= BP_SMC_MAX_INSTANCES || !g_bp_smc[handle].active)
      return false;

   string          sym = g_bp_smc[handle].symbol;
   ENUM_TIMEFRAMES tf  = g_bp_smc[handle].tf;

   switch(concept)
   {
      case BP_SMC_FVG_BULL:   return _FVG_Bull(sym, tf, shift);
      case BP_SMC_FVG_BEAR:   return _FVG_Bear(sym, tf, shift);
      case BP_SMC_BOS_BULL:   return _BoS_Bull(sym, tf, 20, shift);
      case BP_SMC_BOS_BEAR:   return _BoS_Bear(sym, tf, 20, shift);
      case BP_SMC_CHOCH_BULL: return _CHoCH_Bull(sym, tf, 30, shift);
      case BP_SMC_CHOCH_BEAR: return _CHoCH_Bear(sym, tf, 30, shift);
      case BP_SMC_OB_BULL:    return _OB_Bull(sym, tf, 10, shift);
      case BP_SMC_OB_BEAR:    return _OB_Bear(sym, tf, 10, shift);
      case BP_SMC_SWEEP_HIGH: return _Sweep_High(sym, tf, 20, shift);
      case BP_SMC_SWEEP_LOW:  return _Sweep_Low(sym, tf, 20, shift);
      case BP_SMC_NONE:       return true;
      default:                return false;
   }
}

//+------------------------------------------------------------------+
//| Retorna se conceito e de alta (buy) ou baixa (sell)             |
//+------------------------------------------------------------------+
ENUM_BP_SIGNAL BP_SmartMoney_GetDirection(ENUM_BP_SMC_CONCEPT concept)
{
   switch(concept)
   {
      case BP_SMC_FVG_BULL:
      case BP_SMC_BOS_BULL:
      case BP_SMC_CHOCH_BULL:
      case BP_SMC_OB_BULL:
      case BP_SMC_SWEEP_LOW:   // sweep de minimas -> price revertes para cima
         return BP_SIGNAL_BUY;
      case BP_SMC_FVG_BEAR:
      case BP_SMC_BOS_BEAR:
      case BP_SMC_CHOCH_BEAR:
      case BP_SMC_OB_BEAR:
      case BP_SMC_SWEEP_HIGH:  // sweep de maximas -> price reverte para baixo
         return BP_SIGNAL_SELL;
      default:
         return BP_SIGNAL_NONE;
   }
}

#endif // __BP_SMART_MONEY_MQH__

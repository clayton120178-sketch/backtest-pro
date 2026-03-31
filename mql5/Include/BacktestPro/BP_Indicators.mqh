//+------------------------------------------------------------------+
//|                                              BP_Indicators.mqh   |
//|                                             BacktestPro v1.0     |
//| Gerencia handles de indicadores nativos do MT5 e expoe           |
//| funcoes de calculo de valor para outros modulos BP               |
//+------------------------------------------------------------------+
#ifndef __BP_INDICATORS_MQH__
#define __BP_INDICATORS_MQH__
#include <BacktestPro/BP_Constants.mqh>

//+------------------------------------------------------------------+
//| Pool de instancias                                               |
//+------------------------------------------------------------------+
#define BP_IND_MAX_INSTANCES 4

struct BPIndicatorsInstance
{
   bool            active;
   string          symbol;
   ENUM_TIMEFRAMES tf;
   int             loggerHandle;
};

BPIndicatorsInstance g_bp_ind[BP_IND_MAX_INSTANCES];
bool                 g_bp_ind_init = false;

//+------------------------------------------------------------------+
//| Inicializa pool                                                  |
//+------------------------------------------------------------------+
void _BP_Ind_Init()
{
   if(g_bp_ind_init) return;
   for(int i = 0; i < BP_IND_MAX_INSTANCES; i++)
      g_bp_ind[i].active = false;
   g_bp_ind_init = true;
}

//+------------------------------------------------------------------+
//| Cria instancia                                                   |
//+------------------------------------------------------------------+
int BP_Indicators_Create(const string symbol, ENUM_TIMEFRAMES tf, int loggerHandle)
{
   _BP_Ind_Init();
   for(int i = 0; i < BP_IND_MAX_INSTANCES; i++)
   {
      if(!g_bp_ind[i].active)
      {
         g_bp_ind[i].active        = true;
         g_bp_ind[i].symbol        = symbol;
         g_bp_ind[i].tf            = tf;
         g_bp_ind[i].loggerHandle  = loggerHandle;
         return i;
      }
   }
   return -1;
}

//+------------------------------------------------------------------+
//| Destroi instancia                                                |
//+------------------------------------------------------------------+
bool BP_Indicators_Destroy(int handle)
{
   if(handle < 0 || handle >= BP_IND_MAX_INSTANCES || !g_bp_ind[handle].active)
      return false;
   g_bp_ind[handle].active = false;
   return true;
}

//+------------------------------------------------------------------+
//| Helper: le buffer de indicador MT5                              |
//+------------------------------------------------------------------+
double _BP_Ind_BufVal(int mt5handle, int bufIdx, int shift)
{
   if(mt5handle == INVALID_HANDLE) return EMPTY_VALUE;
   double buf[];
   ArraySetAsSeries(buf, true);
   if(CopyBuffer(mt5handle, bufIdx, shift, 1, buf) <= 0) return EMPTY_VALUE;
   return buf[0];
}

//+------------------------------------------------------------------+
//| API PUBLICA: Obtem valor de indicador (cria handle temporario)  |
//+------------------------------------------------------------------+
double BP_Indicators_GetValue(int handle, ENUM_BP_INDICATOR indicator,
                               int period, int shift = 1, int bufferIdx = 0)
{
   if(handle < 0 || handle >= BP_IND_MAX_INSTANCES || !g_bp_ind[handle].active)
      return EMPTY_VALUE;

   string sym          = g_bp_ind[handle].symbol;
   ENUM_TIMEFRAMES tf  = g_bp_ind[handle].tf;
   int mt5h            = INVALID_HANDLE;

   switch(indicator)
   {
      case BP_IND_RSI:       mt5h = iRSI(sym, tf, period, PRICE_CLOSE);                           break;
      case BP_IND_STOCH:     mt5h = iStochastic(sym, tf, period, 3, 3, MODE_SMA, STO_LOWHIGH);   break;
      case BP_IND_CCI:       mt5h = iCCI(sym, tf, period, PRICE_TYPICAL);                         break;
      case BP_IND_WILLIAMS:  mt5h = iWPR(sym, tf, period);                                        break;
      case BP_IND_MACD:      mt5h = iMACD(sym, tf, 12, 26, period, PRICE_CLOSE);                  break;
      case BP_IND_SMA:       mt5h = iMA(sym, tf, period, 0, MODE_SMA, PRICE_CLOSE);               break;
      case BP_IND_EMA:       mt5h = iMA(sym, tf, period, 0, MODE_EMA, PRICE_CLOSE);               break;
      case BP_IND_ADX:       mt5h = iADX(sym, tf, period);                                        break;
      case BP_IND_SAR:       mt5h = iSAR(sym, tf, 0.02, 0.2);                                     break;
      case BP_IND_BOLLINGER: mt5h = iBands(sym, tf, period, 0, 2.0, PRICE_CLOSE);                 break;
      case BP_IND_ATR:       mt5h = iATR(sym, tf, period);                                        break;
      case BP_IND_VOLUME:    mt5h = iVolumes(sym, tf, VOLUME_TICK);                               break;
      case BP_IND_OBV:       mt5h = iOBV(sym, tf, VOLUME_TICK);                                   break;
      default: return EMPTY_VALUE;
   }

   if(mt5h == INVALID_HANDLE) return EMPTY_VALUE;
   double val = _BP_Ind_BufVal(mt5h, bufferIdx, shift);
   IndicatorRelease(mt5h);
   return val;
}

//+------------------------------------------------------------------+
//| Funcoes de atalho                                                |
//+------------------------------------------------------------------+
double BP_Indicators_RSI(int h, int period, int shift=1)           { return BP_Indicators_GetValue(h, BP_IND_RSI,       period, shift, 0); }
double BP_Indicators_StochK(int h, int period, int shift=1)        { return BP_Indicators_GetValue(h, BP_IND_STOCH,     period, shift, 0); }
double BP_Indicators_StochD(int h, int period, int shift=1)        { return BP_Indicators_GetValue(h, BP_IND_STOCH,     period, shift, 1); }
double BP_Indicators_CCI(int h, int period, int shift=1)           { return BP_Indicators_GetValue(h, BP_IND_CCI,       period, shift, 0); }
double BP_Indicators_Williams(int h, int period, int shift=1)      { return BP_Indicators_GetValue(h, BP_IND_WILLIAMS,  period, shift, 0); }
double BP_Indicators_MACDMain(int h, int sigPeriod, int shift=1)   { return BP_Indicators_GetValue(h, BP_IND_MACD,      sigPeriod, shift, 0); }
double BP_Indicators_MACDSignal(int h, int sigPeriod, int shift=1) { return BP_Indicators_GetValue(h, BP_IND_MACD,      sigPeriod, shift, 1); }
double BP_Indicators_SMA(int h, int period, int shift=1)           { return BP_Indicators_GetValue(h, BP_IND_SMA,       period, shift, 0); }
double BP_Indicators_EMA(int h, int period, int shift=1)           { return BP_Indicators_GetValue(h, BP_IND_EMA,       period, shift, 0); }
double BP_Indicators_ADX(int h, int period, int shift=1)           { return BP_Indicators_GetValue(h, BP_IND_ADX,       period, shift, 0); }
double BP_Indicators_BollUpper(int h, int period, int shift=1)     { return BP_Indicators_GetValue(h, BP_IND_BOLLINGER, period, shift, 1); }
double BP_Indicators_BollLower(int h, int period, int shift=1)     { return BP_Indicators_GetValue(h, BP_IND_BOLLINGER, period, shift, 2); }
double BP_Indicators_BollMiddle(int h, int period, int shift=1)    { return BP_Indicators_GetValue(h, BP_IND_BOLLINGER, period, shift, 0); }
double BP_Indicators_ATR(int h, int period, int shift=1)           { return BP_Indicators_GetValue(h, BP_IND_ATR,       period, shift, 0); }
double BP_Indicators_SAR(int h, int shift=1)                       { return BP_Indicators_GetValue(h, BP_IND_SAR,       0, shift, 0); }
double BP_Indicators_Volume(int h, int shift=1)                    { return BP_Indicators_GetValue(h, BP_IND_VOLUME,    0, shift, 0); }
double BP_Indicators_OBV(int h, int shift=1)                       { return BP_Indicators_GetValue(h, BP_IND_OBV,       0, shift, 0); }

double BP_Indicators_VolumeMA(int handle, int period, int shift=1)
{
   if(handle < 0 || handle >= BP_IND_MAX_INSTANCES || !g_bp_ind[handle].active || period <= 0)
      return EMPTY_VALUE;
   double sum = 0;
   for(int i = shift; i < shift + period; i++)
      sum += (double)iVolume(g_bp_ind[handle].symbol, g_bp_ind[handle].tf, i);
   return sum / period;
}

double BP_Indicators_HighN(int handle, int period, int shift=1)
{
   if(handle < 0 || handle >= BP_IND_MAX_INSTANCES || !g_bp_ind[handle].active) return EMPTY_VALUE;
   int idx = iHighest(g_bp_ind[handle].symbol, g_bp_ind[handle].tf, MODE_HIGH, period, shift);
   return (idx >= 0) ? iHigh(g_bp_ind[handle].symbol, g_bp_ind[handle].tf, idx) : EMPTY_VALUE;
}

double BP_Indicators_LowN(int handle, int period, int shift=1)
{
   if(handle < 0 || handle >= BP_IND_MAX_INSTANCES || !g_bp_ind[handle].active) return EMPTY_VALUE;
   int idx = iLowest(g_bp_ind[handle].symbol, g_bp_ind[handle].tf, MODE_LOW, period, shift);
   return (idx >= 0) ? iLow(g_bp_ind[handle].symbol, g_bp_ind[handle].tf, idx) : EMPTY_VALUE;
}

double BP_Indicators_Close(int handle, int shift=1)
{
   if(handle < 0 || handle >= BP_IND_MAX_INSTANCES || !g_bp_ind[handle].active) return EMPTY_VALUE;
   return iClose(g_bp_ind[handle].symbol, g_bp_ind[handle].tf, shift);
}

double BP_Indicators_Open(int handle, int shift=1)
{
   if(handle < 0 || handle >= BP_IND_MAX_INSTANCES || !g_bp_ind[handle].active) return EMPTY_VALUE;
   return iOpen(g_bp_ind[handle].symbol, g_bp_ind[handle].tf, shift);
}

double BP_Indicators_High(int handle, int shift=1)
{
   if(handle < 0 || handle >= BP_IND_MAX_INSTANCES || !g_bp_ind[handle].active) return EMPTY_VALUE;
   return iHigh(g_bp_ind[handle].symbol, g_bp_ind[handle].tf, shift);
}

double BP_Indicators_Low(int handle, int shift=1)
{
   if(handle < 0 || handle >= BP_IND_MAX_INSTANCES || !g_bp_ind[handle].active) return EMPTY_VALUE;
   return iLow(g_bp_ind[handle].symbol, g_bp_ind[handle].tf, shift);
}

string          BP_Indicators_GetSymbol(int h) { return (h>=0&&h<BP_IND_MAX_INSTANCES&&g_bp_ind[h].active)?g_bp_ind[h].symbol:""; }
ENUM_TIMEFRAMES BP_Indicators_GetTF(int h)     { return (h>=0&&h<BP_IND_MAX_INSTANCES&&g_bp_ind[h].active)?g_bp_ind[h].tf:PERIOD_CURRENT; }

//+------------------------------------------------------------------+
//| HiLo Activator                                                    |
//| Retorna +1 (compra), -1 (venda), 0 (indefinido)                  |
//| HiLo = SMA das maximas ou minimas dos ultimos N periodos          |
//| Se close > SMA(low,N) -> compra; se close < SMA(high,N) -> venda |
//+------------------------------------------------------------------+
int BP_Indicators_HiLo(int handle, int period, int shift=1)
{
   if(handle < 0 || handle >= BP_IND_MAX_INSTANCES || !g_bp_ind[handle].active) return 0;
   if(period <= 0) period = 4;

   string sym = g_bp_ind[handle].symbol;
   ENUM_TIMEFRAMES tf = g_bp_ind[handle].tf;

   // Calcula SMA das maximas e minimas
   double sumHigh = 0, sumLow = 0;
   for(int i = 0; i < period; i++)
   {
      sumHigh += iHigh(sym, tf, shift + i);
      sumLow  += iLow(sym, tf, shift + i);
   }
   double avgHigh = sumHigh / period;
   double avgLow  = sumLow  / period;

   double close = iClose(sym, tf, shift);

   if(close > avgLow)  return +1;  // Compra
   if(close < avgHigh) return -1;  // Venda
   return 0;
}

//+------------------------------------------------------------------+
//| HiLo Activator: retorna valor da linha ativa (avgLow ou avgHigh) |
//+------------------------------------------------------------------+
double BP_Indicators_HiLoValue(int handle, int period, int shift=1)
{
   if(handle < 0 || handle >= BP_IND_MAX_INSTANCES || !g_bp_ind[handle].active) return EMPTY_VALUE;
   if(period <= 0) period = 4;

   string sym = g_bp_ind[handle].symbol;
   ENUM_TIMEFRAMES tf = g_bp_ind[handle].tf;

   double sumHigh = 0, sumLow = 0;
   for(int i = 0; i < period; i++)
   {
      sumHigh += iHigh(sym, tf, shift + i);
      sumLow  += iLow(sym, tf, shift + i);
   }
   double avgHigh = sumHigh / period;
   double avgLow  = sumLow  / period;

   double close = iClose(sym, tf, shift);

   // Retorna a linha ativa (a que esta sendo usada como referencia)
   if(close > avgLow) return avgLow;   // Modo compra: linha de referencia = avgLow
   return avgHigh;                       // Modo venda: linha de referencia = avgHigh
}

#endif // __BP_INDICATORS_MQH__

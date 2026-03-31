//+------------------------------------------------------------------+
//|                                             BP_Oscillators.mqh   |
//|                                             BacktestPro v1.0     |
//| Logica de condicoes para osciladores: cruzamentos, zonas,       |
//| tendencia, volume. Avalia BPCondition e retorna true/false.     |
//+------------------------------------------------------------------+
#ifndef __BP_OSCILLATORS_MQH__
#define __BP_OSCILLATORS_MQH__
#include <BacktestPro/BP_Constants.mqh>
#include <BacktestPro/BP_Indicators.mqh>

#define BP_OSC_MAX_INSTANCES 4

struct BPOscillatorsInstance
{
   bool active;
   int  indHandle;
   int  loggerHandle;
};

BPOscillatorsInstance g_bp_osc[BP_OSC_MAX_INSTANCES];
bool                  g_bp_osc_init = false;

void _BP_Osc_Init()
{
   if(g_bp_osc_init) return;
   for(int i = 0; i < BP_OSC_MAX_INSTANCES; i++) g_bp_osc[i].active = false;
   g_bp_osc_init = true;
}

int BP_Oscillators_Create(int indicatorsHandle, int loggerHandle)
{
   _BP_Osc_Init();
   for(int i = 0; i < BP_OSC_MAX_INSTANCES; i++)
   {
      if(!g_bp_osc[i].active)
      {
         g_bp_osc[i].active        = true;
         g_bp_osc[i].indHandle     = indicatorsHandle;
         g_bp_osc[i].loggerHandle  = loggerHandle;
         return i;
      }
   }
   return -1;
}

bool BP_Oscillators_Destroy(int handle)
{
   if(handle < 0 || handle >= BP_OSC_MAX_INSTANCES || !g_bp_osc[handle].active)
      return false;
   g_bp_osc[handle].active = false;
   return true;
}

//+------------------------------------------------------------------+
//| Verifica cruzamento: val_now cruzou acima de val_prev           |
//+------------------------------------------------------------------+
bool _CrossedAbove(double val_now, double val_prev, double ref)
{
   return (val_prev < ref && val_now >= ref);
}

bool _CrossedBelow(double val_now, double val_prev, double ref)
{
   return (val_prev > ref && val_now <= ref);
}

//+------------------------------------------------------------------+
//| Avalia uma BPCondition e retorna true se satisfeita             |
//| shift=1: candle anterior (fechado), shift=2: dois atras          |
//+------------------------------------------------------------------+
bool BP_Oscillators_EvaluateCondition(int handle, const BPCondition &cond)
{
   if(handle < 0 || handle >= BP_OSC_MAX_INSTANCES || !g_bp_osc[handle].active)
      return false;

   int ih = g_bp_osc[handle].indHandle;
   double v1 = 0, v2 = 0;  // valor atual (candle 1) e anterior (candle 2)
   double preco1 = BP_Indicators_Close(ih, 1);
   double preco2 = BP_Indicators_Close(ih, 2);

   //--- Obtem valores do indicador (candle 1 e 2 para detectar cruzamento)
   switch(cond.indicator)
   {
      case BP_IND_RSI:
         v1 = BP_Indicators_RSI(ih, cond.period, 1);
         v2 = BP_Indicators_RSI(ih, cond.period, 2);
         break;
      case BP_IND_STOCH:
         v1 = BP_Indicators_StochK(ih, cond.period, 1);
         v2 = BP_Indicators_StochK(ih, cond.period, 2);
         break;
      case BP_IND_CCI:
         v1 = BP_Indicators_CCI(ih, cond.period, 1);
         v2 = BP_Indicators_CCI(ih, cond.period, 2);
         break;
      case BP_IND_WILLIAMS:
         v1 = BP_Indicators_Williams(ih, cond.period, 1);
         v2 = BP_Indicators_Williams(ih, cond.period, 2);
         break;
      case BP_IND_MACD:
         v1 = BP_Indicators_MACDMain(ih, cond.period, 1);
         v2 = BP_Indicators_MACDMain(ih, cond.period, 2);
         break;
      case BP_IND_SMA:
         v1 = BP_Indicators_SMA(ih, cond.period, 1);
         v2 = BP_Indicators_SMA(ih, cond.period, 2);
         break;
      case BP_IND_EMA:
         v1 = BP_Indicators_EMA(ih, cond.period, 1);
         v2 = BP_Indicators_EMA(ih, cond.period, 2);
         break;
      case BP_IND_ADX:
         v1 = BP_Indicators_ADX(ih, cond.period, 1);
         v2 = BP_Indicators_ADX(ih, cond.period, 2);
         break;
      case BP_IND_VOLUME:
         v1 = BP_Indicators_Volume(ih, 1);
         v2 = BP_Indicators_Volume(ih, 2);
         break;
      case BP_IND_OBV:
         v1 = BP_Indicators_OBV(ih, 1);
         v2 = BP_Indicators_OBV(ih, 2);
         break;

      //--- Bollinger Bands: v1/v2 = banda escolhida, comparacao feita com preco
      //    cond.value seleciona a banda: 0=inferior (default), 1=media, 2=superior
      case BP_IND_BOLLINGER:
      {
         int banda = (int)cond.value;  // 0=lower, 1=middle, 2=upper
         if(banda == 2)
         {
            v1 = BP_Indicators_BollUpper(ih, cond.period, 1);
            v2 = BP_Indicators_BollUpper(ih, cond.period, 2);
         }
         else if(banda == 1)
         {
            v1 = BP_Indicators_BollMiddle(ih, cond.period, 1);
            v2 = BP_Indicators_BollMiddle(ih, cond.period, 2);
         }
         else  // 0 = inferior (default)
         {
            v1 = BP_Indicators_BollLower(ih, cond.period, 1);
            v2 = BP_Indicators_BollLower(ih, cond.period, 2);
         }
         //--- Para Bollinger as condicoes ABOVE/BELOW/CROSS comparam preco vs banda
         //    substituimos ref por 0 para forcar a logica de comparacao com preco
         //    (tratado abaixo na avaliacao de condicao)
         if(v1 == EMPTY_VALUE || v2 == EMPTY_VALUE) return false;
         switch(cond.condition)
         {
            case BP_COND_CROSS_ABOVE: return _CrossedAbove(preco1, preco2, v1);   // preco cruza acima da banda
            case BP_COND_CROSS_BELOW: return _CrossedBelow(preco1, preco2, v1);   // preco cruza abaixo da banda
            case BP_COND_ABOVE:       return (preco1 > v1);                        // preco acima da banda
            case BP_COND_BELOW:       return (preco1 < v1);                        // preco abaixo da banda
            default:                  return false;
         }
      }

      default:
         return false;
   }

   if(v1 == EMPTY_VALUE || v2 == EMPTY_VALUE) return false;

   double ref = cond.value;

   //--- Avalia condicao
   switch(cond.condition)
   {
      case BP_COND_CROSS_ABOVE:
         return _CrossedAbove(v1, v2, ref);

      case BP_COND_CROSS_BELOW:
         return _CrossedBelow(v1, v2, ref);

      case BP_COND_ABOVE:
         // value=0 significa "compare com preco" (ex: SMA acima do preco = preco abaixo da SMA)
         // Para MA/indicadores de tendencia: preco > indicador
         // Para osciladores com value>0: indicador > value
         if(ref == 0.0) return (preco1 > v1);  // preco acima do indicador
         return (v1 > ref);                     // indicador acima do valor fixo

      case BP_COND_BELOW:
         // value=0 significa "compare com preco"
         if(ref == 0.0) return (preco1 < v1);  // preco abaixo do indicador
         return (v1 < ref);                     // indicador abaixo do valor fixo

      case BP_COND_IN_ZONE_OB:
         // Zona sobrecompra: RSI/Stoch > 70, CCI > 100, Williams > -20
         if(cond.indicator == BP_IND_RSI  || cond.indicator == BP_IND_STOCH) return (v1 >= 70.0);
         if(cond.indicator == BP_IND_CCI)     return (v1 >= 100.0);
         if(cond.indicator == BP_IND_WILLIAMS)return (v1 >= -20.0);
         return (v1 >= ref);

      case BP_COND_IN_ZONE_OS:
         // Zona sobrevenda: RSI/Stoch < 30, CCI < -100, Williams < -80
         if(cond.indicator == BP_IND_RSI  || cond.indicator == BP_IND_STOCH) return (v1 <= 30.0);
         if(cond.indicator == BP_IND_CCI)     return (v1 <= -100.0);
         if(cond.indicator == BP_IND_WILLIAMS)return (v1 <= -80.0);
         return (v1 <= ref);

      case BP_COND_CROSS_ABOVE_PRICE:
         // Indicador (ex: SMA) cruza acima do preco
         return (v2 <= preco2 && v1 > preco1);

      case BP_COND_CROSS_BELOW_PRICE:
         return (v2 >= preco2 && v1 < preco1);

      case BP_COND_MACD_CROSS_UP:
      {
         double sig1 = BP_Indicators_MACDSignal(ih, cond.period, 1);
         double sig2 = BP_Indicators_MACDSignal(ih, cond.period, 2);
         if(sig1 == EMPTY_VALUE || sig2 == EMPTY_VALUE) return false;
         return _CrossedAbove(v1 - sig1, v2 - sig2, 0.0);
      }
      case BP_COND_MACD_CROSS_DOWN:
      {
         double sig1 = BP_Indicators_MACDSignal(ih, cond.period, 1);
         double sig2 = BP_Indicators_MACDSignal(ih, cond.period, 2);
         if(sig1 == EMPTY_VALUE || sig2 == EMPTY_VALUE) return false;
         return _CrossedBelow(v1 - sig1, v2 - sig2, 0.0);
      }
      case BP_COND_MACD_ABOVE_ZERO:
         return (v1 > 0.0);

      case BP_COND_MACD_BELOW_ZERO:
         return (v1 < 0.0);

      // Cruzamento MA rapida (period) vs MA lenta (period2)
      // Funciona com BP_IND_SMA ou BP_IND_EMA
      case BP_COND_MA_CROSS_ABOVE:
      case BP_COND_MA_CROSS_BELOW:
      {
         double fast1, fast2, slow1, slow2;
         if(cond.indicator == BP_IND_EMA)
         {
            fast1 = BP_Indicators_EMA(ih, cond.period,  1);
            fast2 = BP_Indicators_EMA(ih, cond.period,  2);
            slow1 = BP_Indicators_EMA(ih, cond.period2, 1);
            slow2 = BP_Indicators_EMA(ih, cond.period2, 2);
         }
         else  // SMA por padrao
         {
            fast1 = BP_Indicators_SMA(ih, cond.period,  1);
            fast2 = BP_Indicators_SMA(ih, cond.period,  2);
            slow1 = BP_Indicators_SMA(ih, cond.period2, 1);
            slow2 = BP_Indicators_SMA(ih, cond.period2, 2);
         }
         if(fast1 == EMPTY_VALUE || fast2 == EMPTY_VALUE ||
            slow1 == EMPTY_VALUE || slow2 == EMPTY_VALUE) return false;
         if(cond.condition == BP_COND_MA_CROSS_ABOVE)
            return (fast2 <= slow2 && fast1 > slow1);  // rapida cruzou acima da lenta
         else
            return (fast2 >= slow2 && fast1 < slow1);  // rapida cruzou abaixo da lenta
      }

      default:
         return false;
   }
}

//+------------------------------------------------------------------+
//| Avalia multiplas condicoes (AND logico)                         |
//| Retorna SIGNAL_BUY, SIGNAL_SELL ou SIGNAL_NONE                  |
//| Para cada condicao: se satisfeita para compra -> buy++          |
//|                     se satisfeita para venda  -> sell++         |
//| Obs: a direcao e determinada pelo SignalEngine                  |
//+------------------------------------------------------------------+
bool BP_Oscillators_EvaluateAll(int handle, const BPCondition &conditions[], int count)
{
   if(count == 0) return true;  // sem condicoes = nao filtra
   for(int i = 0; i < count; i++)
   {
      if(!BP_Oscillators_EvaluateCondition(handle, conditions[i]))
         return false;
   }
   return true;
}

#endif // __BP_OSCILLATORS_MQH__

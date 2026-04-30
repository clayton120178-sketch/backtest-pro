//+------------------------------------------------------------------+
//|                                           BP_SignalEngine.mqh    |
//|                                             BacktestPro v1.0     |
//| Orquestracao de sinais: recebe condicoes dos modulos e retorna  |
//| SIGNAL_BUY, SIGNAL_SELL ou SIGNAL_NONE                         |
//|                                                                  |
//| Logica:                                                          |
//|   Modo SMC: usa BP_SmartMoney para determinar sinal (isolado)   |
//|   Modo Normal: avalia BPConditions via BP_Oscillators           |
//|               + filtra por BP_CandlePatterns (se ativo)         |
//|   Direcao: determinada pela condicao 1 (pode ser overriden)     |
//+------------------------------------------------------------------+
#ifndef __BP_SIGNAL_ENGINE_MQH__
#define __BP_SIGNAL_ENGINE_MQH__
#include <BacktestPro/BP_Constants.mqh>
#include <BacktestPro/BP_Oscillators.mqh>
#include <BacktestPro/BP_CandlePatterns.mqh>
#include <BacktestPro/BP_SmartMoney.mqh>

#define BP_SE_MAX_INSTANCES 4

struct BPSignalEngineInstance
{
   bool active;
   int  hIndicators;
   int  hOscillators;
   int  hCandles;
   int  hSmartMoney;
   int  loggerHandle;
};

BPSignalEngineInstance g_bp_se[BP_SE_MAX_INSTANCES];
bool                   g_bp_se_init = false;

void _BP_SE_Init()
{
   if(g_bp_se_init) return;
   for(int i = 0; i < BP_SE_MAX_INSTANCES; i++) g_bp_se[i].active = false;
   g_bp_se_init = true;
}

int BP_SignalEngine_Create(int hIndicators, int hOscillators,
                            int hCandles, int hSmartMoney, int loggerHandle)
{
   _BP_SE_Init();
   for(int i = 0; i < BP_SE_MAX_INSTANCES; i++)
   {
      if(!g_bp_se[i].active)
      {
         g_bp_se[i].active        = true;
         g_bp_se[i].hIndicators   = hIndicators;
         g_bp_se[i].hOscillators  = hOscillators;
         g_bp_se[i].hCandles      = hCandles;
         g_bp_se[i].hSmartMoney   = hSmartMoney;
         g_bp_se[i].loggerHandle  = loggerHandle;
         return i;
      }
   }
   return -1;
}

bool BP_SignalEngine_Destroy(int handle)
{
   if(handle < 0 || handle >= BP_SE_MAX_INSTANCES || !g_bp_se[handle].active)
      return false;
   g_bp_se[handle].active = false;
   return true;
}

//+------------------------------------------------------------------+
//| _IsOscillator: alias para _BP_IsOscillator (definida em         |
//| BP_Oscillators.mqh, incluida via BP_Oscillators.mqh acima)      |
//+------------------------------------------------------------------+
bool _IsOscillator(ENUM_BP_INDICATOR ind) { return _BP_IsOscillator(ind); }

//+------------------------------------------------------------------+
//| Determina a direcao do sinal a partir da condicao principal     |
//|                                                                  |
//| Regras:                                                          |
//|   CROSS_ABOVE, IN_ZONE_OS, MACD_CROSS_UP  -> sempre BUY        |
//|   CROSS_BELOW, IN_ZONE_OB, MACD_CROSS_DOWN -> sempre SELL      |
//|                                                                  |
//|   ABOVE / BELOW: depende do tipo de indicador                   |
//|     Oscilador (RSI/Stoch/CCI/Williams):                         |
//|       ABOVE de valor alto (>=50) -> BUY (oscilador em forca)    |
//|       ABOVE de valor baixo (<50) -> BUY (oscilador acima ref)   |
//|       BELOW de valor baixo (<50) -> BUY (sobrevenda -> compra)  |
//|       BELOW de valor alto (>=50) -> SELL (sobrecompra -> venda) |
//|     MA/Tendencia (SMA/EMA/ADX/...):                             |
//|       ABOVE (preco acima da MA) -> BUY                          |
//|       BELOW (preco abaixo da MA) -> SELL                        |
//+------------------------------------------------------------------+
ENUM_BP_SIGNAL _InferDirection(const BPCondition &cond)
{
   switch(cond.condition)
   {
      // Cruzamentos e zonas: direcao e inequivoca
      case BP_COND_CROSS_ABOVE:
      case BP_COND_IN_ZONE_OS:
      case BP_COND_MACD_CROSS_UP:
      case BP_COND_MACD_ABOVE_ZERO:
      case BP_COND_CROSS_ABOVE_PRICE:
         return BP_SIGNAL_BUY;

      case BP_COND_CROSS_BELOW:
      case BP_COND_IN_ZONE_OB:
      case BP_COND_MACD_CROSS_DOWN:
      case BP_COND_MACD_BELOW_ZERO:
      case BP_COND_CROSS_BELOW_PRICE:
      case BP_COND_MA_CROSS_BELOW:
         return BP_SIGNAL_SELL;

      case BP_COND_MA_CROSS_ABOVE:
      case BP_COND_HILO_BUY:
         return BP_SIGNAL_BUY;

      case BP_COND_HILO_SELL:
         return BP_SIGNAL_SELL;

      case BP_COND_HILO_CHANGED:
         return BP_SIGNAL_NONE;  // direcao indefinida, requer tradingDir fixo

      // ABOVE: para osciladores o valor de referencia define o sentido
      //   Ex: RSI ABOVE 50 -> mercado forte -> BUY (valor >= 50)
      //   Ex: Stoch ABOVE 80 -> sobrecompra -> SELL (valor >= 50)
      //   Ex: Williams ABOVE -20 (ou 20) -> sobrecompra -> SELL
      //   Ex: SMA ABOVE (preco > MA) -> sempre BUY
      case BP_COND_ABOVE:
         if(_IsOscillator(cond.indicator))
         {
            // Williams: escala 0 a -100; normaliza para comparacao
            // ABOVE perto de 0 (ex: -20 ou 20) = sobrecompra = SELL
            // ABOVE perto de -100 (ex: -80 ou 80) = nao faz sentido mas trata como BUY
            if(cond.indicator == BP_IND_WILLIAMS)
            {
               double wRef = (cond.value > 0.0) ? -cond.value : cond.value;
               return (wRef >= -50.0) ? BP_SIGNAL_SELL : BP_SIGNAL_BUY;
            }
            return (cond.value >= 50.0) ? BP_SIGNAL_SELL : BP_SIGNAL_BUY;
         }
         return BP_SIGNAL_BUY;  // MA/tendencia: preco acima = alta

      // BELOW: para osciladores o valor de referencia define o sentido
      //   Ex: Stoch BELOW 20 -> sobrevenda -> BUY (valor < 50)
      //   Ex: RSI BELOW 70   -> ainda forte mas caindo -> SELL (valor >= 50)
      //   Ex: Williams BELOW -80 (ou 80) -> sobrevenda -> BUY
      //   Ex: SMA BELOW (preco < MA) -> sempre SELL
      case BP_COND_BELOW:
         if(_IsOscillator(cond.indicator))
         {
            // Williams: escala 0 a -100; normaliza para comparacao
            // BELOW perto de -100 (ex: -80 ou 80) = sobrevenda = BUY
            // BELOW perto de 0 (ex: -20 ou 20) = sobrecompra saindo = SELL
            if(cond.indicator == BP_IND_WILLIAMS)
            {
               double wRef = (cond.value > 0.0) ? -cond.value : cond.value;
               return (wRef < -50.0) ? BP_SIGNAL_BUY : BP_SIGNAL_SELL;
            }
            return (cond.value < 50.0) ? BP_SIGNAL_BUY : BP_SIGNAL_SELL;
         }
         return BP_SIGNAL_SELL;  // MA/tendencia: preco abaixo = queda

      default:
         return BP_SIGNAL_NONE;
   }
}

//+------------------------------------------------------------------+
//| Verifica se padrao de candle confirma a direcao do sinal        |
//+------------------------------------------------------------------+
bool _CandleConfirms(int hCandles, ENUM_BP_CANDLE_PATTERN bull, ENUM_BP_CANDLE_PATTERN bear,
                     ENUM_BP_SIGNAL signal)
{
   if(hCandles < 0) return true;  // modulo nao ativo = sem filtro

   if(signal == BP_SIGNAL_BUY)
   {
      if(bull == BP_CANDLE_NONE) return true;  // sem padrao definido = sem filtro
      return BP_CandlePatterns_Detect(hCandles, bull, 1);
   }
   else if(signal == BP_SIGNAL_SELL)
   {
      if(bear == BP_CANDLE_NONE) return true;
      return BP_CandlePatterns_Detect(hCandles, bear, 1);
   }
   return true;
}

//+------------------------------------------------------------------+
//| API PRINCIPAL: avalia todos os modulos e retorna sinal final    |
//|                                                                  |
//| Parametros:                                                      |
//|   handle       - handle do SignalEngine                         |
//|   conditions[] - array de BPCondition                           |
//|   count        - numero de condicoes validas                    |
//|   candleBull   - padrao de candle para confirmar BUY           |
//|   candleBear   - padrao de candle para confirmar SELL          |
//|   smcConcept   - conceito SMC (se SMC_NONE, usa modo normal)   |
//|   tradingDir   - direcao definida pelo usuario                  |
//|                  TRADING_BUY_ONLY  -> retorna so BUY            |
//|                  TRADING_SELL_ONLY -> retorna so SELL           |
//|                  TRADING_BOTH      -> usa _InferDirection       |
//+------------------------------------------------------------------+
ENUM_BP_SIGNAL BP_SignalEngine_Evaluate(
   int handle,
   const BPCondition &conditions[],
   int count,
   ENUM_BP_CANDLE_PATTERN candleBull,
   ENUM_BP_CANDLE_PATTERN candleBear,
   ENUM_BP_SMC_CONCEPT smcConcept,
   int tradingDir = 0    // 0=BOTH, 1=BUY_ONLY, -1=SELL_ONLY
)
{
   if(handle < 0 || handle >= BP_SE_MAX_INSTANCES || !g_bp_se[handle].active)
      return BP_SIGNAL_NONE;

   //=== MODO SMC (isolado, ignora conditions e candles) ===
   if(smcConcept != BP_SMC_NONE && g_bp_se[handle].hSmartMoney >= 0)
   {
      ENUM_BP_SIGNAL smcDir = BP_SmartMoney_GetDirection(smcConcept);
      if(tradingDir == 1  && smcDir != BP_SIGNAL_BUY)  return BP_SIGNAL_NONE;
      if(tradingDir == -1 && smcDir != BP_SIGNAL_SELL) return BP_SIGNAL_NONE;
      if(BP_SmartMoney_Detect(g_bp_se[handle].hSmartMoney, smcConcept, 1))
         return smcDir;
      return BP_SIGNAL_NONE;
   }

   //=== MODO NORMAL ===
   if(count == 0) return BP_SIGNAL_NONE;

   // 1. Determina direcao
   ENUM_BP_SIGNAL direction;
   if(tradingDir == 1)
      direction = BP_SIGNAL_BUY;
   else if(tradingDir == -1)
      direction = BP_SIGNAL_SELL;
   else
   {
      // TRADING_BOTH: infere pela condicao principal
      direction = _InferDirection(conditions[0]);
      if(direction == BP_SIGNAL_NONE) return BP_SIGNAL_NONE;
   }

   // 2. Avalia todas as condicoes (AND logico)
   if(g_bp_se[handle].hOscillators >= 0)
   {
      if(!BP_Oscillators_EvaluateAll(g_bp_se[handle].hOscillators, conditions, count))
         return BP_SIGNAL_NONE;
   }

   // 3. Confirma com padrao de candle (se modulo ativo)
   if(!_CandleConfirms(g_bp_se[handle].hCandles, candleBull, candleBear, direction))
      return BP_SIGNAL_NONE;

   return direction;
}

#endif // __BP_SIGNAL_ENGINE_MQH__

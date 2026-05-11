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
//| Avalia sempre candles fechados: [shift], [shift+1], [shift+2]   |
//| shift=1 (default) -> candles [1],[2],[3]                        |
//| Bullish FVG: Low[1] > High[3] — gap entre candle 1 e 3         |
//|   Candle[3]: referencia  Candle[2]: impulso  Candle[1]: confirmacao|
//| Bearish FVG: High[1] < Low[3]                                   |
//+------------------------------------------------------------------+
bool _FVG_Bull(string sym, ENUM_TIMEFRAMES tf, int shift = 1)
{
   double low1  = iLow(sym, tf, shift);       // candle mais recente (confirmacao)
   double high3 = iHigh(sym, tf, shift + 2);  // candle mais antigo (referencia)
   return (low1 > high3);
}

bool _FVG_Bear(string sym, ENUM_TIMEFRAMES tf, int shift = 1)
{
   double high1 = iHigh(sym, tf, shift);      // candle mais recente (confirmacao)
   double low3  = iLow(sym, tf, shift + 2);   // candle mais antigo (referencia)
   return (high1 < low3);
}

//+------------------------------------------------------------------+
//| Retorna a zona do FVG (limites do gap)                           |
//| Bullish: zoneHigh = Low[1], zoneLow = High[3]                   |
//|   -> Entrada limite no zoneHigh, stop no zoneLow                |
//| Bearish: zoneHigh = Low[3], zoneLow = High[1]                   |
//|   -> Entrada limite no zoneLow, stop no zoneHigh                |
//| Retorna false se nao houver FVG valido                           |
//+------------------------------------------------------------------+
bool _FVG_GetZone(string sym, ENUM_TIMEFRAMES tf, bool isBull,
                  double &zoneHigh, double &zoneLow, int shift = 1)
{
   if(isBull)
   {
      double low1  = iLow(sym, tf, shift);
      double high3 = iHigh(sym, tf, shift + 2);
      if(low1 <= high3) return false;  // sem gap
      zoneHigh = low1;   // topo da zona (preco entra aqui no reteste)
      zoneLow  = high3;  // fundo da zona (stop aqui)
      return true;
   }
   else
   {
      double high1 = iHigh(sym, tf, shift);
      double low3  = iLow(sym, tf, shift + 2);
      if(high1 >= low3) return false;  // sem gap
      zoneHigh = low3;   // topo da zona (stop aqui)
      zoneLow  = high1;  // fundo da zona (preco entra aqui no reteste)
      return true;
   }
}

//+------------------------------------------------------------------+
//| BREAK OF STRUCTURE (BoS) - Logica de 3 fases com limites        |
//|                                                                  |
//| Bullish BoS:                                                     |
//|   Fase 1: Primeira perna de alta (candles bullish consecutivos)   |
//|           Minimo: g_bos_leg1_min (default 2)                     |
//|           Maximo: g_bos_leg1_max (default 5)                     |
//|           Low1 = low do candle mais antigo da perna (inicio)     |
//|           High1 = high mais alto da perna (topo)                 |
//|   Fase 2: Correcao - candles bearish consecutivos                |
//|           Minimo: 1 candle bearish                               |
//|           Maximo: g_bos_correction_max (default 3)               |
//|           Nao pode ter mais candles que a Fase 1                  |
//|           pullbackLow deve ser > Low1 (senao invalido)           |
//|           Termina no primeiro candle bullish (inicia Fase 3)     |
//|   Fase 3: Segunda perna de alta (candles bullish consecutivos)    |
//|           Maximo: g_bos_leg2_max (default 3)                     |
//|           Se close rompe High1 -> BoS confirmado                  |
//|           Se candle bearish sem romper -> invalido (topo menor)   |
//|           Se excede maximo sem romper -> invalido (sem forca)     |
//|                                                                  |
//| Bearish BoS: logica espelhada                                    |
//+------------------------------------------------------------------+

// Configuracao dos limites do BoS (ajustaveis via BP_SmartMoney_SetBOSLimits)
int g_bos_leg1_min       = 2;  // Min candles da 1a perna
int g_bos_leg1_max       = 5;  // Max candles da 1a perna
int g_bos_correction_max = 3;  // Max candles da correcao
int g_bos_leg2_max       = 3;  // Max candles da 2a perna

// Variaveis internas para armazenar niveis do ultimo BOS detectado
double g_bos_legStart = 0.0;  // Low1 (bull) ou High1 (bear) - ponto de invalidacao/stop
double g_bos_legHigh  = 0.0;  // High1 (bull) ou Low1 (bear) - nivel rompido

// Configuracao dos limites do CHoCH (ajustaveis via BP_SmartMoney_SetCHoCHLimits)
int    g_choch_trend_min          = 5;   // Min candles na tendencia previa
int    g_choch_trend_max          = 15;  // Max candles na tendencia previa
int    g_choch_min_amplitude_ratio = 40; // Min % da amplitude previa que a 1a perna deve cobrir

//+------------------------------------------------------------------+
//| Configura limites do BoS (chamar antes de Detect)                |
//+------------------------------------------------------------------+
void BP_SmartMoney_SetBOSLimits(int handle,
                                int leg1Min, int leg1Max,
                                int correctionMax, int leg2Max)
{
   if(handle < 0 || handle >= BP_SMC_MAX_INSTANCES || !g_bp_smc[handle].active)
      return;
   if(leg1Min >= 2)       g_bos_leg1_min       = leg1Min;
   if(leg1Max >= leg1Min) g_bos_leg1_max       = leg1Max;
   if(correctionMax >= 1) g_bos_correction_max = correctionMax;
   if(leg2Max >= 1)       g_bos_leg2_max       = leg2Max;
}

//+------------------------------------------------------------------+
//| Configura limites do CHoCH (chamar antes de Detect)              |
//+------------------------------------------------------------------+
void BP_SmartMoney_SetCHoCHLimits(int handle,
                                  int trendMin, int trendMax,
                                  int minAmplitudeRatio)
{
   if(handle < 0 || handle >= BP_SMC_MAX_INSTANCES || !g_bp_smc[handle].active)
      return;
   if(trendMin >= 2)          g_choch_trend_min          = trendMin;
   if(trendMax >= trendMin)   g_choch_trend_max          = trendMax;
   if(minAmplitudeRatio >= 1) g_choch_min_amplitude_ratio = minAmplitudeRatio;
}

bool _BoS_Bull(string sym, ENUM_TIMEFRAMES tf, int lookback = 20, int shift = 1)
{
   g_bos_legStart = 0.0;
   g_bos_legHigh  = 0.0;

   // ================================================================
   // FASE 1: Primeira perna de alta (candles bullish consecutivos)
   // Varre de shift para tras procurando a sequencia
   // ================================================================
   int legStart = -1;   // indice do candle mais antigo da perna
   int legEnd   = -1;   // indice do candle mais recente da perna
   int bullCount = 0;

   for(int i = shift + 1; i <= shift + lookback; i++)
   {
      bool isBull = (iClose(sym, tf, i) > iOpen(sym, tf, i));
      if(isBull)
      {
         if(bullCount == 0) legEnd = i;
         bullCount++;
         legStart = i;

         // Excedeu maximo da perna 1: invalido (movimento esticado)
         if(bullCount > g_bos_leg1_max)
            return false;
      }
      else
      {
         if(bullCount >= g_bos_leg1_min) break;  // perna valida encontrada
         // Reset: menos que o minimo, reinicia busca
         bullCount = 0;
         legStart = -1;
         legEnd   = -1;
      }
   }

   if(bullCount < g_bos_leg1_min || legStart < 0 || legEnd < 0) return false;

   // Low1: low do candle mais antigo da perna (ponto de invalidacao)
   double low1 = iLow(sym, tf, legStart);
   // High1: high mais alto de toda a primeira perna
   double high1 = -DBL_MAX;
   for(int i = legEnd; i <= legStart; i++)
      high1 = MathMax(high1, iHigh(sym, tf, i));

   if(high1 <= low1) return false;

   // ================================================================
   // FASE 2: Correcao (candles bearish consecutivos apos a perna 1)
   // Inicia no candle seguinte ao fim da perna (legEnd - 1)
   // Termina no primeiro candle bullish (inicio da fase 3)
   // ================================================================
   int corrCount = 0;
   double pullbackLow = DBL_MAX;
   int corrEnd = -1;    // indice do ultimo candle da correcao (mais recente)
   int corrStart = -1;  // indice do 1o candle da correcao (mais antigo)

   for(int i = legEnd - 1; i >= shift; i--)
   {
      bool isBull = (iClose(sym, tf, i) > iOpen(sym, tf, i));
      if(!isBull)
      {
         corrCount++;
         pullbackLow = MathMin(pullbackLow, iLow(sym, tf, i));
         corrEnd = i;
         if(corrStart < 0) corrStart = i;  // 1o candle (maior indice)

         // Excedeu maximo de candles na correcao: invalido (consolidacao)
         if(corrCount > g_bos_correction_max)
            return false;
      }
      else
      {
         break;  // Candle bullish: fim da correcao, inicio da fase 3
      }
   }

   // Precisa de pelo menos 1 candle de correcao
   if(corrCount < 1) return false;

   // Regra adicional: correcao nao pode ter mais candles que a perna 1
   if(corrCount > bullCount) return false;

   // Correcao nao pode romper o inicio da primeira perna
   if(pullbackLow <= low1) return false;

   // Filtro OB: zona = [low, close] do 1o candle bullish da 1a perna (legStart)
   double obTop_BoS = iClose(sym, tf, legStart);
   double obLow_BoS = iLow(sym, tf, legStart);
   if(!_OB_ValidateBull(sym, tf, obTop_BoS, obLow_BoS,
                        corrStart, corrEnd, pullbackLow))
      return false;

   // ================================================================
   // FASE 3: Segunda perna de alta (candles bullish consecutivos)
   // Inicia no primeiro candle bullish apos a correcao
   // Termina com rompimento de High1 ou invalidacao
   // ================================================================
   int leg2Count = 0;

   for(int i = corrEnd - 1; i >= shift; i--)
   {
      bool isBull = (iClose(sym, tf, i) > iOpen(sym, tf, i));
      if(!isBull)
      {
         // Candle bearish na 2a perna sem romper High1: topo mais baixo -> invalido
         return false;
      }

      leg2Count++;

      // Verifica rompimento: close acima de High1
      double closeCandle = iClose(sym, tf, i);
      if(closeCandle > high1)
      {
         // BoS confirmado
         g_bos_legStart = low1;    // stop sugerido
         g_bos_legHigh  = high1;   // nivel rompido
         return true;
      }

      // Excedeu maximo da 2a perna sem romper: sem forca -> invalido
      if(leg2Count >= g_bos_leg2_max)
         return false;
   }

   // Chegou ao candle mais recente sem rompimento
   return false;
}

bool _BoS_Bear(string sym, ENUM_TIMEFRAMES tf, int lookback = 20, int shift = 1)
{
   g_bos_legStart = 0.0;
   g_bos_legHigh  = 0.0;

   // ================================================================
   // FASE 1: Primeira perna de baixa (candles bearish consecutivos)
   // ================================================================
   int legStart = -1;
   int legEnd   = -1;
   int bearCount = 0;

   for(int i = shift + 1; i <= shift + lookback; i++)
   {
      bool isBear = (iClose(sym, tf, i) < iOpen(sym, tf, i));
      if(isBear)
      {
         if(bearCount == 0) legEnd = i;
         bearCount++;
         legStart = i;

         if(bearCount > g_bos_leg1_max)
            return false;
      }
      else
      {
         if(bearCount >= g_bos_leg1_min) break;
         bearCount = 0;
         legStart = -1;
         legEnd   = -1;
      }
   }

   if(bearCount < g_bos_leg1_min || legStart < 0 || legEnd < 0) return false;

   // High1: high do candle mais antigo da perna (ponto de invalidacao)
   double high1 = iHigh(sym, tf, legStart);
   // Low1: low mais baixo de toda a primeira perna
   double low1 = DBL_MAX;
   for(int i = legEnd; i <= legStart; i++)
      low1 = MathMin(low1, iLow(sym, tf, i));

   if(low1 >= high1) return false;

   // ================================================================
   // FASE 2: Correcao (candles bullish consecutivos)
   // ================================================================
   int corrCount = 0;
   double pullbackHigh = -DBL_MAX;
   int corrEnd = -1;
   int corrStart = -1;

   for(int i = legEnd - 1; i >= shift; i--)
   {
      bool isBear = (iClose(sym, tf, i) < iOpen(sym, tf, i));
      if(!isBear)
      {
         corrCount++;
         pullbackHigh = MathMax(pullbackHigh, iHigh(sym, tf, i));
         corrEnd = i;
         if(corrStart < 0) corrStart = i;

         if(corrCount > g_bos_correction_max)
            return false;
      }
      else
      {
         break;
      }
   }

   if(corrCount < 1) return false;
   if(corrCount > bearCount) return false;
   if(pullbackHigh >= high1) return false;

   // Filtro OB: zona = [close, high] do 1o candle bearish da 1a perna (legStart)
   double obHigh_BoS   = iHigh(sym, tf, legStart);
   double obBottom_BoS = iClose(sym, tf, legStart);
   if(!_OB_ValidateBear(sym, tf, obBottom_BoS, obHigh_BoS,
                        corrStart, corrEnd, pullbackHigh))
      return false;

   // ================================================================
   // FASE 3: Segunda perna de baixa (candles bearish consecutivos)
   // ================================================================
   int leg2Count = 0;

   for(int i = corrEnd - 1; i >= shift; i--)
   {
      bool isBear = (iClose(sym, tf, i) < iOpen(sym, tf, i));
      if(!isBear)
      {
         // Candle bullish na 2a perna sem romper Low1: fundo mais alto -> invalido
         return false;
      }

      leg2Count++;

      double closeCandle = iClose(sym, tf, i);
      if(closeCandle < low1)
      {
         // BoS confirmado
         g_bos_legStart = high1;   // stop sugerido
         g_bos_legHigh  = low1;    // nivel rompido
         return true;
      }

      if(leg2Count >= g_bos_leg2_max)
         return false;
   }

   return false;
}

//+------------------------------------------------------------------+
//| CHANGE OF CHARACTER (CHoCH)                                     |
//| CHoCH de alta: mercado em downtrend (HH/HL decrescentes)        |
//|   quebra pela primeira vez uma maxima relevante                  |
//| CHoCH de baixa: mercado em uptrend que quebra uma minima        |
//+------------------------------------------------------------------+
//+------------------------------------------------------------------+
//| CHANGE OF CHARACTER (CHoCH) - Tendencia previa + BoS             |
//|                                                                  |
//| CHoCH Bullish:                                                    |
//|   ETAPA 1: Tendencia previa de BAIXA (candles bearish consec.)    |
//|     - Minimo: g_choch_trend_min (default 5)                       |
//|     - Maximo: g_choch_trend_max (default 15)                      |
//|     - Amplitude: high do inicio - low do fim (em pontos)          |
//|                                                                  |
//|   ETAPA 2: Primeira perna de ALTA (impulso de reversao)           |
//|     - Usa limites do BoS: g_bos_leg1_min / g_bos_leg1_max        |
//|     - Regra de forca (candles): leg1 candles <= trend candles     |
//|     - Regra de forca (amplitude): leg1 amplitude >=               |
//|       g_choch_min_amplitude_ratio % da amplitude da tendencia     |
//|                                                                  |
//|   ETAPA 3: Correcao + 2a perna de alta (mecanica BoS)             |
//|     - Reutiliza Fases 2 e 3 do BoS (correcao + rompimento)       |
//|     - Close > high da 1a perna = CHoCH confirmado                 |
//|                                                                  |
//| CHoCH Bearish: logica espelhada                                   |
//+------------------------------------------------------------------+
bool _CHoCH_Bull(string sym, ENUM_TIMEFRAMES tf, int lookback = 30, int shift = 1)
{
   g_bos_legStart = 0.0;
   g_bos_legHigh  = 0.0;

   // ================================================================
   // ETAPA 1: Tendencia previa de BAIXA (candles bearish consecutivos)
   // Varre a partir do candle mais antigo encontrado pela perna de alta
   // Primeiro, precisamos encontrar onde a perna de alta comeca para
   // buscar a tendencia previa antes dela
   // ================================================================

   // Passo 1a: Encontra a 1a perna de alta (igual Fase 1 do BoS)
   int legStart = -1;   // candle mais antigo da perna de alta
   int legEnd   = -1;   // candle mais recente da perna de alta
   int bullCount = 0;

   for(int i = shift + 1; i <= shift + lookback; i++)
   {
      bool isBull = (iClose(sym, tf, i) > iOpen(sym, tf, i));
      if(isBull)
      {
         if(bullCount == 0) legEnd = i;
         bullCount++;
         legStart = i;
         if(bullCount > g_bos_leg1_max) return false;
      }
      else
      {
         if(bullCount >= g_bos_leg1_min) break;
         bullCount = 0;
         legStart = -1;
         legEnd   = -1;
      }
   }

   if(bullCount < g_bos_leg1_min || legStart < 0 || legEnd < 0) return false;

   // Low1 e High1 da 1a perna de alta
   double low1 = iLow(sym, tf, legStart);
   double high1 = -DBL_MAX;
   for(int i = legEnd; i <= legStart; i++)
      high1 = MathMax(high1, iHigh(sym, tf, i));
   if(high1 <= low1) return false;

   double leg1Amplitude = high1 - low1;  // amplitude da 1a perna em pontos

   // ================================================================
   // Passo 1b: Tendencia previa de BAIXA (imediatamente antes da perna)
   // Candles bearish consecutivos a partir de legStart + 1
   // ================================================================
   int trendCount = 0;
   int trendStart = -1;  // candle mais antigo da tendencia (inicio)
   int trendEnd   = -1;  // candle mais recente da tendencia (fim, proximo a legStart)

   for(int i = legStart + 1; i <= shift + lookback; i++)
   {
      bool isBear = (iClose(sym, tf, i) < iOpen(sym, tf, i));
      if(isBear)
      {
         if(trendCount == 0) trendEnd = i;
         trendCount++;
         trendStart = i;
         if(trendCount > g_choch_trend_max) break;  // suficiente, para busca
      }
      else
      {
         break;  // primeiro candle nao-bearish termina a tendencia
      }
   }

   if(trendCount < g_choch_trend_min) return false;
   // Limita ao maximo configurado
   if(trendCount > g_choch_trend_max) return false;

   // Amplitude da tendencia previa: high do inicio - low do fim
   double trendHigh = iHigh(sym, tf, trendStart);  // topo no inicio da queda
   double trendLow  = iLow(sym, tf, trendEnd);     // fundo no fim da queda
   double trendAmplitude = trendHigh - trendLow;
   if(trendAmplitude <= 0) return false;

   // ================================================================
   // ETAPA 2: Regras de forca do impulso
   // - Candles da 1a perna <= candles da tendencia previa
   // - Amplitude da 1a perna >= MinAmplitudeRatio% da tendencia
   // ================================================================
   if(bullCount > trendCount) return false;  // mais candles que a tendencia = sem forca

   double requiredAmplitude = trendAmplitude * g_choch_min_amplitude_ratio / 100.0;
   if(leg1Amplitude < requiredAmplitude) return false;  // impulso fraco

   // ================================================================
   // ETAPA 3: Correcao + 2a perna (mecanica BoS Fases 2 e 3)
   // ================================================================

   // Fase 2: Correcao (candles bearish consecutivos apos a perna de alta)
   int corrCount = 0;
   double pullbackLow = DBL_MAX;
   int corrEnd = -1;
   int corrStart = -1;

   for(int i = legEnd - 1; i >= shift; i--)
   {
      bool isBull = (iClose(sym, tf, i) > iOpen(sym, tf, i));
      if(!isBull)
      {
         corrCount++;
         pullbackLow = MathMin(pullbackLow, iLow(sym, tf, i));
         corrEnd = i;
         if(corrStart < 0) corrStart = i;
         if(corrCount > g_bos_correction_max) return false;
      }
      else
      {
         break;
      }
   }

   if(corrCount < 1) return false;
   if(corrCount > bullCount) return false;  // correcao > perna = invalido
   if(pullbackLow <= low1) return false;    // rompeu inicio da perna

   // Filtro OB (CHoCH_Bull):
   //   Pivo = candle com menor low entre:
   //     (a) trendEnd  = ultimo bearish da tendencia previa (zona [low, open])
   //     (b) legStart  = 1o bullish da 1a perna de reversao (zona [low, close])
   {
      double lowA = iLow(sym, tf, trendEnd);
      double lowB = iLow(sym, tf, legStart);
      double obTop_CHoCH, obLow_CHoCH;
      if(lowA <= lowB)
      {
         obLow_CHoCH = lowA;
         obTop_CHoCH = iOpen(sym, tf, trendEnd);   // pivo bearish: borda sup = open
      }
      else
      {
         obLow_CHoCH = lowB;
         obTop_CHoCH = iClose(sym, tf, legStart);  // pivo bullish: borda sup = close
      }
      if(!_OB_ValidateBull(sym, tf, obTop_CHoCH, obLow_CHoCH,
                           corrStart, corrEnd, pullbackLow))
         return false;
   }

   // Fase 3: 2a perna de alta (rompimento de high1)
   int leg2Count = 0;

   for(int i = corrEnd - 1; i >= shift; i--)
   {
      bool isBull = (iClose(sym, tf, i) > iOpen(sym, tf, i));
      if(!isBull) return false;  // bearish sem romper = topo menor

      leg2Count++;

      double closeCandle = iClose(sym, tf, i);
      if(closeCandle > high1)
      {
         // CHoCH confirmado
         g_bos_legStart = low1;
         g_bos_legHigh  = high1;
         return true;
      }

      if(leg2Count >= g_bos_leg2_max) return false;
   }

   return false;
}

bool _CHoCH_Bear(string sym, ENUM_TIMEFRAMES tf, int lookback = 30, int shift = 1)
{
   g_bos_legStart = 0.0;
   g_bos_legHigh  = 0.0;

   // ================================================================
   // ETAPA 1: Tendencia previa de ALTA + 1a perna de BAIXA
   // ================================================================

   // Passo 1a: Encontra a 1a perna de baixa (candles bearish consecutivos)
   int legStart = -1;
   int legEnd   = -1;
   int bearCount = 0;

   for(int i = shift + 1; i <= shift + lookback; i++)
   {
      bool isBear = (iClose(sym, tf, i) < iOpen(sym, tf, i));
      if(isBear)
      {
         if(bearCount == 0) legEnd = i;
         bearCount++;
         legStart = i;
         if(bearCount > g_bos_leg1_max) return false;
      }
      else
      {
         if(bearCount >= g_bos_leg1_min) break;
         bearCount = 0;
         legStart = -1;
         legEnd   = -1;
      }
   }

   if(bearCount < g_bos_leg1_min || legStart < 0 || legEnd < 0) return false;

   // High1 e Low1 da 1a perna de baixa
   double high1 = iHigh(sym, tf, legStart);
   double low1 = DBL_MAX;
   for(int i = legEnd; i <= legStart; i++)
      low1 = MathMin(low1, iLow(sym, tf, i));
   if(low1 >= high1) return false;

   double leg1Amplitude = high1 - low1;

   // ================================================================
   // Passo 1b: Tendencia previa de ALTA (candles bullish consecutivos)
   // ================================================================
   int trendCount = 0;
   int trendStart = -1;
   int trendEnd   = -1;

   for(int i = legStart + 1; i <= shift + lookback; i++)
   {
      bool isBull = (iClose(sym, tf, i) > iOpen(sym, tf, i));
      if(isBull)
      {
         if(trendCount == 0) trendEnd = i;
         trendCount++;
         trendStart = i;
         if(trendCount > g_choch_trend_max) break;
      }
      else
      {
         break;
      }
   }

   if(trendCount < g_choch_trend_min) return false;
   if(trendCount > g_choch_trend_max) return false;

   // Amplitude da tendencia previa: high do fim - low do inicio
   double trendLow  = iLow(sym, tf, trendStart);   // fundo no inicio da alta
   double trendHigh = iHigh(sym, tf, trendEnd);     // topo no fim da alta
   double trendAmplitude = trendHigh - trendLow;
   if(trendAmplitude <= 0) return false;

   // ================================================================
   // ETAPA 2: Regras de forca do impulso
   // ================================================================
   if(bearCount > trendCount) return false;

   double requiredAmplitude = trendAmplitude * g_choch_min_amplitude_ratio / 100.0;
   if(leg1Amplitude < requiredAmplitude) return false;

   // ================================================================
   // ETAPA 3: Correcao + 2a perna (mecanica BoS espelhada)
   // ================================================================

   // Fase 2: Correcao (candles bullish consecutivos)
   int corrCount = 0;
   double pullbackHigh = -DBL_MAX;
   int corrEnd = -1;
   int corrStart = -1;

   for(int i = legEnd - 1; i >= shift; i--)
   {
      bool isBear = (iClose(sym, tf, i) < iOpen(sym, tf, i));
      if(!isBear)
      {
         corrCount++;
         pullbackHigh = MathMax(pullbackHigh, iHigh(sym, tf, i));
         corrEnd = i;
         if(corrStart < 0) corrStart = i;
         if(corrCount > g_bos_correction_max) return false;
      }
      else
      {
         break;
      }
   }

   if(corrCount < 1) return false;
   if(corrCount > bearCount) return false;
   if(pullbackHigh >= high1) return false;

   // Filtro OB (CHoCH_Bear):
   //   Pivo = candle com maior high entre:
   //     (a) trendEnd  = ultimo bullish da tendencia previa (zona [open, high])
   //     (b) legStart  = 1o bearish da 1a perna de reversao (zona [close, high])
   {
      double highA = iHigh(sym, tf, trendEnd);
      double highB = iHigh(sym, tf, legStart);
      double obBottom_CHoCH, obHigh_CHoCH;
      if(highA >= highB)
      {
         obHigh_CHoCH   = highA;
         obBottom_CHoCH = iOpen(sym, tf, trendEnd);   // pivo bullish: borda inf = open
      }
      else
      {
         obHigh_CHoCH   = highB;
         obBottom_CHoCH = iClose(sym, tf, legStart);  // pivo bearish: borda inf = close
      }
      if(!_OB_ValidateBear(sym, tf, obBottom_CHoCH, obHigh_CHoCH,
                           corrStart, corrEnd, pullbackHigh))
         return false;
   }

   // Fase 3: 2a perna de baixa (rompimento de low1)
   int leg2Count = 0;

   for(int i = corrEnd - 1; i >= shift; i--)
   {
      bool isBear = (iClose(sym, tf, i) < iOpen(sym, tf, i));
      if(!isBear) return false;

      leg2Count++;

      double closeCandle = iClose(sym, tf, i);
      if(closeCandle < low1)
      {
         g_bos_legStart = high1;
         g_bos_legHigh  = low1;
         return true;
      }

      if(leg2Count >= g_bos_leg2_max) return false;
   }

   return false;
}

//+------------------------------------------------------------------+
//| ORDER BLOCK (OB) - Filtro de mitigacao para BoS/CHoCH            |
//|                                                                  |
//| OB nao e mais um padrao isolado. E um filtro de qualidade         |
//| aplicado DENTRO dos padroes BoS e CHoCH via InpOB_Mitigation.    |
//|                                                                  |
//| Zona do OB (Bull):                                                |
//|   BoS_Bull  -> [low, close] do 1o candle bullish da 1a perna     |
//|   CHoCH_Bull -> candle com menor low entre:                        |
//|     (a) ultimo bearish da tendencia previa: zona [low, open]     |
//|     (b) 1o bullish da 1a perna de reversao: zona [low, close]    |
//|                                                                  |
//| Zona do OB (Bear): espelhada                                      |
//|   BoS_Bear  -> [open, high] do 1o candle bearish da 1a perna... |
//|     NOTA: em candle bearish, open > close. Zona = [close, high]? |
//|     Correcao: zona = [close, high] (corpo superior + pavio sup.) |
//|   CHoCH_Bear -> candle com maior high, espelhado                  |
//|                                                                  |
//| Modos:                                                            |
//|   NONE       = sem filtro                                         |
//|   TOUCH      = pullback do lado testa a zona (pavio)             |
//|   VALIDATION = ALGUM candle da correcao fecha dentro da zona     |
//+------------------------------------------------------------------+

// Configuracao do filtro OB (ajustavel via BP_SmartMoney_SetOBMitigation)
ENUM_BP_OB_MITIGATION g_ob_mitigation = OB_MITIGATION_NONE;

//+------------------------------------------------------------------+
//| Configura modo de mitigacao do OB                                 |
//+------------------------------------------------------------------+
void BP_SmartMoney_SetOBMitigation(int handle, ENUM_BP_OB_MITIGATION mode)
{
   if(handle < 0 || handle >= BP_SMC_MAX_INSTANCES || !g_bp_smc[handle].active)
      return;
   g_ob_mitigation = mode;
}

//+------------------------------------------------------------------+
//| Valida filtro OB no lado BULL                                     |
//| obTop = borda superior da zona (close do pivo bullish ou open do  |
//|         pivo bearish no CHoCH)                                    |
//| obLow = borda inferior da zona (low do candle pivo)               |
//| corrEndIdx = indice do candle mais recente da correcao             |
//| corrStartIdx = indice do candle mais antigo da correcao            |
//| pullbackLow = low mais baixo da correcao                           |
//|                                                                  |
//| Retorna true se o filtro atual esta satisfeito (ou se e NONE)     |
//+------------------------------------------------------------------+
bool _OB_ValidateBull(string sym, ENUM_TIMEFRAMES tf,
                      double obTop, double obLow,
                      int corrStartIdx, int corrEndIdx,
                      double pullbackLow)
{
   if(g_ob_mitigation == OB_MITIGATION_NONE) return true;
   if(obTop <= obLow) return false;  // zona invalida

   if(g_ob_mitigation == OB_MITIGATION_TOUCH)
   {
      // pavio da correcao atingiu a borda superior da zona
      return (pullbackLow <= obTop);
   }

   if(g_ob_mitigation == OB_MITIGATION_VALIDATION)
   {
      // algum candle da correcao tem close dentro de (obLow, obTop]
      // varre de corrStartIdx (mais antigo) ate corrEndIdx (mais recente)
      for(int i = corrStartIdx; i >= corrEndIdx; i--)
      {
         double closeC = iClose(sym, tf, i);
         if(closeC > obLow && closeC < obTop) return true;
      }
      return false;
   }

   return true;
}

//+------------------------------------------------------------------+
//| Valida filtro OB no lado BEAR (espelhado)                         |
//| obBottom = borda inferior da zona (close do pivo bearish ou open  |
//|            do pivo bullish no CHoCH)                              |
//| obHigh   = borda superior da zona (high do candle pivo)           |
//+------------------------------------------------------------------+
bool _OB_ValidateBear(string sym, ENUM_TIMEFRAMES tf,
                      double obBottom, double obHigh,
                      int corrStartIdx, int corrEndIdx,
                      double pullbackHigh)
{
   if(g_ob_mitigation == OB_MITIGATION_NONE) return true;
   if(obBottom >= obHigh) return false;

   if(g_ob_mitigation == OB_MITIGATION_TOUCH)
   {
      return (pullbackHigh >= obBottom);
   }

   if(g_ob_mitigation == OB_MITIGATION_VALIDATION)
   {
      for(int i = corrStartIdx; i >= corrEndIdx; i--)
      {
         double closeC = iClose(sym, tf, i);
         if(closeC > obBottom && closeC < obHigh) return true;
      }
      return false;
   }

   return true;
}

//+------------------------------------------------------------------+
//| LIQUIDITY GRAB & SWEEP - Baseados em BoS                         |
//|                                                                  |
//| [BSL] Buy-Side Liquidity: regiao no topo do padrao BoS_Bull      |
//|   - Candle pivo = aquele com maior high entre:                   |
//|       (a) ultimo candle bullish da 1a perna                      |
//|       (b) 1o candle bearish da correcao                          |
//|   - Borda superior = high do candle pivo                         |
//|   - Borda inferior = max(open, close) do candle pivo             |
//|                                                                  |
//| [SSL] Sell-Side Liquidity: regiao no fundo do padrao BoS_Bear    |
//|   - Candle pivo = aquele com menor low entre:                    |
//|       (a) ultimo candle bearish da 1a perna                      |
//|       (b) 1o candle bullish da correcao                          |
//|   - Borda inferior = low do candle pivo                          |
//|   - Borda superior = min(open, close) do candle pivo             |
//|                                                                  |
//| LIQUIDITY GRAB (High): BoS falhado                                |
//|   - Padrao BoS_Bull ate a correcao detectado                     |
//|   - Candle da 2a perna rompe high do [BSL] (high > borda_sup)    |
//|   - Mas close < borda superior (rejeicao imediata)               |
//|   - Qualificacao: pavio superior >= 50% do range do candle       |
//|   - Qualificacao: close na metade inferior do range              |
//|                                                                  |
//| LIQUIDITY SWEEP (High): BoS confirmado + consolidacao + reversao |
//|   - Padrao BoS_Bull confirmado (close > high da 1a perna)        |
//|   - Candles subsequentes consolidam: low <= borda_superior       |
//|   - Anulacao: primeiro candle com low > borda_superior           |
//|   - Confirmacao da reversao: close < borda_inferior              |
//+------------------------------------------------------------------+

// Qualificacao do Grab (hardcoded, nao expostos)
#define BP_GRAB_WICK_RATIO     0.5   // Pavio >= 50% do range
#define BP_GRAB_CLOSE_IN_LOWER 0.5   // Close na metade inferior (bear) / superior (bull)

//+------------------------------------------------------------------+
//| Helper: detecta 1a perna de alta + correcao e retorna dados do   |
//| candle pivo do [BSL] e indice do primeiro candle da 2a perna.    |
//| Reusa as Fases 1 e 2 do _BoS_Bull.                               |
//|                                                                  |
//| Retornos (via ref):                                              |
//|   bslTop    = borda superior do [BSL] (high do candle pivo)      |
//|   bslBottom = borda inferior do [BSL] (max(open,close) do pivo)  |
//|   low1      = low do inicio da 1a perna (invalidacao)            |
//|   high1     = high da 1a perna (nivel rompido pelo BoS)          |
//|   leg2Start = indice do 1o candle apos a correcao                |
//|   bullCount = numero de candles da 1a perna                      |
//|   corrCount = numero de candles da correcao                      |
//+------------------------------------------------------------------+
bool _BSL_GetZone(string sym, ENUM_TIMEFRAMES tf, int lookback, int shift,
                  double &bslTop, double &bslBottom,
                  double &low1, double &high1,
                  int &leg2Start, int &bullCount, int &corrCount)
{
   // FASE 1: 1a perna de alta
   int legStart = -1, legEnd = -1;
   bullCount = 0;

   for(int i = shift + 1; i <= shift + lookback; i++)
   {
      bool isBull = (iClose(sym, tf, i) > iOpen(sym, tf, i));
      if(isBull)
      {
         if(bullCount == 0) legEnd = i;
         bullCount++;
         legStart = i;
         if(bullCount > g_bos_leg1_max) return false;
      }
      else
      {
         if(bullCount >= g_bos_leg1_min) break;
         bullCount = 0;
         legStart = -1;
         legEnd   = -1;
      }
   }

   if(bullCount < g_bos_leg1_min || legStart < 0 || legEnd < 0) return false;

   low1 = iLow(sym, tf, legStart);
   high1 = -DBL_MAX;
   for(int i = legEnd; i <= legStart; i++)
      high1 = MathMax(high1, iHigh(sym, tf, i));
   if(high1 <= low1) return false;

   // FASE 2: Correcao (candles bearish consecutivos)
   corrCount = 0;
   double pullbackLow = DBL_MAX;
   int corrEnd = -1;
   int corrFirst = -1;  // 1o candle da correcao (mais antigo)

   for(int i = legEnd - 1; i >= shift; i--)
   {
      bool isBull = (iClose(sym, tf, i) > iOpen(sym, tf, i));
      if(!isBull)
      {
         corrCount++;
         pullbackLow = MathMin(pullbackLow, iLow(sym, tf, i));
         corrEnd = i;
         if(corrFirst < 0) corrFirst = i;  // 1o candle da correcao (maior indice)
         if(corrCount > g_bos_correction_max) return false;
      }
      else
      {
         break;
      }
   }

   if(corrCount < 1) return false;
   if(corrCount > bullCount) return false;
   if(pullbackLow <= low1) return false;

   // CANDLE PIVO do [BSL]: maior high entre (ultimo candle da 1a perna, 1o da correcao)
   // legEnd = ultimo candle da 1a perna (mais recente, menor indice dentro da perna)
   // corrFirst = 1o candle da correcao (indice = legEnd - 1)
   double highLegEnd   = iHigh(sym, tf, legEnd);
   double highCorrFirst = iHigh(sym, tf, corrFirst);

   int pivotIdx;
   if(highLegEnd >= highCorrFirst)
   {
      pivotIdx  = legEnd;
      bslTop    = highLegEnd;
      // candle bullish: borda inferior = close (>= open)
      bslBottom = MathMax(iOpen(sym, tf, pivotIdx), iClose(sym, tf, pivotIdx));
   }
   else
   {
      pivotIdx  = corrFirst;
      bslTop    = highCorrFirst;
      // candle bearish: borda inferior = open (>= close)
      bslBottom = MathMax(iOpen(sym, tf, pivotIdx), iClose(sym, tf, pivotIdx));
   }

   if(bslBottom >= bslTop) return false;  // zona degenerada

   leg2Start = corrEnd - 1;  // 1o candle apos a correcao
   return true;
}

//+------------------------------------------------------------------+
//| Helper espelhado para [SSL] (Bear)                                |
//+------------------------------------------------------------------+
bool _SSL_GetZone(string sym, ENUM_TIMEFRAMES tf, int lookback, int shift,
                  double &sslBottom, double &sslTop,
                  double &high1, double &low1,
                  int &leg2Start, int &bearCount, int &corrCount)
{
   // FASE 1: 1a perna de baixa
   int legStart = -1, legEnd = -1;
   bearCount = 0;

   for(int i = shift + 1; i <= shift + lookback; i++)
   {
      bool isBear = (iClose(sym, tf, i) < iOpen(sym, tf, i));
      if(isBear)
      {
         if(bearCount == 0) legEnd = i;
         bearCount++;
         legStart = i;
         if(bearCount > g_bos_leg1_max) return false;
      }
      else
      {
         if(bearCount >= g_bos_leg1_min) break;
         bearCount = 0;
         legStart = -1;
         legEnd   = -1;
      }
   }

   if(bearCount < g_bos_leg1_min || legStart < 0 || legEnd < 0) return false;

   high1 = iHigh(sym, tf, legStart);
   low1 = DBL_MAX;
   for(int i = legEnd; i <= legStart; i++)
      low1 = MathMin(low1, iLow(sym, tf, i));
   if(low1 >= high1) return false;

   // FASE 2: Correcao (candles bullish consecutivos)
   corrCount = 0;
   double pullbackHigh = -DBL_MAX;
   int corrEnd = -1;
   int corrFirst = -1;

   for(int i = legEnd - 1; i >= shift; i--)
   {
      bool isBear = (iClose(sym, tf, i) < iOpen(sym, tf, i));
      if(!isBear)
      {
         corrCount++;
         pullbackHigh = MathMax(pullbackHigh, iHigh(sym, tf, i));
         corrEnd = i;
         if(corrFirst < 0) corrFirst = i;
         if(corrCount > g_bos_correction_max) return false;
      }
      else
      {
         break;
      }
   }

   if(corrCount < 1) return false;
   if(corrCount > bearCount) return false;
   if(pullbackHigh >= high1) return false;

   // CANDLE PIVO do [SSL]: menor low entre (ultimo candle da 1a perna, 1o da correcao)
   double lowLegEnd    = iLow(sym, tf, legEnd);
   double lowCorrFirst = iLow(sym, tf, corrFirst);

   int pivotIdx;
   if(lowLegEnd <= lowCorrFirst)
   {
      pivotIdx  = legEnd;
      sslBottom = lowLegEnd;
      // candle bearish: borda superior = close (<= open)
      sslTop    = MathMin(iOpen(sym, tf, pivotIdx), iClose(sym, tf, pivotIdx));
   }
   else
   {
      pivotIdx  = corrFirst;
      sslBottom = lowCorrFirst;
      // candle bullish: borda superior = open (<= close)
      sslTop    = MathMin(iOpen(sym, tf, pivotIdx), iClose(sym, tf, pivotIdx));
   }

   if(sslTop <= sslBottom) return false;

   leg2Start = corrEnd - 1;
   return true;
}

//+------------------------------------------------------------------+
//| LIQUIDITY GRAB HIGH (BoS falhado no topo)                         |
//| - Padrao BoS_Bull detectado ate a correcao                        |
//| - Candle da 2a perna tem high > bslTop (violacao/rompimento)      |
//| - MAS close < bslTop (rejeicao, BoS falhou)                       |
//| - Qualificacao:                                                    |
//|     pavio superior >= 50% do range do candle                       |
//|     close na metade inferior do range                              |
//+------------------------------------------------------------------+
bool _Grab_High(string sym, ENUM_TIMEFRAMES tf, int lookback = 20, int shift = 1)
{
   double bslTop, bslBottom, low1, high1;
   int leg2Start, bullCount, corrCount;

   if(!_BSL_GetZone(sym, tf, lookback, shift, bslTop, bslBottom,
                    low1, high1, leg2Start, bullCount, corrCount))
      return false;

   // Procura candle que violou [BSL] mas foi rejeitado (close abaixo do topo)
   // Varre da 2a perna ate shift
   int leg2Count = 0;
   for(int i = leg2Start; i >= shift; i--)
   {
      double highC  = iHigh(sym, tf, i);
      double closeC = iClose(sym, tf, i);
      double openC  = iOpen(sym, tf, i);
      double lowC   = iLow(sym, tf, i);

      leg2Count++;
      if(leg2Count > g_bos_leg2_max) return false;

      // Candle violou o topo do BSL?
      if(highC > bslTop)
      {
         // Rejeicao: close abaixo do topo do BSL (BoS falhou)
         if(closeC >= bslTop) return false;  // BoS confirmado, nao e Grab

         // Qualificacao de rejeicao
         double range = highC - lowC;
         if(range <= 0) return false;

         double upperWick = highC - MathMax(openC, closeC);
         double wickRatio = upperWick / range;
         if(wickRatio < BP_GRAB_WICK_RATIO) return false;

         // Close na metade inferior do range
         double closePos = (closeC - lowC) / range;
         if(closePos > BP_GRAB_CLOSE_IN_LOWER) return false;

         // Guarda niveis para consulta (topo rompido = bslTop, stop = acima de highC)
         g_bos_legStart = highC;    // stop acima do pavio
         g_bos_legHigh  = bslTop;   // nivel da liquidez
         return true;
      }
   }

   return false;
}

//+------------------------------------------------------------------+
//| LIQUIDITY GRAB LOW (BoS falhado no fundo)                         |
//+------------------------------------------------------------------+
bool _Grab_Low(string sym, ENUM_TIMEFRAMES tf, int lookback = 20, int shift = 1)
{
   double sslBottom, sslTop, high1, low1;
   int leg2Start, bearCount, corrCount;

   if(!_SSL_GetZone(sym, tf, lookback, shift, sslBottom, sslTop,
                    high1, low1, leg2Start, bearCount, corrCount))
      return false;

   int leg2Count = 0;
   for(int i = leg2Start; i >= shift; i--)
   {
      double lowC   = iLow(sym, tf, i);
      double closeC = iClose(sym, tf, i);
      double openC  = iOpen(sym, tf, i);
      double highC  = iHigh(sym, tf, i);

      leg2Count++;
      if(leg2Count > g_bos_leg2_max) return false;

      if(lowC < sslBottom)
      {
         if(closeC <= sslBottom) return false;  // BoS_Bear confirmado

         double range = highC - lowC;
         if(range <= 0) return false;

         double lowerWick = MathMin(openC, closeC) - lowC;
         double wickRatio = lowerWick / range;
         if(wickRatio < BP_GRAB_WICK_RATIO) return false;

         // Close na metade superior do range
         double closePos = (highC - closeC) / range;
         if(closePos > BP_GRAB_CLOSE_IN_LOWER) return false;

         g_bos_legStart = lowC;       // stop abaixo do pavio
         g_bos_legHigh  = sslBottom;  // nivel da liquidez
         return true;
      }
   }

   return false;
}

//+------------------------------------------------------------------+
//| LIQUIDITY SWEEP HIGH (BoS confirmado + consolidacao + reversao)   |
//| - Padrao BoS_Bull confirmado (candle rompe com close > bslTop)    |
//| - Consolidacao: candles seguintes com low <= bslTop (tocam zona)  |
//| - Anulacao: primeiro candle com low > bslTop                      |
//| - Confirmacao reversao: close < bslBottom                         |
//+------------------------------------------------------------------+
bool _Sweep_High(string sym, ENUM_TIMEFRAMES tf, int lookback = 20, int shift = 1)
{
   double bslTop, bslBottom, low1, high1;
   int leg2Start, bullCount, corrCount;

   if(!_BSL_GetZone(sym, tf, lookback, shift, bslTop, bslBottom,
                    low1, high1, leg2Start, bullCount, corrCount))
      return false;

   // ETAPA 1: Procura candle de rompimento (close > bslTop) dentro da 2a perna
   int breakoutIdx = -1;
   int leg2Count = 0;

   for(int i = leg2Start; i >= shift; i--)
   {
      double highC  = iHigh(sym, tf, i);
      double closeC = iClose(sym, tf, i);

      leg2Count++;
      if(leg2Count > g_bos_leg2_max) return false;

      if(highC > bslTop && closeC > bslTop)
      {
         breakoutIdx = i;
         break;
      }
      // Candle bearish antes de romper = invalido (nao eh BoS)
      bool isBull = (iClose(sym, tf, i) > iOpen(sym, tf, i));
      if(!isBull) return false;
   }

   if(breakoutIdx < 0) return false;
   if(breakoutIdx <= shift) return false;  // precisa de pelo menos 1 candle apos rompimento

   // ETAPA 2: Consolidacao - candles entre breakoutIdx-1 e shift
   // Cada candle deve ter low <= bslTop (tocar a zona)
   // Procura candle de confirmacao: close < bslBottom (reversao)
   bool hasConsolidation = false;

   for(int i = breakoutIdx - 1; i >= shift; i--)
   {
      double lowC   = iLow(sym, tf, i);
      double closeC = iClose(sym, tf, i);

      // Anulacao: low > bslTop (nao tocou mais a zona)
      if(lowC > bslTop) return false;

      // Confirmacao da reversao: close < bslBottom
      if(closeC < bslBottom)
      {
         if(!hasConsolidation) return false;  // precisa ter pelo menos 1 candle de consolidacao antes
         g_bos_legStart = bslTop;     // stop acima do topo do BSL
         g_bos_legHigh  = bslBottom;  // nivel rompido (confirmacao)
         return true;
      }

      // Tocou a zona: e consolidacao
      hasConsolidation = true;
   }

   return false;
}

//+------------------------------------------------------------------+
//| LIQUIDITY SWEEP LOW (espelhado)                                   |
//+------------------------------------------------------------------+
bool _Sweep_Low(string sym, ENUM_TIMEFRAMES tf, int lookback = 20, int shift = 1)
{
   double sslBottom, sslTop, high1, low1;
   int leg2Start, bearCount, corrCount;

   if(!_SSL_GetZone(sym, tf, lookback, shift, sslBottom, sslTop,
                    high1, low1, leg2Start, bearCount, corrCount))
      return false;

   int breakoutIdx = -1;
   int leg2Count = 0;

   for(int i = leg2Start; i >= shift; i--)
   {
      double lowC   = iLow(sym, tf, i);
      double closeC = iClose(sym, tf, i);

      leg2Count++;
      if(leg2Count > g_bos_leg2_max) return false;

      if(lowC < sslBottom && closeC < sslBottom)
      {
         breakoutIdx = i;
         break;
      }
      bool isBear = (iClose(sym, tf, i) < iOpen(sym, tf, i));
      if(!isBear) return false;
   }

   if(breakoutIdx < 0) return false;
   if(breakoutIdx <= shift) return false;

   bool hasConsolidation = false;

   for(int i = breakoutIdx - 1; i >= shift; i--)
   {
      double highC  = iHigh(sym, tf, i);
      double closeC = iClose(sym, tf, i);

      if(highC < sslBottom) return false;

      if(closeC > sslTop)
      {
         if(!hasConsolidation) return false;
         g_bos_legStart = sslBottom;
         g_bos_legHigh  = sslTop;
         return true;
      }

      hasConsolidation = true;
   }

   return false;
}

//+------------------------------------------------------------------+
//| API PUBLICA: retorna zona do FVG                                 |
//| zoneHigh/zoneLow definem o "caixote" do gap                     |
//| Bull: entrada BUY_LIMIT no zoneHigh, stop no zoneLow            |
//| Bear: entrada SELL_LIMIT no zoneLow, stop no zoneHigh           |
//+------------------------------------------------------------------+
bool BP_SmartMoney_GetFVGZone(int handle, ENUM_BP_SMC_CONCEPT concept,
                               double &zoneHigh, double &zoneLow, int shift = 1)
{
   if(handle < 0 || handle >= BP_SMC_MAX_INSTANCES || !g_bp_smc[handle].active)
      return false;

   string          sym = g_bp_smc[handle].symbol;
   ENUM_TIMEFRAMES tf  = g_bp_smc[handle].tf;

   if(concept == BP_SMC_FVG_BULL)
      return _FVG_GetZone(sym, tf, true, zoneHigh, zoneLow, shift);
   if(concept == BP_SMC_FVG_BEAR)
      return _FVG_GetZone(sym, tf, false, zoneHigh, zoneLow, shift);

   return false;
}

//+------------------------------------------------------------------+
//| API PUBLICA: retorna niveis do BOS                               |
//| legStart = ponto de invalidacao/stop (Low1 bull, High1 bear)     |
//| legHigh  = nivel rompido (High1 bull, Low1 bear)                 |
//| Deve ser chamado APOS BP_SmartMoney_Detect retornar true         |
//+------------------------------------------------------------------+
bool BP_SmartMoney_GetBOSLevels(int handle, ENUM_BP_SMC_CONCEPT concept,
                                 double &legStart, double &legHigh)
{
   if(handle < 0 || handle >= BP_SMC_MAX_INSTANCES || !g_bp_smc[handle].active)
      return false;
   if(concept != BP_SMC_BOS_BULL && concept != BP_SMC_BOS_BEAR)
      return false;
   if(g_bos_legStart == 0.0 || g_bos_legHigh == 0.0)
      return false;

   legStart = g_bos_legStart;
   legHigh  = g_bos_legHigh;
   return true;
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
      case BP_SMC_SWEEP_HIGH: return _Sweep_High(sym, tf, 20, shift);
      case BP_SMC_SWEEP_LOW:  return _Sweep_Low(sym, tf, 20, shift);
      case BP_SMC_GRAB_HIGH:  return _Grab_High(sym, tf, 20, shift);
      case BP_SMC_GRAB_LOW:   return _Grab_Low(sym, tf, 20, shift);
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
      case BP_SMC_SWEEP_LOW:   // sweep de minimas: BoS_Bear confirmado + reversao -> compra
      case BP_SMC_GRAB_LOW:    // grab de minimas: rejeicao no fundo -> compra
         return BP_SIGNAL_BUY;
      case BP_SMC_FVG_BEAR:
      case BP_SMC_BOS_BEAR:
      case BP_SMC_CHOCH_BEAR:
      case BP_SMC_SWEEP_HIGH:  // sweep de maximas: BoS_Bull confirmado + reversao -> venda
      case BP_SMC_GRAB_HIGH:   // grab de maximas: rejeicao no topo -> venda
         return BP_SIGNAL_SELL;
      default:
         return BP_SIGNAL_NONE;
   }
}

#endif // __BP_SMART_MONEY_MQH__

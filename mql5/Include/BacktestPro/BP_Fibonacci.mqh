//+------------------------------------------------------------------+
//|                                              BP_Fibonacci.mqh    |
//|                                             BacktestPro v1.0     |
//| Detecta perna de impulso via ZigZag (iCustom local) e expoe      |
//| niveis de retracao (23.6/38.2/50/61.8/78.6/100) e projecao       |
//| (127.2/161.8/200/261.8) para uso como:                            |
//|   - gatilho de entrada (TOQUE ou VALIDACAO)                       |
//|   - preco de Stop Loss   (BP_SL_FIBO, calculado no EA)            |
//|   - preco de Take Profit (BP_TP_FIBO, calculado no EA)            |
//|                                                                    |
//| A perna de impulso e definida pelos DOIS ultimos pivos alternados |
//| do ZigZag (um topo e um fundo). Direcao:                           |
//|   pivo mais recente = topo  -> impulso de ALTA  -> setup de COMPRA|
//|   pivo mais recente = fundo -> impulso de BAIXA -> setup de VENDA |
//|                                                                    |
//| O modulo mantem os niveis ATUALIZADOS a cada nova barra. O EA     |
//| congela os niveis copiando-os no momento do trigger (ver SL/TP).  |
//+------------------------------------------------------------------+
#ifndef __BP_FIBONACCI_MQH__
#define __BP_FIBONACCI_MQH__
#include <BacktestPro/BP_Constants.mqh>
#include <BacktestPro/BP_DebugViz.mqh>

//+------------------------------------------------------------------+
//| Pool de instancias                                                |
//+------------------------------------------------------------------+
#define BP_FIBO_MAX_INSTANCES 4

// Buffers do indicador Examples\ZigZag.ex5
#define BP_FIBO_ZZ_BUF_ZIGZAG   0  // valor do pivo (0 fora de pivo)
#define BP_FIBO_ZZ_BUF_HIGH     1  // valor de topo (0 se nao for topo)
#define BP_FIBO_ZZ_BUF_LOW      2  // valor de fundo (0 se nao for fundo)

// Quantas barras retroceder para localizar os 2 pivos alternados mais recentes.
// Com ZigZag depth padrao (12) e timeframe intradiario, 500 barras e margem segura.
#define BP_FIBO_MAX_LOOKBACK    1000

struct BPFibonacciInstance
{
   bool            active;
   string          symbol;
   ENUM_TIMEFRAMES tf;
   int             loggerHandle;
   int             zzHandle;       // iCustom handle
   int             depth;
   int             deviation;
   int             backstep;

   // Estado da perna detectada
   bool            legValid;
   ENUM_BP_SIGNAL  legDirection;   // BUY = impulso alta, SELL = impulso baixa
   double          legHigh;        // preco do topo da perna
   double          legLow;         // preco do fundo da perna
   datetime        legHighTime;
   datetime        legLowTime;
   int             legHighBar;     // shift no momento do ultimo Update
   int             legLowBar;

   // Controle de trigger por barra (evita disparar multiplas vezes no mesmo candle)
   datetime        lastTriggerBarTime;

   // Bloqueio de reentrada (Rigor B): apos uma posicao ser aberta numa perna,
   // bloqueia novos triggers do mesmo lado ate o pivo de referencia mudar.
   //   COMPRA: bloqueia enquanto legHighTime == lastEnteredHighTime_BUY
   //   VENDA : bloqueia enquanto legLowTime  == lastEnteredLowTime_SELL
   // Registrado em OnTradeTransaction quando o deal de abertura e confirmado.
   datetime        lastEnteredHighTime_BUY;
   datetime        lastEnteredLowTime_SELL;

   // Debug visual (opt-in via BP_Fibonacci_SetDebugViz)
   bool                      debugViz;
   ENUM_BP_TRIGGER_HIGHLIGHT highlightMode;

   // Guardamos os niveis configurados para redesenhar no Draw
   ENUM_BP_FIBO_LEVEL triggerLevel;
   ENUM_BP_FIBO_LEVEL slLevel;
   ENUM_BP_FIBO_LEVEL tpLevel;
};

BPFibonacciInstance g_bp_fibo[BP_FIBO_MAX_INSTANCES];
bool                g_bp_fibo_init = false;

//+------------------------------------------------------------------+
//| Inicializa pool                                                  |
//+------------------------------------------------------------------+
void _BP_Fibo_Init()
{
   if(g_bp_fibo_init) return;
   for(int i = 0; i < BP_FIBO_MAX_INSTANCES; i++)
   {
      g_bp_fibo[i].active   = false;
      g_bp_fibo[i].zzHandle = INVALID_HANDLE;
   }
   g_bp_fibo_init = true;
}

//+------------------------------------------------------------------+
//| Helper: valida handle                                             |
//+------------------------------------------------------------------+
bool _BP_Fibo_IsValid(int handle)
{
   if(handle < 0 || handle >= BP_FIBO_MAX_INSTANCES) return false;
   return g_bp_fibo[handle].active;
}

//+------------------------------------------------------------------+
//| Converte nivel enum para ratio [0.0..2.618]                       |
//| Retracao: 0 = inicio da perna (fundo na compra, topo na venda)    |
//|           1 = fim da perna   (topo na compra, fundo na venda)     |
//| Projecao: > 1 extrapola alem do fim da perna                       |
//+------------------------------------------------------------------+
double _BP_Fibo_LevelToRatio(ENUM_BP_FIBO_LEVEL level)
{
   switch(level)
   {
      case BP_FIBO_236:  return 0.236;
      case BP_FIBO_382:  return 0.382;
      case BP_FIBO_500:  return 0.500;
      case BP_FIBO_618:  return 0.618;
      case BP_FIBO_786:  return 0.786;
      case BP_FIBO_100:  return 1.000;
      case BP_FIBO_1272: return 1.272;
      case BP_FIBO_1618: return 1.618;
      case BP_FIBO_200:  return 2.000;
      case BP_FIBO_2618: return 2.618;
   }
   return 0.0;
}

//+------------------------------------------------------------------+
//| Converte nivel enum para string legivel                          |
//+------------------------------------------------------------------+
string _BP_Fibo_LevelToStr(ENUM_BP_FIBO_LEVEL level)
{
   switch(level)
   {
      case BP_FIBO_236:  return "23.6%";
      case BP_FIBO_382:  return "38.2%";
      case BP_FIBO_500:  return "50.0%";
      case BP_FIBO_618:  return "61.8%";
      case BP_FIBO_786:  return "78.6%";
      case BP_FIBO_100:  return "100%";
      case BP_FIBO_1272: return "127.2%";
      case BP_FIBO_1618: return "161.8%";
      case BP_FIBO_200:  return "200%";
      case BP_FIBO_2618: return "261.8%";
   }
   return "?";
}

//+------------------------------------------------------------------+
//| Cria instancia                                                   |
//|   depth/deviation/backstep: parametros do ZigZag (iguais ao      |
//|                              indicador Examples\ZigZag.ex5)       |
//+------------------------------------------------------------------+
int BP_Fibonacci_Create(const string symbol, ENUM_TIMEFRAMES tf, int loggerHandle,
                         int depth, int deviation, int backstep)
{
   _BP_Fibo_Init();

   for(int i = 0; i < BP_FIBO_MAX_INSTANCES; i++)
   {
      if(!g_bp_fibo[i].active)
      {
         int zz = iCustom(symbol, tf, "Examples\\ZigZag", depth, deviation, backstep);
         if(zz == INVALID_HANDLE)
         {
            if(loggerHandle >= 0)
               Logger_Error(loggerHandle, "BP_Fibonacci: iCustom(Examples\\ZigZag) falhou");
            return -1;
         }

         g_bp_fibo[i].active              = true;
         g_bp_fibo[i].symbol              = symbol;
         g_bp_fibo[i].tf                  = tf;
         g_bp_fibo[i].loggerHandle        = loggerHandle;
         g_bp_fibo[i].zzHandle            = zz;
         g_bp_fibo[i].depth               = depth;
         g_bp_fibo[i].deviation           = deviation;
         g_bp_fibo[i].backstep            = backstep;
         g_bp_fibo[i].legValid            = false;
         g_bp_fibo[i].legDirection        = BP_SIGNAL_NONE;
         g_bp_fibo[i].legHigh             = 0.0;
         g_bp_fibo[i].legLow              = 0.0;
         g_bp_fibo[i].legHighTime         = 0;
         g_bp_fibo[i].legLowTime          = 0;
         g_bp_fibo[i].legHighBar          = -1;
         g_bp_fibo[i].legLowBar           = -1;
         g_bp_fibo[i].lastTriggerBarTime  = 0;
         g_bp_fibo[i].lastEnteredHighTime_BUY = 0;
         g_bp_fibo[i].lastEnteredLowTime_SELL = 0;
         g_bp_fibo[i].debugViz            = false;
         g_bp_fibo[i].highlightMode       = BP_HL_BOTH;
         g_bp_fibo[i].triggerLevel        = BP_FIBO_618;
         g_bp_fibo[i].slLevel             = BP_FIBO_100;
         g_bp_fibo[i].tpLevel             = BP_FIBO_1618;
         return i;
      }
   }
   return -1;
}

//+------------------------------------------------------------------+
//| Destroi instancia                                                |
//+------------------------------------------------------------------+
bool BP_Fibonacci_Destroy(int handle)
{
   if(!_BP_Fibo_IsValid(handle)) return false;
   if(g_bp_fibo[handle].zzHandle != INVALID_HANDLE)
      IndicatorRelease(g_bp_fibo[handle].zzHandle);
   g_bp_fibo[handle].active   = false;
   g_bp_fibo[handle].zzHandle = INVALID_HANDLE;
   return true;
}

//+------------------------------------------------------------------+
//| Atualiza perna corrente lendo buffers do ZigZag                  |
//| Estrategia: percorre candle[1] ate candle[BP_FIBO_MAX_LOOKBACK],  |
//| coleta os 2 pivos alternados mais recentes (um topo e um fundo). |
//| O mais proximo de candle[1] define a direcao do impulso.         |
//|                                                                    |
//| Retorna true se uma perna valida foi encontrada.                  |
//+------------------------------------------------------------------+
bool BP_Fibonacci_Update(int handle)
{
   if(!_BP_Fibo_IsValid(handle)) return false;

   string sym          = g_bp_fibo[handle].symbol;
   ENUM_TIMEFRAMES tf  = g_bp_fibo[handle].tf;
   int zz              = g_bp_fibo[handle].zzHandle;

   // Disponibilidade minima de barras
   int bars = Bars(sym, tf);
   int lookback = MathMin(BP_FIBO_MAX_LOOKBACK, bars - 1);
   if(lookback < 20) { g_bp_fibo[handle].legValid = false; return false; }

   // Copia buffers High e Low do ZigZag do candle[1] para tras.
   // offset=1 ignora o candle[0] (em formacao).
   double bufHigh[];
   double bufLow[];
   ArraySetAsSeries(bufHigh, true);
   ArraySetAsSeries(bufLow,  true);

   if(CopyBuffer(zz, BP_FIBO_ZZ_BUF_HIGH, 1, lookback, bufHigh) <= 0)
   { g_bp_fibo[handle].legValid = false; return false; }
   if(CopyBuffer(zz, BP_FIBO_ZZ_BUF_LOW,  1, lookback, bufLow)  <= 0)
   { g_bp_fibo[handle].legValid = false; return false; }

   // Varre do mais recente para o mais antigo, procurando:
   //   recentPivot: primeiro pivo encontrado (topo OU fundo)
   //   olderPivot : proximo pivo de tipo oposto
   //
   // Regra "shift >= 2": o pivo recente precisa estar a pelo menos 1 candle
   // de distancia do candle trigger (bar[1]). Isso evita aceitar como "topo"
   // o high do proprio candle que esta sendo avaliado (perna ainda em formacao).
   // Como i=0 na varredura corresponde a bar[1] do grafico (offset +1 ao final),
   // exigir i>=1 garante que o pivo esta em bar[2] ou mais antigo.
   int    recentIdx   = -1;  // shift no grafico (ja com offset +1)
   bool   recentIsHigh = false;
   double recentPrice = 0.0;

   int    olderIdx   = -1;
   bool   olderIsHigh = false;
   double olderPrice = 0.0;

   for(int i = 0; i < lookback; i++)
   {
      double h = bufHigh[i];
      double l = bufLow[i];
      bool isHigh = (h > 0.0);
      bool isLow  = (l > 0.0);
      if(!isHigh && !isLow) continue;

      // Se um candle marca topo e fundo simultaneamente (raro), privilegia o
      // que for oposto ao recente ja capturado; na primeira captura, usa topo.
      if(recentIdx < 0)
      {
         // Rejeita pivo em bar[1] (i==0 aqui) - perna ainda nao formada
         if(i < 1) continue;

         if(isHigh) { recentIsHigh = true;  recentPrice = h; }
         else       { recentIsHigh = false; recentPrice = l; }
         recentIdx = i;
         continue;
      }

      // Procura pivo oposto
      if(recentIsHigh && isLow)
      {
         olderIsHigh = false;
         olderPrice  = l;
         olderIdx    = i;
         break;
      }
      if(!recentIsHigh && isHigh)
      {
         olderIsHigh = true;
         olderPrice  = h;
         olderIdx    = i;
         break;
      }
      // Pivo do mesmo tipo que o recente: ZigZag pode re-pintar; atualiza o "recente"
      // para o mais proximo (i ja e mais antigo, entao descarta)
   }

   if(recentIdx < 0 || olderIdx < 0)
   {
      g_bp_fibo[handle].legValid = false;
      return false;
   }

   // Monta a perna: o pivo recente define o fim; o pivo antigo define o inicio.
   // Direcao: recente=topo -> impulso de alta -> setup de compra
   //          recente=fundo-> impulso de baixa-> setup de venda
   ENUM_BP_SIGNAL dir = recentIsHigh ? BP_SIGNAL_BUY : BP_SIGNAL_SELL;
   double legHigh, legLow;
   datetime tHighBar, tLowBar;
   int barHigh, barLow;

   if(recentIsHigh)
   {
      legHigh   = recentPrice;  barHigh = recentIdx + 1;   // reaplica offset
      legLow    = olderPrice;   barLow  = olderIdx + 1;
   }
   else
   {
      legLow    = recentPrice;  barLow  = recentIdx + 1;
      legHigh   = olderPrice;   barHigh = olderIdx + 1;
   }

   tHighBar = iTime(sym, tf, barHigh);
   tLowBar  = iTime(sym, tf, barLow);

   // Valida: perna precisa ter amplitude > 0
   if(legHigh <= legLow)
   {
      g_bp_fibo[handle].legValid = false;
      return false;
   }

   g_bp_fibo[handle].legValid      = true;
   g_bp_fibo[handle].legDirection  = dir;
   g_bp_fibo[handle].legHigh       = legHigh;
   g_bp_fibo[handle].legLow        = legLow;
   g_bp_fibo[handle].legHighTime   = tHighBar;
   g_bp_fibo[handle].legLowTime    = tLowBar;
   g_bp_fibo[handle].legHighBar    = barHigh;
   g_bp_fibo[handle].legLowBar     = barLow;

   return true;
}

//+------------------------------------------------------------------+
//| Queries da perna atual                                            |
//+------------------------------------------------------------------+
bool   BP_Fibonacci_HasValidLeg(int handle)
{
   if(!_BP_Fibo_IsValid(handle)) return false;
   return g_bp_fibo[handle].legValid;
}

ENUM_BP_SIGNAL BP_Fibonacci_GetLegDirection(int handle)
{
   if(!_BP_Fibo_IsValid(handle)) return BP_SIGNAL_NONE;
   if(!g_bp_fibo[handle].legValid) return BP_SIGNAL_NONE;
   return g_bp_fibo[handle].legDirection;
}

double BP_Fibonacci_GetLegHigh(int handle)
{
   if(!_BP_Fibo_IsValid(handle)) return 0.0;
   return g_bp_fibo[handle].legHigh;
}

double BP_Fibonacci_GetLegLow(int handle)
{
   if(!_BP_Fibo_IsValid(handle)) return 0.0;
   return g_bp_fibo[handle].legLow;
}

//+------------------------------------------------------------------+
//| Normaliza preco para o tick size do simbolo                       |
//| Necessario porque calculos Fibonacci produzem precos fracionarios |
//| que o broker rejeita com "Invalid stops" (ex: WIN tick=5).        |
//+------------------------------------------------------------------+
double _BP_Fibo_NormalizePrice(const string symbol, double price)
{
   if(price <= 0.0) return 0.0;
   double tickSize = SymbolInfoDouble(symbol, SYMBOL_TRADE_TICK_SIZE);
   int    digits   = (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS);
   if(tickSize <= 0.0) return NormalizeDouble(price, digits);
   double normalized = MathRound(price / tickSize) * tickSize;
   return NormalizeDouble(normalized, digits);
}

//+------------------------------------------------------------------+
//| Calcula preco de um nivel na perna atual                         |
//|                                                                    |
//| Retracao (ratio <= 1.0):                                          |
//|   compra: preco = legHigh - ratio * (legHigh - legLow)            |
//|   venda : preco = legLow  + ratio * (legHigh - legLow)            |
//| Projecao (ratio > 1.0):                                           |
//|   compra: preco = legHigh + (ratio-1) * (legHigh - legLow)        |
//|   venda : preco = legLow  - (ratio-1) * (legHigh - legLow)        |
//|                                                                    |
//| Preco e normalizado ao tick size do simbolo.                      |
//| Retorna 0.0 se perna invalida.                                    |
//+------------------------------------------------------------------+
double BP_Fibonacci_GetLevelPrice(int handle, ENUM_BP_FIBO_LEVEL level)
{
   if(!_BP_Fibo_IsValid(handle)) return 0.0;
   if(!g_bp_fibo[handle].legValid) return 0.0;

   double ratio   = _BP_Fibo_LevelToRatio(level);
   double high    = g_bp_fibo[handle].legHigh;
   double low     = g_bp_fibo[handle].legLow;
   double range   = high - low;
   if(range <= 0.0) return 0.0;

   ENUM_BP_SIGNAL dir = g_bp_fibo[handle].legDirection;
   string sym         = g_bp_fibo[handle].symbol;
   double price       = 0.0;

   if(ratio <= 1.0)
   {
      // retracao (interna a perna)
      if(dir == BP_SIGNAL_BUY)  price = high - ratio * range;
      else if(dir == BP_SIGNAL_SELL) price = low  + ratio * range;
   }
   else
   {
      // projecao (alem do fim da perna)
      double extra = (ratio - 1.0) * range;
      if(dir == BP_SIGNAL_BUY)  price = high + extra;
      else if(dir == BP_SIGNAL_SELL) price = low  - extra;
   }

   if(price <= 0.0) return 0.0;
   return _BP_Fibo_NormalizePrice(sym, price);
}

//+------------------------------------------------------------------+
//| Avalia gatilho de entrada no candle[1] (candle que acabou de     |
//| fechar). Retorna BP_SIGNAL_BUY / BP_SIGNAL_SELL / BP_SIGNAL_NONE. |
//|                                                                    |
//| Regras:                                                            |
//|   TOQUE (compra): low[1] <= precoNivel                             |
//|   TOQUE (venda) : high[1] >= precoNivel                            |
//|   VALIDACAO (compra): low[1] <= precoNivel E close[1] > precoNivel |
//|   VALIDACAO (venda) : high[1] >= precoNivel E close[1] < precoNivel|
//|                                                                    |
//| A direcao do sinal e SEMPRE a direcao da perna (compra em impulso |
//| de alta, venda em impulso de baixa).                               |
//|                                                                    |
//| Anti-duplicata: dispara no maximo uma vez por candle trigger.     |
//+------------------------------------------------------------------+
ENUM_BP_SIGNAL BP_Fibonacci_CheckTrigger(int handle,
                                         ENUM_BP_FIBO_LEVEL triggerLevel,
                                         ENUM_BP_FIBO_TRIGGER_MODE mode)
{
   if(!_BP_Fibo_IsValid(handle)) return BP_SIGNAL_NONE;
   if(!g_bp_fibo[handle].legValid) return BP_SIGNAL_NONE;

   ENUM_BP_SIGNAL dir = g_bp_fibo[handle].legDirection;
   if(dir == BP_SIGNAL_NONE) return BP_SIGNAL_NONE;

   int loggerH = g_bp_fibo[handle].loggerHandle;

   // Bloqueio de reentrada: se ja entramos nessa perna para essa direcao,
   // aguarda o pivo de referencia mudar.
   if(BP_Fibonacci_IsLegBlocked(handle, dir))
   {
      if(loggerH >= 0 && Logger_GetLevel(loggerH) >= LOG_LEVEL_DEBUG)
      {
         datetime pivotTime = (dir == BP_SIGNAL_BUY)
            ? g_bp_fibo[handle].legHighTime
            : g_bp_fibo[handle].legLowTime;
         string side = (dir == BP_SIGNAL_BUY) ? "COMPRA (topo" : "VENDA (fundo";
         Logger_Debug(loggerH, StringFormat("  Fibo trigger bloqueado: %s @ %s ja usado)",
                                            side,
                                            TimeToString(pivotTime, TIME_DATE|TIME_MINUTES)));
      }
      return BP_SIGNAL_NONE;
   }

   double levelPrice = BP_Fibonacci_GetLevelPrice(handle, triggerLevel);
   if(levelPrice <= 0.0) return BP_SIGNAL_NONE;

   string sym         = g_bp_fibo[handle].symbol;
   ENUM_TIMEFRAMES tf = g_bp_fibo[handle].tf;
   int digits         = (int)SymbolInfoInteger(sym, SYMBOL_DIGITS);

   // Candle de referencia = candle[1] (acabou de fechar)
   datetime barTime = iTime(sym, tf, 1);
   if(barTime == g_bp_fibo[handle].lastTriggerBarTime) return BP_SIGNAL_NONE;

   double high  = iHigh (sym, tf, 1);
   double low   = iLow  (sym, tf, 1);
   double close = iClose(sym, tf, 1);

   bool penetrou  = false;
   bool triggered = false;

   if(dir == BP_SIGNAL_BUY)
   {
      // Correcao contra o impulso de alta: preco cai ATE o nivel
      penetrou = (low <= levelPrice);
      if(mode == BP_FIBO_TRIG_TOUCH)
         triggered = penetrou;
      else
         triggered = penetrou && (close > levelPrice);  // rejeitou a retracao
   }
   else  // BP_SIGNAL_SELL
   {
      penetrou = (high >= levelPrice);
      if(mode == BP_FIBO_TRIG_TOUCH)
         triggered = penetrou;
      else
         triggered = penetrou && (close < levelPrice);
   }

   // Log detalhado (so em nivel DEBUG)
   if(loggerH >= 0 && Logger_GetLevel(loggerH) >= LOG_LEVEL_DEBUG)
   {
      string dirStr  = (dir == BP_SIGNAL_BUY) ? "COMPRA" : "VENDA";
      string modeStr = (mode == BP_FIBO_TRIG_TOUCH) ? "TOQUE" : "VALIDACAO";
      string refStr  = (dir == BP_SIGNAL_BUY)
         ? StringFormat("low=%s close=%s", DoubleToString(low, digits), DoubleToString(close, digits))
         : StringFormat("high=%s close=%s", DoubleToString(high, digits), DoubleToString(close, digits));
      string result  = triggered ? "DISPAROU"
                                 : (penetrou ? "penetrou mas nao validou" : "nivel nao atingido");
      Logger_Debug(loggerH, StringFormat("  Fibo trigger: %s %s @ %s | %s | [%s] %s",
                                         dirStr,
                                         _BP_Fibo_LevelToStr(triggerLevel),
                                         DoubleToString(levelPrice, digits),
                                         refStr,
                                         modeStr,
                                         result));
   }

   if(!triggered) return BP_SIGNAL_NONE;

   g_bp_fibo[handle].lastTriggerBarTime = barTime;
   return dir;
}

//+------------------------------------------------------------------+
//| Calcula preco de Stop Loss segundo nivel Fibonacci               |
//|                                                                    |
//| Compra (impulso alta): SL abaixo do nivel (normalmente 78.6% ou   |
//|                        100% = fundo da perna). Buffer em pontos   |
//|                        aplicado a MAIS para baixo.                 |
//| Venda (impulso baixa): SL acima do nivel. Buffer a MAIS para cima.|
//|                                                                    |
//| Retorna 0.0 se perna invalida.                                    |
//+------------------------------------------------------------------+
double BP_Fibonacci_CalculateSL(int handle, ENUM_BP_SIGNAL signal,
                                 ENUM_BP_FIBO_LEVEL slLevel, int bufferPoints)
{
   if(!_BP_Fibo_IsValid(handle)) return 0.0;
   if(!g_bp_fibo[handle].legValid) return 0.0;

   double levelPrice = BP_Fibonacci_GetLevelPrice(handle, slLevel);
   if(levelPrice <= 0.0) return 0.0;

   string sym   = g_bp_fibo[handle].symbol;
   double point = SymbolInfoDouble(sym, SYMBOL_POINT);
   double buf   = bufferPoints * point;
   double sl    = 0.0;

   if(signal == BP_SIGNAL_BUY)  sl = levelPrice - buf;
   else if(signal == BP_SIGNAL_SELL) sl = levelPrice + buf;
   else return 0.0;

   return _BP_Fibo_NormalizePrice(sym, sl);
}

//+------------------------------------------------------------------+
//| Calcula preco de Take Profit segundo nivel de projecao Fibonacci |
//|                                                                    |
//| Compra: TP = preco do nivel (ja fica acima do topo se ratio>1)    |
//| Venda : TP = preco do nivel (ja fica abaixo do fundo se ratio>1)  |
//|                                                                    |
//| Retorna 0.0 se perna invalida ou nivel nao projecao.              |
//+------------------------------------------------------------------+
double BP_Fibonacci_CalculateTP(int handle, ENUM_BP_SIGNAL signal,
                                 ENUM_BP_FIBO_LEVEL tpLevel)
{
   if(!_BP_Fibo_IsValid(handle)) return 0.0;
   if(!g_bp_fibo[handle].legValid) return 0.0;
   if(signal == BP_SIGNAL_NONE) return 0.0;

   return BP_Fibonacci_GetLevelPrice(handle, tpLevel);
}

//+------------------------------------------------------------------+
//| Helper de log: string com estado atual da perna                   |
//+------------------------------------------------------------------+
string BP_Fibonacci_DescribeState(int handle)
{
   if(!_BP_Fibo_IsValid(handle)) return "Fibo: handle invalido";
   if(!g_bp_fibo[handle].legValid) return "Fibo: sem perna valida";

   int digits = (int)SymbolInfoInteger(g_bp_fibo[handle].symbol, SYMBOL_DIGITS);
   string dirStr = (g_bp_fibo[handle].legDirection == BP_SIGNAL_BUY) ? "COMPRA" : "VENDA";
   string timeHigh = TimeToString(g_bp_fibo[handle].legHighTime, TIME_DATE|TIME_MINUTES);
   string timeLow  = TimeToString(g_bp_fibo[handle].legLowTime,  TIME_DATE|TIME_MINUTES);
   return StringFormat("Fibo: %s | topo=%s (bar %d @ %s) | fundo=%s (bar %d @ %s) | range=%s",
                       dirStr,
                       DoubleToString(g_bp_fibo[handle].legHigh, digits),
                       g_bp_fibo[handle].legHighBar, timeHigh,
                       DoubleToString(g_bp_fibo[handle].legLow, digits),
                       g_bp_fibo[handle].legLowBar,  timeLow,
                       DoubleToString(g_bp_fibo[handle].legHigh - g_bp_fibo[handle].legLow, digits));
}

//+------------------------------------------------------------------+
//| BLOQUEIO DE REENTRADA (Rigor B)                                   |
//+------------------------------------------------------------------+
// Registra que uma posicao foi efetivamente aberta na perna atual.
// Apos isso, novos triggers do mesmo lado ficam bloqueados ate o
// pivo correspondente mudar:
//   COMPRA -> bloqueia ate novo topo (legHighTime != lastEnteredHighTime_BUY)
//   VENDA  -> bloqueia ate novo fundo (legLowTime != lastEnteredLowTime_SELL)
//
// Chamar do EA em OnTradeTransaction (branch DealEntry confirmado).
void BP_Fibonacci_RegisterEntry(int handle, ENUM_BP_SIGNAL signal)
{
   if(!_BP_Fibo_IsValid(handle)) return;
   if(!g_bp_fibo[handle].legValid) return;

   if(signal == BP_SIGNAL_BUY)
   {
      g_bp_fibo[handle].lastEnteredHighTime_BUY = g_bp_fibo[handle].legHighTime;
      if(g_bp_fibo[handle].loggerHandle >= 0)
         Logger_Info(g_bp_fibo[handle].loggerHandle,
            StringFormat("Fibo: compra registrada, bloqueado ate novo topo (topo atual @ %s)",
                         TimeToString(g_bp_fibo[handle].legHighTime, TIME_DATE|TIME_MINUTES)));
   }
   else if(signal == BP_SIGNAL_SELL)
   {
      g_bp_fibo[handle].lastEnteredLowTime_SELL = g_bp_fibo[handle].legLowTime;
      if(g_bp_fibo[handle].loggerHandle >= 0)
         Logger_Info(g_bp_fibo[handle].loggerHandle,
            StringFormat("Fibo: venda registrada, bloqueado ate novo fundo (fundo atual @ %s)",
                         TimeToString(g_bp_fibo[handle].legLowTime, TIME_DATE|TIME_MINUTES)));
   }
}

// Retorna true se a perna atual ja foi consumida para o lado indicado.
bool BP_Fibonacci_IsLegBlocked(int handle, ENUM_BP_SIGNAL direction)
{
   if(!_BP_Fibo_IsValid(handle)) return false;
   if(!g_bp_fibo[handle].legValid) return false;

   if(direction == BP_SIGNAL_BUY)
   {
      // Bloqueado se o topo da perna atual e o mesmo da ultima entrada comprada
      datetime marker = g_bp_fibo[handle].lastEnteredHighTime_BUY;
      return (marker != 0 && marker == g_bp_fibo[handle].legHighTime);
   }
   if(direction == BP_SIGNAL_SELL)
   {
      datetime marker = g_bp_fibo[handle].lastEnteredLowTime_SELL;
      return (marker != 0 && marker == g_bp_fibo[handle].legLowTime);
   }
   return false;
}

//+------------------------------------------------------------------+
//| DEBUG VISUAL                                                      |
//+------------------------------------------------------------------+
// Ativa debug visual para este handle. Os niveis configurados (trigger,
// SL, TP) sao guardados no handle para serem redesenhados.
void BP_Fibonacci_SetDebugViz(int handle, bool enabled,
                               ENUM_BP_TRIGGER_HIGHLIGHT highlightMode,
                               ENUM_BP_FIBO_LEVEL triggerLevel,
                               ENUM_BP_FIBO_LEVEL slLevel,
                               ENUM_BP_FIBO_LEVEL tpLevel)
{
   if(!_BP_Fibo_IsValid(handle)) return;
   g_bp_fibo[handle].debugViz      = enabled;
   g_bp_fibo[handle].highlightMode = highlightMode;
   g_bp_fibo[handle].triggerLevel  = triggerLevel;
   g_bp_fibo[handle].slLevel       = slLevel;
   g_bp_fibo[handle].tpLevel       = tpLevel;
}

//+------------------------------------------------------------------+
//| Redesenha todos os elementos Fibonacci no chart.                  |
//| Chamar apos BP_Fibonacci_Update (a cada nova barra).              |
//|                                                                    |
//| Elementos desenhados (prefixo "BP_VIZ_FIBO_"):                    |
//|   - Perna (trend line do topo ao fundo)                           |
//|   - Linha horizontal do topo (azul) e fundo (vermelho)            |
//|   - Nivel de trigger (magenta destacado)                          |
//|   - Nivel de SL (tomato, tracejado)                               |
//|   - Nivel de TP (azul claro, tracejado)                           |
//+------------------------------------------------------------------+
void BP_Fibonacci_DrawDebug(int handle)
{
   if(!_BP_Fibo_IsValid(handle)) return;
   if(!g_bp_fibo[handle].debugViz) return;
   if(!BP_Viz_IsEnabled()) return;

   // Limpa desenhos anteriores (mantem highlight de candles antigos)
   BP_Viz_DeleteByPrefix("BP_VIZ_FIBO_leg");
   BP_Viz_DeleteByPrefix("BP_VIZ_FIBO_top");
   BP_Viz_DeleteByPrefix("BP_VIZ_FIBO_bot");
   BP_Viz_DeleteByPrefix("BP_VIZ_FIBO_trig");
   BP_Viz_DeleteByPrefix("BP_VIZ_FIBO_sl");
   BP_Viz_DeleteByPrefix("BP_VIZ_FIBO_tp");

   if(!g_bp_fibo[handle].legValid) { BP_Viz_Refresh(); return; }

   string sym   = g_bp_fibo[handle].symbol;
   int digits   = (int)SymbolInfoInteger(sym, SYMBOL_DIGITS);
   double high  = g_bp_fibo[handle].legHigh;
   double low   = g_bp_fibo[handle].legLow;
   datetime tH  = g_bp_fibo[handle].legHighTime;
   datetime tL  = g_bp_fibo[handle].legLowTime;

   // Perna: trend line conectando topo e fundo
   BP_Viz_DrawTrendLine("BP_VIZ_FIBO_leg", tH, high, tL, low,
                        BP_VIZ_COLOR_LEG, STYLE_DASH, 2, false);

   // Linhas horizontais do topo e fundo
   BP_Viz_DrawHLine("BP_VIZ_FIBO_top", high, BP_VIZ_COLOR_LEG, STYLE_SOLID, 1,
                    "Topo " + DoubleToString(high, digits));
   BP_Viz_DrawHLine("BP_VIZ_FIBO_bot", low,  BP_VIZ_COLOR_LEG, STYLE_SOLID, 1,
                    "Fundo " + DoubleToString(low, digits));

   // Nivel de trigger
   double trigPrice = BP_Fibonacci_GetLevelPrice(handle, g_bp_fibo[handle].triggerLevel);
   if(trigPrice > 0.0)
   {
      string trigName = "BP_VIZ_FIBO_trig";
      string trigText = "Trigger " + _BP_Fibo_LevelToStr(g_bp_fibo[handle].triggerLevel)
                      + " = " + DoubleToString(trigPrice, digits);
      BP_Viz_DrawHLine(trigName, trigPrice, BP_VIZ_COLOR_TRIGGER, STYLE_SOLID, 2, trigText);
   }

   // Nivel de SL
   double slPrice = BP_Fibonacci_GetLevelPrice(handle, g_bp_fibo[handle].slLevel);
   if(slPrice > 0.0)
   {
      string slText = "SL " + _BP_Fibo_LevelToStr(g_bp_fibo[handle].slLevel)
                    + " = " + DoubleToString(slPrice, digits);
      BP_Viz_DrawHLine("BP_VIZ_FIBO_sl", slPrice, BP_VIZ_COLOR_SL, STYLE_DOT, 1, slText);
   }

   // Nivel de TP
   double tpPrice = BP_Fibonacci_GetLevelPrice(handle, g_bp_fibo[handle].tpLevel);
   if(tpPrice > 0.0)
   {
      string tpText = "TP " + _BP_Fibo_LevelToStr(g_bp_fibo[handle].tpLevel)
                    + " = " + DoubleToString(tpPrice, digits);
      BP_Viz_DrawHLine("BP_VIZ_FIBO_tp", tpPrice, BP_VIZ_COLOR_TP, STYLE_DOT, 1, tpText);
   }

   BP_Viz_Refresh();
}

//+------------------------------------------------------------------+
//| Destaca o candle que disparou o trigger.                          |
//| Chamar quando BP_Fibonacci_CheckTrigger retorna != NONE.          |
//| Cada candle disparado ganha um highlight permanente (com timestamp|
//| no nome) para que historico nao seja apagado entre updates.       |
//+------------------------------------------------------------------+
void BP_Fibonacci_HighlightTriggerCandle(int handle, ENUM_BP_SIGNAL signal, datetime barTime)
{
   if(!_BP_Fibo_IsValid(handle)) return;
   if(!g_bp_fibo[handle].debugViz) return;
   if(!BP_Viz_IsEnabled()) return;
   if(g_bp_fibo[handle].highlightMode == BP_HL_NONE) return;

   string tag = StringFormat("BP_VIZ_FIBO_candle_%I64d", (long)barTime);
   BP_Viz_HighlightCandle(tag, barTime,
                          g_bp_fibo[handle].tf,
                          g_bp_fibo[handle].symbol,
                          signal,
                          g_bp_fibo[handle].highlightMode,
                          BP_VIZ_COLOR_HIGHLIGHT);
   BP_Viz_Refresh();
}

#endif // __BP_FIBONACCI_MQH__

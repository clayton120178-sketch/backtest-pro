//+------------------------------------------------------------------+
//|                                              BP_DebugViz.mqh    |
//|                                             BacktestPro v1.0     |
//| Modulo consolidado de debug visual.                               |
//|                                                                    |
//| Fornece API para desenhar primitivas no chart (HLine, VLine,     |
//| TrendLine, Rectangle, Arrow, Label, Text, Channel) com gestao    |
//| automatica de prefixos por modulo e limpeza seletiva.             |
//|                                                                    |
//| Uso tipico por modulo cliente (ex: BP_Fibonacci):                 |
//|   if(g_bp_fibo[h].debugViz) {                                     |
//|      BP_Viz_DeleteByPrefix("BP_VIZ_FIBO_");                       |
//|      BP_Viz_DrawHLine("BP_VIZ_FIBO_top", legHigh, ...);           |
//|      BP_Viz_DrawTrendLine("BP_VIZ_FIBO_leg", t1, p1, t2, p2,...);|
//|   }                                                                |
//|                                                                    |
//| Master-switch: BP_Viz_SetEnabled(true/false). Em produtivo,       |
//| qualquer chamada retorna cedo (custo ~ns).                        |
//|                                                                    |
//| Namespace padrao: "BP_VIZ_<MODULO>_<TAG>"                         |
//|   ex: BP_VIZ_FIBO_top, BP_VIZ_FIBO_leg, BP_VIZ_TRIG_candle        |
//+------------------------------------------------------------------+
#ifndef __BP_DEBUG_VIZ_MQH__
#define __BP_DEBUG_VIZ_MQH__

//+------------------------------------------------------------------+
//| Paleta padrao (podem ser referenciados pelos modulos clientes)   |
//+------------------------------------------------------------------+
#define BP_VIZ_COLOR_BUY          clrLime
#define BP_VIZ_COLOR_SELL         clrRed
#define BP_VIZ_COLOR_LEG          clrGoldenrod
#define BP_VIZ_COLOR_LEVEL        clrGoldenrod
#define BP_VIZ_COLOR_TRIGGER      clrMagenta
#define BP_VIZ_COLOR_SL           clrTomato
#define BP_VIZ_COLOR_TP           clrDodgerBlue
#define BP_VIZ_COLOR_HIGHLIGHT    clrYellow
#define BP_VIZ_COLOR_TEXT         clrWhite

//+------------------------------------------------------------------+
//| Estado global do modulo                                           |
//+------------------------------------------------------------------+
bool   g_bp_viz_enabled = false;
long   g_bp_viz_chartId = 0;           // 0 = chart corrente
int    g_bp_viz_subwin  = 0;           // subwindow (0 = main chart)

// Counter de objetos (para diagnostico)
int    g_bp_viz_obj_created = 0;
int    g_bp_viz_obj_deleted = 0;

//+------------------------------------------------------------------+
//| Master-switch                                                     |
//+------------------------------------------------------------------+
void BP_Viz_SetEnabled(bool enabled) { g_bp_viz_enabled = enabled; }
bool BP_Viz_IsEnabled()              { return g_bp_viz_enabled; }

void BP_Viz_SetChart(long chartId, int subwindow = 0)
{
   g_bp_viz_chartId = chartId;
   g_bp_viz_subwin  = subwindow;
}

int  BP_Viz_GetObjectsCreated() { return g_bp_viz_obj_created; }
int  BP_Viz_GetObjectsDeleted() { return g_bp_viz_obj_deleted; }

//+------------------------------------------------------------------+
//| Helper interno: recria objeto (deleta se existe)                  |
//+------------------------------------------------------------------+
bool _BP_Viz_Recreate(const string name, ENUM_OBJECT objType,
                      datetime t1, double p1, datetime t2 = 0, double p2 = 0.0,
                      datetime t3 = 0, double p3 = 0.0)
{
   if(ObjectFind(g_bp_viz_chartId, name) >= 0)
   {
      ObjectDelete(g_bp_viz_chartId, name);
      g_bp_viz_obj_deleted++;
   }
   bool ok = false;
   // ObjectCreate com 1/2/3 pontos conforme o tipo
   if(objType == OBJ_HLINE)
      ok = ObjectCreate(g_bp_viz_chartId, name, objType, g_bp_viz_subwin, 0, p1);
   else if(objType == OBJ_VLINE)
      ok = ObjectCreate(g_bp_viz_chartId, name, objType, g_bp_viz_subwin, t1, 0);
   else if(objType == OBJ_LABEL)
      ok = ObjectCreate(g_bp_viz_chartId, name, objType, g_bp_viz_subwin, 0, 0);
   else if(objType == OBJ_CHANNEL)
      ok = ObjectCreate(g_bp_viz_chartId, name, objType, g_bp_viz_subwin,
                        t1, p1, t2, p2, t3, p3);
   else if(objType == OBJ_RECTANGLE || objType == OBJ_TREND)
      ok = ObjectCreate(g_bp_viz_chartId, name, objType, g_bp_viz_subwin,
                        t1, p1, t2, p2);
   else  // OBJ_ARROW, OBJ_TEXT e afins (1 ponto)
      ok = ObjectCreate(g_bp_viz_chartId, name, objType, g_bp_viz_subwin, t1, p1);

   if(ok) g_bp_viz_obj_created++;
   return ok;
}

//+------------------------------------------------------------------+
//| Linha horizontal                                                  |
//+------------------------------------------------------------------+
void BP_Viz_DrawHLine(const string name, double price, color clr,
                      ENUM_LINE_STYLE style = STYLE_DOT, int width = 1,
                      const string text = "")
{
   if(!g_bp_viz_enabled) return;
   if(!_BP_Viz_Recreate(name, OBJ_HLINE, 0, price)) return;
   ObjectSetInteger(g_bp_viz_chartId, name, OBJPROP_COLOR, clr);
   ObjectSetInteger(g_bp_viz_chartId, name, OBJPROP_STYLE, style);
   ObjectSetInteger(g_bp_viz_chartId, name, OBJPROP_WIDTH, width);
   ObjectSetInteger(g_bp_viz_chartId, name, OBJPROP_BACK, true);
   ObjectSetInteger(g_bp_viz_chartId, name, OBJPROP_SELECTABLE, false);
   ObjectSetInteger(g_bp_viz_chartId, name, OBJPROP_HIDDEN,  true);
   if(StringLen(text) > 0)
      ObjectSetString(g_bp_viz_chartId, name, OBJPROP_TEXT, text);
}

//+------------------------------------------------------------------+
//| Linha vertical                                                    |
//+------------------------------------------------------------------+
void BP_Viz_DrawVLine(const string name, datetime t, color clr,
                      ENUM_LINE_STYLE style = STYLE_DOT, int width = 1,
                      const string text = "")
{
   if(!g_bp_viz_enabled) return;
   if(!_BP_Viz_Recreate(name, OBJ_VLINE, t, 0)) return;
   ObjectSetInteger(g_bp_viz_chartId, name, OBJPROP_COLOR, clr);
   ObjectSetInteger(g_bp_viz_chartId, name, OBJPROP_STYLE, style);
   ObjectSetInteger(g_bp_viz_chartId, name, OBJPROP_WIDTH, width);
   ObjectSetInteger(g_bp_viz_chartId, name, OBJPROP_BACK, true);
   ObjectSetInteger(g_bp_viz_chartId, name, OBJPROP_SELECTABLE, false);
   ObjectSetInteger(g_bp_viz_chartId, name, OBJPROP_HIDDEN,  true);
   if(StringLen(text) > 0)
      ObjectSetString(g_bp_viz_chartId, name, OBJPROP_TEXT, text);
}

//+------------------------------------------------------------------+
//| Trend Line (segmento entre dois pontos)                          |
//+------------------------------------------------------------------+
void BP_Viz_DrawTrendLine(const string name,
                          datetime t1, double p1,
                          datetime t2, double p2,
                          color clr,
                          ENUM_LINE_STYLE style = STYLE_SOLID,
                          int width = 1,
                          bool rayRight = false)
{
   if(!g_bp_viz_enabled) return;
   if(!_BP_Viz_Recreate(name, OBJ_TREND, t1, p1, t2, p2)) return;
   ObjectSetInteger(g_bp_viz_chartId, name, OBJPROP_COLOR, clr);
   ObjectSetInteger(g_bp_viz_chartId, name, OBJPROP_STYLE, style);
   ObjectSetInteger(g_bp_viz_chartId, name, OBJPROP_WIDTH, width);
   ObjectSetInteger(g_bp_viz_chartId, name, OBJPROP_BACK, true);
   ObjectSetInteger(g_bp_viz_chartId, name, OBJPROP_SELECTABLE, false);
   ObjectSetInteger(g_bp_viz_chartId, name, OBJPROP_HIDDEN,  true);
   ObjectSetInteger(g_bp_viz_chartId, name, OBJPROP_RAY_RIGHT, rayRight);
}

//+------------------------------------------------------------------+
//| Retangulo (zona delimitada por 2 pontos)                         |
//+------------------------------------------------------------------+
void BP_Viz_DrawRect(const string name,
                     datetime t1, double p1,
                     datetime t2, double p2,
                     color clr,
                     bool fill = false,
                     ENUM_LINE_STYLE style = STYLE_SOLID,
                     int width = 1)
{
   if(!g_bp_viz_enabled) return;
   if(!_BP_Viz_Recreate(name, OBJ_RECTANGLE, t1, p1, t2, p2)) return;
   ObjectSetInteger(g_bp_viz_chartId, name, OBJPROP_COLOR, clr);
   ObjectSetInteger(g_bp_viz_chartId, name, OBJPROP_STYLE, style);
   ObjectSetInteger(g_bp_viz_chartId, name, OBJPROP_WIDTH, width);
   ObjectSetInteger(g_bp_viz_chartId, name, OBJPROP_FILL,  fill);
   ObjectSetInteger(g_bp_viz_chartId, name, OBJPROP_BACK,  true);
   ObjectSetInteger(g_bp_viz_chartId, name, OBJPROP_SELECTABLE, false);
   ObjectSetInteger(g_bp_viz_chartId, name, OBJPROP_HIDDEN, true);
}

//+------------------------------------------------------------------+
//| Seta (arrow code - tabela MT5 de wingdings)                      |
//| Codigos uteis: 233=up, 234=down, 181=buy, 182=sell                |
//+------------------------------------------------------------------+
void BP_Viz_DrawArrow(const string name,
                      datetime t, double price,
                      int arrowCode,
                      color clr,
                      int width = 2,
                      ENUM_ARROW_ANCHOR anchor = ANCHOR_BOTTOM)
{
   if(!g_bp_viz_enabled) return;
   if(!_BP_Viz_Recreate(name, OBJ_ARROW, t, price)) return;
   ObjectSetInteger(g_bp_viz_chartId, name, OBJPROP_COLOR, clr);
   ObjectSetInteger(g_bp_viz_chartId, name, OBJPROP_WIDTH, width);
   ObjectSetInteger(g_bp_viz_chartId, name, OBJPROP_ARROWCODE, arrowCode);
   ObjectSetInteger(g_bp_viz_chartId, name, OBJPROP_ANCHOR, anchor);
   ObjectSetInteger(g_bp_viz_chartId, name, OBJPROP_BACK, false);
   ObjectSetInteger(g_bp_viz_chartId, name, OBJPROP_SELECTABLE, false);
   ObjectSetInteger(g_bp_viz_chartId, name, OBJPROP_HIDDEN, true);
}

//+------------------------------------------------------------------+
//| Seta COMPRA (codigo 233 = up arrow) ancorada no low do candle     |
//+------------------------------------------------------------------+
void BP_Viz_DrawArrowBuy(const string name, datetime t, double price,
                         color clr = BP_VIZ_COLOR_BUY, int width = 3)
{
   BP_Viz_DrawArrow(name, t, price, 233, clr, width, ANCHOR_TOP);
}

//+------------------------------------------------------------------+
//| Seta VENDA (codigo 234 = down arrow) ancorada no high do candle   |
//+------------------------------------------------------------------+
void BP_Viz_DrawArrowSell(const string name, datetime t, double price,
                          color clr = BP_VIZ_COLOR_SELL, int width = 3)
{
   BP_Viz_DrawArrow(name, t, price, 234, clr, width, ANCHOR_BOTTOM);
}

//+------------------------------------------------------------------+
//| Texto flutuante em coordenadas de preco/tempo                    |
//+------------------------------------------------------------------+
void BP_Viz_DrawText(const string name,
                     datetime t, double price,
                     const string text,
                     color clr = BP_VIZ_COLOR_TEXT,
                     int fontSize = 9,
                     const string font = "Arial")
{
   if(!g_bp_viz_enabled) return;
   if(!_BP_Viz_Recreate(name, OBJ_TEXT, t, price)) return;
   ObjectSetString (g_bp_viz_chartId, name, OBJPROP_TEXT, text);
   ObjectSetString (g_bp_viz_chartId, name, OBJPROP_FONT, font);
   ObjectSetInteger(g_bp_viz_chartId, name, OBJPROP_FONTSIZE, fontSize);
   ObjectSetInteger(g_bp_viz_chartId, name, OBJPROP_COLOR, clr);
   ObjectSetInteger(g_bp_viz_chartId, name, OBJPROP_BACK, false);
   ObjectSetInteger(g_bp_viz_chartId, name, OBJPROP_SELECTABLE, false);
   ObjectSetInteger(g_bp_viz_chartId, name, OBJPROP_HIDDEN, true);
}

//+------------------------------------------------------------------+
//| Label fixa em coordenadas da tela (pixels)                        |
//| corner: 0=top-left, 1=top-right, 2=bottom-left, 3=bottom-right   |
//+------------------------------------------------------------------+
void BP_Viz_DrawLabel(const string name,
                      int xDistance, int yDistance,
                      const string text,
                      color clr = BP_VIZ_COLOR_TEXT,
                      int fontSize = 10,
                      ENUM_BASE_CORNER corner = CORNER_LEFT_UPPER,
                      const string font = "Arial")
{
   if(!g_bp_viz_enabled) return;
   if(!_BP_Viz_Recreate(name, OBJ_LABEL, 0, 0)) return;
   ObjectSetInteger(g_bp_viz_chartId, name, OBJPROP_CORNER,    corner);
   ObjectSetInteger(g_bp_viz_chartId, name, OBJPROP_XDISTANCE, xDistance);
   ObjectSetInteger(g_bp_viz_chartId, name, OBJPROP_YDISTANCE, yDistance);
   ObjectSetString (g_bp_viz_chartId, name, OBJPROP_TEXT, text);
   ObjectSetString (g_bp_viz_chartId, name, OBJPROP_FONT, font);
   ObjectSetInteger(g_bp_viz_chartId, name, OBJPROP_FONTSIZE, fontSize);
   ObjectSetInteger(g_bp_viz_chartId, name, OBJPROP_COLOR, clr);
   ObjectSetInteger(g_bp_viz_chartId, name, OBJPROP_BACK, false);
   ObjectSetInteger(g_bp_viz_chartId, name, OBJPROP_SELECTABLE, false);
   ObjectSetInteger(g_bp_viz_chartId, name, OBJPROP_HIDDEN, true);
}

//+------------------------------------------------------------------+
//| Canal equidistante (3 pontos: 2 na linha principal + 1 na paralela)|
//+------------------------------------------------------------------+
void BP_Viz_DrawChannel(const string name,
                        datetime t1, double p1,
                        datetime t2, double p2,
                        datetime t3, double p3,
                        color clr,
                        ENUM_LINE_STYLE style = STYLE_SOLID,
                        int width = 1)
{
   if(!g_bp_viz_enabled) return;
   if(!_BP_Viz_Recreate(name, OBJ_CHANNEL, t1, p1, t2, p2, t3, p3)) return;
   ObjectSetInteger(g_bp_viz_chartId, name, OBJPROP_COLOR, clr);
   ObjectSetInteger(g_bp_viz_chartId, name, OBJPROP_STYLE, style);
   ObjectSetInteger(g_bp_viz_chartId, name, OBJPROP_WIDTH, width);
   ObjectSetInteger(g_bp_viz_chartId, name, OBJPROP_BACK,  true);
   ObjectSetInteger(g_bp_viz_chartId, name, OBJPROP_SELECTABLE, false);
   ObjectSetInteger(g_bp_viz_chartId, name, OBJPROP_HIDDEN, true);
}

//+------------------------------------------------------------------+
//| Destaca um candle: seta + retangulo em torno do OHLC              |
//+------------------------------------------------------------------+
void BP_Viz_HighlightCandle(const string namePrefix,
                            datetime t, ENUM_TIMEFRAMES tf,
                            const string symbol,
                            ENUM_BP_SIGNAL direction,
                            ENUM_BP_TRIGGER_HIGHLIGHT mode,
                            color clr = BP_VIZ_COLOR_HIGHLIGHT)
{
   if(!g_bp_viz_enabled) return;
   if(mode == BP_HL_NONE) return;

   // Resolve OHLC do candle
   int shift = iBarShift(symbol, tf, t, false);
   if(shift < 0) return;
   double h = iHigh(symbol, tf, shift);
   double l = iLow (symbol, tf, shift);
   if(h <= 0.0 || l <= 0.0) return;

   // Periodo do timeframe em segundos (largura do retangulo)
   int secs = PeriodSeconds(tf);
   datetime tEnd = t + secs;

   // Retangulo envolvendo o candle
   if(mode == BP_HL_RECTANGLE || mode == BP_HL_BOTH)
   {
      string rectName = namePrefix + "_rect";
      double point   = SymbolInfoDouble(symbol, SYMBOL_POINT);
      double padding = (h - l) * 0.05;   // 5% de padding vertical
      if(padding < point * 2) padding = point * 2;
      BP_Viz_DrawRect(rectName, t, h + padding, tEnd, l - padding,
                      clr, false, STYLE_SOLID, 2);
   }

   // Seta direcional
   if(mode == BP_HL_ARROW || mode == BP_HL_BOTH)
   {
      string arrowName = namePrefix + "_arrow";
      if(direction == BP_SIGNAL_BUY)
         BP_Viz_DrawArrowBuy(arrowName, t, l, clr);
      else if(direction == BP_SIGNAL_SELL)
         BP_Viz_DrawArrowSell(arrowName, t, h, clr);
   }
}

//+------------------------------------------------------------------+
//| Deleta objeto por nome exato                                      |
//+------------------------------------------------------------------+
void BP_Viz_Delete(const string name)
{
   if(ObjectFind(g_bp_viz_chartId, name) >= 0)
   {
      ObjectDelete(g_bp_viz_chartId, name);
      g_bp_viz_obj_deleted++;
   }
}

//+------------------------------------------------------------------+
//| Deleta todos os objetos que comecam com o prefixo dado            |
//+------------------------------------------------------------------+
void BP_Viz_DeleteByPrefix(const string prefix)
{
   int total = ObjectsTotal(g_bp_viz_chartId, g_bp_viz_subwin);
   for(int i = total - 1; i >= 0; i--)
   {
      string objName = ObjectName(g_bp_viz_chartId, i, g_bp_viz_subwin);
      if(StringLen(objName) < StringLen(prefix)) continue;
      if(StringFind(objName, prefix) != 0) continue;
      ObjectDelete(g_bp_viz_chartId, objName);
      g_bp_viz_obj_deleted++;
   }
}

//+------------------------------------------------------------------+
//| Deleta todos os objetos do BP_DebugViz (chamar no OnDeinit)      |
//+------------------------------------------------------------------+
void BP_Viz_Clear()
{
   BP_Viz_DeleteByPrefix("BP_VIZ_");
}

//+------------------------------------------------------------------+
//| Forca redraw do chart                                             |
//+------------------------------------------------------------------+
void BP_Viz_Refresh()
{
   if(!g_bp_viz_enabled) return;
   ChartRedraw(g_bp_viz_chartId);
}

#endif // __BP_DEBUG_VIZ_MQH__

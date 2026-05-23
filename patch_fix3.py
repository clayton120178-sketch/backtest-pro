#!/usr/bin/env python3
# patch_fix3.py — SMC previews: same visual quality as BB chart
# 18-20 realistic candles per pattern, clear pattern structure, 180px height

FPATH = 'C:/Users/Clayton Barros/AppData/Local/Temp/backtest-pro/app.html'
with open(FPATH, 'r', encoding='utf-8') as f:
    content = f.read()

# ── shared chart options snippet (reused in markers below) ────────────────
CHART_CREATE = lambda h: (
    f"        width:chartW,height:{h},layout:{{background:{{color:bg}},textColor:text}},\n"
    f"        grid:{{vertLines:{{color:grid}},horzLines:{{color:grid}}}},\n"
    f"        rightPriceScale:{{borderColor:'transparent',scaleMargins:{{top:0.08,bottom:0.08}}}},\n"
    f"        timeScale:{{borderColor:'transparent',visible:false}},crosshair:{{mode:0}},\n"
    f"        handleScroll:false,handleScale:false,\n"
)

# =============================================================================
# 1. FVG — Fair Value Gap  (19 candles: 12 context + 3 FVG candles + 4 post)
#
#  Bullish: 12-candle ranging/slight-bear drift (all below fvgBot) →
#           Candle A (high=fvgBot) → Candle B (huge impulse) →
#           Candle C (low=fvgTop) → 4 post candles
#  Bearish: mirror image (all above fvgTop before impulse)
# =============================================================================
OLD_FVG_BLOCK = """  // -- FVG - Fair Value Gap
  // Classic 3-candle imbalance: candle A → huge impulse B → candle C
  // Gap = space between A.high (fvgBot) and C.low (fvgTop) for bullish,
  //        space between A.low (fvgTop) and C.high (fvgBot) for bearish
  if (indId === 'fvg') {"""

NEW_FVG_BLOCK = """  // -- FVG - Fair Value Gap
  // 19 candles: 12-candle context, 3-candle FVG formation (A/B/C), 4 post
  if (indId === 'fvg') {"""

# Just replace the comment header — keep the rest for now
# (full block replacement below)
content = content.replace(OLD_FVG_BLOCK, NEW_FVG_BLOCK, 1)

# ── Full FVG block ─────────────────────────────────────────────────────────
OLD_FVG = """  // -- FVG - Fair Value Gap
  // 19 candles: 12-candle context, 3-candle FVG formation (A/B/C), 4 post
  if (indId === 'fvg') {
    container.style.height = '160px';
    _lwcRender(container, (chartW) => {
      if (!window.LightweightCharts) { container.appendChild(_buildCondPreviewSVG(indId,condText,params,isDark,up,cross,sc,ct)); return; }
      const chart = LightweightCharts.createChart(container, {
        width:chartW,height:160,layout:{background:{color:bg},textColor:text},
        grid:{vertLines:{color:grid},horzLines:{color:grid}},
        rightPriceScale:{borderColor:'transparent',scaleMargins:{top:0.08,bottom:0.08}},
        timeScale:{borderColor:'transparent',visible:false},crosshair:{mode:0},
        handleScroll:false,handleScale:false,
        watermark:{visible:true,fontSize:11,horzAlign:'left',vertAlign:'top',color:text,text:'FVG - Fair Value Gap'}
      });
      const cs = chart.addCandlestickSeries({
        upColor:'#26a69a',downColor:'#ef5350',
        borderUpColor:'#26a69a',borderDownColor:'#ef5350',
        wickUpColor:isDark?'rgba(38,166,154,0.5)':'rgba(38,166,154,0.7)',
        wickDownColor:isDark?'rgba(239,83,80,0.5)':'rgba(239,83,80,0.7)',
        priceLineVisible:false,lastValueVisible:false,
      });
      const isMit=(params.entryMode==='mitigation')||ct.includes('retornar');
      const t0s=Math.floor(new Date('2024-01-02').getTime()/1000),BS=300;
      let fd,fvgTop,fvgBot;

      if(up){
        // Bullish FVG: A.high=fvgBot, C.low=fvgTop  (gap zone between them)
        fvgBot=101; fvgTop=107;
        fd=[
          // Context: 2 bearish candles building pressure
          {time:t0s,      open:106,high:107,low:103,close:104},
          {time:t0s+BS,   open:104,high:105,low:100,close:101},
          // [2] Candle A — high touches fvgBot=101, closes bearish (tight body)
          {time:t0s+2*BS, open:101,high:fvgBot,low:98,close:99},
          // [3] Candle B — HUGE bullish impulse; body leaves empty space above A.high
          {time:t0s+3*BS, open:99,high:119,low:98,close:116},
          // [4] Candle C — low = fvgTop=107, confirms the unmitigated gap
          {time:t0s+4*BS, open:116,high:120,low:fvgTop,close:118},
          // Continuation after impulse
          {time:t0s+5*BS, open:118,high:120,low:115,close:117},
          {time:t0s+6*BS, open:117,high:119,low:114,close:116},
        ];
        if(isMit){
          // Mitigation: price returns to fill the gap
          fd.push(
            {time:t0s+7*BS, open:116,high:117,low:112,close:113},
            {time:t0s+8*BS, open:113,high:114,low:fvgTop+1,close:108},
            // Touch of fvgTop and bounce — entry point
            {time:t0s+9*BS, open:108,high:114,low:fvgTop,close:113}
          );
        }
      }else{
        // Bearish FVG: A.low=fvgTop, C.high=fvgBot  (gap zone between them)
        fvgTop=103; fvgBot=97;
        fd=[
          // Context: 2 bullish candles building pressure
          {time:t0s,      open:96,high:99,low:95,close:98},
          {time:t0s+BS,   open:98,high:102,low:97,close:101},
          // [2] Candle A — low touches fvgTop=103, closes bullish (tight body)
          {time:t0s+2*BS, open:101,high:105,low:fvgTop,close:104},
          // [3] Candle B — HUGE bearish impulse; body leaves empty space below A.low
          {time:t0s+3*BS, open:104,high:105,low:83,close:86},
          // [4] Candle C — high = fvgBot=97, confirms the unmitigated gap
          {time:t0s+4*BS, open:86,high:fvgBot,low:83,close:84},
          // Continuation after impulse
          {time:t0s+5*BS, open:84,high:87,low:81,close:83},
          {time:t0s+6*BS, open:83,high:86,low:80,close:82},
        ];
        if(isMit){
          // Mitigation: price returns to fill the gap
          fd.push(
            {time:t0s+7*BS, open:82,high:86,low:81,close:85},
            {time:t0s+8*BS, open:85,high:92,low:84,close:91},
            // Touch of fvgBot from below and rejection — entry point
            {time:t0s+9*BS, open:91,high:fvgBot,low:87,close:88}
          );
        }
      }

      // Gap zone — drawn BEFORE cs so candles render on top
      // Zone spans from candle C (index 4) through all remaining candles
      const zoneStart = fd.slice(4);
      const zt = zoneStart.map(b=>b.time);
      const zc = up?'rgba(38,166,154,0.90)':'rgba(239,83,80,0.90)';
      const zf = up?'rgba(38,166,154,0.14)':'rgba(239,83,80,0.14)';
      // Upper boundary: AreaSeries fills downward from fvgTop, creating the zone shade
      chart.addAreaSeries({
        topColor:zf,bottomColor:zf,lineColor:zc,lineWidth:1.5,
        priceLineVisible:false,lastValueVisible:false,
      }).setData(zt.map(t=>({time:t,value:fvgTop})));
      // Lower boundary: dashed line at fvgBot
      chart.addLineSeries({
        color:zc,lineWidth:1.5,lineStyle:1,
        priceLineVisible:false,lastValueVisible:false,
      }).setData(zt.map(t=>({time:t,value:fvgBot})));

      // Label "FVG" on the gap zone (small label series at midpoint)
      const fvgMid=(fvgTop+fvgBot)/2;
      chart.addLineSeries({
        color:'transparent',lineWidth:0,
        priceLineVisible:false,lastValueVisible:false,
      }).setData([{time:zt[0],value:fvgMid}]);

      cs.setData(fd);

      // Entry marker
      const entryIdx = isMit ? fd.length-1 : 4;
      cs.setMarkers([{
        time:fd[entryIdx].time,
        position:up?'belowBar':'aboveBar',
        color:up?'#26a69a':'#ef5350',
        shape:up?'arrowUp':'arrowDown',
        text:isMit?'Retorno':'Entrada',
      }]);
      chart.timeScale().fitContent();
    });
    return container;
  }"""

NEW_FVG = """  // -- FVG - Fair Value Gap
  // 19 candles: 12-candle context, 3-candle FVG formation (A/B/C), 4 post
  if (indId === 'fvg') {
    container.style.height = '180px';
    _lwcRender(container, (chartW) => {
      if (!window.LightweightCharts) { container.appendChild(_buildCondPreviewSVG(indId,condText,params,isDark,up,cross,sc,ct)); return; }
      const chart = LightweightCharts.createChart(container, {
        width:chartW,height:180,layout:{background:{color:bg},textColor:text},
        grid:{vertLines:{color:grid},horzLines:{color:grid}},
        rightPriceScale:{borderColor:'transparent',scaleMargins:{top:0.10,bottom:0.08}},
        timeScale:{borderColor:'transparent',visible:false},crosshair:{mode:0},
        handleScroll:false,handleScale:false,
        watermark:{visible:true,fontSize:11,horzAlign:'left',vertAlign:'top',color:text,text:'FVG — Fair Value Gap'}
      });
      const isMit=(params.entryMode==='mitigation')||ct.includes('retornar');
      const t0s=Math.floor(new Date('2024-01-02').getTime()/1000),BS=86400;
      let fd,fvgTop,fvgBot,aIdx,cIdx;

      if(up){
        // Bullish FVG: A.high=fvgBot=102, C.low=fvgTop=109
        // Context: 12 candles of ranging/slight bear drift, all prices ≤ 102
        fvgBot=102; fvgTop=109; aIdx=12; cIdx=14;
        fd=[
          {time:t0s+ 0*BS,open:101,high:103,low: 99,close:100},
          {time:t0s+ 1*BS,open:100,high:102,low: 98,close: 99},
          {time:t0s+ 2*BS,open: 99,high:101,low: 97,close:100},
          {time:t0s+ 3*BS,open:100,high:102,low: 98,close: 99},
          {time:t0s+ 4*BS,open: 99,high:101,low: 97,close: 98},
          {time:t0s+ 5*BS,open: 98,high:100,low: 96,close: 99},
          {time:t0s+ 6*BS,open: 99,high:101,low: 97,close: 98},
          {time:t0s+ 7*BS,open: 98,high:100,low: 96,close: 99},
          {time:t0s+ 8*BS,open: 99,high:101,low: 97,close: 98},
          {time:t0s+ 9*BS,open: 98,high:100,low: 96,close: 97},
          {time:t0s+10*BS,open: 97,high: 99,low: 95,close: 98},
          {time:t0s+11*BS,open: 98,high:100,low: 96,close: 97},
          // [12=A] last bearish candle, high touches fvgBot=102 (ceiling of context range)
          {time:t0s+12*BS,open: 97,high:fvgBot,low: 96,close: 97},
          // [13=B] HUGE IMPULSE — leaves gap; open near 97, close at 117
          {time:t0s+13*BS,open: 97,high:120,low: 96,close:117},
          // [14=C] First post-impulse candle: low=fvgTop=109 (confirms gap above A.high)
          {time:t0s+14*BS,open:117,high:121,low:fvgTop,close:119},
          // Post: continuation
          {time:t0s+15*BS,open:119,high:122,low:117,close:120},
          {time:t0s+16*BS,open:120,high:122,low:117,close:118},
          {time:t0s+17*BS,open:118,high:121,low:116,close:119},
          {time:t0s+18*BS,open:119,high:121,low:116,close:120},
        ];
        if(isMit){
          fd[15]={time:t0s+15*BS,open:119,high:121,low:117,close:118};
          fd[16]={time:t0s+16*BS,open:118,high:120,low:114,close:115};
          fd[17]={time:t0s+17*BS,open:115,high:116,low:110,close:111};
          fd[18]={time:t0s+18*BS,open:111,high:113,low:fvgTop,close:112};
          fd.push({time:t0s+19*BS,open:112,high:116,low:fvgTop-1,close:115});
        }
      }else{
        // Bearish FVG: A.low=fvgTop=101, C.high=fvgBot=94
        // Context: 12 candles of ranging/slight bull drift, all prices ≥ 101
        fvgTop=101; fvgBot=94; aIdx=12; cIdx=14;
        fd=[
          {time:t0s+ 0*BS,open:102,high:104,low:100,close:103},
          {time:t0s+ 1*BS,open:103,high:105,low:101,close:102},
          {time:t0s+ 2*BS,open:102,high:104,low:100,close:103},
          {time:t0s+ 3*BS,open:103,high:105,low:101,close:102},
          {time:t0s+ 4*BS,open:102,high:104,low:100,close:103},
          {time:t0s+ 5*BS,open:103,high:105,low:101,close:104},
          {time:t0s+ 6*BS,open:104,high:106,low:102,close:103},
          {time:t0s+ 7*BS,open:103,high:105,low:101,close:102},
          {time:t0s+ 8*BS,open:102,high:104,low:100,close:103},
          {time:t0s+ 9*BS,open:103,high:105,low:101,close:104},
          {time:t0s+10*BS,open:104,high:106,low:102,close:103},
          {time:t0s+11*BS,open:103,high:105,low:101,close:102},
          // [12=A] last bullish candle, low touches fvgTop=101 (floor of context range)
          {time:t0s+12*BS,open:102,high:105,low:fvgTop,close:104},
          // [13=B] HUGE IMPULSE down — leaves gap; open near 104, close at 85
          {time:t0s+13*BS,open:104,high:105,low:82,close:85},
          // [14=C] First post-impulse candle: high=fvgBot=94 (confirms gap below A.low)
          {time:t0s+14*BS,open:85,high:fvgBot,low:82,close:83},
          // Post: continuation down
          {time:t0s+15*BS,open:83,high:86,low:81,close:82},
          {time:t0s+16*BS,open:82,high:85,low:80,close:81},
          {time:t0s+17*BS,open:81,high:84,low:79,close:82},
          {time:t0s+18*BS,open:82,high:84,low:79,close:80},
        ];
        if(isMit){
          fd[15]={time:t0s+15*BS,open:83,high:86,low:81,close:84};
          fd[16]={time:t0s+16*BS,open:84,high:88,low:83,close:87};
          fd[17]={time:t0s+17*BS,open:87,high:92,low:86,close:91};
          fd[18]={time:t0s+18*BS,open:91,high:fvgBot,low:88,close:90};
          fd.push({time:t0s+19*BS,open:90,high:fvgBot+1,low:86,close:87});
        }
      }

      // ── Zone fill drawn BEFORE candles (candles render on top) ──────────
      // Spans from candle C onwards — the CONFIRMED unmitigated gap region
      const zt = fd.slice(cIdx).map(b=>b.time);
      const zc = up?'rgba(38,166,154,0.85)':'rgba(239,83,80,0.85)';
      const zf = up?'rgba(38,166,154,0.14)':'rgba(239,83,80,0.14)';
      // Upper boundary (AreaSeries fills downward, creating the highlighted band)
      chart.addAreaSeries({
        topColor:zf,bottomColor:zf,lineColor:zc,lineWidth:1.5,
        priceLineVisible:false,lastValueVisible:false,
      }).setData(zt.map(t=>({time:t,value:fvgTop})));
      // Lower boundary (dashed line)
      chart.addLineSeries({
        color:zc,lineWidth:1.5,lineStyle:1,
        priceLineVisible:false,lastValueVisible:false,
      }).setData(zt.map(t=>({time:t,value:fvgBot})));

      // Candles on top
      const cs = chart.addCandlestickSeries({
        upColor:'#26a69a',downColor:'#ef5350',
        borderUpColor:'#26a69a',borderDownColor:'#ef5350',
        wickUpColor:isDark?'rgba(38,166,154,0.6)':'rgba(38,166,154,0.8)',
        wickDownColor:isDark?'rgba(239,83,80,0.6)':'rgba(239,83,80,0.8)',
        priceLineVisible:false,lastValueVisible:false,
      });
      cs.setData(fd);

      // Entry marker
      const entryIdx = isMit ? fd.length-1 : cIdx;
      cs.setMarkers([{
        time:fd[entryIdx].time,
        position:up?'belowBar':'aboveBar',
        color:up?'#26a69a':'#ef5350',
        shape:up?'arrowUp':'arrowDown',
        text:isMit?'Retorno':'Entrada',
      }]);
      chart.timeScale().fitContent();
    });
    return container;
  }"""

ok1 = OLD_FVG in content
content = content.replace(OLD_FVG, NEW_FVG, 1)
print('FVG:', 'OK' if ok1 else 'NOT FOUND')

# =============================================================================
# 2. BoS — Break of Structure  (19 candles)
#
#  Bullish: 6 context candles → swing HIGH at bsl (index 6) →
#           5-candle pullback → advancing recovery →
#           BoS break candle (index 16) → 2 follow-through
#  Bearish: mirror
# =============================================================================
OLD_BOS = """  // -- BoS - Break of Structure
  // Shows: swing HIGH/LOW formed → pullback → decisive break of that level
  if (indId === 'bos') {
    container.style.height = '160px';
    _lwcRender(container, (chartW) => {
      if (!window.LightweightCharts) { container.appendChild(_buildCondPreviewSVG(indId,condText,params,isDark,up,cross,sc,ct)); return; }
      const chart = LightweightCharts.createChart(container, {
        width:chartW,height:160,layout:{background:{color:bg},textColor:text},
        grid:{vertLines:{color:grid},horzLines:{color:grid}},
        rightPriceScale:{borderColor:'transparent',scaleMargins:{top:0.10,bottom:0.10}},
        timeScale:{borderColor:'transparent',visible:false},crosshair:{mode:0},
        handleScroll:false,handleScale:false,
        watermark:{visible:true,fontSize:11,horzAlign:'left',vertAlign:'top',color:text,text:'BoS - Break of Structure'}
      });
      const cs = chart.addCandlestickSeries({
        upColor:'#26a69a',downColor:'#ef5350',
        borderUpColor:'#26a69a',borderDownColor:'#ef5350',
        wickUpColor:isDark?'rgba(38,166,154,0.5)':'rgba(38,166,154,0.7)',
        wickDownColor:isDark?'rgba(239,83,80,0.5)':'rgba(239,83,80,0.7)',
        priceLineVisible:false,lastValueVisible:false,
      });
      const t0s=Math.floor(new Date('2024-01-02').getTime()/1000),BS=300;
      let bd,bsl;

      if(up){
        // Bullish BoS: price below bsl → swing HIGH at bsl → pullback → BREAKS ABOVE
        bsl=110;
        bd=[
          // Context: ranging / slight bearish
          {time:t0s,      open:104,high:107,low:103,close:105},
          {time:t0s+BS,   open:105,high:108,low:104,close:106},
          // [2] Swing HIGH forms — candle whose high = bsl
          {time:t0s+2*BS, open:106,high:bsl,low:105,close:107},
          // Pullback — price retreats from the swing high
          {time:t0s+3*BS, open:107,high:108,low:104,close:105},
          {time:t0s+4*BS, open:105,high:107,low:102,close:103},
          // Higher Low — structure improving
          {time:t0s+5*BS, open:103,high:106,low:101,close:105},
          {time:t0s+6*BS, open:105,high:108,low:103,close:107},
          // [7] BoS candle — CLOSES above bsl = confirmed break
          {time:t0s+7*BS, open:107,high:bsl+4,low:106,close:bsl+3},
          // Continuation
          {time:t0s+8*BS, open:bsl+3,high:bsl+6,low:bsl+1,close:bsl+5},
        ];
      }else{
        // Bearish BoS: price above bsl → swing LOW at bsl → rally → BREAKS BELOW
        bsl=93;
        bd=[
          // Context: ranging / slight bullish
          {time:t0s,      open:99,high:100,low:96,close:98},
          {time:t0s+BS,   open:98,high:100,low:95,close:97},
          // [2] Swing LOW forms — candle whose low = bsl
          {time:t0s+2*BS, open:97,high:98,low:bsl,close:96},
          // Rally — price bounces from the swing low
          {time:t0s+3*BS, open:96,high:99,low:95,close:98},
          {time:t0s+4*BS, open:98,high:101,low:97,close:100},
          // Lower High — structure weakening
          {time:t0s+5*BS, open:100,high:102,low:97,close:98},
          {time:t0s+6*BS, open:98,high:99,low:95,close:96},
          // [7] BoS candle — CLOSES below bsl = confirmed break
          {time:t0s+7*BS, open:96,high:97,low:bsl-4,close:bsl-3},
          // Continuation
          {time:t0s+8*BS, open:bsl-3,high:bsl-1,low:bsl-7,close:bsl-5},
        ];
      }

      cs.setData(bd);

      // Horizontal level from swing pivot to break candle
      const bt = bd.slice(2, 9).map(b=>b.time);
      chart.addLineSeries({
        color:'#F0A020',lineWidth:2,lineStyle:1,
        priceLineVisible:false,lastValueVisible:false,
      }).setData(bt.map(t=>({time:t,value:bsl})));

      cs.setMarkers([
        // Mark the swing HIGH/LOW that defines the structure level
        {time:bd[2].time, position:up?'aboveBar':'belowBar',
         color:'#F0A020', shape:'circle', text:up?'Topo':'Fundo'},
        // Mark the break candle — confirmed BoS
        {time:bd[7].time, position:up?'belowBar':'aboveBar',
         color:up?'#26a69a':'#ef5350', shape:up?'arrowUp':'arrowDown', text:'BoS ✓'},
      ]);
      chart.timeScale().fitContent();
    });
    return container;
  }"""

NEW_BOS = """  // -- BoS - Break of Structure  (19 candles)
  if (indId === 'bos') {
    container.style.height = '180px';
    _lwcRender(container, (chartW) => {
      if (!window.LightweightCharts) { container.appendChild(_buildCondPreviewSVG(indId,condText,params,isDark,up,cross,sc,ct)); return; }
      const chart = LightweightCharts.createChart(container, {
        width:chartW,height:180,layout:{background:{color:bg},textColor:text},
        grid:{vertLines:{color:grid},horzLines:{color:grid}},
        rightPriceScale:{borderColor:'transparent',scaleMargins:{top:0.10,bottom:0.10}},
        timeScale:{borderColor:'transparent',visible:false},crosshair:{mode:0},
        handleScroll:false,handleScale:false,
        watermark:{visible:true,fontSize:11,horzAlign:'left',vertAlign:'top',color:text,text:'BoS — Break of Structure'}
      });
      const t0s=Math.floor(new Date('2024-01-02').getTime()/1000),BS=86400;
      let bd,bsl,swingIdx,bosIdx;

      if(up){
        // Bullish BoS: ranging context → swing HIGH at bsl → pullback (HL) → BREAKS ABOVE bsl
        bsl=110; swingIdx=6; bosIdx=16;
        bd=[
          // Context: 6 ranging candles, prices stay below bsl
          {time:t0s+ 0*BS,open:104,high:107,low:103,close:106},
          {time:t0s+ 1*BS,open:106,high:108,low:104,close:105},
          {time:t0s+ 2*BS,open:105,high:107,low:103,close:106},
          {time:t0s+ 3*BS,open:106,high:109,low:105,close:107},
          {time:t0s+ 4*BS,open:107,high:109,low:105,close:106},
          {time:t0s+ 5*BS,open:106,high:108,low:104,close:107},
          // [6] Swing HIGH — high = bsl=110, bearish close (rejection)
          {time:t0s+ 6*BS,open:107,high:bsl,low:106,close:107},
          // Pullback from swing high (5 candles)
          {time:t0s+ 7*BS,open:107,high:108,low:105,close:106},
          {time:t0s+ 8*BS,open:106,high:107,low:103,close:104},
          {time:t0s+ 9*BS,open:104,high:106,low:102,close:103},
          {time:t0s+10*BS,open:103,high:105,low:101,close:103},
          // Higher Low forms — momentum shift
          {time:t0s+11*BS,open:103,high:106,low:102,close:105},
          // Advance begins
          {time:t0s+12*BS,open:105,high:107,low:103,close:106},
          {time:t0s+13*BS,open:106,high:108,low:104,close:107},
          {time:t0s+14*BS,open:107,high:109,low:105,close:108},
          {time:t0s+15*BS,open:108,high:110,low:106,close:109},
          // [16] BoS — closes ABOVE bsl=110 (confirmed break)
          {time:t0s+16*BS,open:109,high:bsl+4,low:108,close:bsl+3},
          // Follow-through
          {time:t0s+17*BS,open:bsl+3,high:bsl+6,low:bsl+1,close:bsl+5},
          {time:t0s+18*BS,open:bsl+5,high:bsl+8,low:bsl+3,close:bsl+7},
        ];
      }else{
        // Bearish BoS: ranging context → swing LOW at bsl → rally (LH) → BREAKS BELOW bsl
        bsl=93; swingIdx=6; bosIdx=16;
        bd=[
          // Context: 6 ranging candles, prices stay above bsl
          {time:t0s+ 0*BS,open: 99,high:102,low: 98,close: 97},
          {time:t0s+ 1*BS,open: 97,high: 99,low: 95,close: 98},
          {time:t0s+ 2*BS,open: 98,high:100,low: 96,close: 97},
          {time:t0s+ 3*BS,open: 97,high: 99,low: 94,close: 96},
          {time:t0s+ 4*BS,open: 96,high: 98,low: 94,close: 97},
          {time:t0s+ 5*BS,open: 97,high: 99,low: 95,close: 96},
          // [6] Swing LOW — low = bsl=93, bullish close (bounce)
          {time:t0s+ 6*BS,open: 96,high: 97,low:bsl,close: 96},
          // Rally from swing low (5 candles)
          {time:t0s+ 7*BS,open: 96,high: 98,low: 95,close: 97},
          {time:t0s+ 8*BS,open: 97,high: 99,low: 95,close: 98},
          {time:t0s+ 9*BS,open: 98,high:101,low: 97,close:100},
          {time:t0s+10*BS,open:100,high:102,low: 98,close:100},
          // Lower High forms — momentum failing
          {time:t0s+11*BS,open:100,high:101,low: 97,close: 98},
          // Decline begins
          {time:t0s+12*BS,open: 98,high:100,low: 96,close: 97},
          {time:t0s+13*BS,open: 97,high: 99,low: 95,close: 96},
          {time:t0s+14*BS,open: 96,high: 98,low: 94,close: 95},
          {time:t0s+15*BS,open: 95,high: 97,low: 93,close: 94},
          // [16] BoS — closes BELOW bsl=93 (confirmed break)
          {time:t0s+16*BS,open: 94,high: 95,low:bsl-4,close:bsl-3},
          // Follow-through
          {time:t0s+17*BS,open:bsl-3,high:bsl-1,low:bsl-6,close:bsl-5},
          {time:t0s+18*BS,open:bsl-5,high:bsl-3,low:bsl-8,close:bsl-7},
        ];
      }

      // Level line: swing pivot → break candle
      const bt = bd.slice(swingIdx, bosIdx+1).map(b=>b.time);
      chart.addLineSeries({
        color:'#F0A020',lineWidth:2,lineStyle:1,
        priceLineVisible:false,lastValueVisible:false,
      }).setData(bt.map(t=>({time:t,value:bsl})));

      const cs = chart.addCandlestickSeries({
        upColor:'#26a69a',downColor:'#ef5350',
        borderUpColor:'#26a69a',borderDownColor:'#ef5350',
        wickUpColor:isDark?'rgba(38,166,154,0.6)':'rgba(38,166,154,0.8)',
        wickDownColor:isDark?'rgba(239,83,80,0.6)':'rgba(239,83,80,0.8)',
        priceLineVisible:false,lastValueVisible:false,
      });
      cs.setData(bd);
      cs.setMarkers([
        {time:bd[swingIdx].time, position:up?'aboveBar':'belowBar',
         color:'#F0A020', shape:'circle', text:up?'Topo':'Fundo'},
        {time:bd[bosIdx].time, position:up?'belowBar':'aboveBar',
         color:up?'#26a69a':'#ef5350', shape:up?'arrowUp':'arrowDown', text:'BoS'},
      ]);
      chart.timeScale().fitContent();
    });
    return container;
  }"""

ok2 = OLD_BOS in content
content = content.replace(OLD_BOS, NEW_BOS, 1)
print('BoS:', 'OK' if ok2 else 'NOT FOUND')

# =============================================================================
# 3. CHoCH — Change of Character  (17 candles)
#
#  Bullish CHoCH: 4 candles downtrend context → swing HIGH (LH1, above chlvl)
#    → LL1 → LH2=chlvl (lower high, THIS is the key level) →
#    LL2 → break ABOVE chlvl (CHoCH!) → 2 follow-through
#
#  Bearish CHoCH: mirror (uptrend → HL1 below chlvl → HH1 →
#    HL2=chlvl → HH2 → break BELOW chlvl)
# =============================================================================
OLD_CHOCH = """  // -- CHoCH - Change of Character
  // Shows the FIRST break against the prevailing trend:
  //  Bullish CHoCH: downtrend (LH→LL→LH) then breaks the last LH
  //  Bearish CHoCH: uptrend  (HL→HH→HL) then breaks the last HL
  if (indId === 'choch') {
    container.style.height = '160px';
    _lwcRender(container, (chartW) => {
      if (!window.LightweightCharts) { container.appendChild(_buildCondPreviewSVG(indId,condText,params,isDark,up,cross,sc,ct)); return; }
      const chart = LightweightCharts.createChart(container, {
        width:chartW,height:160,layout:{background:{color:bg},textColor:text},
        grid:{vertLines:{color:grid},horzLines:{color:grid}},
        rightPriceScale:{borderColor:'transparent',scaleMargins:{top:0.10,bottom:0.10}},
        timeScale:{borderColor:'transparent',visible:false},crosshair:{mode:0},
        handleScroll:false,handleScale:false,
        watermark:{visible:true,fontSize:11,horzAlign:'left',vertAlign:'top',color:text,text:'CHoCH - Change of Character'}
      });
      const cs = chart.addCandlestickSeries({
        upColor:'#26a69a',downColor:'#ef5350',
        borderUpColor:'#26a69a',borderDownColor:'#ef5350',
        wickUpColor:isDark?'rgba(38,166,154,0.5)':'rgba(38,166,154,0.7)',
        wickDownColor:isDark?'rgba(239,83,80,0.5)':'rgba(239,83,80,0.7)',
        priceLineVisible:false,lastValueVisible:false,
      });
      const t0s=Math.floor(new Date('2024-01-02').getTime()/1000),BS=300;
      let cd2,chlvl,brk;

      if(up){
        // Bullish CHoCH: downtrend → breaks LAST Lower High
        // LH1 (high candle) → LL1 → LH2=chlvl (lower than LH1) → LL2 → CHoCH break
        chlvl=111; // last lower high
        cd2=[
          // Downtrend context: first swing high (LH1 > chlvl)
          {time:t0s,      open:116,high:117,low:112,close:113},  // LH1 area
          {time:t0s+BS,   open:113,high:114,low:109,close:110},  // impulse down
          {time:t0s+2*BS, open:110,high:111,low:106,close:108},  // LL1
          // [3] Lower High forms at chlvl — the key level
          {time:t0s+3*BS, open:108,high:chlvl,low:107,close:109},  // LH2 = chlvl
          // Continuation down (lower low)
          {time:t0s+4*BS, open:109,high:110,low:105,close:106},
          {time:t0s+5*BS, open:106,high:108,low:103,close:104},  // LL2
          // Weak recovery (lower momentum)
          {time:t0s+6*BS, open:104,high:108,low:103,close:107},
          // [7] CHoCH: closes ABOVE chlvl = first break of downtrend
          {time:t0s+7*BS, open:107,high:chlvl+3,low:106,close:chlvl+2},
          // Confirmation / follow-through
          {time:t0s+8*BS, open:chlvl+2,high:chlvl+5,low:chlvl+1,close:chlvl+4},
        ];
        brk=7;
      }else{
        // Bearish CHoCH: uptrend → breaks LAST Higher Low
        // HL1 (low candle) → HH1 → HL2=chlvl (higher than HL1) → HH2 → CHoCH break
        chlvl=96; // last higher low
        cd2=[
          // Uptrend context: first swing low (HL1 < chlvl)
          {time:t0s,      open:91,high:95,low:90,close:94},  // HL1 area
          {time:t0s+BS,   open:94,high:98,low:93,close:97},  // impulse up
          {time:t0s+2*BS, open:97,high:101,low:96,close:100}, // HH1
          // [3] Higher Low forms at chlvl — the key level
          {time:t0s+3*BS, open:100,high:101,low:chlvl,close:97}, // HL2 = chlvl
          // Continuation up (higher high)
          {time:t0s+4*BS, open:97,high:101,low:96,close:100},
          {time:t0s+5*BS, open:100,high:104,low:99,close:103}, // HH2
          // Weak pullback (lower momentum)
          {time:t0s+6*BS, open:103,high:104,low:99,close:100},
          // [7] CHoCH: closes BELOW chlvl = first break of uptrend
          {time:t0s+7*BS, open:100,high:101,low:chlvl-3,close:chlvl-2},
          // Confirmation / follow-through
          {time:t0s+8*BS, open:chlvl-2,high:chlvl-1,low:chlvl-5,close:chlvl-4},
        ];
        brk=7;
      }

      cs.setData(cd2);

      // Level line from the LH/HL pivot through the break candle
      const ct2 = cd2.slice(3, brk+1).map(b=>b.time);
      chart.addLineSeries({
        color:'#EF4444',lineWidth:2,lineStyle:1,
        priceLineVisible:false,lastValueVisible:false,
      }).setData(ct2.map(t=>({time:t,value:chlvl})));

      cs.setMarkers([
        // Mark the Lower High / Higher Low that defines the CHoCH level
        {time:cd2[3].time, position:up?'aboveBar':'belowBar',
         color:'#EF4444', shape:'circle', text:up?'LH':'HL'},
        // Mark the CHoCH break candle
        {time:cd2[brk].time, position:up?'belowBar':'aboveBar',
         color:up?'#26a69a':'#ef5350', shape:up?'arrowUp':'arrowDown', text:'CHoCH ✓'},
      ]);
      chart.timeScale().fitContent();
    });
    return container;
  }"""

NEW_CHOCH = """  // -- CHoCH - Change of Character  (17 candles)
  if (indId === 'choch') {
    container.style.height = '180px';
    _lwcRender(container, (chartW) => {
      if (!window.LightweightCharts) { container.appendChild(_buildCondPreviewSVG(indId,condText,params,isDark,up,cross,sc,ct)); return; }
      const chart = LightweightCharts.createChart(container, {
        width:chartW,height:180,layout:{background:{color:bg},textColor:text},
        grid:{vertLines:{color:grid},horzLines:{color:grid}},
        rightPriceScale:{borderColor:'transparent',scaleMargins:{top:0.10,bottom:0.10}},
        timeScale:{borderColor:'transparent',visible:false},crosshair:{mode:0},
        handleScroll:false,handleScale:false,
        watermark:{visible:true,fontSize:11,horzAlign:'left',vertAlign:'top',color:text,text:'CHoCH — Change of Character'}
      });
      const t0s=Math.floor(new Date('2024-01-02').getTime()/1000),BS=86400;
      let cd2,chlvl,lhIdx,bosIdx;

      if(up){
        // Bullish CHoCH: clear downtrend (LH1→LL1→LH2→LL2) → breaks ABOVE last LH (chlvl)
        // LH1 > chlvl (higher), LH2 = chlvl (lower high = CHoCH level)
        chlvl=112; lhIdx=6; bosIdx=14;
        cd2=[
          // LH1 zone: initial high > chlvl — establishes the downtrend
          {time:t0s+ 0*BS,open:117,high:119,low:115,close:116},
          {time:t0s+ 1*BS,open:116,high:117,low:113,close:114},
          // Impulse down to LL1
          {time:t0s+ 2*BS,open:114,high:115,low:110,close:111},
          {time:t0s+ 3*BS,open:111,high:112,low:108,close:109},  // LL1
          // Dead-cat bounce toward LH2
          {time:t0s+ 4*BS,open:109,high:111,low:108,close:110},
          {time:t0s+ 5*BS,open:110,high:112,low:109,close:111},
          // [6] LH2 = chlvl: lower high — downtrend intact, THIS is the key level
          {time:t0s+ 6*BS,open:111,high:chlvl,low:110,close:111},
          // Continuation down to LL2 (lower than LL1)
          {time:t0s+ 7*BS,open:111,high:112,low:108,close:109},
          {time:t0s+ 8*BS,open:109,high:110,low:106,close:107},
          {time:t0s+ 9*BS,open:107,high:109,low:105,close:106},  // LL2
          // Reversal momentum building — small bullish candles
          {time:t0s+10*BS,open:106,high:108,low:105,close:107},
          {time:t0s+11*BS,open:107,high:109,low:106,close:108},
          {time:t0s+12*BS,open:108,high:110,low:107,close:109},
          {time:t0s+13*BS,open:109,high:111,low:108,close:110},
          // [14] CHoCH — closes ABOVE chlvl=112 (first break of downtrend)
          {time:t0s+14*BS,open:110,high:chlvl+3,low:109,close:chlvl+2},
          // Follow-through
          {time:t0s+15*BS,open:chlvl+2,high:chlvl+5,low:chlvl+1,close:chlvl+4},
          {time:t0s+16*BS,open:chlvl+4,high:chlvl+7,low:chlvl+2,close:chlvl+6},
        ];
      }else{
        // Bearish CHoCH: clear uptrend (HL1→HH1→HL2→HH2) → breaks BELOW last HL (chlvl)
        chlvl=96; lhIdx=6; bosIdx=14;
        cd2=[
          // HL1 zone: initial low < chlvl — establishes uptrend
          {time:t0s+ 0*BS,open:90,high:92,low:88,close:91},
          {time:t0s+ 1*BS,open:91,high:93,low:89,close:92},
          // Impulse up to HH1
          {time:t0s+ 2*BS,open:92,high:96,low:91,close:95},
          {time:t0s+ 3*BS,open:95,high:98,low:94,close:97},  // HH1
          // Pullback toward HL2
          {time:t0s+ 4*BS,open:97,high:99,low:95,close:96},
          {time:t0s+ 5*BS,open:96,high:98,low:95,close:97},
          // [6] HL2 = chlvl: higher low — uptrend intact, THIS is the key level
          {time:t0s+ 6*BS,open:97,high:98,low:chlvl,close:97},
          // Continuation up to HH2 (higher than HH1)
          {time:t0s+ 7*BS,open:97,high:100,low:96,close:99},
          {time:t0s+ 8*BS,open:99,high:102,low:98,close:101},
          {time:t0s+ 9*BS,open:101,high:104,low:100,close:102},  // HH2
          // Reversal momentum building — small bearish candles
          {time:t0s+10*BS,open:102,high:103,low:100,close:101},
          {time:t0s+11*BS,open:101,high:102,low: 99,close:100},
          {time:t0s+12*BS,open:100,high:101,low: 98,close: 99},
          {time:t0s+13*BS,open: 99,high:100,low: 97,close: 98},
          // [14] CHoCH — closes BELOW chlvl=96 (first break of uptrend)
          {time:t0s+14*BS,open: 98,high: 99,low:chlvl-3,close:chlvl-2},
          // Follow-through
          {time:t0s+15*BS,open:chlvl-2,high:chlvl-1,low:chlvl-5,close:chlvl-4},
          {time:t0s+16*BS,open:chlvl-4,high:chlvl-2,low:chlvl-7,close:chlvl-6},
        ];
      }

      // Level line: from LH2/HL2 pivot → CHoCH break candle
      const ct2 = cd2.slice(lhIdx, bosIdx+1).map(b=>b.time);
      chart.addLineSeries({
        color:'#EF4444',lineWidth:2,lineStyle:1,
        priceLineVisible:false,lastValueVisible:false,
      }).setData(ct2.map(t=>({time:t,value:chlvl})));

      const cs = chart.addCandlestickSeries({
        upColor:'#26a69a',downColor:'#ef5350',
        borderUpColor:'#26a69a',borderDownColor:'#ef5350',
        wickUpColor:isDark?'rgba(38,166,154,0.6)':'rgba(38,166,154,0.8)',
        wickDownColor:isDark?'rgba(239,83,80,0.6)':'rgba(239,83,80,0.8)',
        priceLineVisible:false,lastValueVisible:false,
      });
      cs.setData(cd2);
      cs.setMarkers([
        {time:cd2[lhIdx].time, position:up?'aboveBar':'belowBar',
         color:'#EF4444', shape:'circle', text:up?'LH':'HL'},
        {time:cd2[bosIdx].time, position:up?'belowBar':'aboveBar',
         color:up?'#26a69a':'#ef5350', shape:up?'arrowUp':'arrowDown', text:'CHoCH'},
      ]);
      chart.timeScale().fitContent();
    });
    return container;
  }"""

ok3 = OLD_CHOCH in content
content = content.replace(OLD_CHOCH, NEW_CHOCH, 1)
print('CHoCH:', 'OK' if ok3 else 'NOT FOUND')

# =============================================================================
# 4. Sweep — Liquidity Sweep  (16 candles)
#
#  5 approach candles → 3 equal lows/highs (LIQUIDITY POOL) →
#  PIN BAR (sweep candle): wick goes far through level, body closes
#  back on the correct side → 7 reversal + continuation candles
# =============================================================================
OLD_SWEEP = """  // -- SWEEP / GRAB - Liquidity Sweep
  // Equal lows/highs form a liquidity pool → ONE pin-bar candle spikes
  // THROUGH the level (hunting stops) then closes BACK on the correct
  // side → the sweep is the long wick; reversal follows immediately.
  if (indId === 'sweep' || indId === 'grab') {
    container.style.height = '160px';
    _lwcRender(container, (chartW) => {
      if (!window.LightweightCharts) { container.appendChild(_buildCondPreviewSVG(indId,condText,params,isDark,up,cross,sc,ct)); return; }
      const chart = LightweightCharts.createChart(container, {
        width:chartW,height:160,layout:{background:{color:bg},textColor:text},
        grid:{vertLines:{color:grid},horzLines:{color:grid}},
        rightPriceScale:{borderColor:'transparent',scaleMargins:{top:0.12,bottom:0.12}},
        timeScale:{borderColor:'transparent',visible:false},crosshair:{mode:0},
        handleScroll:false,handleScale:false,
        watermark:{visible:true,fontSize:11,horzAlign:'left',vertAlign:'top',color:text,text:indId==='grab'?'Grab de Liquidez':'Sweep de Liquidez'}
      });
      const cs = chart.addCandlestickSeries({
        upColor:'#26a69a',downColor:'#ef5350',
        borderUpColor:'#26a69a',borderDownColor:'#ef5350',
        wickUpColor:isDark?'rgba(38,166,154,0.5)':'rgba(38,166,154,0.7)',
        wickDownColor:isDark?'rgba(239,83,80,0.5)':'rgba(239,83,80,0.7)',
        priceLineVisible:false,lastValueVisible:false,
      });
      const t0s=Math.floor(new Date('2024-01-02').getTime()/1000),BS=300;
      let sd,slvl,swpi,revi;

      if(up){
        // Bullish sweep: equal LOWS form liquidity → spike BELOW level →
        //   pin bar (hammer) closes ABOVE slvl → reversal up
        slvl=96; swpi=4; revi=5;
        sd=[
          // Approach: slight drift toward support
          {time:t0s,      open:103,high:105,low:100,close:101},
          {time:t0s+BS,   open:101,high:103,low:slvl,close:99},   // 1st touch
          {time:t0s+2*BS, open:99, high:102,low:slvl,close:100},  // 2nd touch (equal low)
          {time:t0s+3*BS, open:100,high:103,low:slvl,close:101},  // 3rd touch (equal low)
          // [4] SWEEP candle — PIN BAR: wick dips FAR below slvl, closes back above
          //     long lower wick = liquidity grabbed below equal lows
          {time:t0s+4*BS, open:100,high:101,low:slvl-7,close:slvl+1},
          // [5] Reversal confirmation — strong bullish candle
          {time:t0s+5*BS, open:slvl+1,high:slvl+8, low:slvl,  close:slvl+7},
          // Continuation
          {time:t0s+6*BS, open:slvl+7,high:slvl+12,low:slvl+5,close:slvl+11},
          {time:t0s+7*BS, open:slvl+11,high:slvl+15,low:slvl+9,close:slvl+14},
        ];
      }else{
        // Bearish sweep: equal HIGHS form liquidity → spike ABOVE level →
        //   shooting star closes BELOW slvl → reversal down
        slvl=106; swpi=4; revi=5;
        sd=[
          // Approach: slight drift toward resistance
          {time:t0s,      open:99, high:102,low:97, close:101},
          {time:t0s+BS,   open:101,high:slvl,low:99, close:103},  // 1st touch
          {time:t0s+2*BS, open:103,high:slvl,low:100,close:102},  // 2nd touch (equal high)
          {time:t0s+3*BS, open:102,high:slvl,low:100,close:103},  // 3rd touch (equal high)
          // [4] SWEEP candle — SHOOTING STAR: wick spikes FAR above slvl, closes back below
          //     long upper wick = liquidity grabbed above equal highs
          {time:t0s+4*BS, open:103,high:slvl+7,low:102,close:slvl-1},
          // [5] Reversal confirmation — strong bearish candle
          {time:t0s+5*BS, open:slvl-1,high:slvl,   low:slvl-8, close:slvl-7},
          // Continuation
          {time:t0s+6*BS, open:slvl-7,high:slvl-5, low:slvl-12,close:slvl-11},
          {time:t0s+7*BS, open:slvl-11,high:slvl-9,low:slvl-15,close:slvl-14},
        ];
      }

      cs.setData(sd);

      // Level line across the consolidation zone (touches 1–3 + sweep candle)
      const st = sd.slice(1, swpi+1).map(b=>b.time);
      chart.addLineSeries({
        color:'#F0A020',lineWidth:2,lineStyle:1,
        priceLineVisible:false,lastValueVisible:false,
      }).setData(st.map(t=>({time:t,value:slvl})));

      cs.setMarkers([
        // Sweep candle: red marker on the spike side
        {time:sd[swpi].time,
         position:up?'belowBar':'aboveBar',
         color:'#ef5350', shape:up?'arrowDown':'arrowUp', text:'Sweep'},
        // Reversal: green arrow in the reversal direction
        {time:sd[revi].time,
         position:up?'belowBar':'aboveBar',
         color:'#26a69a', shape:up?'arrowUp':'arrowDown', text:'Reversão'},
      ]);
      chart.timeScale().fitContent();
    });
    return container;
  }"""

NEW_SWEEP = """  // -- SWEEP / GRAB - Liquidity Sweep  (16 candles)
  if (indId === 'sweep' || indId === 'grab') {
    container.style.height = '180px';
    _lwcRender(container, (chartW) => {
      if (!window.LightweightCharts) { container.appendChild(_buildCondPreviewSVG(indId,condText,params,isDark,up,cross,sc,ct)); return; }
      const chart = LightweightCharts.createChart(container, {
        width:chartW,height:180,layout:{background:{color:bg},textColor:text},
        grid:{vertLines:{color:grid},horzLines:{color:grid}},
        rightPriceScale:{borderColor:'transparent',scaleMargins:{top:0.12,bottom:0.12}},
        timeScale:{borderColor:'transparent',visible:false},crosshair:{mode:0},
        handleScroll:false,handleScale:false,
        watermark:{visible:true,fontSize:11,horzAlign:'left',vertAlign:'top',color:text,text:indId==='grab'?'Grab de Liquidez':'Sweep de Liquidez'}
      });
      const t0s=Math.floor(new Date('2024-01-02').getTime()/1000),BS=86400;
      let sd,slvl,swpi,revi;

      if(up){
        // Bullish sweep: 5 approach → 3 equal LOWS (liquidity pool) →
        //   HAMMER pin bar (wick far below slvl, body closes above slvl) → reversal
        slvl=96; swpi=8; revi=9;
        sd=[
          // Approach: gentle drift down toward support zone
          {time:t0s+ 0*BS,open:104,high:106,low:102,close:103},
          {time:t0s+ 1*BS,open:103,high:105,low:101,close:102},
          {time:t0s+ 2*BS,open:102,high:104,low:100,close:101},
          {time:t0s+ 3*BS,open:101,high:103,low: 99,close:100},
          {time:t0s+ 4*BS,open:100,high:102,low: 98,close: 99},
          // Equal lows — liquidity pool builds (3 touches of slvl=96)
          {time:t0s+ 5*BS,open: 99,high:101,low:slvl,close: 98},   // 1st touch
          {time:t0s+ 6*BS,open: 98,high:100,low:slvl,close: 99},   // 2nd equal low
          {time:t0s+ 7*BS,open: 99,high:101,low:slvl,close: 98},   // 3rd equal low
          // [8] SWEEP — HAMMER: tiny body above slvl, wick reaches 8pts BELOW slvl
          //     This candle grabs all the stop losses below the equal lows
          {time:t0s+ 8*BS,open: 97,high: 98,low:slvl-8,close:slvl+1},
          // [9] Strong bullish reversal — closes well above slvl
          {time:t0s+ 9*BS,open:slvl+1,high:slvl+7, low:slvl-1,close:slvl+6},
          // Continuation up
          {time:t0s+10*BS,open:slvl+6, high:slvl+10,low:slvl+4, close:slvl+9},
          {time:t0s+11*BS,open:slvl+9, high:slvl+13,low:slvl+7, close:slvl+12},
          {time:t0s+12*BS,open:slvl+12,high:slvl+15,low:slvl+10,close:slvl+11},
          {time:t0s+13*BS,open:slvl+11,high:slvl+15,low:slvl+ 9,close:slvl+14},
          {time:t0s+14*BS,open:slvl+14,high:slvl+18,low:slvl+12,close:slvl+17},
          {time:t0s+15*BS,open:slvl+17,high:slvl+20,low:slvl+15,close:slvl+19},
        ];
      }else{
        // Bearish sweep: 5 approach → 3 equal HIGHS (liquidity pool) →
        //   SHOOTING STAR pin bar (wick far above slvl, body closes below slvl) → reversal
        slvl=106; swpi=8; revi=9;
        sd=[
          // Approach: gentle drift up toward resistance zone
          {time:t0s+ 0*BS,open: 98,high:100,low: 96,close: 99},
          {time:t0s+ 1*BS,open: 99,high:101,low: 97,close:100},
          {time:t0s+ 2*BS,open:100,high:102,low: 98,close:101},
          {time:t0s+ 3*BS,open:101,high:103,low: 99,close:102},
          {time:t0s+ 4*BS,open:102,high:104,low:100,close:103},
          // Equal highs — liquidity pool builds (3 touches of slvl=106)
          {time:t0s+ 5*BS,open:103,high:slvl,low:101,close:104},   // 1st touch
          {time:t0s+ 6*BS,open:104,high:slvl,low:102,close:103},   // 2nd equal high
          {time:t0s+ 7*BS,open:103,high:slvl,low:101,close:104},   // 3rd equal high
          // [8] SWEEP — SHOOTING STAR: tiny body below slvl, wick reaches 8pts ABOVE slvl
          //     Grabs all the stop losses above the equal highs
          {time:t0s+ 8*BS,open:105,high:slvl+8,low:104,close:slvl-1},
          // [9] Strong bearish reversal — closes well below slvl
          {time:t0s+ 9*BS,open:slvl-1,high:slvl+1,low:slvl-7,close:slvl-6},
          // Continuation down
          {time:t0s+10*BS,open:slvl-6, high:slvl-2, low:slvl-10,close:slvl-9},
          {time:t0s+11*BS,open:slvl-9, high:slvl-5, low:slvl-13,close:slvl-12},
          {time:t0s+12*BS,open:slvl-12,high:slvl- 9,low:slvl-15,close:slvl-11},
          {time:t0s+13*BS,open:slvl-11,high:slvl- 8,low:slvl-15,close:slvl-14},
          {time:t0s+14*BS,open:slvl-14,high:slvl-10,low:slvl-18,close:slvl-17},
          {time:t0s+15*BS,open:slvl-17,high:slvl-13,low:slvl-20,close:slvl-19},
        ];
      }

      // Level line across ALL equal lows/highs + sweep candle
      const st = sd.slice(5, swpi+1).map(b=>b.time);
      chart.addLineSeries({
        color:'#F0A020',lineWidth:2,lineStyle:1,
        priceLineVisible:false,lastValueVisible:false,
      }).setData(st.map(t=>({time:t,value:slvl})));

      const cs = chart.addCandlestickSeries({
        upColor:'#26a69a',downColor:'#ef5350',
        borderUpColor:'#26a69a',borderDownColor:'#ef5350',
        wickUpColor:isDark?'rgba(38,166,154,0.6)':'rgba(38,166,154,0.8)',
        wickDownColor:isDark?'rgba(239,83,80,0.6)':'rgba(239,83,80,0.8)',
        priceLineVisible:false,lastValueVisible:false,
      });
      cs.setData(sd);
      cs.setMarkers([
        {time:sd[swpi].time,
         position:up?'belowBar':'aboveBar',
         color:'#ef5350', shape:up?'arrowDown':'arrowUp', text:'Sweep'},
        {time:sd[revi].time,
         position:up?'belowBar':'aboveBar',
         color:'#26a69a', shape:up?'arrowUp':'arrowDown', text:'Reversão'},
      ]);
      chart.timeScale().fitContent();
    });
    return container;
  }"""

ok4 = OLD_SWEEP in content
content = content.replace(OLD_SWEEP, NEW_SWEEP, 1)
print('Sweep:', 'OK' if ok4 else 'NOT FOUND')

# =============================================================================
# Write back
# =============================================================================
with open(FPATH, 'w', encoding='utf-8') as f:
    f.write(content)
print('File written:', len(content), 'chars')
print('patch_fix3 DONE')

#!/usr/bin/env python3
# patch_fix2.py — Redesign SMC candle data for visual fidelity to each pattern

FPATH = 'C:/Users/Clayton Barros/AppData/Local/Temp/backtest-pro/app.html'
with open(FPATH, 'r', encoding='utf-8') as f:
    content = f.read()

# ============================================================
# Helper: standard CS options block (already has priceLineVisible
# added by patch_fix.py — we recreate it cleanly inline)
# ============================================================
CS_OPTS = (
    "      const cs = chart.addCandlestickSeries({\n"
    "        upColor:'#26a69a',downColor:'#ef5350',\n"
    "        borderUpColor:'#26a69a',borderDownColor:'#ef5350',\n"
    "        wickUpColor:isDark?'rgba(38,166,154,0.5)':'rgba(38,166,154,0.7)',\n"
    "        wickDownColor:isDark?'rgba(239,83,80,0.5)':'rgba(239,83,80,0.7)',\n"
    "        priceLineVisible:false,lastValueVisible:false,\n"
    "      });\n"
)

# ============================================================
# 1. FVG — rebuild candle data to show the classic 3-candle gap
#
#  Bullish FVG: context down → candle A (fvgBot=A.high) →
#               candle B (huge impulse UP) →
#               candle C (fvgTop=C.low) → continuation
#  Bearish FVG: context up → candle A (fvgTop=A.low) →
#               candle B (huge impulse DOWN) →
#               candle C (fvgBot=C.high) → continuation
#
#  Zone fill (AreaSeries) from t of candle C onwards so the GAP
#  region is clearly highlighted with NO spurious lines before it.
# ============================================================
OLD_FVG = """\
  // -- FVG - Fair Value Gap
  if (indId === 'fvg') {
    container.style.height = '160px';
    _lwcRender(container, (chartW) => {
      if (!window.LightweightCharts) { container.appendChild(_buildCondPreviewSVG(indId,condText,params,isDark,up,cross,sc,ct)); return; }
      const chart = LightweightCharts.createChart(container, {
        width:chartW,height:160,layout:{background:{color:bg},textColor:text},
        grid:{vertLines:{color:grid},horzLines:{color:grid}},
        rightPriceScale:{borderColor:'transparent',scaleMargins:{top:0.08,bottom:0.08}},
        timeScale:{borderColor:'transparent',visible:false},crosshair:{mode:1},
        handleScroll:false,handleScale:false,
        watermark:{visible:true,fontSize:11,horzAlign:'left',vertAlign:'top',color:text,text:'FVG - Fair Value Gap'}
      });
      const cs = chart.addCandlestickSeries({
        upColor:'#26a69a',downColor:'#ef5350',borderUpColor:'#26a69a',borderDownColor:'#ef5350',
        wickUpColor:isDark?'rgba(38,166,154,0.5)':'rgba(38,166,154,0.7)',
        wickDownColor:isDark?'rgba(239,83,80,0.5)':'rgba(239,83,80,0.7)',
      priceLineVisible:false,lastValueVisible:false,
      });
      const isMit=(params.entryMode==='mitigation')||ct.includes('retornar');
      const t0s=Math.floor(new Date('2024-01-02').getTime()/1000),BS=300;
      let fd,fvgTop,fvgBot;
      if(up){
        fvgBot=102;fvgTop=108;
        fd=[
          {time:t0s,open:101,high:103,low:98,close:99},{time:t0s+BS,open:100,high:102,low:97,close:98},
          {time:t0s+2*BS,open:99,high:101,low:96,close:100},{time:t0s+3*BS,open:100,high:fvgBot,low:98,close:fvgBot},
          {time:t0s+4*BS,open:fvgBot,high:118,low:fvgBot-1,close:116},
          {time:t0s+5*BS,open:115,high:119,low:fvgTop,close:113},
          {time:t0s+6*BS,open:113,high:116,low:110,close:114},{time:t0s+7*BS,open:114,high:117,low:111,close:115},
        ];
        if(isMit)fd.push({time:t0s+8*BS,open:115,high:116,low:112,close:112},{time:t0s+9*BS,open:112,high:114,low:fvgTop+1,close:fvgTop+2});
      }else{
        fvgTop=97;fvgBot=92;
        fd=[
          {time:t0s,open:99,high:102,low:97,close:101},{time:t0s+BS,open:101,high:104,low:99,close:102},
          {time:t0s+2*BS,open:102,high:105,low:100,close:101},{time:t0s+3*BS,open:101,high:fvgTop,low:97,close:fvgTop},
          {time:t0s+4*BS,open:fvgTop,high:fvgTop+1,low:82,close:84},
          {time:t0s+5*BS,open:85,high:fvgBot,low:81,close:88},
          {time:t0s+6*BS,open:88,high:91,low:85,close:87},{time:t0s+7*BS,open:87,high:90,low:84,close:86},
        ];
        if(isMit)fd.push({time:t0s+8*BS,open:86,high:90,low:85,close:89},{time:t0s+9*BS,open:89,high:fvgBot-1,low:87,close:fvgBot-2});
      }
      // Zone fill drawn BEFORE candles → candles render on top
      const zt=fd.slice(3).map(b=>b.time);
      const zc=up?'rgba(38,166,154,0.85)':'rgba(239,83,80,0.85)';
      const zf=up?'rgba(38,166,154,0.13)':'rgba(239,83,80,0.13)';
      // Upper boundary with shaded fill (AreaSeries fills down — covers gap zone)
      chart.addAreaSeries({topColor:zf,bottomColor:zf,lineColor:zc,lineWidth:1.5,lineStyle:0,priceLineVisible:false,lastValueVisible:false}).setData(zt.map(t=>({time:t,value:fvgTop})));
      // Lower boundary line
      chart.addLineSeries({color:zc,lineWidth:1.5,lineStyle:1,priceLineVisible:false,lastValueVisible:false}).setData(zt.map(t=>({time:t,value:fvgBot})));
      cs.setData(fd);
      const eb=isMit?fd[fd.length-1]:fd[5];
      cs.setMarkers([{time:eb.time,position:up?'belowBar':'aboveBar',color:up?'#26a69a':'#ef5350',shape:up?'arrowUp':'arrowDown',text:isMit?'Retorno':'Entrada'}]);
      chart.timeScale().fitContent();
    });
    return container;
  }"""

NEW_FVG = """\
  // -- FVG - Fair Value Gap
  // Classic 3-candle imbalance: candle A → huge impulse B → candle C
  // Gap = space between A.high (fvgBot) and C.low (fvgTop) for bullish,
  //        space between A.low (fvgTop) and C.high (fvgBot) for bearish
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

ok1 = OLD_FVG in content
content = content.replace(OLD_FVG, NEW_FVG, 1)
print('FVG redesign:', 'OK' if ok1 else 'NOT FOUND')

# ============================================================
# 2. BoS — rebuild to show proper swing formation → pullback → break
#
#  Bullish BoS: context bears → swing HIGH at bsl forms →
#               pullback (Higher Low) → BREAKS ABOVE bsl
#  Bearish BoS: context bulls → swing LOW at bsl forms →
#               rally (Lower High) → BREAKS BELOW bsl
# ============================================================
OLD_BOS = """\
  // -- BoS - Break of Structure
  if (indId === 'bos') {
    container.style.height = '160px';
    _lwcRender(container, (chartW) => {
      if (!window.LightweightCharts) { container.appendChild(_buildCondPreviewSVG(indId,condText,params,isDark,up,cross,sc,ct)); return; }
      const chart = LightweightCharts.createChart(container, {
        width:chartW,height:160,layout:{background:{color:bg},textColor:text},
        grid:{vertLines:{color:grid},horzLines:{color:grid}},
        rightPriceScale:{borderColor:'transparent',scaleMargins:{top:0.1,bottom:0.1}},
        timeScale:{borderColor:'transparent',visible:false},crosshair:{mode:1},
        handleScroll:false,handleScale:false,
        watermark:{visible:true,fontSize:11,horzAlign:'left',vertAlign:'top',color:text,text:'BoS - Break of Structure'}
      });
      const cs = chart.addCandlestickSeries({
        upColor:'#26a69a',downColor:'#ef5350',borderUpColor:'#26a69a',borderDownColor:'#ef5350',
        wickUpColor:isDark?'rgba(38,166,154,0.5)':'rgba(38,166,154,0.7)',
        wickDownColor:isDark?'rgba(239,83,80,0.5)':'rgba(239,83,80,0.7)',
      priceLineVisible:false,lastValueVisible:false,
      });
      const t0s=Math.floor(new Date('2024-01-02').getTime()/1000),BS=300;
      let bd,bsl;
      if(up){
        bsl=107;
        bd=[
          {time:t0s,open:112,high:114,low:109,close:110},{time:t0s+BS,open:110,high:112,low:106,close:107},
          {time:t0s+2*BS,open:107,high:bsl,low:103,close:104},{time:t0s+3*BS,open:104,high:106,low:100,close:101},
          {time:t0s+4*BS,open:101,high:103,low:97,close:98},{time:t0s+5*BS,open:98,high:102,low:96,close:100},
          {time:t0s+6*BS,open:100,high:105,low:98,close:104},{time:t0s+7*BS,open:104,high:110,low:102,close:109},
          {time:t0s+8*BS,open:109,high:112,low:107,close:110},
        ];
      }else{
        bsl=96;
        bd=[
          {time:t0s,open:90,high:93,low:87,close:91},{time:t0s+BS,open:91,high:95,low:89,close:93},
          {time:t0s+2*BS,open:93,high:97,low:90,close:bsl},{time:t0s+3*BS,open:96,high:100,low:94,close:99},
          {time:t0s+4*BS,open:99,high:103,low:97,close:101},{time:t0s+5*BS,open:101,high:103,low:97,close:99},
          {time:t0s+6*BS,open:99,high:101,low:95,close:97},{time:t0s+7*BS,open:97,high:98,low:92,close:93},
          {time:t0s+8*BS,open:93,high:95,low:90,close:91},
        ];
      }
      cs.setData(bd);
      // Level line from structure pivot to break candle only
      const bt=bd.slice(2,9).map(b=>b.time);
      chart.addLineSeries({color:'#F0A020',lineWidth:2,lineStyle:1,priceLineVisible:false,lastValueVisible:false}).setData(bt.map(t=>({time:t,value:bsl})));
      cs.setMarkers([
        {time:bd[2].time,position:up?'aboveBar':'belowBar',color:'#F0A020',shape:'circle',text:up?'HH':'LL'},
        {time:bd[7].time,position:up?'belowBar':'aboveBar',color:up?'#26a69a':'#ef5350',shape:up?'arrowUp':'arrowDown',text:'BoS'}
      ]);
      chart.timeScale().fitContent();
    });
    return container;
  }"""

NEW_BOS = """\
  // -- BoS - Break of Structure
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

ok2 = OLD_BOS in content
content = content.replace(OLD_BOS, NEW_BOS, 1)
print('BoS redesign:', 'OK' if ok2 else 'NOT FOUND')

# ============================================================
# 3. CHoCH — rebuild to show visible trend + first break against it
#
#  Bullish CHoCH: downtrend (LH, LL sequence) →
#                 price breaks ABOVE last Lower High = trend change
#  Bearish CHoCH: uptrend (HH, HL sequence) →
#                 price breaks BELOW last Higher Low = trend change
# ============================================================
OLD_CHOCH = """\
  // -- CHoCH - Change of Character
  if (indId === 'choch') {
    container.style.height = '160px';
    _lwcRender(container, (chartW) => {
      if (!window.LightweightCharts) { container.appendChild(_buildCondPreviewSVG(indId,condText,params,isDark,up,cross,sc,ct)); return; }
      const chart = LightweightCharts.createChart(container, {
        width:chartW,height:160,layout:{background:{color:bg},textColor:text},
        grid:{vertLines:{color:grid},horzLines:{color:grid}},
        rightPriceScale:{borderColor:'transparent',scaleMargins:{top:0.1,bottom:0.1}},
        timeScale:{borderColor:'transparent',visible:false},crosshair:{mode:1},
        handleScroll:false,handleScale:false,
        watermark:{visible:true,fontSize:11,horzAlign:'left',vertAlign:'top',color:text,text:'CHoCH - Change of Character'}
      });
      const cs = chart.addCandlestickSeries({
        upColor:'#26a69a',downColor:'#ef5350',borderUpColor:'#26a69a',borderDownColor:'#ef5350',
        wickUpColor:isDark?'rgba(38,166,154,0.5)':'rgba(38,166,154,0.7)',
        wickDownColor:isDark?'rgba(239,83,80,0.5)':'rgba(239,83,80,0.7)',
      priceLineVisible:false,lastValueVisible:false,
      });
      const t0s=Math.floor(new Date('2024-01-02').getTime()/1000),BS=300;
      let cd2,chlvl,brk;
      if(up){
        chlvl=109;
        cd2=[
          {time:t0s,open:114,high:116,low:110,close:111},{time:t0s+BS,open:111,high:113,low:107,close:108},
          {time:t0s+2*BS,open:108,high:chlvl,low:105,close:107},{time:t0s+3*BS,open:107,high:108,low:103,close:104},
          {time:t0s+4*BS,open:104,high:107,low:101,close:106},{time:t0s+5*BS,open:106,high:110,low:104,close:109},
          {time:t0s+6*BS,open:109,high:113,low:107,close:112},{time:t0s+7*BS,open:112,high:115,low:110,close:113},
        ];
        brk=5;
      }else{
        chlvl=98;
        cd2=[
          {time:t0s,open:90,high:93,low:88,close:92},{time:t0s+BS,open:92,high:96,low:90,close:95},
          {time:t0s+2*BS,open:95,high:chlvl,low:93,close:97},{time:t0s+3*BS,open:97,high:100,low:95,close:99},
          {time:t0s+4*BS,open:99,high:101,low:96,close:97},{time:t0s+5*BS,open:97,high:99,low:94,close:95},
          {time:t0s+6*BS,open:95,high:97,low:91,close:93},{time:t0s+7*BS,open:93,high:95,low:90,close:91},
        ];
        brk=6;
      }
      cs.setData(cd2);
      // Level line from structure pivot to reversal break only
      const ct2=cd2.slice(2,brk+1).map(b=>b.time);
      chart.addLineSeries({color:'#EF4444',lineWidth:2,lineStyle:1,priceLineVisible:false,lastValueVisible:false}).setData(ct2.map(t=>({time:t,value:chlvl})));
      cs.setMarkers([
        {time:cd2[2].time,position:up?'aboveBar':'belowBar',color:'#EF4444',shape:'circle',text:up?'HH':'LL'},
        {time:cd2[brk].time,position:up?'belowBar':'aboveBar',color:up?'#26a69a':'#ef5350',shape:up?'arrowUp':'arrowDown',text:'CHoCH'}
      ]);
      chart.timeScale().fitContent();
    });
    return container;
  }"""

NEW_CHOCH = """\
  // -- CHoCH - Change of Character
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

ok3 = OLD_CHOCH in content
content = content.replace(OLD_CHOCH, NEW_CHOCH, 1)
print('CHoCH redesign:', 'OK' if ok3 else 'NOT FOUND')

# ============================================================
# 4. Sweep — rebuild to show a proper PIN BAR at the level
#
#  Equal highs/lows build up a liquidity pool (3 touches),
#  then ONE candle is a pin bar / hammer that SPIKES through the
#  level but CLOSES BACK ON THE CORRECT SIDE → clear sweep signal.
#
#  Bullish sweep: equal lows → hammer (low < slvl, close > slvl)
#  Bearish sweep: equal highs → shooting star (high > slvl, close < slvl)
# ============================================================
OLD_SWEEP = """\
  // -- SWEEP / GRAB - Liquidity Sweep
  if (indId === 'sweep' || indId === 'grab') {
    container.style.height = '160px';
    _lwcRender(container, (chartW) => {
      if (!window.LightweightCharts) { container.appendChild(_buildCondPreviewSVG(indId,condText,params,isDark,up,cross,sc,ct)); return; }
      const chart = LightweightCharts.createChart(container, {
        width:chartW,height:160,layout:{background:{color:bg},textColor:text},
        grid:{vertLines:{color:grid},horzLines:{color:grid}},
        rightPriceScale:{borderColor:'transparent',scaleMargins:{top:0.1,bottom:0.1}},
        timeScale:{borderColor:'transparent',visible:false},crosshair:{mode:1},
        handleScroll:false,handleScale:false,
        watermark:{visible:true,fontSize:11,horzAlign:'left',vertAlign:'top',color:text,text:indId==='grab'?'Grab de Liquidez':'Sweep de Liquidez'}
      });
      const cs = chart.addCandlestickSeries({
        upColor:'#26a69a',downColor:'#ef5350',borderUpColor:'#26a69a',borderDownColor:'#ef5350',
        wickUpColor:isDark?'rgba(38,166,154,0.5)':'rgba(38,166,154,0.7)',
        wickDownColor:isDark?'rgba(239,83,80,0.5)':'rgba(239,83,80,0.7)',
      priceLineVisible:false,lastValueVisible:false,
      });
      const t0s=Math.floor(new Date('2024-01-02').getTime()/1000),BS=300;
      let sd,slvl;
      if(up){
        slvl=96;
        sd=[
          {time:t0s,open:103,high:106,low:100,close:101},{time:t0s+BS,open:101,high:104,low:97,close:99},
          {time:t0s+2*BS,open:99,high:102,low:slvl,close:98},{time:t0s+3*BS,open:98,high:101,low:slvl,close:99},
          {time:t0s+4*BS,open:99,high:102,low:slvl,close:100},{time:t0s+5*BS,open:100,high:103,low:slvl,close:101},
          {time:t0s+6*BS,open:100,high:102,low:slvl-4,close:101},{time:t0s+7*BS,open:102,high:109,low:101,close:108},
          {time:t0s+8*BS,open:108,high:112,low:106,close:110},
        ];
      }else{
        slvl=106;
        sd=[
          {time:t0s,open:99,high:103,low:97,close:101},{time:t0s+BS,open:101,high:slvl,low:99,close:103},
          {time:t0s+2*BS,open:103,high:slvl,low:100,close:104},{time:t0s+3*BS,open:104,high:slvl,low:101,close:102},
          {time:t0s+4*BS,open:102,high:slvl,low:99,close:103},{time:t0s+5*BS,open:103,high:slvl+4,low:101,close:102},
          {time:t0s+6*BS,open:102,high:103,low:95,close:96},{time:t0s+7*BS,open:96,high:98,low:92,close:94},
          {time:t0s+8*BS,open:94,high:96,low:90,close:92},
        ];
      }
      cs.setData(sd);
      // Level line only across the consolidation / multiple-touch range
      const swpi=up?6:5,revi=up?7:6;
      const st=sd.slice(0,swpi+1).map(b=>b.time);
      chart.addLineSeries({color:'#F0A020',lineWidth:2,lineStyle:1,priceLineVisible:false,lastValueVisible:false}).setData(st.map(t=>({time:t,value:slvl})));
      cs.setMarkers([
        {time:sd[swpi].time,position:up?'belowBar':'aboveBar',color:'#ef5350',shape:up?'arrowDown':'arrowUp',text:'Sweep'},
        {time:sd[revi].time,position:up?'belowBar':'aboveBar',color:'#26a69a',shape:up?'arrowUp':'arrowDown',text:'Reversão'}
      ]);
      chart.timeScale().fitContent();
    });
    return container;
  }"""

NEW_SWEEP = """\
  // -- SWEEP / GRAB - Liquidity Sweep
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

ok4 = OLD_SWEEP in content
content = content.replace(OLD_SWEEP, NEW_SWEEP, 1)
print('Sweep redesign:', 'OK' if ok4 else 'NOT FOUND')

# ============================================================
# Write back
# ============================================================
with open(FPATH, 'w', encoding='utf-8') as f:
    f.write(content)
print('File written:', len(content), 'chars')
print('patch_fix2 DONE')

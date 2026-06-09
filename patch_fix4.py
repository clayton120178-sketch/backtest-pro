#!/usr/bin/env python3
# patch_fix4.py — Split sweep/grab into separate blocks
# Sweep keeps its 3-equal-touch visualization.
# Grab gets its own: single KEY level established early → price drifts away
# → ONE extreme-wick pin bar grabs through the level → explosive reversal.

FPATH = 'C:/Users/Clayton Barros/AppData/Local/Temp/backtest-pro/app.html'
with open(FPATH, 'r', encoding='utf-8') as f:
    content = f.read()

# ── 1. Remove 'grab' from the sweep condition ─────────────────────────────
OLD_COND = "  if (indId === 'sweep' || indId === 'grab') {"
NEW_COND = "  if (indId === 'sweep') {"
ok1 = OLD_COND in content
content = content.replace(OLD_COND, NEW_COND, 1)
print('sweep condition narrowed:', 'OK' if ok1 else 'NOT FOUND')

# ── 2. Also fix the watermark inside the sweep block (was ternary) ─────────
OLD_WM = "        watermark:{visible:true,fontSize:11,horzAlign:'left',vertAlign:'top',color:text,text:indId==='grab'?'Grab de Liquidez':'Sweep de Liquidez'}"
NEW_WM = "        watermark:{visible:true,fontSize:11,horzAlign:'left',vertAlign:'top',color:text,text:'Sweep de Liquidez'}"
ok2 = OLD_WM in content
content = content.replace(OLD_WM, NEW_WM, 1)
print('sweep watermark fixed:', 'OK' if ok2 else 'NOT FOUND')

# ── 3. Insert the new GRAB block right AFTER the sweep's closing  }  ──────
# The sweep block ends with "    return container;\n  }" followed by
# "  // -- CANDLE PATTERNS"
OLD_ANCHOR = """\
    return container;
  }

  // -- CANDLE PATTERNS"""

NEW_GRAB = """\
    return container;
  }

  // -- GRAB - Grab de Liquidez  (16 candles)
  // Distinct from Sweep: ONE significant swing level is established early,
  // price drifts away, then ONE extreme-wick pin bar grabs through the level
  // and closes back on the correct side → explosive reversal.
  // (Sweep = gradual 3-touch pool. Grab = single aggressive spike at a key pivot.)
  if (indId === 'grab') {
    container.style.height = '180px';
    _lwcRender(container, (chartW) => {
      if (!window.LightweightCharts) { container.appendChild(_buildCondPreviewSVG(indId,condText,params,isDark,up,cross,sc,ct)); return; }
      const chart = LightweightCharts.createChart(container, {
        width:chartW,height:180,layout:{background:{color:bg},textColor:text},
        grid:{vertLines:{color:grid},horzLines:{color:grid}},
        rightPriceScale:{borderColor:'transparent',scaleMargins:{top:0.12,bottom:0.12}},
        timeScale:{borderColor:'transparent',visible:false},crosshair:{mode:0},
        handleScroll:false,handleScale:false,
        watermark:{visible:true,fontSize:11,horzAlign:'left',vertAlign:'top',color:text,text:'Grab de Liquidez'}
      });
      const t0s=Math.floor(new Date('2024-01-02').getTime()/1000),BS=86400;
      let gd,slvl,grabIdx,revIdx;

      if(up){
        // Bullish grab: key support at slvl established → drift up → return →
        // ONE hammer pin bar (wick 9 pts BELOW slvl, tiny body ABOVE slvl) → reversal
        slvl=94; grabIdx=12; revIdx=13;
        gd=[
          // [0] First touch: approach + bounce off slvl (establishes the level)
          {time:t0s+ 0*BS,open: 97,high: 98,low:slvl,   close: 96},
          {time:t0s+ 1*BS,open: 96,high: 99,low: 95,   close: 98},
          // Price moves away from slvl (bullish drift)
          {time:t0s+ 2*BS,open: 98,high:101,low: 97,   close:100},
          {time:t0s+ 3*BS,open:100,high:102,low: 98,   close: 99},
          {time:t0s+ 4*BS,open: 99,high:102,low: 97,   close:101},
          {time:t0s+ 5*BS,open:101,high:103,low: 99,   close:100},
          // Starts drifting back toward slvl
          {time:t0s+ 6*BS,open:100,high:102,low: 98,   close: 99},
          {time:t0s+ 7*BS,open: 99,high:101,low: 97,   close: 98},
          {time:t0s+ 8*BS,open: 98,high:100,low: 96,   close: 97},
          {time:t0s+ 9*BS,open: 97,high: 99,low: 95,   close: 96},
          // Testing the area just above slvl — two candles holding above it
          {time:t0s+10*BS,open: 96,high: 98,low:slvl,  close: 96},
          {time:t0s+11*BS,open: 96,high: 98,low:slvl,  close: 95},
          // [12] GRAB — extreme hammer: wick goes 9 pts BELOW slvl, body closes ABOVE
          //      This single candle hunts ALL stop losses below slvl
          {time:t0s+12*BS,open: 95,high: 96,low:slvl-9,close: 96},
          // [13] Explosive reversal — strong bullish engulfing
          {time:t0s+13*BS,open: 96,high:104,low: 95,   close:103},
          // Continuation up
          {time:t0s+14*BS,open:103,high:107,low:102,   close:106},
          {time:t0s+15*BS,open:106,high:110,low:105,   close:109},
        ];
      }else{
        // Bearish grab: key resistance at slvl established → drift down → return →
        // ONE shooting-star pin bar (wick 9 pts ABOVE slvl, tiny body BELOW slvl) → reversal
        slvl=108; grabIdx=12; revIdx=13;
        gd=[
          // [0] First touch: approach + rejection from slvl (establishes the level)
          {time:t0s+ 0*BS,open:105,high:slvl,  low:104,close:106},
          {time:t0s+ 1*BS,open:106,high:107,   low:103,close:104},
          // Price moves away from slvl (bearish drift)
          {time:t0s+ 2*BS,open:104,high:106,   low:102,close:103},
          {time:t0s+ 3*BS,open:103,high:105,   low:101,close:104},
          {time:t0s+ 4*BS,open:104,high:106,   low:102,close:103},
          {time:t0s+ 5*BS,open:103,high:105,   low:101,close:102},
          // Starts drifting back toward slvl
          {time:t0s+ 6*BS,open:102,high:104,   low:100,close:103},
          {time:t0s+ 7*BS,open:103,high:105,   low:101,close:104},
          {time:t0s+ 8*BS,open:104,high:106,   low:102,close:105},
          {time:t0s+ 9*BS,open:105,high:107,   low:103,close:106},
          // Testing the area just below slvl — two candles holding below it
          {time:t0s+10*BS,open:106,high:slvl,  low:105,close:106},
          {time:t0s+11*BS,open:106,high:slvl,  low:105,close:107},
          // [12] GRAB — extreme shooting star: wick goes 9 pts ABOVE slvl, body closes BELOW
          //      This single candle hunts ALL stop losses above slvl
          {time:t0s+12*BS,open:107,high:slvl+9,low:106,close:106},
          // [13] Explosive reversal — strong bearish engulfing
          {time:t0s+13*BS,open:106,high:107,   low: 99,close:100},
          // Continuation down
          {time:t0s+14*BS,open:100,high:101,   low: 96,close: 97},
          {time:t0s+15*BS,open: 97,high: 98,   low: 93,close: 94},
        ];
      }

      // Level line: spans from [0] (first touch) through [grabIdx] (grab candle)
      // — shows the level persisting over time until the grab
      const lt = gd.slice(0, grabIdx+1).map(b=>b.time);
      chart.addLineSeries({
        color:'#F0A020',lineWidth:2,lineStyle:1,
        priceLineVisible:false,lastValueVisible:false,
      }).setData(lt.map(t=>({time:t,value:slvl})));

      const cs = chart.addCandlestickSeries({
        upColor:'#26a69a',downColor:'#ef5350',
        borderUpColor:'#26a69a',borderDownColor:'#ef5350',
        wickUpColor:isDark?'rgba(38,166,154,0.6)':'rgba(38,166,154,0.8)',
        wickDownColor:isDark?'rgba(239,83,80,0.6)':'rgba(239,83,80,0.8)',
        priceLineVisible:false,lastValueVisible:false,
      });
      cs.setData(gd);
      cs.setMarkers([
        // First touch — shows the level is significant
        {time:gd[0].time,
         position:up?'belowBar':'aboveBar',
         color:'#F0A020', shape:'circle', text:up?'Suporte':'Resistência'},
        // The grab candle
        {time:gd[grabIdx].time,
         position:up?'belowBar':'aboveBar',
         color:'#ef5350', shape:up?'arrowDown':'arrowUp', text:'Grab'},
        // Reversal
        {time:gd[revIdx].time,
         position:up?'belowBar':'aboveBar',
         color:'#26a69a', shape:up?'arrowUp':'arrowDown', text:'Reversão'},
      ]);
      chart.timeScale().fitContent();
    });
    return container;
  }

  // -- CANDLE PATTERNS"""

ok3 = OLD_ANCHOR in content
content = content.replace(OLD_ANCHOR, NEW_GRAB, 1)
print('grab block inserted:', 'OK' if ok3 else 'NOT FOUND')

# ── 4. Write back ──────────────────────────────────────────────────────────
with open(FPATH, 'w', encoding='utf-8') as f:
    f.write(content)
print('File written:', len(content), 'chars')
print('patch_fix4 DONE')

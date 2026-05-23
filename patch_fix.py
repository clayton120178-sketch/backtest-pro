#!/usr/bin/env python3
# patch_fix.py — Fix priceLineVisible on all CandlestickSeries + SMC previews
import re

FPATH = 'C:/Users/Clayton Barros/AppData/Local/Temp/backtest-pro/app.html'
with open(FPATH, 'r', encoding='utf-8') as f:
    content = f.read()

# ============================================================
# 1. Add priceLineVisible:false,lastValueVisible:false to ALL
#    addCandlestickSeries() blocks via regex
# ============================================================
before = len(re.findall(r'addCandlestickSeries', content))

def _add_pl(m):
    wdc_line = m.group(1)   # line ending with wickDownColor:...,\n
    close_line = m.group(2) # the    }); line
    indent = re.match(r'^([ \t]*)', close_line).group(1)
    return wdc_line + indent + 'priceLineVisible:false,lastValueVisible:false,\n' + close_line

# Match any line containing wickDownColor followed immediately by });
content, n = re.subn(
    r'([^\n]*wickDownColor:[^\n]+\n)([ \t]+\}\);)',
    _add_pl,
    content
)
print(f'priceLineVisible: {n} CandlestickSeries blocks patched (total series in file: {before})')

# ============================================================
# 2. FVG — zone fill (AreaSeries behind candles) + lines
#    restricted to gap area only (fd.slice(3))
# ============================================================
OLD_FVG = (
    "      cs.setData(fd);\n"
    "      const ft=fd.map(b=>b.time),zc=up?'rgba(38,166,154,0.7)':'rgba(239,83,80,0.7)';\n"
    "      chart.addLineSeries({color:zc,lineWidth:1.5,lineStyle:1,priceLineVisible:false,lastValueVisible:false}).setData(ft.map(t=>({time:t,value:fvgTop})));\n"
    "      chart.addLineSeries({color:zc,lineWidth:1.5,lineStyle:1,priceLineVisible:false,lastValueVisible:false}).setData(ft.map(t=>({time:t,value:fvgBot})));"
)
NEW_FVG = (
    "      // Zone fill drawn BEFORE candles → candles render on top\n"
    "      const zt=fd.slice(3).map(b=>b.time);\n"
    "      const zc=up?'rgba(38,166,154,0.85)':'rgba(239,83,80,0.85)';\n"
    "      const zf=up?'rgba(38,166,154,0.13)':'rgba(239,83,80,0.13)';\n"
    "      // Upper boundary with shaded fill (AreaSeries fills down — covers gap zone)\n"
    "      chart.addAreaSeries({topColor:zf,bottomColor:zf,lineColor:zc,lineWidth:1.5,lineStyle:0,priceLineVisible:false,lastValueVisible:false}).setData(zt.map(t=>({time:t,value:fvgTop})));\n"
    "      // Lower boundary line\n"
    "      chart.addLineSeries({color:zc,lineWidth:1.5,lineStyle:1,priceLineVisible:false,lastValueVisible:false}).setData(zt.map(t=>({time:t,value:fvgBot})));\n"
    "      cs.setData(fd);"
)
ok2 = OLD_FVG in content
content = content.replace(OLD_FVG, NEW_FVG, 1)
print('FVG zone fix:', 'OK' if ok2 else 'NOT FOUND')

# ============================================================
# 3. BoS — level line only from structure pivot → break candle
# ============================================================
OLD_BOS = (
    "      cs.setData(bd);\n"
    "      const bt=bd.map(b=>b.time);\n"
    "      chart.addLineSeries({color:'#F0A020',lineWidth:1.5,lineStyle:1,priceLineVisible:false,lastValueVisible:false}).setData(bt.map(t=>({time:t,value:bsl})));\n"
    "      cs.setMarkers([{time:bd[7].time,position:up?'belowBar':'aboveBar',color:'#F0A020',shape:'circle',text:'BoS'}]);"
)
NEW_BOS = (
    "      cs.setData(bd);\n"
    "      // Level line from structure pivot to break candle only\n"
    "      const bt=bd.slice(2,9).map(b=>b.time);\n"
    "      chart.addLineSeries({color:'#F0A020',lineWidth:2,lineStyle:1,priceLineVisible:false,lastValueVisible:false}).setData(bt.map(t=>({time:t,value:bsl})));\n"
    "      cs.setMarkers([\n"
    "        {time:bd[2].time,position:up?'aboveBar':'belowBar',color:'#F0A020',shape:'circle',text:up?'HH':'LL'},\n"
    "        {time:bd[7].time,position:up?'belowBar':'aboveBar',color:up?'#26a69a':'#ef5350',shape:up?'arrowUp':'arrowDown',text:'BoS'}\n"
    "      ]);"
)
ok3 = OLD_BOS in content
content = content.replace(OLD_BOS, NEW_BOS, 1)
print('BoS line fix:', 'OK' if ok3 else 'NOT FOUND')

# ============================================================
# 4. CHoCH — level line only from structure pivot → reversal
# ============================================================
OLD_CHOCH = (
    "      cs.setData(cd2);\n"
    "      const ct2=cd2.map(b=>b.time);\n"
    "      chart.addLineSeries({color:'#EF4444',lineWidth:1.5,lineStyle:1,priceLineVisible:false,lastValueVisible:false}).setData(ct2.map(t=>({time:t,value:chlvl})));\n"
    "      cs.setMarkers([{time:cd2[brk].time,position:up?'belowBar':'aboveBar',color:'#F0A020',shape:'circle',text:'CHoCH'}]);"
)
NEW_CHOCH = (
    "      cs.setData(cd2);\n"
    "      // Level line from structure pivot to reversal break only\n"
    "      const ct2=cd2.slice(2,brk+1).map(b=>b.time);\n"
    "      chart.addLineSeries({color:'#EF4444',lineWidth:2,lineStyle:1,priceLineVisible:false,lastValueVisible:false}).setData(ct2.map(t=>({time:t,value:chlvl})));\n"
    "      cs.setMarkers([\n"
    "        {time:cd2[2].time,position:up?'aboveBar':'belowBar',color:'#EF4444',shape:'circle',text:up?'HH':'LL'},\n"
    "        {time:cd2[brk].time,position:up?'belowBar':'aboveBar',color:up?'#26a69a':'#ef5350',shape:up?'arrowUp':'arrowDown',text:'CHoCH'}\n"
    "      ]);"
)
ok4 = OLD_CHOCH in content
content = content.replace(OLD_CHOCH, NEW_CHOCH, 1)
print('CHoCH line fix:', 'OK' if ok4 else 'NOT FOUND')

# ============================================================
# 5. Sweep — level line only across consolidation/touch range
# ============================================================
OLD_SWEEP = (
    "      cs.setData(sd);\n"
    "      const st=sd.map(b=>b.time);\n"
    "      chart.addLineSeries({color:'#F0A020',lineWidth:1.5,lineStyle:1,priceLineVisible:false,lastValueVisible:false}).setData(st.map(t=>({time:t,value:slvl})));\n"
    "      const swpi=up?6:5,revi=up?7:6;\n"
    "      cs.setMarkers([\n"
    "        {time:sd[swpi].time,position:up?'belowBar':'aboveBar',color:'#ef5350',shape:up?'arrowDown':'arrowUp',text:'Sweep'},\n"
    "        {time:sd[revi].time,position:up?'belowBar':'aboveBar',color:'#26a69a',shape:up?'arrowUp':'arrowDown',text:'Reversao'}\n"
    "      ]);"
)
NEW_SWEEP = (
    "      cs.setData(sd);\n"
    "      // Level line only across the consolidation / multiple-touch range\n"
    "      const swpi=up?6:5,revi=up?7:6;\n"
    "      const st=sd.slice(0,swpi+1).map(b=>b.time);\n"
    "      chart.addLineSeries({color:'#F0A020',lineWidth:2,lineStyle:1,priceLineVisible:false,lastValueVisible:false}).setData(st.map(t=>({time:t,value:slvl})));\n"
    "      cs.setMarkers([\n"
    "        {time:sd[swpi].time,position:up?'belowBar':'aboveBar',color:'#ef5350',shape:up?'arrowDown':'arrowUp',text:'Sweep'},\n"
    "        {time:sd[revi].time,position:up?'belowBar':'aboveBar',color:'#26a69a',shape:up?'arrowUp':'arrowDown',text:'Reversão'}\n"
    "      ]);"
)
ok5 = OLD_SWEEP in content
content = content.replace(OLD_SWEEP, NEW_SWEEP, 1)
print('Sweep line fix:', 'OK' if ok5 else 'NOT FOUND')

# ============================================================
# 6. Write back
# ============================================================
with open(FPATH, 'w', encoding='utf-8') as f:
    f.write(content)
print('File written:', len(content), 'chars')
print('patch_fix DONE')

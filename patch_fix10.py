#!/usr/bin/env python3
# patch_fix10.py — 3 ajustes visuais
#
# 1. FVG preview de topo  — remove texto "Entrada"/"Retorno" da seta
# 2. CHoCH preview de topo — "LH"/"HL" -> "Topo"/"Suporte"
# 3. Sweep preview de topo + cards — marcador "Sweep" trocado de lado
#    para nao clippar no wick extremo

FPATH = 'C:/Users/Clayton Barros/AppData/Local/Temp/backtest-pro/app.html'
with open(FPATH, 'r', encoding='utf-8') as f:
    content = f.read()

# ─────────────────────────────────────────────────────────────────────────────
# FIX 1 — FVG preview de topo: remover texto da seta de entrada
# ─────────────────────────────────────────────────────────────────────────────
OLD_FVG_TXT = "        text:isMit?'Retorno':'Entrada',\n      }]);"
NEW_FVG_TXT = "        text:'',\n      }]);"

ok1 = OLD_FVG_TXT in content
content = content.replace(OLD_FVG_TXT, NEW_FVG_TXT, 1)
print(f'FIX 1 FVG remove Entrada text: {"OK" if ok1 else "NOT FOUND"}')

# ─────────────────────────────────────────────────────────────────────────────
# FIX 2 — CHoCH preview de topo: LH/HL -> Topo/Suporte
# ─────────────────────────────────────────────────────────────────────────────
OLD_CHOCH_LH_PREV = "         color:'#EF4444', shape:'circle', text:up?'LH':'HL'},"
NEW_CHOCH_LH_PREV = "         color:'#EF4444', shape:'circle', text:up?'Topo':'Suporte'},"

ok2 = OLD_CHOCH_LH_PREV in content
content = content.replace(OLD_CHOCH_LH_PREV, NEW_CHOCH_LH_PREV, 1)
print(f'FIX 2 CHoCH preview LH/HL->Topo/Suporte: {"OK" if ok2 else "NOT FOUND"}')

# ─────────────────────────────────────────────────────────────────────────────
# FIX 3a — Sweep preview de topo: trocar posicao do marker "Sweep"
#   Bullish sweep: wick extremo vai ABAIXO do slvl → belowBar clipa → usar aboveBar
#   Bearish sweep: wick extremo vai ACIMA do slvl → aboveBar clipa → usar belowBar
# ─────────────────────────────────────────────────────────────────────────────
OLD_SWEEP_PREV = ("        {time:sd[swpi].time,\n"
                  "         position:up?'belowBar':'aboveBar',\n"
                  "         color:'#ef5350', shape:up?'arrowDown':'arrowUp', text:'Sweep'},")
NEW_SWEEP_PREV = ("        {time:sd[swpi].time,\n"
                  "         position:up?'aboveBar':'belowBar',\n"
                  "         color:'#ef5350', shape:up?'arrowDown':'arrowUp', text:'Sweep'},")

ok3a = OLD_SWEEP_PREV in content
content = content.replace(OLD_SWEEP_PREV, NEW_SWEEP_PREV, 1)
print(f'FIX 3a Sweep preview marker pos: {"OK" if ok3a else "NOT FOUND"}')

# ─────────────────────────────────────────────────────────────────────────────
# FIX 3b — Sweep direction card Compra: "Sweep" belowBar → aboveBar
#   candle[7]: wick 11pts abaixo do nivel; belowBar vai alem do limite inferior
# ─────────────────────────────────────────────────────────────────────────────
OLD_SWEEP_C = ("                  {time:_cd[7].time,position:'belowBar',"
               "color:'#ef5350',shape:'arrowDown',text:'Sweep'},")
NEW_SWEEP_C = ("                  {time:_cd[7].time,position:'aboveBar',"
               "color:'#ef5350',shape:'arrowDown',text:'Sweep'},")

ok3b = OLD_SWEEP_C in content
content = content.replace(OLD_SWEEP_C, NEW_SWEEP_C, 1)
print(f'FIX 3b Sweep Compra card marker: {"OK" if ok3b else "NOT FOUND"}')

# ─────────────────────────────────────────────────────────────────────────────
# FIX 3c — Sweep direction card Venda: "Sweep" aboveBar → belowBar
#   candle[7]: wick 11pts acima do nivel; aboveBar vai alem do limite superior
# ─────────────────────────────────────────────────────────────────────────────
OLD_SWEEP_V = ("                  {time:_cd[7].time,position:'aboveBar',"
               "color:'#ef5350',shape:'arrowUp',text:'Sweep'},")
NEW_SWEEP_V = ("                  {time:_cd[7].time,position:'belowBar',"
               "color:'#ef5350',shape:'arrowUp',text:'Sweep'},")

ok3c = OLD_SWEEP_V in content
content = content.replace(OLD_SWEEP_V, NEW_SWEEP_V, 1)
print(f'FIX 3c Sweep Venda card marker: {"OK" if ok3c else "NOT FOUND"}')

# ─────────────────────────────────────────────────────────────────────────────
with open(FPATH, 'w', encoding='utf-8') as f:
    f.write(content)
print(f'File written: {len(content)} chars')
print('patch_fix10 DONE')

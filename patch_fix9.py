#!/usr/bin/env python3
# patch_fix9.py — 6 visual corrections
#
# 1. FVG preview de topo  — adiciona pullback ao gap depois do impulso
# 2. FVG cards desc       — remove "[3]"/"[1]" (linguagem de prog.)
# 3. FVG cards markers    — remove "A"/"C" cortados; mantém so "Entrada"
# 4. BoS diagrama         — "HL" → "Suporte" (texto legivel)
# 5. CHoCH cards+diagrama — "LH"→"Topo", "HL"→"Fundo", "LL"→"Fundo"
# 6. Grab em tudo         — marcador "Grab" posicionado acima/abaixo correto

FPATH = 'C:/Users/Clayton Barros/AppData/Local/Temp/backtest-pro/app.html'
with open(FPATH, 'r', encoding='utf-8') as f:
    content = f.read()

# ─────────────────────────────────────────────────────────────────────────────
# FIX 1a — FVG buildCondPreview: pullback BULLISH (non-mitigation candles)
# fd[15..18] ficam inalterados quando isMit=false (overridados quando isMit=true)
# ─────────────────────────────────────────────────────────────────────────────
OLD_FVG_UP_CONT = """\
          {time:t0s+15*BS,open:119,high:122,low:117,close:120},
          {time:t0s+16*BS,open:120,high:122,low:117,close:118},
          {time:t0s+17*BS,open:118,high:121,low:116,close:119},
          {time:t0s+18*BS,open:119,high:121,low:116,close:120},"""

NEW_FVG_UP_CONT = """\
          {time:t0s+15*BS,open:119,high:120,low:113,close:114},
          {time:t0s+16*BS,open:114,high:115,low:109,close:111},
          {time:t0s+17*BS,open:111,high:118,low:110,close:116},
          {time:t0s+18*BS,open:116,high:122,low:115,close:120},"""

ok1a = OLD_FVG_UP_CONT in content
content = content.replace(OLD_FVG_UP_CONT, NEW_FVG_UP_CONT, 1)
print(f'FIX 1a FVG bullish pullback: {"OK" if ok1a else "NOT FOUND"}')

# ─────────────────────────────────────────────────────────────────────────────
# FIX 1b — FVG buildCondPreview: pullback BEARISH
# ─────────────────────────────────────────────────────────────────────────────
OLD_FVG_DN_CONT = """\
          {time:t0s+15*BS,open:83,high:86,low:81,close:82},
          {time:t0s+16*BS,open:82,high:85,low:80,close:81},
          {time:t0s+17*BS,open:81,high:84,low:79,close:82},
          {time:t0s+18*BS,open:82,high:84,low:79,close:80},"""

NEW_FVG_DN_CONT = """\
          {time:t0s+15*BS,open:83,high:89,low:82,close:88},
          {time:t0s+16*BS,open:88,high:94,low:87,close:90},
          {time:t0s+17*BS,open:90,high:91,low:84,close:85},
          {time:t0s+18*BS,open:85,high:86,low:79,close:80},"""

ok1b = OLD_FVG_DN_CONT in content
content = content.replace(OLD_FVG_DN_CONT, NEW_FVG_DN_CONT, 1)
print(f'FIX 1b FVG bearish pullback: {"OK" if ok1b else "NOT FOUND"}')

# ─────────────────────────────────────────────────────────────────────────────
# FIX 2 — FVG cards: remove [3] / [1] das descriptions
# ─────────────────────────────────────────────────────────────────────────────
OLD_DESC_AGG = ("desc:'Quando a mínima do candle [3] fica acima da máxima do candle [1], "
                "o gap é confirmado. A entrada ocorre no candle seguinte — apostando na "
                "continuação do movimento.'")
NEW_DESC_AGG = ("desc:'Quando a mínima do candle pós-impulso fica acima da máxima do candle "
                "pré-impulso, o gap é confirmado. A entrada ocorre imediatamente no candle seguinte.'")

ok2a = OLD_DESC_AGG in content
content = content.replace(OLD_DESC_AGG, NEW_DESC_AGG, 1)
print(f'FIX 2a FVG desc agressivo: {"OK" if ok2a else "NOT FOUND"}')

OLD_DESC_MIT = ("desc:'Após o gap ser confirmado, o mercado sobe além do candle [3]. "
                "Quando o preço recua até a zona do gap (entre máx. do [1] e mín. do [3]), "
                "a entrada ocorre ali.'")
NEW_DESC_MIT = ("desc:'Após o gap se formar, o preço sobe além da zona. Quando ele recua e "
                "toca a zona do gap, a entrada ocorre — com preço melhor e risco controlado.'")

ok2b = OLD_DESC_MIT in content
content = content.replace(OLD_DESC_MIT, NEW_DESC_MIT, 1)
print(f'FIX 2b FVG desc mitigacao: {"OK" if ok2b else "NOT FOUND"}')

# ─────────────────────────────────────────────────────────────────────────────
# FIX 3 — FVG cards: remove marcadores "A" e "C" (cortados/confusos)
#          mantém só a seta "Entrada"
# ─────────────────────────────────────────────────────────────────────────────
OLD_FVG_MARKERS = """\
            cCs.setMarkers([
              {time:_cd[_aI].time,position:'aboveBar',color:'#F0A020',shape:'circle',text:'A'},
              {time:_cd[_cI].time,position:'aboveBar',color:'#F0A020',shape:'circle',text:'C'},
              {time:_cd[_eI].time,position:'belowBar',color:'#26a69a',shape:'arrowUp',text:'Entrada'},
            ]);"""
NEW_FVG_MARKERS = """\
            cCs.setMarkers([
              {time:_cd[_eI].time,position:'belowBar',color:'#26a69a',shape:'arrowUp',text:'Entrada'},
            ]);"""

ok3 = OLD_FVG_MARKERS in content
content = content.replace(OLD_FVG_MARKERS, NEW_FVG_MARKERS, 1)
print(f'FIX 3 FVG markers A/C removidos: {"OK" if ok3 else "NOT FOUND"}')

# ─────────────────────────────────────────────────────────────────────────────
# FIX 4 — BoS diagrama de sequência: "HL" → "Suporte"
# ─────────────────────────────────────────────────────────────────────────────
OLD_BOS_HL = "            {time:_bd[7].time, position:'belowBar',color:'#26a69a',shape:'circle',  text:'HL'},"
NEW_BOS_HL = "            {time:_bd[7].time, position:'belowBar',color:'#26a69a',shape:'circle',  text:'Suporte'},"

ok4 = OLD_BOS_HL in content
content = content.replace(OLD_BOS_HL, NEW_BOS_HL, 1)
print(f'FIX 4 BoS HL->Suporte: {"OK" if ok4 else "NOT FOUND"}')

# ─────────────────────────────────────────────────────────────────────────────
# FIX 5a — CHoCH direction card Compra: "LH" → "Topo"
# ─────────────────────────────────────────────────────────────────────────────
OLD_CHOCH_LH = ("                _markers=[\n"
                "                  {time:_cd[4].time,position:'aboveBar',color:'#EF4444',shape:'circle',text:'LH'},\n"
                "                  {time:_cd[10].time,position:'belowBar',color:'#26a69a',shape:'arrowUp',text:'CHoCH'},\n"
                "                ];")
NEW_CHOCH_LH = ("                _markers=[\n"
                "                  {time:_cd[4].time,position:'aboveBar',color:'#EF4444',shape:'circle',text:'Topo'},\n"
                "                  {time:_cd[10].time,position:'belowBar',color:'#26a69a',shape:'arrowUp',text:'Reversão'},\n"
                "                ];")

ok5a = OLD_CHOCH_LH in content
content = content.replace(OLD_CHOCH_LH, NEW_CHOCH_LH, 1)
print(f'FIX 5a CHoCH card Compra LH->Topo: {"OK" if ok5a else "NOT FOUND"}')

# ─────────────────────────────────────────────────────────────────────────────
# FIX 5b — CHoCH direction card Venda: "HL" → "Topo" (nessa direcao o nivel
#           é um Higher Low que falha → use "Topo" para a resistência)
# ─────────────────────────────────────────────────────────────────────────────
OLD_CHOCH_HL = ("                _markers=[\n"
                "                  {time:_cd[4].time,position:'belowBar',color:'#EF4444',shape:'circle',text:'HL'},\n"
                "                  {time:_cd[10].time,position:'aboveBar',color:'#ef5350',shape:'arrowDown',text:'CHoCH'},\n"
                "                ];")
NEW_CHOCH_HL = ("                _markers=[\n"
                "                  {time:_cd[4].time,position:'belowBar',color:'#EF4444',shape:'circle',text:'Suporte'},\n"
                "                  {time:_cd[10].time,position:'aboveBar',color:'#ef5350',shape:'arrowDown',text:'Reversão'},\n"
                "                ];")

ok5b = OLD_CHOCH_HL in content
content = content.replace(OLD_CHOCH_HL, NEW_CHOCH_HL, 1)
print(f'FIX 5b CHoCH card Venda HL->Suporte: {"OK" if ok5b else "NOT FOUND"}')

# ─────────────────────────────────────────────────────────────────────────────
# FIX 5c — CHoCH diagrama de sequência: LH→Topo, LL→Fundo
# ─────────────────────────────────────────────────────────────────────────────
OLD_CHOCH_DIAG = """\
          _cs2.setMarkers([
            {time:_bd2[0].time, position:'aboveBar',color:'#EF4444',shape:'circle',  text:'LH'},
            {time:_bd2[5].time, position:'aboveBar',color:'#EF4444',shape:'circle',  text:'LH'},
            {time:_bd2[7].time, position:'belowBar',color:'#EF4444',shape:'circle',  text:'LL'},
            {time:_bd2[10].time,position:'belowBar',color:'#00D4AA',shape:'arrowUp', text:'CHoCH'},
          ]);"""
NEW_CHOCH_DIAG = """\
          _cs2.setMarkers([
            {time:_bd2[0].time, position:'aboveBar',color:'#EF4444',shape:'circle',  text:'Topo'},
            {time:_bd2[5].time, position:'aboveBar',color:'#EF4444',shape:'circle',  text:'Topo'},
            {time:_bd2[7].time, position:'belowBar',color:'#EF4444',shape:'circle',  text:'Fundo'},
            {time:_bd2[10].time,position:'belowBar',color:'#00D4AA',shape:'arrowUp', text:'Reversão'},
          ]);"""

ok5c = OLD_CHOCH_DIAG in content
content = content.replace(OLD_CHOCH_DIAG, NEW_CHOCH_DIAG, 1)
print(f'FIX 5c CHoCH diagrama LH/LL->Topo/Fundo: {"OK" if ok5c else "NOT FOUND"}')

# ─────────────────────────────────────────────────────────────────────────────
# FIX 6a — Grab buildCondPreview: trocar posicao do marker "Grab"
#   Bullish: belowBar → aboveBar  (wick extremo vai pra baixo; colocar acima evita clip)
#   Bearish: aboveBar → belowBar  (wick extremo vai pra cima; colocar abaixo evita clip)
# ─────────────────────────────────────────────────────────────────────────────
OLD_GRAB_PREVIEW_MKR = """\
        {time:gd[grabIdx].time,
         position:up?'belowBar':'aboveBar',
         color:'#ef5350', shape:up?'arrowDown':'arrowUp', text:'Grab'},"""
NEW_GRAB_PREVIEW_MKR = """\
        {time:gd[grabIdx].time,
         position:up?'aboveBar':'belowBar',
         color:'#ef5350', shape:up?'arrowDown':'arrowUp', text:'Grab'},"""

ok6a = OLD_GRAB_PREVIEW_MKR in content
content = content.replace(OLD_GRAB_PREVIEW_MKR, NEW_GRAB_PREVIEW_MKR, 1)
print(f'FIX 6a Grab preview marker pos: {"OK" if ok6a else "NOT FOUND"}')

# ─────────────────────────────────────────────────────────────────────────────
# FIX 6b — Grab direction card Compra: "Grab" belowBar → aboveBar
#   candle[6]: extreme hammer (wick 12pts abaixo); belowBar clippa o wick
# ─────────────────────────────────────────────────────────────────────────────
OLD_GRAB_C_MKR = ("                  {time:_cd[6].time,position:'belowBar',"
                  "color:'#ef5350',shape:'arrowDown',text:'Grab'},")
NEW_GRAB_C_MKR = ("                  {time:_cd[6].time,position:'aboveBar',"
                  "color:'#ef5350',shape:'arrowDown',text:'Grab'},")

ok6b = OLD_GRAB_C_MKR in content
content = content.replace(OLD_GRAB_C_MKR, NEW_GRAB_C_MKR, 1)
print(f'FIX 6b Grab Compra card marker: {"OK" if ok6b else "NOT FOUND"}')

# ─────────────────────────────────────────────────────────────────────────────
# FIX 6c — Grab direction card Venda: "Grab" aboveBar → belowBar
#   candle[6]: extreme shooting star (wick 12pts acima); aboveBar clippa
# ─────────────────────────────────────────────────────────────────────────────
OLD_GRAB_V_MKR = ("                  {time:_cd[6].time,position:'aboveBar',"
                  "color:'#ef5350',shape:'arrowUp',text:'Grab'},")
NEW_GRAB_V_MKR = ("                  {time:_cd[6].time,position:'belowBar',"
                  "color:'#ef5350',shape:'arrowUp',text:'Grab'},")

ok6c = OLD_GRAB_V_MKR in content
content = content.replace(OLD_GRAB_V_MKR, NEW_GRAB_V_MKR, 1)
print(f'FIX 6c Grab Venda card marker: {"OK" if ok6c else "NOT FOUND"}')

# ─────────────────────────────────────────────────────────────────────────────
# Write
# ─────────────────────────────────────────────────────────────────────────────
with open(FPATH, 'w', encoding='utf-8') as f:
    f.write(content)
print(f'File written: {len(content)} chars')
print('patch_fix9 DONE')

#!/usr/bin/env python3
# patch_fix7.py — Direction cards for BoS, CHoCH, Grab, Sweep
# Replace plain pills('Direção',...) with illustrated LWC cards
# following the same visual pattern as FVG condition cards.

FPATH = 'C:/Users/Clayton Barros/AppData/Local/Temp/backtest-pro/app.html'
with open(FPATH, 'r', encoding='utf-8') as f:
    content = f.read()

# ─── SHARED CARD SHELL ───────────────────────────────────────────────────────
# Used as template — chart data/markers/lines differ per indicator.
# _INNER is replaced per indicator with specific JS for candles/lines/markers.

def dir_cards_block(lbl_tooltip, buy_title, buy_desc, sell_title, sell_desc, inner_js):
    """Build the complete direction-cards JS block."""
    return (
        "        // Direction selection — illustrated cards (like FVG)\n"
        "        {\n"
        "          const _dirLbl=div('');_dirLbl.appendChild(slabel('Direção','" + lbl_tooltip + "'));frag.appendChild(_dirLbl);\n"
        "          const _dc=div('');_dc.style.cssText='display:flex;flex-direction:column;gap:8px';\n"
        "          [\n"
        "            {dir:'Compra',title:'" + buy_title + "',desc:'" + buy_desc + "'},\n"
        "            {dir:'Venda',title:'" + sell_title + "',desc:'" + sell_desc + "'},\n"
        "          ].forEach(opt=>{\n"
        "            const card=div('');\n"
        "            const isSel=ms.params.dir===opt.dir;\n"
        "            card.style.cssText='border:1px solid '+(isSel?'var(--ac)':'var(--bd)')+';border-radius:10px;overflow:hidden;cursor:pointer;transition:border-color .15s;background:'+(isSel?'rgba(0,212,170,0.04)':'transparent');\n"
        "            const top=div('');top.style.cssText='display:flex;align-items:flex-start;gap:10px;padding:12px 14px 10px';\n"
        "            top.appendChild(cring(isSel));\n"
        "            const info=div('');\n"
        "            const nm=div('');nm.style.cssText='font-size:13px;font-weight:600;color:var(--tx);margin-bottom:3px';nm.textContent=opt.title;\n"
        "            const ds=div('');ds.style.cssText='font-size:12px;color:var(--txs);line-height:1.45';ds.textContent=opt.desc;\n"
        "            info.append(nm,ds);top.appendChild(info);card.appendChild(top);\n"
        "            // LWC chart\n"
        "            const _ch=130;const _cc=div('');_cc.style.cssText='height:'+_ch+'px;pointer-events:none;overflow:hidden;border-top:1px solid var(--bd)';\n"
        "            _lwcRender(_cc,(cW)=>{\n"
        "              if(!window.LightweightCharts)return;\n"
        "              const _dk=document.documentElement.getAttribute('data-theme')!=='light';\n"
        "              const _bg=_dk?'#0E0E16':'#F0F0EB',_gr=_dk?'rgba(255,255,255,0.04)':'rgba(0,0,0,0.05)',_xt=_dk?'#8888A0':'#909090';\n"
        "              const ch=LightweightCharts.createChart(_cc,{width:cW,height:_ch,layout:{background:{color:_bg},textColor:_xt},grid:{vertLines:{color:_gr},horzLines:{color:_gr}},rightPriceScale:{borderColor:'transparent',scaleMargins:{top:0.08,bottom:0.22}},timeScale:{borderColor:'transparent',visible:false},crosshair:{mode:0},handleScroll:false,handleScale:false});\n"
        "              const _t0=Math.floor(new Date('2024-01-02').getTime()/1000),_BS=86400;\n"
        "              const _up=opt.dir==='Compra';\n"
        "              let _cd;\n"
        + inner_js +
        "              const cs=ch.addCandlestickSeries({upColor:'#26a69a',downColor:'#ef5350',borderUpColor:'#26a69a',borderDownColor:'#ef5350',wickUpColor:_dk?'rgba(38,166,154,0.65)':'rgba(38,166,154,0.85)',wickDownColor:_dk?'rgba(239,83,80,0.65)':'rgba(239,83,80,0.85)',priceLineVisible:false,lastValueVisible:false});\n"
        "              cs.setData(_cd);\n"
        "              const _ap=_cd.flatMap(c=>[c.high,c.low]);\n"
        "              const _mn=Math.min(..._ap),_mx=Math.max(..._ap),_pd=(_mx-_mn)*0.09;\n"
        "              cs.applyOptions({autoscaleInfoProvider:()=>({priceRange:{minValue:_mn-_pd,maxValue:_mx+_pd}})});\n"
        "              _MARKERS_CALL_\n"
        "              ch.timeScale().fitContent();\n"
        "            });\n"
        "            card.appendChild(_cc);\n"
        "            card.dataset.smcDir=opt.dir;\n"
        "            card.addEventListener('click',()=>{\n"
        "              ms.params.dir=opt.dir;\n"
        "              _dc.querySelectorAll('[data-smc-dir]').forEach(c2=>{\n"
        "                const sel=c2.dataset.smcDir===ms.params.dir;\n"
        "                c2.style.borderColor=sel?'var(--ac)':'var(--bd)';\n"
        "                c2.style.background=sel?'rgba(0,212,170,0.04)':'transparent';\n"
        "                const ring=c2.querySelector('.cring');\n"
        "                if(ring){ring.className='cring'+(sel?' on':'');ring.innerHTML=sel?'<svg width=\"10\" height=\"10\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"#0A0A0F\" stroke-width=\"3\" stroke-linecap=\"round\"><polyline points=\"20 6 9 17 4 12\"/></svg>':'';}});\n"
        "              const _pw=document.getElementById('cond-preview-wrap');\n"
        "              if(_pw){_pw.innerHTML='';const _ct=ms.params.cond+' '+ms.params.dir;_pw.appendChild(buildCondPreview(smcId,_ct,ms.params));_lwcFlush();}\n"
        "            });\n"
        "            _dc.appendChild(card);\n"
        "          });\n"
        "          frag.appendChild(_dc);\n"
        "        }"
    )

# ─── BoS ─────────────────────────────────────────────────────────────────────
BOS_INNER = """\
              if(_up){
                const _bsl=108;
                _cd=[
                  {time:_t0+0*_BS,open:102,high:105,low:101,close:104},
                  {time:_t0+1*_BS,open:104,high:106,low:102,close:103},
                  {time:_t0+2*_BS,open:103,high:105,low:101,close:104},
                  // Swing HIGH = _bsl
                  {time:_t0+3*_BS,open:104,high:_bsl,low:103,close:104},
                  // Pullback — Higher Low
                  {time:_t0+4*_BS,open:104,high:105,low:102,close:103},
                  {time:_t0+5*_BS,open:103,high:104,low:101,close:102},
                  {time:_t0+6*_BS,open:102,high:104,low:101,close:103},
                  // Advance
                  {time:_t0+7*_BS,open:103,high:106,low:102,close:105},
                  {time:_t0+8*_BS,open:105,high:107,low:104,close:106},
                  // BoS: close ABOVE _bsl
                  {time:_t0+9*_BS,open:106,high:_bsl+4,low:105,close:_bsl+3},
                  {time:_t0+10*_BS,open:_bsl+3,high:_bsl+6,low:_bsl+2,close:_bsl+5},
                ];
                ch.addLineSeries({color:'#F0A020',lineWidth:1.5,lineStyle:1,priceLineVisible:false,lastValueVisible:false}).setData(_cd.slice(3,10).map(b=>({time:b.time,value:_bsl})));
                cs.setMarkers([
                  {time:_cd[3].time,position:'aboveBar',color:'#F0A020',shape:'circle',text:'Topo'},
                  {time:_cd[9].time,position:'belowBar',color:'#26a69a',shape:'arrowUp',text:'BoS'},
                ]);
              }else{
                const _bsl=100;
                _cd=[
                  {time:_t0+0*_BS,open:106,high:109,low:105,close:108},
                  {time:_t0+1*_BS,open:108,high:109,low:105,close:106},
                  {time:_t0+2*_BS,open:106,high:108,low:104,close:107},
                  // Swing LOW = _bsl
                  {time:_t0+3*_BS,open:107,high:108,low:_bsl,close:107},
                  // Rally — Lower High
                  {time:_t0+4*_BS,open:107,high:109,low:106,close:108},
                  {time:_t0+5*_BS,open:108,high:110,low:107,close:109},
                  {time:_t0+6*_BS,open:109,high:110,low:107,close:108},
                  // Decline
                  {time:_t0+7*_BS,open:108,high:109,low:105,close:106},
                  {time:_t0+8*_BS,open:106,high:107,low:103,close:104},
                  // BoS: close BELOW _bsl
                  {time:_t0+9*_BS,open:104,high:105,low:_bsl-4,close:_bsl-3},
                  {time:_t0+10*_BS,open:_bsl-3,high:_bsl-2,low:_bsl-6,close:_bsl-5},
                ];
                ch.addLineSeries({color:'#F0A020',lineWidth:1.5,lineStyle:1,priceLineVisible:false,lastValueVisible:false}).setData(_cd.slice(3,10).map(b=>({time:b.time,value:_bsl})));
                cs.setMarkers([
                  {time:_cd[3].time,position:'belowBar',color:'#F0A020',shape:'circle',text:'Fundo'},
                  {time:_cd[9].time,position:'aboveBar',color:'#ef5350',shape:'arrowDown',text:'BoS'},
                ]);
              }
"""

# ─── CHoCH ───────────────────────────────────────────────────────────────────
CHOCH_INNER = """\
              if(_up){
                // Downtrend (LH→LL→LH→LL) then break ABOVE last LH = CHoCH
                const _cl=109;
                _cd=[
                  {time:_t0+0*_BS,open:112,high:_cl+3,low:110,close:110},   // LH1
                  {time:_t0+1*_BS,open:110,high:111,low:106,close:107},
                  {time:_t0+2*_BS,open:107,high:108,low:104,close:105},      // LL1
                  {time:_t0+3*_BS,open:105,high:108,low:104,close:107},
                  {time:_t0+4*_BS,open:107,high:_cl,low:106,close:107},      // LH2 = CHoCH level
                  {time:_t0+5*_BS,open:107,high:108,low:103,close:104},
                  {time:_t0+6*_BS,open:104,high:105,low:101,close:102},      // LL2
                  {time:_t0+7*_BS,open:102,high:105,low:101,close:104},
                  {time:_t0+8*_BS,open:104,high:107,low:103,close:106},
                  {time:_t0+9*_BS,open:106,high:109,low:105,close:108},
                  // CHoCH: closes ABOVE _cl=109
                  {time:_t0+10*_BS,open:108,high:_cl+2,low:107,close:_cl+1},
                  {time:_t0+11*_BS,open:_cl+1,high:_cl+4,low:_cl,close:_cl+3},
                ];
                ch.addLineSeries({color:'#EF4444',lineWidth:1.5,lineStyle:1,priceLineVisible:false,lastValueVisible:false}).setData(_cd.slice(4,11).map(b=>({time:b.time,value:_cl})));
                cs.setMarkers([
                  {time:_cd[4].time,position:'aboveBar',color:'#EF4444',shape:'circle',text:'LH'},
                  {time:_cd[10].time,position:'belowBar',color:'#26a69a',shape:'arrowUp',text:'CHoCH'},
                ]);
              }else{
                // Uptrend (HL→HH→HL→HH) then break BELOW last HL = CHoCH
                const _cl=103;
                _cd=[
                  {time:_t0+0*_BS,open:101,high:102,low:_cl-3,close:102},   // HL1
                  {time:_t0+1*_BS,open:102,high:106,low:101,close:105},
                  {time:_t0+2*_BS,open:105,high:108,low:104,close:107},      // HH1
                  {time:_t0+3*_BS,open:107,high:108,low:104,close:105},
                  {time:_t0+4*_BS,open:105,high:106,low:_cl,close:105},      // HL2 = CHoCH level
                  {time:_t0+5*_BS,open:105,high:108,low:104,close:107},
                  {time:_t0+6*_BS,open:107,high:111,low:106,close:110},      // HH2
                  {time:_t0+7*_BS,open:110,high:111,low:107,close:108},
                  {time:_t0+8*_BS,open:108,high:109,low:105,close:106},
                  {time:_t0+9*_BS,open:106,high:107,low:103,close:104},
                  // CHoCH: closes BELOW _cl=103
                  {time:_t0+10*_BS,open:104,high:105,low:_cl-2,close:_cl-1},
                  {time:_t0+11*_BS,open:_cl-1,high:_cl,low:_cl-4,close:_cl-3},
                ];
                ch.addLineSeries({color:'#EF4444',lineWidth:1.5,lineStyle:1,priceLineVisible:false,lastValueVisible:false}).setData(_cd.slice(4,11).map(b=>({time:b.time,value:_cl})));
                cs.setMarkers([
                  {time:_cd[4].time,position:'belowBar',color:'#EF4444',shape:'circle',text:'HL'},
                  {time:_cd[10].time,position:'aboveBar',color:'#ef5350',shape:'arrowDown',text:'CHoCH'},
                ]);
              }
"""

# ─── Grab ─────────────────────────────────────────────────────────────────────
GRAB_INNER = """\
              if(_up){
                // Bullish: key level at low, extreme hammer, explosive reversal up
                const _gl=100;
                _cd=[
                  {time:_t0+0*_BS,open:104,high:107,low:103,close:106},
                  {time:_t0+1*_BS,open:106,high:108,low:104,close:105},
                  {time:_t0+2*_BS,open:105,high:106,low:102,close:103},
                  {time:_t0+3*_BS,open:103,high:105,low:_gl,close:103},    // first touch — level
                  {time:_t0+4*_BS,open:103,high:105,low:101,close:102},
                  {time:_t0+5*_BS,open:102,high:104,low:_gl,close:102},    // second touch
                  // GRAB: extreme hammer — wick 12pts below level
                  {time:_t0+6*_BS,open:102,high:103,low:_gl-12,close:103},
                  // Explosive reversal
                  {time:_t0+7*_BS,open:103,high:110,low:102,close:108},
                  {time:_t0+8*_BS,open:108,high:114,low:107,close:112},
                  {time:_t0+9*_BS,open:112,high:117,low:111,close:115},
                ];
                ch.addLineSeries({color:'#F0A020',lineWidth:1.5,lineStyle:1,priceLineVisible:false,lastValueVisible:false}).setData(_cd.slice(0,7).map(b=>({time:b.time,value:_gl})));
                cs.setMarkers([
                  {time:_cd[3].time,position:'belowBar',color:'#F0A020',shape:'circle',text:'Nível'},
                  {time:_cd[6].time,position:'belowBar',color:'#ef5350',shape:'arrowDown',text:'Grab'},
                  {time:_cd[7].time,position:'belowBar',color:'#26a69a',shape:'arrowUp',text:'Reversão'},
                ]);
              }else{
                // Bearish: key level at high, extreme shooting star, explosive reversal down
                const _gl=106;
                _cd=[
                  {time:_t0+0*_BS,open:102,high:104,low:101,close:103},
                  {time:_t0+1*_BS,open:103,high:105,low:102,close:104},
                  {time:_t0+2*_BS,open:104,high:107,low:103,close:106},
                  {time:_t0+3*_BS,open:106,high:_gl,low:104,close:104},    // first touch — level
                  {time:_t0+4*_BS,open:104,high:106,low:103,close:105},
                  {time:_t0+5*_BS,open:105,high:_gl,low:103,close:104},    // second touch
                  // GRAB: extreme shooting star — wick 12pts above level
                  {time:_t0+6*_BS,open:104,high:_gl+12,low:103,close:104},
                  // Explosive reversal
                  {time:_t0+7*_BS,open:104,high:105,low:98,close:100},
                  {time:_t0+8*_BS,open:100,high:101,low:95,close:97},
                  {time:_t0+9*_BS,open:97,high:98,low:93,close:95},
                ];
                ch.addLineSeries({color:'#F0A020',lineWidth:1.5,lineStyle:1,priceLineVisible:false,lastValueVisible:false}).setData(_cd.slice(0,7).map(b=>({time:b.time,value:_gl})));
                cs.setMarkers([
                  {time:_cd[3].time,position:'aboveBar',color:'#F0A020',shape:'circle',text:'Nível'},
                  {time:_cd[6].time,position:'aboveBar',color:'#ef5350',shape:'arrowUp',text:'Grab'},
                  {time:_cd[7].time,position:'aboveBar',color:'#26a69a',shape:'arrowDown',text:'Reversão'},
                ]);
              }
"""

# ─── Sweep ────────────────────────────────────────────────────────────────────
SWEEP_INNER = """\
              if(_up){
                // Bullish: 3 equal lows (liquidity pool), extreme pin bar sweeps below, reversal up
                const _sl=100;
                _cd=[
                  {time:_t0+0*_BS,open:106,high:108,low:104,close:105},
                  {time:_t0+1*_BS,open:105,high:107,low:103,close:104},
                  {time:_t0+2*_BS,open:104,high:106,low:_sl,close:104},    // equal low 1
                  {time:_t0+3*_BS,open:104,high:107,low:103,close:105},
                  {time:_t0+4*_BS,open:105,high:106,low:_sl,close:104},    // equal low 2
                  {time:_t0+5*_BS,open:104,high:106,low:102,close:104},
                  {time:_t0+6*_BS,open:104,high:105,low:_sl,close:103},    // equal low 3
                  // SWEEP: extreme pin bar — wick 11pts below level, body closes back above
                  {time:_t0+7*_BS,open:103,high:104,low:_sl-11,close:104},
                  // Explosive reversal
                  {time:_t0+8*_BS,open:104,high:110,low:103,close:108},
                  {time:_t0+9*_BS,open:108,high:114,low:107,close:112},
                  {time:_t0+10*_BS,open:112,high:117,low:111,close:115},
                ];
                ch.addLineSeries({color:'#F0A020',lineWidth:1.5,lineStyle:1,priceLineVisible:false,lastValueVisible:false}).setData(_cd.slice(0,8).map(b=>({time:b.time,value:_sl})));
                cs.setMarkers([
                  {time:_cd[2].time,position:'belowBar',color:'#F0A020',shape:'circle',text:'1'},
                  {time:_cd[4].time,position:'belowBar',color:'#F0A020',shape:'circle',text:'2'},
                  {time:_cd[6].time,position:'belowBar',color:'#F0A020',shape:'circle',text:'3'},
                  {time:_cd[7].time,position:'belowBar',color:'#ef5350',shape:'arrowDown',text:'Sweep'},
                  {time:_cd[8].time,position:'belowBar',color:'#26a69a',shape:'arrowUp',text:'Reversão'},
                ]);
              }else{
                // Bearish: 3 equal highs (liquidity pool), extreme shooting star sweeps above, reversal down
                const _sl=106;
                _cd=[
                  {time:_t0+0*_BS,open:100,high:102,low:99,close:101},
                  {time:_t0+1*_BS,open:101,high:103,low:100,close:102},
                  {time:_t0+2*_BS,open:102,high:_sl,low:100,close:102},    // equal high 1
                  {time:_t0+3*_BS,open:102,high:104,low:100,close:101},
                  {time:_t0+4*_BS,open:101,high:_sl,low:100,close:102},    // equal high 2
                  {time:_t0+5*_BS,open:102,high:104,low:100,close:102},
                  {time:_t0+6*_BS,open:102,high:_sl,low:101,close:103},    // equal high 3
                  // SWEEP: extreme shooting star — wick 11pts above level, body closes back below
                  {time:_t0+7*_BS,open:103,high:_sl+11,low:102,close:102},
                  // Explosive reversal
                  {time:_t0+8*_BS,open:102,high:103,low:97,close:98},
                  {time:_t0+9*_BS,open:98,high:99,low:94,close:95},
                  {time:_t0+10*_BS,open:95,high:96,low:91,close:92},
                ];
                ch.addLineSeries({color:'#F0A020',lineWidth:1.5,lineStyle:1,priceLineVisible:false,lastValueVisible:false}).setData(_cd.slice(0,8).map(b=>({time:b.time,value:_sl})));
                cs.setMarkers([
                  {time:_cd[2].time,position:'aboveBar',color:'#F0A020',shape:'circle',text:'1'},
                  {time:_cd[4].time,position:'aboveBar',color:'#F0A020',shape:'circle',text:'2'},
                  {time:_cd[6].time,position:'aboveBar',color:'#F0A020',shape:'circle',text:'3'},
                  {time:_cd[7].time,position:'aboveBar',color:'#ef5350',shape:'arrowUp',text:'Sweep'},
                  {time:_cd[8].time,position:'aboveBar',color:'#26a69a',shape:'arrowDown',text:'Reversão'},
                ]);
              }
"""

# ── The _MARKERS_CALL_ placeholder must be removed since markers are set
#    inside each if/else branch above. Replace placeholder with empty string.
def build_block(tooltip, buy_title, buy_desc, sell_title, sell_desc, inner):
    block = dir_cards_block(tooltip, buy_title, buy_desc, sell_title, sell_desc, inner)
    return block.replace('              _MARKERS_CALL_\n', '')

# ─── BoS replacement ──────────────────────────────────────────────────────────
OLD_BOS_PILLS = "        frag.appendChild(pills('Direção','Compra = detecta BoS de alta (rompimento de topo). Venda = detecta BoS de baixa (rompimento de fundo).',['Compra','Venda'],ms.params.dir,v=>{ms.params.dir=v;}));"
NEW_BOS = build_block(
    'Compra detecta rompimento de topo (estrutura de alta). Venda detecta rompimento de fundo (estrutura de baixa).',
    'Compra — BoS de Alta',
    'Rompimento de topo: swing HIGH estabelecido → pullback com Higher Low → fechamento acima do topo.',
    'Venda — BoS de Baixa',
    'Rompimento de fundo: swing LOW estabelecido → rally com Lower High → fechamento abaixo do fundo.',
    BOS_INNER
)
ok1 = OLD_BOS_PILLS in content
content = content.replace(OLD_BOS_PILLS, NEW_BOS, 1)
print('BoS direction cards:', 'OK' if ok1 else 'NOT FOUND')

# ─── CHoCH replacement ────────────────────────────────────────────────────────
OLD_CHOCH_PILLS = "        frag.appendChild(pills('Direção','Compra = detecta reversão de baixa para alta. Venda = detecta reversão de alta para baixa.',['Compra','Venda'],ms.params.dir,v=>{ms.params.dir=v;}));"
NEW_CHOCH = build_block(
    'Compra detecta reversão de baixa para alta (CHoCH bullish). Venda detecta reversão de alta para baixa (CHoCH bearish).',
    'Compra — CHoCH de Alta',
    'Downtrend (LH→LL→LH→LL) seguido de fechamento acima da última máxima relevante — sinaliza reversão.',
    'Venda — CHoCH de Baixa',
    'Uptrend (HL→HH→HL→HH) seguido de fechamento abaixo do último fundo relevante — sinaliza reversão.',
    CHOCH_INNER
)
ok2 = OLD_CHOCH_PILLS in content
content = content.replace(OLD_CHOCH_PILLS, NEW_CHOCH, 1)
print('CHoCH direction cards:', 'OK' if ok2 else 'NOT FOUND')

# ─── Grab replacement ─────────────────────────────────────────────────────────
OLD_GRAB_PILLS = "        frag.appendChild(pills('Direção','Compra = rejeição em fundo (pavio longo para baixo, fechamento na metade superior). Venda = rejeição em topo (pavio longo para cima, fechamento na metade inferior).',['Compra','Venda'],ms.params.dir,v=>{ms.params.dir=v;}));"
NEW_GRAB = build_block(
    'Compra: pavio longo para baixo, fechamento na metade superior do candle. Venda: pavio longo para cima, fechamento na metade inferior.',
    'Compra — Grab em Suporte',
    'Pavio ≥ 50% do range captura stops abaixo do nível. Corpo fecha na metade superior — sinal de rejeição agressiva.',
    'Venda — Grab em Resistência',
    'Pavio ≥ 50% do range captura stops acima do nível. Corpo fecha na metade inferior — sinal de rejeição agressiva.',
    GRAB_INNER
)
ok3 = OLD_GRAB_PILLS in content
content = content.replace(OLD_GRAB_PILLS, NEW_GRAB, 1)
print('Grab direction cards:', 'OK' if ok3 else 'NOT FOUND')

# ─── Sweep replacement ────────────────────────────────────────────────────────
OLD_SWEEP_PILLS = "        frag.appendChild(pills('Direção','Compra = sweep de mínimas (falso rompimento para baixo, reversão para cima). Venda = sweep de máximas (falso rompimento para cima, reversão para baixo).',['Compra','Venda'],ms.params.dir,v=>{ms.params.dir=v;}));"
NEW_SWEEP = build_block(
    'Compra: sweep de mínimas (stop hunt para baixo, reversão para cima). Venda: sweep de máximas (stop hunt para cima, reversão para baixo).',
    'Compra — Sweep de Mínimas',
    '3+ mínimas iguais formam pool de liquidez. Pin bar com pavio longo para baixo captura os stops e reverte para cima.',
    'Venda — Sweep de Máximas',
    '3+ máximas iguais formam pool de liquidez. Pin bar com pavio longo para cima captura os stops e reverte para baixo.',
    SWEEP_INNER
)
ok4 = OLD_SWEEP_PILLS in content
content = content.replace(OLD_SWEEP_PILLS, NEW_SWEEP, 1)
print('Sweep direction cards:', 'OK' if ok4 else 'NOT FOUND')

# ─── Write back ───────────────────────────────────────────────────────────────
with open(FPATH, 'w', encoding='utf-8') as f:
    f.write(content)
print('File written:', len(content), 'chars')
print('patch_fix7 DONE')

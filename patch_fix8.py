#!/usr/bin/env python3
# patch_fix8.py — Two critical fixes:
#
# FIX A — cs-before-declaration in all 4 direction card _lwcRender blocks
#   root cause: INNER_JS had cs.setMarkers([...]) INSIDE if(_up)/else,
#   but `const cs=ch.addCandlestickSeries` was AFTER the if/else block.
#   JS temporal dead zone → ReferenceError → LWC charts silently blank.
#   fix:  (1) move const cs BEFORE if(_up)
#         (2) change cs.setMarkers([...]) → _markers=[...] in if/else
#         (3) add cs.setMarkers(_markers) AFTER cs.setData(_cd)
#
# FIX B — Replace BoS and CHoCH miniSVG info diagrams with LWC charts
#   These static SVG diagrams (FASE 1/2/3, ETAPA 1/2/3) were never
#   replaced — they're what the user sees as "unchanged".

FPATH = 'C:/Users/Clayton Barros/AppData/Local/Temp/backtest-pro/app.html'
with open(FPATH, 'r', encoding='utf-8') as f:
    content = f.read()

CS_DECL = ("              const cs=ch.addCandlestickSeries({upColor:'#26a69a',downColor:'#ef5350',"
           "borderUpColor:'#26a69a',borderDownColor:'#ef5350',"
           "wickUpColor:_dk?'rgba(38,166,154,0.65)':'rgba(38,166,154,0.85)',"
           "wickDownColor:_dk?'rgba(239,83,80,0.65)':'rgba(239,83,80,0.85)',"
           "priceLineVisible:false,lastValueVisible:false});")

# ══════════════════════════════════════════════════════════════════════════════
# FIX A-1  Move `const cs` BEFORE `if(_up)` + add `let _markers=[]`
# Safe: `if(_up)` only appears in direction card blocks (buildCondPreview uses `if(up)`)
# ══════════════════════════════════════════════════════════════════════════════
OLD_LET = "              let _cd;\n              if(_up){"
NEW_LET = ("              let _cd;let _markers=[];\n"
           + CS_DECL + "\n"
           "              if(_up){")
n1 = content.count(OLD_LET)
content = content.replace(OLD_LET, NEW_LET)
print(f'FIX A-1 (moved const cs before if): {n1} blocks')

# ══════════════════════════════════════════════════════════════════════════════
# FIX A-2  Replace each cs.setMarkers([...]) in if/else with _markers=[...]
# Each block is unique by its marker text — replace individually (8 total)
# ══════════════════════════════════════════════════════════════════════════════
MARKER_FIXES = [
    # ── BoS Compra ──
    (
        "                cs.setMarkers([\n"
        "                  {time:_cd[3].time,position:'aboveBar',color:'#F0A020',shape:'circle',text:'Topo'},\n"
        "                  {time:_cd[9].time,position:'belowBar',color:'#26a69a',shape:'arrowUp',text:'BoS'},\n"
        "                ]);"
        ,
        "                _markers=[\n"
        "                  {time:_cd[3].time,position:'aboveBar',color:'#F0A020',shape:'circle',text:'Topo'},\n"
        "                  {time:_cd[9].time,position:'belowBar',color:'#26a69a',shape:'arrowUp',text:'BoS'},\n"
        "                ];"
    ),
    # ── BoS Venda ──
    (
        "                cs.setMarkers([\n"
        "                  {time:_cd[3].time,position:'belowBar',color:'#F0A020',shape:'circle',text:'Fundo'},\n"
        "                  {time:_cd[9].time,position:'aboveBar',color:'#ef5350',shape:'arrowDown',text:'BoS'},\n"
        "                ]);"
        ,
        "                _markers=[\n"
        "                  {time:_cd[3].time,position:'belowBar',color:'#F0A020',shape:'circle',text:'Fundo'},\n"
        "                  {time:_cd[9].time,position:'aboveBar',color:'#ef5350',shape:'arrowDown',text:'BoS'},\n"
        "                ];"
    ),
    # ── CHoCH Compra ──
    (
        "                cs.setMarkers([\n"
        "                  {time:_cd[4].time,position:'aboveBar',color:'#EF4444',shape:'circle',text:'LH'},\n"
        "                  {time:_cd[10].time,position:'belowBar',color:'#26a69a',shape:'arrowUp',text:'CHoCH'},\n"
        "                ]);"
        ,
        "                _markers=[\n"
        "                  {time:_cd[4].time,position:'aboveBar',color:'#EF4444',shape:'circle',text:'LH'},\n"
        "                  {time:_cd[10].time,position:'belowBar',color:'#26a69a',shape:'arrowUp',text:'CHoCH'},\n"
        "                ];"
    ),
    # ── CHoCH Venda ──
    (
        "                cs.setMarkers([\n"
        "                  {time:_cd[4].time,position:'belowBar',color:'#EF4444',shape:'circle',text:'HL'},\n"
        "                  {time:_cd[10].time,position:'aboveBar',color:'#ef5350',shape:'arrowDown',text:'CHoCH'},\n"
        "                ]);"
        ,
        "                _markers=[\n"
        "                  {time:_cd[4].time,position:'belowBar',color:'#EF4444',shape:'circle',text:'HL'},\n"
        "                  {time:_cd[10].time,position:'aboveBar',color:'#ef5350',shape:'arrowDown',text:'CHoCH'},\n"
        "                ];"
    ),
    # ── Grab Compra ──
    (
        "                cs.setMarkers([\n"
        "                  {time:_cd[3].time,position:'belowBar',color:'#F0A020',shape:'circle',text:'Nível'},\n"
        "                  {time:_cd[6].time,position:'belowBar',color:'#ef5350',shape:'arrowDown',text:'Grab'},\n"
        "                  {time:_cd[7].time,position:'belowBar',color:'#26a69a',shape:'arrowUp',text:'Reversão'},\n"
        "                ]);"
        ,
        "                _markers=[\n"
        "                  {time:_cd[3].time,position:'belowBar',color:'#F0A020',shape:'circle',text:'Nível'},\n"
        "                  {time:_cd[6].time,position:'belowBar',color:'#ef5350',shape:'arrowDown',text:'Grab'},\n"
        "                  {time:_cd[7].time,position:'belowBar',color:'#26a69a',shape:'arrowUp',text:'Reversão'},\n"
        "                ];"
    ),
    # ── Grab Venda ──
    (
        "                cs.setMarkers([\n"
        "                  {time:_cd[3].time,position:'aboveBar',color:'#F0A020',shape:'circle',text:'Nível'},\n"
        "                  {time:_cd[6].time,position:'aboveBar',color:'#ef5350',shape:'arrowUp',text:'Grab'},\n"
        "                  {time:_cd[7].time,position:'aboveBar',color:'#26a69a',shape:'arrowDown',text:'Reversão'},\n"
        "                ]);"
        ,
        "                _markers=[\n"
        "                  {time:_cd[3].time,position:'aboveBar',color:'#F0A020',shape:'circle',text:'Nível'},\n"
        "                  {time:_cd[6].time,position:'aboveBar',color:'#ef5350',shape:'arrowUp',text:'Grab'},\n"
        "                  {time:_cd[7].time,position:'aboveBar',color:'#26a69a',shape:'arrowDown',text:'Reversão'},\n"
        "                ];"
    ),
    # ── Sweep Compra ──
    (
        "                cs.setMarkers([\n"
        "                  {time:_cd[2].time,position:'belowBar',color:'#F0A020',shape:'circle',text:'1'},\n"
        "                  {time:_cd[4].time,position:'belowBar',color:'#F0A020',shape:'circle',text:'2'},\n"
        "                  {time:_cd[6].time,position:'belowBar',color:'#F0A020',shape:'circle',text:'3'},\n"
        "                  {time:_cd[7].time,position:'belowBar',color:'#ef5350',shape:'arrowDown',text:'Sweep'},\n"
        "                  {time:_cd[8].time,position:'belowBar',color:'#26a69a',shape:'arrowUp',text:'Reversão'},\n"
        "                ]);"
        ,
        "                _markers=[\n"
        "                  {time:_cd[2].time,position:'belowBar',color:'#F0A020',shape:'circle',text:'1'},\n"
        "                  {time:_cd[4].time,position:'belowBar',color:'#F0A020',shape:'circle',text:'2'},\n"
        "                  {time:_cd[6].time,position:'belowBar',color:'#F0A020',shape:'circle',text:'3'},\n"
        "                  {time:_cd[7].time,position:'belowBar',color:'#ef5350',shape:'arrowDown',text:'Sweep'},\n"
        "                  {time:_cd[8].time,position:'belowBar',color:'#26a69a',shape:'arrowUp',text:'Reversão'},\n"
        "                ];"
    ),
    # ── Sweep Venda ──
    (
        "                cs.setMarkers([\n"
        "                  {time:_cd[2].time,position:'aboveBar',color:'#F0A020',shape:'circle',text:'1'},\n"
        "                  {time:_cd[4].time,position:'aboveBar',color:'#F0A020',shape:'circle',text:'2'},\n"
        "                  {time:_cd[6].time,position:'aboveBar',color:'#F0A020',shape:'circle',text:'3'},\n"
        "                  {time:_cd[7].time,position:'aboveBar',color:'#ef5350',shape:'arrowUp',text:'Sweep'},\n"
        "                  {time:_cd[8].time,position:'aboveBar',color:'#26a69a',shape:'arrowDown',text:'Reversão'},\n"
        "                ]);"
        ,
        "                _markers=[\n"
        "                  {time:_cd[2].time,position:'aboveBar',color:'#F0A020',shape:'circle',text:'1'},\n"
        "                  {time:_cd[4].time,position:'aboveBar',color:'#F0A020',shape:'circle',text:'2'},\n"
        "                  {time:_cd[6].time,position:'aboveBar',color:'#F0A020',shape:'circle',text:'3'},\n"
        "                  {time:_cd[7].time,position:'aboveBar',color:'#ef5350',shape:'arrowUp',text:'Sweep'},\n"
        "                  {time:_cd[8].time,position:'aboveBar',color:'#26a69a',shape:'arrowDown',text:'Reversão'},\n"
        "                ];"
    ),
]

for i, (old, new) in enumerate(MARKER_FIXES):
    found = old in content
    content = content.replace(old, new, 1)
    labels = ['BoS-C','BoS-V','CHoCH-C','CHoCH-V','Grab-C','Grab-V','Sweep-C','Sweep-V']
    print(f'  FIX A-2 markers {labels[i]}: {"OK" if found else "NOT FOUND"}')

# ══════════════════════════════════════════════════════════════════════════════
# FIX A-3  Remove duplicate `const cs` (now after if/else) + add setMarkers after setData
# The pattern `CS_DECL\n              cs.setData(_cd)` only matches the
# original post-if/else position (Fix A-1 put cs BEFORE if/else followed by
# `if(_up){`, not `cs.setData`).
# ══════════════════════════════════════════════════════════════════════════════
OLD_CS_DATA = CS_DECL + "\n              cs.setData(_cd);"
NEW_CS_DATA = "              cs.setData(_cd);\n              cs.setMarkers(_markers);"
n3 = content.count(OLD_CS_DATA)
content = content.replace(OLD_CS_DATA, NEW_CS_DATA)
print(f'FIX A-3 (removed dup cs + added setMarkers after setData): {n3} blocks')

# ══════════════════════════════════════════════════════════════════════════════
# FIX B-1  Replace BoS miniSVG with LWC chart
# ══════════════════════════════════════════════════════════════════════════════
OLD_BOS_SVG = """\
        // Visualização gráfica do padrão BoS — 3 fases
        frag.appendChild(miniSVG(500,130,(ln,rc,tx,cd,ci,th)=>{
          // Contexto — candles anteriores neutros
          cd(8,80,12,60,86,0.3); cd(22,74,10,56,80,0.3);

          // FASE 1 — 1ª perna de alta (3 candles bullish consecutivos)
          rc(36,54,12,22,'#10B981',0.85,1); ln(42,48,42,80,'#10B981',1.5);
          rc(52,36,12,24,'#10B981',0.9,1);  ln(58,30,58,64,'#10B981',1.5);
          rc(68,22,12,20,'#10B981',0.85,1); ln(74,16,74,46,'#10B981',1.5);
          // High1 — nível a ser rompido
          ln(36,22,500,22,'#F59E0B',0.8,'4,3');
          tx(80,18,'High1',th.txs,9);
          // Low1 — ponto de invalidação
          ln(36,76,180,76,'#EF4444',0.5,'3,2');
          tx(80,82,'Low1 (stop)',th.txs,8);
          tx(36,120,'FASE 1',th.txm,9,'start');

          // FASE 2 — Correção (2 candles bearish, não rompe Low1)
          rc(86,38,12,28,'#EF4444',0.7,1); ln(92,32,92,70,'#EF4444',1.2);
          rc(102,52,12,22,'#EF4444',0.65,1); ln(108,46,108,78,'#EF4444',1.2);
          tx(86,120,'FASE 2',th.txm,9,'start');

          // FASE 3 — 2ª perna rompe High1
          rc(118,34,12,28,'#10B981',0.85,1); ln(124,28,124,66,'#10B981',1.5);
          rc(134,10,12,30,'#10B981',0.9,1);  ln(140,4,140,44,'#10B981',1.5);
          // Seta de confirmação no rompimento
          ci(140,10,'#00D4AA',4);
          ln(148,14,162,14,'#00D4AA',1.5);
          tx(164,18,'BoS!','#00D4AA',11);
          tx(118,120,'FASE 3',th.txm,9,'start');

          // Linha divisória entre fases
          ln(82,10,82,118,th.bd,0.6,'2,3');
          ln(114,10,114,118,th.bd,0.6,'2,3');
        }));"""

NEW_BOS_SVG = """\
        // Visualização gráfica do padrão BoS — LWC
        {const _bh=160;const _bc=div('');_bc.style.cssText='height:'+_bh+'px;overflow:hidden;margin-bottom:8px';
        _lwcRender(_bc,(cW)=>{
          if(!window.LightweightCharts)return;
          const _dk=document.documentElement.getAttribute('data-theme')!=='light';
          const _bg=_dk?'#0E0E16':'#F0F0EB',_gr=_dk?'rgba(255,255,255,0.04)':'rgba(0,0,0,0.05)',_xt=_dk?'#8888A0':'#909090';
          const _ch=LightweightCharts.createChart(_bc,{width:cW,height:_bh,
            layout:{background:{color:_bg},textColor:_xt},
            grid:{vertLines:{color:_gr},horzLines:{color:_gr}},
            rightPriceScale:{borderColor:'transparent',scaleMargins:{top:0.1,bottom:0.22}},
            timeScale:{borderColor:'transparent',visible:false},crosshair:{mode:0},
            handleScroll:false,handleScale:false,
            watermark:{visible:true,fontSize:10,horzAlign:'left',vertAlign:'top',color:_xt,text:'Sequência BoS de Alta'}
          });
          const _t0s=Math.floor(new Date('2024-01-02').getTime()/1000),_BS=86400;
          const _lvl=108;
          const _bd=[
            {time:_t0s+0*_BS,open:100,high:102,low:99, close:101},
            {time:_t0s+1*_BS,open:101,high:103,low:100,close:102},
            {time:_t0s+2*_BS,open:102,high:104,low:101,close:103},
            {time:_t0s+3*_BS,open:103,high:106,low:102,close:105},
            {time:_t0s+4*_BS,open:105,high:_lvl,low:104,close:106},
            {time:_t0s+5*_BS,open:106,high:107,low:104,close:105},
            {time:_t0s+6*_BS,open:105,high:106,low:103,close:104},
            {time:_t0s+7*_BS,open:104,high:105,low:103,close:104},
            {time:_t0s+8*_BS,open:104,high:106,low:103,close:105},
            {time:_t0s+9*_BS,open:105,high:108,low:104,close:107},
            {time:_t0s+10*_BS,open:107,high:_lvl+3,low:106,close:_lvl+2},
            {time:_t0s+11*_BS,open:_lvl+2,high:_lvl+5,low:_lvl+1,close:_lvl+4},
            {time:_t0s+12*_BS,open:_lvl+4,high:_lvl+7,low:_lvl+3,close:_lvl+6},
          ];
          _ch.addLineSeries({color:'#F59E0B',lineWidth:1.5,lineStyle:2,
            priceLineVisible:false,lastValueVisible:false
          }).setData(_bd.slice(4,11).map(b=>({time:b.time,value:_lvl})));
          const _cs=_ch.addCandlestickSeries({
            upColor:'#26a69a',downColor:'#ef5350',
            borderUpColor:'#26a69a',borderDownColor:'#ef5350',
            wickUpColor:_dk?'rgba(38,166,154,0.6)':'rgba(38,166,154,0.8)',
            wickDownColor:_dk?'rgba(239,83,80,0.6)':'rgba(239,83,80,0.8)',
            priceLineVisible:false,lastValueVisible:false
          });
          _cs.setData(_bd);
          const _ap=_bd.flatMap(c=>[c.high,c.low]);
          const _mn=Math.min(..._ap),_mx=Math.max(..._ap),_pd=(_mx-_mn)*0.08;
          _cs.applyOptions({autoscaleInfoProvider:()=>({priceRange:{minValue:_mn-_pd,maxValue:_mx+_pd}})});
          _cs.setMarkers([
            {time:_bd[4].time, position:'aboveBar',color:'#F59E0B',shape:'circle',  text:'Topo'},
            {time:_bd[7].time, position:'belowBar',color:'#26a69a',shape:'circle',  text:'HL'},
            {time:_bd[10].time,position:'belowBar',color:'#00D4AA',shape:'arrowUp', text:'BoS'},
          ]);
          _ch.timeScale().fitContent();
        });
        frag.appendChild(_bc);}"""

ok_b1 = OLD_BOS_SVG in content
content = content.replace(OLD_BOS_SVG, NEW_BOS_SVG, 1)
print(f'FIX B-1 (BoS miniSVG->LWC): {"OK" if ok_b1 else "NOT FOUND"}')

# ══════════════════════════════════════════════════════════════════════════════
# FIX B-2  Replace CHoCH miniSVG with LWC chart
# ══════════════════════════════════════════════════════════════════════════════
OLD_CHOCH_SVG = """\
        // Visualização das 3 etapas do CHoCH
        // Divisórias: x=125 e x=240 — calculadas para evitar sobreposição de texto
        frag.appendChild(miniSVG(500,160,(ln,rc,tx,cd,ci,th)=>{
          // ── ETAPA 1 — Tendência prévia de BAIXA (x: 0–125) ──
          rc(8,22,14,32,'#EF4444',0.85,1);  ln(15,17,15,58,'#EF4444',1.5);
          rc(26,36,14,28,'#EF4444',0.8,1);  ln(33,31,33,68,'#EF4444',1.5);
          rc(44,50,14,26,'#EF4444',0.75,1); ln(51,45,51,80,'#EF4444',1.5);
          rc(62,62,14,24,'#EF4444',0.7,1);  ln(69,57,69,90,'#EF4444',1.5);
          rc(80,74,14,22,'#EF4444',0.65,1); ln(87,69,87,100,'#EF4444',1.5);
          tx(8,142,'ETAPA 1',th.txm,9,'start');
          tx(8,155,'Tendência de baixa',th.txs,9,'start');

          // Divisória 1 (x=125)
          ln(125,6,125,132,th.bd,0.7,'3,3');

          // ── ETAPA 2 — Impulso de alta (x: 125–240) ──
          // High1 — nível a ser rompido na etapa 3
          ln(125,46,500,46,'#F59E0B',0.75,'5,4');
          tx(380,40,'High1','#F59E0B',9);
          // 3 candles bullish subindo
          rc(131,58,14,36,'#10B981',0.9,1); ln(138,18,138,98,'#10B981',1.5);
          rc(149,36,14,32,'#10B981',0.9,1); ln(156,10,156,72,'#10B981',1.5);
          rc(167,18,14,28,'#10B981',0.85,1);ln(174,6,174,50,'#10B981',1.5);
          tx(131,142,'ETAPA 2',th.txm,9,'start');
          tx(131,155,'Impulso de alta',th.txs,9,'start');

          // Divisória 2 (x=240)
          ln(240,6,240,132,th.bd,0.7,'3,3');

          // ── ETAPA 3 — Correção + rompimento (x: 240–500) ──
          // Correção: 2 candles bearish
          rc(246,26,14,24,'#EF4444',0.65,1); ln(253,20,253,54,'#EF4444',1.2);
          rc(264,36,14,20,'#EF4444',0.6,1);  ln(271,30,271,60,'#EF4444',1.2);
          // 2ª perna: rompe High1
          rc(282,18,14,30,'#10B981',0.9,1);  ln(289,4,289,52,'#10B981',1.5);
          rc(300,4,14,26,'#10B981',0.9,1);   ln(307,0,307,34,'#10B981',1.5);
          // Confirmação CHoCH
          ci(307,0,'#00D4AA',5);
          ln(316,4,336,4,'#00D4AA',1.5);
          tx(340,8,'CHoCH!','#00D4AA',12);
          tx(246,142,'ETAPA 3',th.txm,9,'start');
          tx(246,155,'Correção + ruptura',th.txs,9,'start');
        }));"""

NEW_CHOCH_SVG = """\
        // Visualização das 3 etapas do CHoCH — LWC
        {const _bh2=170;const _bc2=div('');_bc2.style.cssText='height:'+_bh2+'px;overflow:hidden;margin-bottom:8px';
        _lwcRender(_bc2,(cW)=>{
          if(!window.LightweightCharts)return;
          const _dk=document.documentElement.getAttribute('data-theme')!=='light';
          const _bg=_dk?'#0E0E16':'#F0F0EB',_gr=_dk?'rgba(255,255,255,0.04)':'rgba(0,0,0,0.05)',_xt=_dk?'#8888A0':'#909090';
          const _ch2=LightweightCharts.createChart(_bc2,{width:cW,height:_bh2,
            layout:{background:{color:_bg},textColor:_xt},
            grid:{vertLines:{color:_gr},horzLines:{color:_gr}},
            rightPriceScale:{borderColor:'transparent',scaleMargins:{top:0.1,bottom:0.22}},
            timeScale:{borderColor:'transparent',visible:false},crosshair:{mode:0},
            handleScroll:false,handleScale:false,
            watermark:{visible:true,fontSize:10,horzAlign:'left',vertAlign:'top',color:_xt,text:'Sequência CHoCH de Alta'}
          });
          const _t0s=Math.floor(new Date('2024-01-02').getTime()/1000),_BS=86400;
          const _lh=109;
          const _bd2=[
            {time:_t0s+0*_BS, open:115,high:116,   low:113,  close:114},
            {time:_t0s+1*_BS, open:114,high:115,   low:111,  close:112},
            {time:_t0s+2*_BS, open:112,high:113,   low:109,  close:110},
            {time:_t0s+3*_BS, open:110,high:_lh+3, low:109,  close:111},
            {time:_t0s+4*_BS, open:111,high:112,   low:108,  close:109},
            {time:_t0s+5*_BS, open:109,high:_lh,   low:108,  close:109},
            {time:_t0s+6*_BS, open:109,high:110,   low:105,  close:106},
            {time:_t0s+7*_BS, open:106,high:107,   low:103,  close:104},
            {time:_t0s+8*_BS, open:104,high:107,   low:103,  close:106},
            {time:_t0s+9*_BS, open:106,high:110,   low:105,  close:109},
            {time:_t0s+10*_BS,open:109,high:_lh+3, low:108,  close:_lh+2},
            {time:_t0s+11*_BS,open:_lh+2,high:_lh+5,low:_lh+1,close:_lh+4},
          ];
          _ch2.addLineSeries({color:'#EF4444',lineWidth:1.5,lineStyle:2,
            priceLineVisible:false,lastValueVisible:false
          }).setData(_bd2.slice(5,11).map(b=>({time:b.time,value:_lh})));
          const _cs2=_ch2.addCandlestickSeries({
            upColor:'#26a69a',downColor:'#ef5350',
            borderUpColor:'#26a69a',borderDownColor:'#ef5350',
            wickUpColor:_dk?'rgba(38,166,154,0.6)':'rgba(38,166,154,0.8)',
            wickDownColor:_dk?'rgba(239,83,80,0.6)':'rgba(239,83,80,0.8)',
            priceLineVisible:false,lastValueVisible:false
          });
          _cs2.setData(_bd2);
          const _ap2=_bd2.flatMap(c=>[c.high,c.low]);
          const _mn2=Math.min(..._ap2),_mx2=Math.max(..._ap2),_pd2=(_mx2-_mn2)*0.08;
          _cs2.applyOptions({autoscaleInfoProvider:()=>({priceRange:{minValue:_mn2-_pd2,maxValue:_mx2+_pd2}})});
          _cs2.setMarkers([
            {time:_bd2[0].time, position:'aboveBar',color:'#EF4444',shape:'circle',  text:'LH'},
            {time:_bd2[5].time, position:'aboveBar',color:'#EF4444',shape:'circle',  text:'LH'},
            {time:_bd2[7].time, position:'belowBar',color:'#EF4444',shape:'circle',  text:'LL'},
            {time:_bd2[10].time,position:'belowBar',color:'#00D4AA',shape:'arrowUp', text:'CHoCH'},
          ]);
          _ch2.timeScale().fitContent();
        });
        frag.appendChild(_bc2);}"""

ok_b2 = OLD_CHOCH_SVG in content
content = content.replace(OLD_CHOCH_SVG, NEW_CHOCH_SVG, 1)
print(f'FIX B-2 (CHoCH miniSVG->LWC): {"OK" if ok_b2 else "NOT FOUND"}')

# ── Write back ────────────────────────────────────────────────────────────────
with open(FPATH, 'w', encoding='utf-8') as f:
    f.write(content)
print(f'File written: {len(content)} chars')
print('patch_fix8 DONE')

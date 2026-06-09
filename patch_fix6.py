#!/usr/bin/env python3
# patch_fix6.py — SMC visual redesign: fix flat candles + redo cards from scratch
#
# Changes:
#  1. All 5 buildCondPreview SMC charts: autoscaleInfoProvider (forces tight scale)
#     + bottom scaleMargin 0.18 for belowBar marker space
#  2. FVG condition cards: replace static svgFn with real LWC candlestick charts
#  3. Grab/Sweep info diagrams: replace miniSVG with compact LWC charts

FPATH = 'C:/Users/Clayton Barros/AppData/Local/Temp/backtest-pro/app.html'
with open(FPATH, 'r', encoding='utf-8') as f:
    content = f.read()

# ─────────────────────────────────────────────────────────────────────────────
# 1. Fix scale margins: all 3 variants → {top:0.08, bottom:0.18}
# ─────────────────────────────────────────────────────────────────────────────
n_sm = 0
for old_sm, new_sm in [
    ("scaleMargins:{top:0.10,bottom:0.08}", "scaleMargins:{top:0.08,bottom:0.18}"),  # FVG
    ("scaleMargins:{top:0.10,bottom:0.10}", "scaleMargins:{top:0.08,bottom:0.18}"),  # BoS+CHoCH
    ("scaleMargins:{top:0.12,bottom:0.12}", "scaleMargins:{top:0.08,bottom:0.18}"),  # Sweep+Grab
]:
    count = content.count(old_sm)
    n_sm += count
    content = content.replace(old_sm, new_sm)
print(f'Scale margins fixed: {n_sm} occurrences')

# ─────────────────────────────────────────────────────────────────────────────
# 2. autoscaleInfoProvider for each chart (forces tight scale, kills flat candles)
# ─────────────────────────────────────────────────────────────────────────────
_ASCALE = '\n      {{const _aP={DA}.flatMap(c=>[c.high,c.low]);const _mn=Math.min(..._aP),_mx=Math.max(..._aP),_pd=(_mx-_mn)*0.09;cs.applyOptions({{autoscaleInfoProvider:()=>({{priceRange:{{minValue:_mn-_pd,maxValue:_mx+_pd}}}})}})}}'

for da, old_next in [
    ('fd',  '      cs.setData(fd);\n\n      // Entry marker'),
    ('bd',  '      cs.setData(bd);\n      cs.setMarkers([\n        {time:bd[swingIdx]'),
    ('cd2', '      cs.setData(cd2);\n      cs.setMarkers([\n        {time:cd2[lhIdx]'),
    ('sd',  '      cs.setData(sd);\n      cs.setMarkers([\n        {time:sd[swpi]'),
    ('gd',  '      cs.setData(gd);\n      cs.setMarkers([\n        // First touch'),
]:
    insert = _ASCALE.format(DA=da)
    # Build old string without the autoscale line
    old_str = old_next
    new_str = old_str.replace(f'      cs.setData({da});', f'      cs.setData({da});{insert}', 1)
    ok = old_str in content
    if ok:
        content = content.replace(old_str, new_str, 1)
    print(f'autoscaleInfoProvider ({da}): {"OK" if ok else "NOT FOUND"}')

# ─────────────────────────────────────────────────────────────────────────────
# 3. FVG condition cards: remove svgFn from COND_OPTIONS, rebuild as LWC
# ─────────────────────────────────────────────────────────────────────────────

# 3a. Replace the entire COND_OPTIONS array (with svgFn) with a clean version
OLD_COND_OPT = """\
        const COND_OPTIONS=[
          {
            cond: FVG_CONDS[0],
            title: 'Logo após o gap ser formado',
            desc: 'Quando a mínima do candle [3] fica acima da máxima do candle [1], o gap é confirmado. A entrada ocorre no candle seguinte — apostando na continuação do movimento.',
            mode: 'aggressive',
            svgFn: (ln,rc,tx,cd,ci,th)=>{
              // Contexto — candles anteriores
              cd(8,68,10,50,74,0.3); ln(13,46,13,78,th.bd,1);
              cd(22,62,10,44,68,0.3); ln(27,40,27,72,th.bd,1);
              // [1] Candle 1 — neutro, máxima em y=48
              rc(36,48,14,18,'#8888A0',0.65,1); ln(43,42,43,70,th.txs,1);
              tx(36,82,'[1]',th.txs,9,'start');
              // GAP — entre máxima do [1] (y=48) e mínima do [3] (y=28)
              // zona em roxo, visível entre os candles
              rc(32,28,54,20,'#6366F1',0.15,2);
              ln(32,28,86,28,'#6366F1',1,'3,2');
              ln(32,48,86,48,'#6366F1',1,'3,2');
              tx(34,41,'GAP','#6366F1',9);
              // [2] Candle 2 — impulso forte de alta (cruza o gap)
              rc(52,12,14,52,'#10B981',0.9,1); ln(59,6,59,68,'#10B981',1.5);
              tx(52,82,'[2]',th.txs,9,'start');
              // [3] Candle 3 — pequeno, mínima acima da máxima do [1] (y=28)
              rc(72,20,14,14,'#10B981',0.65,1); ln(79,14,79,38,'#10B981',1);
              tx(72,82,'[3]',th.txs,9,'start');
              // Entrada no candle seguinte ao [3]
              rc(92,14,14,18,'#10B981',0.85,1); ln(99,8,99,36,'#10B981',1.5);
              ln(99,6,99,0,'#00D4AA',0); // espaço
              ln(106,20,99,8,'#00D4AA',2); ln(93,20,99,8,'#00D4AA',2);
              ln(99,8,99,0,'#00D4AA',2);
              tx(110,18,'ENTRADA','#00D4AA',10);
              // Descrição
              tx(210,22,'FVG altista:',th.txs,10);
              tx(210,36,'mín. do [3] > máx. do [1]',th.txs,10);
              tx(210,54,'O gap fica entre os dois.',th.txs,10);
              tx(210,68,'Entrada: candle após [3]',th.txs,10);
            }
          },
          {
            cond: FVG_CONDS[1],
            title: 'Quando o preço retornar ao gap',
            desc: 'Após o gap ser confirmado, o mercado sobe além do candle [3]. Quando o preço recua até a zona do gap (entre máx. do [1] e mín. do [3]), a entrada ocorre ali.',
            mode: 'mitigation',
            svgFn: (ln,rc,tx,cd,ci,th)=>{
              // [1] Candle 1 — neutro, máxima em y=48
              rc(8,48,14,18,'#8888A0',0.65,1); ln(15,42,15,70,th.txs,1);
              tx(8,82,'[1]',th.txs,9,'start');
              // [2] Candle 2 — impulso forte de alta
              rc(28,12,14,52,'#10B981',0.9,1); ln(35,6,35,68,'#10B981',1.5);
              tx(28,82,'[2]',th.txs,9,'start');
              // [3] Candle 3 — mínima acima da máxima do [1]
              rc(48,18,14,14,'#10B981',0.65,1); ln(55,12,55,36,'#10B981',1);
              tx(48,82,'[3]',th.txs,9,'start');
              // GAP zone (entre máx. [1] y=48 e mín. [3] y=32) — estende à direita
              rc(4,32,170,16,'#6366F1',0.08,2);
              ln(4,32,174,32,'#6366F1',0.9,'3,2');
              ln(4,48,174,48,'#6366F1',0.9,'3,2');
              tx(6,43,'GAP','#6366F1',8);
              // Continuação após [3] — 2 candles de alta
              rc(68,10,12,16,'#10B981',0.7,1); ln(74,4,74,30,'#10B981',1);
              rc(86,4,12,14,'#10B981',0.6,1); ln(92,0,92,22,'#10B981',1);
              // Topo — candle doji
              rc(102,2,10,8,'#8888A0',0.5,1); ln(107,0,107,14,'#8888A0',1);
              // Recuo — 3 candles vermelhos descendo em direção ao gap
              rc(118,10,12,18,'#EF4444',0.65,1); ln(124,6,124,32,'#EF4444',1);
              rc(136,24,12,16,'#EF4444',0.7,1); ln(142,18,142,44,'#EF4444',1);
              rc(154,36,12,14,'#EF4444',0.6,1); ln(160,30,160,54,'#EF4444',1);
              // Entrada quando o preço toca o topo do gap (y=32)
              ci(168,32,'#00D4AA',4);
              ln(168,28,168,14,'#00D4AA',1.5);
              ln(164,19,168,14,'#00D4AA',1.5); ln(172,19,168,14,'#00D4AA',1.5);
              tx(176,18,'ENTRADA','#00D4AA',10);
              // Labels
              tx(216,52,'1. Gap: mín.[3] > máx.[1]',th.txs,10);
              tx(216,66,'2. Mercado sobe além',th.txs,10);
              tx(216,78,'3. Recua até o gap',th.txs,10);
              tx(216,90,'4. Entrada no topo do gap',th.txs,10);
            }
          }
        ];"""

NEW_COND_OPT = """\
        const COND_OPTIONS=[
          {cond:FVG_CONDS[0],title:'Logo após o gap ser formado',
           desc:'Quando a mínima do candle [3] fica acima da máxima do candle [1], o gap é confirmado. A entrada ocorre no candle seguinte — apostando na continuação do movimento.',
           mode:'aggressive'},
          {cond:FVG_CONDS[1],title:'Quando o preço retornar ao gap',
           desc:'Após o gap ser confirmado, o mercado sobe além do candle [3]. Quando o preço recua até a zona do gap (entre máx. do [1] e mín. do [3]), a entrada ocorre ali.',
           mode:'mitigation'}
        ];"""

ok3a = OLD_COND_OPT in content
content = content.replace(OLD_COND_OPT, NEW_COND_OPT, 1)
print('FVG COND_OPTIONS simplified:', 'OK' if ok3a else 'NOT FOUND')

# 3b. Replace the SVG illustration block inside forEach with LWC chart
OLD_SVG_BLOCK = """\
          // SVG illustration
          const svgEl=miniSVG(420,opt.mode==='mitigation'?110:90,opt.svgFn);
          svgEl.style.pointerEvents='none';
          card.appendChild(svgEl);"""

NEW_LWC_BLOCK = """\
          // LWC chart illustration (rebuilt from scratch)
          const _cvh=opt.mode==='mitigation'?160:130;
          const _cv=div('');_cv.style.cssText='height:'+_cvh+'px;pointer-events:none;overflow:hidden;border-top:1px solid var(--bd)';
          _lwcRender(_cv,(cW)=>{
            if(!window.LightweightCharts)return;
            const _dk=document.documentElement.getAttribute('data-theme')!=='light';
            const _bg2=_dk?'#0E0E16':'#F0F0EB',_gr2=_dk?'rgba(255,255,255,0.04)':'rgba(0,0,0,0.05)',_tx2=_dk?'#8888A0':'#909090';
            const cChart=LightweightCharts.createChart(_cv,{
              width:cW,height:_cvh,
              layout:{background:{color:_bg2},textColor:_tx2},
              grid:{vertLines:{color:_gr2},horzLines:{color:_gr2}},
              rightPriceScale:{borderColor:'transparent',scaleMargins:{top:0.06,bottom:0.20}},
              timeScale:{borderColor:'transparent',visible:false},
              crosshair:{mode:0},handleScroll:false,handleScale:false,
            });
            const _t0=Math.floor(new Date('2024-01-02').getTime()/1000),_BS=86400;
            // fvgBot=100 (A.high), fvgTop=110 (C.low) — 10-pt gap, clearly visible
            const _fBot=100,_fTop=110;
            let _cd,_aI,_bI,_cI,_eI;
            if(opt.mode==='aggressive'){
              // 9 candles: 3 context + [A] + [B=impulse] + [C] + entry + 2 continuation
              _aI=3;_bI=4;_cI=5;_eI=6;
              _cd=[
                {time:_t0+0*_BS,open:91,high:95,low:90,close:94},
                {time:_t0+1*_BS,open:94,high:96,low:91,close:92},
                {time:_t0+2*_BS,open:92,high:95,low:90,close:93},
                // [A]: bearish, high = fvgBot=100  (ceiling of range)
                {time:_t0+3*_BS,open:95,high:_fBot,low:92,close:93},
                // [B]: HUGE bullish impulse — closes way above gap
                {time:_t0+4*_BS,open:93,high:124,low:92,close:120},
                // [C]: low = fvgTop=110, gap is confirmed
                {time:_t0+5*_BS,open:120,high:125,low:_fTop,close:122},
                // ENTRY — next candle after gap confirmation
                {time:_t0+6*_BS,open:122,high:127,low:121,close:125},
                // Continuation
                {time:_t0+7*_BS,open:125,high:129,low:124,close:127},
                {time:_t0+8*_BS,open:127,high:131,low:126,close:129},
              ];
            }else{
              // 14 candles: 3 context + [A]+[B]+[C] + 4 extension + 3 return-to-gap + entry + cont
              _aI=3;_bI=4;_cI=5;_eI=11;
              _cd=[
                {time:_t0+0*_BS,open:91,high:95,low:90,close:94},
                {time:_t0+1*_BS,open:94,high:96,low:91,close:92},
                {time:_t0+2*_BS,open:92,high:95,low:90,close:93},
                // [A]
                {time:_t0+3*_BS,open:95,high:_fBot,low:92,close:93},
                // [B] impulse
                {time:_t0+4*_BS,open:93,high:124,low:92,close:120},
                // [C] gap confirmed
                {time:_t0+5*_BS,open:120,high:125,low:_fTop,close:122},
                // Extension above gap
                {time:_t0+6*_BS,open:122,high:127,low:121,close:125},
                {time:_t0+7*_BS,open:125,high:130,low:124,close:128},
                {time:_t0+8*_BS,open:128,high:131,low:126,close:127},
                {time:_t0+9*_BS,open:127,high:129,low:124,close:125},
                // Return — price falls back toward gap
                {time:_t0+10*_BS,open:125,high:126,low:119,close:120},
                // ENTRY at gap zone (close near fvgTop)
                {time:_t0+11*_BS,open:120,high:123,low:_fTop,close:115},
                // Bounce from gap
                {time:_t0+12*_BS,open:115,high:122,low:114,close:120},
                {time:_t0+13*_BS,open:120,high:126,low:119,close:124},
              ];
            }
            // Zone fill: drawn from [C] onwards
            const _zt=_cd.slice(_cI).map(b=>b.time);
            const _zc='rgba(38,166,154,0.85)',_zf='rgba(38,166,154,0.12)';
            cChart.addAreaSeries({topColor:_zf,bottomColor:_zf,lineColor:_zc,lineWidth:1.5,priceLineVisible:false,lastValueVisible:false}).setData(_zt.map(t=>({time:t,value:_fTop})));
            cChart.addLineSeries({color:_zc,lineWidth:1.5,lineStyle:1,priceLineVisible:false,lastValueVisible:false}).setData(_zt.map(t=>({time:t,value:_fBot})));
            // Candles
            const cCs=cChart.addCandlestickSeries({
              upColor:'#26a69a',downColor:'#ef5350',
              borderUpColor:'#26a69a',borderDownColor:'#ef5350',
              wickUpColor:_dk?'rgba(38,166,154,0.65)':'rgba(38,166,154,0.85)',
              wickDownColor:_dk?'rgba(239,83,80,0.65)':'rgba(239,83,80,0.85)',
              priceLineVisible:false,lastValueVisible:false,
            });
            cCs.setData(_cd);
            // Markers: A, C, Entrada
            cCs.setMarkers([
              {time:_cd[_aI].time,position:'aboveBar',color:'#F0A020',shape:'circle',text:'A'},
              {time:_cd[_cI].time,position:'aboveBar',color:'#F0A020',shape:'circle',text:'C'},
              {time:_cd[_eI].time,position:'belowBar',color:'#26a69a',shape:'arrowUp',text:'Entrada'},
            ]);
            // Force tight scale
            const _ap=_cd.flatMap(c=>[c.high,c.low]);
            const _mn=Math.min(..._ap),_mx=Math.max(..._ap),_pd=(_mx-_mn)*0.07;
            cCs.applyOptions({autoscaleInfoProvider:()=>({priceRange:{minValue:_mn-_pd,maxValue:_mx+_pd}})});
            cChart.timeScale().fitContent();
          });
          card.appendChild(_cv);"""

ok3b = OLD_SVG_BLOCK in content
content = content.replace(OLD_SVG_BLOCK, NEW_LWC_BLOCK, 1)
print('FVG condition card LWC rebuilt:', 'OK' if ok3b else 'NOT FOUND')

# ─────────────────────────────────────────────────────────────────────────────
# 4. Grab info diagram: replace miniSVG with compact LWC chart
# ─────────────────────────────────────────────────────────────────────────────
OLD_GRAB_SVG = """\
        // Grab visual
        frag.appendChild(miniSVG(500,140,(ln,rc,tx,cd,ci,th)=>{
          // Level line
          ln(8,90,492,90,'#F59E0B',1.5,'5,4');
          tx(14,108,'nível de liquidez','#F59E0B',11);
          // Approach candles
          cd(16,60,54,46,72,0.4);cd(46,72,62,56,82,0.4);cd(76,82,66,64,90,0.4);
          // Grab candle: large wick below, close above
          rc(118,64,18,22,'#EF4444',0.85,2);ln(127,50,127,118,'#EF4444',2);
          tx(148,120,'wick ≥ 50% range','#EF4444',11);
          tx(148,108,'close na metade sup.','#EF4444',11);
          // Arrow up = buy signal
          ln(180,82,180,58,'#10B981',2);ln(175,64,180,58,'#10B981',2);ln(185,64,180,58,'#10B981',2);
          // Recovery candles
          cd(200,58,36,28,66,0.7);cd(230,36,24,18,44,0.7);cd(260,22,16,10,30,0.7);
          tx(340,36,'BoS falhado:',th.txs,12);
          tx(340,54,'viola o nível mas',th.txs,12);
          tx(340,72,'fecha dentro → venda',th.txs,12);
          tx(200,130,'GRAB LOW → COMPRA',th.tx,12,'middle');
        }));"""

NEW_GRAB_LWC = """\
        // Grab visual — LWC chart (rebuilt from scratch)
        {
          const _gvEl=div('');_gvEl.style.cssText='height:140px;overflow:hidden;border-radius:8px;margin-top:4px';
          _lwcRender(_gvEl,(gW)=>{
            if(!window.LightweightCharts)return;
            const _dk=document.documentElement.getAttribute('data-theme')!=='light';
            const _bg3=_dk?'#0E0E16':'#F0F0EB',_gr3=_dk?'rgba(255,255,255,0.04)':'rgba(0,0,0,0.05)',_tx3=_dk?'#8888A0':'#909090';
            const gChart=LightweightCharts.createChart(_gvEl,{
              width:gW,height:140,
              layout:{background:{color:_bg3},textColor:_tx3},
              grid:{vertLines:{color:_gr3},horzLines:{color:_gr3}},
              rightPriceScale:{borderColor:'transparent',scaleMargins:{top:0.08,bottom:0.22}},
              timeScale:{borderColor:'transparent',visible:false},
              crosshair:{mode:0},handleScroll:false,handleScale:false,
              watermark:{visible:true,fontSize:10,horzAlign:'left',vertAlign:'top',color:_tx3,text:'Qualificação: pavio ≥ 50% do range · fechamento na metade oposta'}
            });
            const _gt0=Math.floor(new Date('2024-01-02').getTime()/1000),_gBS=86400;
            const _gLvl=100;
            // Bullish grab: level at 100, approach → extreme hammer → reversal
            const _gd=[
              {time:_gt0+0*_gBS,open:104,high:106,low:102,close:103},
              {time:_gt0+1*_gBS,open:103,high:105,low:101,close:102},
              {time:_gt0+2*_gBS,open:102,high:104,low:100,close:101},
              {time:_gt0+3*_gBS,open:101,high:103,low:_gLvl,close:101},
              // GRAB: extreme hammer — wick 12pts below level, tiny body at level
              {time:_gt0+4*_gBS,open:101,high:102,low:_gLvl-12,close:102},
              // Explosive reversal
              {time:_gt0+5*_gBS,open:102,high:110,low:101,close:108},
              {time:_gt0+6*_gBS,open:108,high:114,low:107,close:112},
              {time:_gt0+7*_gBS,open:112,high:117,low:111,close:115},
            ];
            gChart.addLineSeries({color:'#F59E0B',lineWidth:1.5,lineStyle:1,priceLineVisible:false,lastValueVisible:false}).setData(_gd.slice(0,5).map(b=>({time:b.time,value:_gLvl})));
            const gCs=gChart.addCandlestickSeries({upColor:'#26a69a',downColor:'#ef5350',borderUpColor:'#26a69a',borderDownColor:'#ef5350',wickUpColor:'rgba(38,166,154,0.7)',wickDownColor:'rgba(239,83,80,0.7)',priceLineVisible:false,lastValueVisible:false});
            gCs.setData(_gd);
            gCs.setMarkers([
              {time:_gd[3].time,position:'belowBar',color:'#F59E0B',shape:'circle',text:'Nível'},
              {time:_gd[4].time,position:'belowBar',color:'#ef5350',shape:'arrowDown',text:'Grab'},
              {time:_gd[5].time,position:'belowBar',color:'#26a69a',shape:'arrowUp',text:'Reversão'},
            ]);
            const _gap=_gd.flatMap(c=>[c.high,c.low]);
            const _gmn=Math.min(..._gap),_gmx=Math.max(..._gap),_gpd=(_gmx-_gmn)*0.09;
            gCs.applyOptions({autoscaleInfoProvider:()=>({priceRange:{minValue:_gmn-_gpd,maxValue:_gmx+_gpd}})});
            gChart.timeScale().fitContent();
          });
          frag.appendChild(_gvEl);
        }"""

ok4 = OLD_GRAB_SVG in content
content = content.replace(OLD_GRAB_SVG, NEW_GRAB_LWC, 1)
print('Grab visual LWC rebuilt:', 'OK' if ok4 else 'NOT FOUND')

# ─────────────────────────────────────────────────────────────────────────────
# 5. Sweep info diagram: replace miniSVG with compact LWC chart
# ─────────────────────────────────────────────────────────────────────────────
OLD_SWEEP_SVG = """\
        // Sweep visual
        frag.appendChild(miniSVG(500,150,(ln,rc,tx,cd,ci,th)=>{
          // Price action approaching level
          cd(16,54,66,46,72,0.4);cd(46,66,58,50,76,0.4);cd(76,58,50,42,68,0.4);cd(106,50,42,34,60,0.4);
          // Liquidity level
          ln(8,82,492,82,'#F59E0B',1.5,'5,4');
          tx(14,100,'nível de liquidez','#F59E0B',11);
          // Sweep candle: wick goes below, body stays above
          rc(150,62,18,16,'#EF4444',0.85,2);ln(159,52,159,115,'#EF4444',2);
          // Sweep zone highlight
          rc(146,82,26,33,'#EF4444',0.08,3);
          tx(180,108,'sweep!','#EF4444',13);
          // Arrow showing reversal
          ln(210,100,210,68,'#10B981',2);ln(205,74,210,68,'#10B981',2);ln(215,74,210,68,'#10B981',2);
          // Reversal candles
          cd(230,64,42,34,72,0.7);cd(260,42,30,24,48,0.7);cd(290,30,18,14,36,0.7);
          tx(240,140,'confirmação →','#10B981',11);
          // Summary steps
          tx(310,28,'1. Preço se aproxima',th.txs,11);
          tx(310,44,'2. Varre além (sweep)',th.txs,11);
          tx(310,60,'3. Reverte e confirma',th.txs,11);
          tx(310,80,'Falso rompimento',th.txm,10);
          tx(310,94,'institucional',th.txm,10);
        }));"""

NEW_SWEEP_LWC = """\
        // Sweep visual — LWC chart (rebuilt from scratch)
        {
          const _svEl=div('');_svEl.style.cssText='height:140px;overflow:hidden;border-radius:8px;margin-top:4px';
          _lwcRender(_svEl,(sW)=>{
            if(!window.LightweightCharts)return;
            const _dk=document.documentElement.getAttribute('data-theme')!=='light';
            const _bg4=_dk?'#0E0E16':'#F0F0EB',_gr4=_dk?'rgba(255,255,255,0.04)':'rgba(0,0,0,0.05)',_tx4=_dk?'#8888A0':'#909090';
            const sChart=LightweightCharts.createChart(_svEl,{
              width:sW,height:140,
              layout:{background:{color:_bg4},textColor:_tx4},
              grid:{vertLines:{color:_gr4},horzLines:{color:_gr4}},
              rightPriceScale:{borderColor:'transparent',scaleMargins:{top:0.08,bottom:0.22}},
              timeScale:{borderColor:'transparent',visible:false},
              crosshair:{mode:0},handleScroll:false,handleScale:false,
              watermark:{visible:true,fontSize:10,horzAlign:'left',vertAlign:'top',color:_tx4,text:'Falso rompimento: varre o nível, fecha de volta · 3+ toques iguais = pool de liquidez'}
            });
            const _st0=Math.floor(new Date('2024-01-02').getTime()/1000),_sBS=86400;
            const _sLvl=100;
            // Bullish sweep: 3 equal lows at level + sweep pin bar + reversal
            const _sd=[
              {time:_st0+0*_sBS,open:106,high:108,low:104,close:105},
              {time:_st0+1*_sBS,open:105,high:107,low:103,close:104},
              // Equal low 1
              {time:_st0+2*_sBS,open:104,high:106,low:_sLvl,close:104},
              {time:_st0+3*_sBS,open:104,high:107,low:103,close:106},
              // Equal low 2
              {time:_st0+4*_sBS,open:106,high:107,low:_sLvl,close:105},
              {time:_st0+5*_sBS,open:105,high:107,low:103,close:105},
              // Equal low 3
              {time:_st0+6*_sBS,open:105,high:106,low:_sLvl,close:104},
              // SWEEP: extreme pin bar — wick 11pts below level, body closes back above
              {time:_st0+7*_sBS,open:104,high:105,low:_sLvl-11,close:105},
              // Explosive reversal
              {time:_st0+8*_sBS,open:105,high:112,low:104,close:110},
              {time:_st0+9*_sBS,open:110,high:115,low:109,close:113},
              {time:_st0+10*_sBS,open:113,high:118,low:112,close:116},
            ];
            sChart.addLineSeries({color:'#F59E0B',lineWidth:1.5,lineStyle:1,priceLineVisible:false,lastValueVisible:false}).setData(_sd.slice(0,8).map(b=>({time:b.time,value:_sLvl})));
            const sCs=sChart.addCandlestickSeries({upColor:'#26a69a',downColor:'#ef5350',borderUpColor:'#26a69a',borderDownColor:'#ef5350',wickUpColor:'rgba(38,166,154,0.7)',wickDownColor:'rgba(239,83,80,0.7)',priceLineVisible:false,lastValueVisible:false});
            sCs.setData(_sd);
            sCs.setMarkers([
              {time:_sd[2].time,position:'belowBar',color:'#F59E0B',shape:'circle',text:'1'},
              {time:_sd[4].time,position:'belowBar',color:'#F59E0B',shape:'circle',text:'2'},
              {time:_sd[6].time,position:'belowBar',color:'#F59E0B',shape:'circle',text:'3'},
              {time:_sd[7].time,position:'belowBar',color:'#ef5350',shape:'arrowDown',text:'Sweep'},
              {time:_sd[8].time,position:'belowBar',color:'#26a69a',shape:'arrowUp',text:'Reversão'},
            ]);
            const _sap=_sd.flatMap(c=>[c.high,c.low]);
            const _smn=Math.min(..._sap),_smx=Math.max(..._sap),_spd=(_smx-_smn)*0.09;
            sCs.applyOptions({autoscaleInfoProvider:()=>({priceRange:{minValue:_smn-_spd,maxValue:_smx+_spd}})});
            sChart.timeScale().fitContent();
          });
          frag.appendChild(_svEl);
        }"""

ok5 = OLD_SWEEP_SVG in content
content = content.replace(OLD_SWEEP_SVG, NEW_SWEEP_LWC, 1)
print('Sweep visual LWC rebuilt:', 'OK' if ok5 else 'NOT FOUND')

# ─────────────────────────────────────────────────────────────────────────────
# 6. Write back
# ─────────────────────────────────────────────────────────────────────────────
with open(FPATH, 'w', encoding='utf-8') as f:
    f.write(content)
print('File written:', len(content), 'chars')
print('patch_fix6 DONE')

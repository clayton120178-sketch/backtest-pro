#!/usr/bin/env python3
# patch_fix5.py — Wire buildCondPreview into the SMC modal path
#
# Root cause: The SMC indicators (fvg/bos/choch/sweep/grab) use a
# dedicated modal branch (else if SMC_IDS.includes(ind.id)) that
# NEVER called buildCondPreview. Our LWC charts were dead code.
#
# Fixes:
#  1. Add 'grab' to LWC_IDS so it gets the LWC chart treatment
#  2. Insert buildCondPreview at the TOP of the SMC modal frag
#  3. Wire the FVG condition card click to refresh that preview

FPATH = 'C:/Users/Clayton Barros/AppData/Local/Temp/backtest-pro/app.html'
with open(FPATH, 'r', encoding='utf-8') as f:
    content = f.read()

# ── 1. Add 'grab' to LWC_IDS ─────────────────────────────────────────────
OLD_LWC = "  const LWC_IDS = ['rsi','stoch','cci','williams','macd','atr','sma','ema','bb','vwap','adx','sar','hilo','hilon','range','gap','prevday','fib','fvg','bos','choch','sweep','candle'];"
NEW_LWC = "  const LWC_IDS = ['rsi','stoch','cci','williams','macd','atr','sma','ema','bb','vwap','adx','sar','hilo','hilon','range','gap','prevday','fib','fvg','bos','choch','sweep','grab','candle'];"
ok1 = OLD_LWC in content
content = content.replace(OLD_LWC, NEW_LWC, 1)
print('grab added to LWC_IDS:', 'OK' if ok1 else 'NOT FOUND')

# ── 2. Insert buildCondPreview at the top of the SMC modal ───────────────
# Right after 'const smcId=ind.id;' and before the pills helper
OLD_SMC_TOP = """\
      const smcId=ind.id;

      // Helper: pills selector (updates locally, no re-render)"""

NEW_SMC_TOP = """\
      const smcId=ind.id;

      // ── LWC pattern preview — top of ALL SMC config modals ──────────
      // condText combines condition + direction so buildCondPreview
      // can detect 'up' from 'Compra' / direction from 'Venda'.
      {
        const _pw=div('cond-preview');_pw.id='cond-preview-wrap';
        const _ct=(ms.params.cond||conds[0]||'')+' '+(ms.params.dir||'');
        _pw.appendChild(buildCondPreview(smcId,_ct,ms.params));
        frag.appendChild(_pw);
        const _lg=div('cond-preview-legend');
        _lg.innerHTML='<span style="opacity:0.6">ⓘ</span> Visualização ilustrativa. Os preços exibidos na grade não correspondem ao ativo selecionado.';
        frag.appendChild(_lg);
      }

      // Helper: pills selector (updates locally, no re-render)"""

ok2 = OLD_SMC_TOP in content
content = content.replace(OLD_SMC_TOP, NEW_SMC_TOP, 1)
print('SMC preview block inserted:', 'OK' if ok2 else 'NOT FOUND')

# ── 3. Refresh preview when FVG condition card is clicked ─────────────────
# The FVG condition cards call syncFVGMode(opt.cond) on click.
# After that call we rebuild the top preview.
OLD_FVG_CLICK = "            syncFVGMode(opt.cond);\n            condCards.querySelectorAll('[data-fvg-cond]')"
NEW_FVG_CLICK = """\
            syncFVGMode(opt.cond);
            {const _pw2=document.getElementById('cond-preview-wrap');
             if(_pw2){_pw2.innerHTML='';const _ct2=ms.params.cond+' '+(ms.params.dir||'');_pw2.appendChild(buildCondPreview(smcId,_ct2,ms.params));_lwcFlush();}}
            condCards.querySelectorAll('[data-fvg-cond]')"""
ok3 = "            syncFVGMode(opt.cond);\n            condCards.querySelectorAll('[data-fvg-cond]')" in content
content = content.replace(OLD_FVG_CLICK, NEW_FVG_CLICK, 1)
print('FVG click refresh wired:', 'OK' if ok3 else 'NOT FOUND')

# ── 4. Write back ──────────────────────────────────────────────────────────
with open(FPATH, 'w', encoding='utf-8') as f:
    f.write(content)
print('File written:', len(content), 'chars')
print('patch_fix5 DONE')

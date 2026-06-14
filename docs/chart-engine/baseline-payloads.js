// BASELINE PAYLOADS — gerado em 2026-06-14 ANTES do reskin
// Replica exatamente a serialização de submitBacktestToBackend()
// body: JSON.stringify({ cfg: { ...state.cfg, stopOffset:..., backtest_period:{...}, initial_capital:..., capital_currency:... } })
// Referência: app.html linhas 8299-8310

'use strict';

// ── Replica toISO e defaultDateFrom ──────────────────────────────────────────
const TODAY = new Date('2026-06-14T00:00:00.000Z');
function defaultDateFrom() {
  const d = new Date(TODAY);
  d.setFullYear(d.getFullYear() - 5);
  d.setHours(0, 0, 0, 0);
  return d;
}
function toISO(d) { return d.toISOString().slice(0, 10); }

// ── Replica findAsset (currency) ──────────────────────────────────────────────
const ASSET_CURRENCY = {
  'WIN$N':'R$','WDO$N':'R$','IND$N':'R$','DOL$N':'R$','DI1$N':'R$',
  'BGI$N':'R$','CCM$N':'R$','ICF$N':'R$','SFI$N':'R$','ETH$N':'R$',
  'BIT$N':'R$','OZ1D$N':'R$','ISP$N':'R$',
  // acoes -> R$
};
function getCurrency(t) { return ASSET_CURRENCY[t] || 'R$'; }

// ── Replica a serialização exata ───────────────────────────────────────────────
function buildPayload(cfg) {
  const stopOffset = cfg.stopType === 'n_candles'
    ? (cfg.stopNOffset || 0)
    : cfg.stopOffset;
  return {
    cfg: {
      ...cfg,
      stopOffset,
      backtest_period: {
        date_from: toISO(cfg.backtestDateFrom || defaultDateFrom()),
        date_to:   toISO(cfg.backtestDateTo   || TODAY),
      },
      initial_capital:  cfg.initialCapital || 10000,
      capital_currency: getCurrency(cfg.asset),
    }
  };
}

// ── Default cfg (espelho de app.html linha 1683) ──────────────────────────────
const DEFAULT_CFG = {
  asset:'WIN$N', market:'local', tf:'5m', tStart:'09:00', tLastEntry:'17:00', tEnd:'17:30', maxDailyTrades:0,
  conditions:[],
  direction:'long', entryType:'breakout', validity:3,
  stopType:'fixed', stopPts:200, stopOffset:10, stopCandles:5, stopNOffset:0, stopAtrPer:14, stopAtrMult:1.5,
  tpType:'rr', tpPts:400, tpRR:2, tpFibLevel:'161.8', tpAtrPer:14, tpAtrMult:2.0,
  useFibonacci:false, fiboZZDepth:12, fiboZZDeviation:5, fiboZZBackstep:3,
  fiboTriggerLevel:'61.8', fiboTriggerMode:'validation', fiboSLLevel:'100.0', fiboTPLevel:'161.8', fiboDirection:'both',
  trailing:false, trailAct:100, trailDist:100, trailStep:50,
  partial:false, partPct:50, partAt:200, partMoveStop:true,
  exitCond:false, exitCondition:null,
  backtestDateFrom: null, backtestDateTo: null, initialCapital: 10000,
};

function cfg(overrides) { return { ...DEFAULT_CFG, ...overrides }; }

// ── 10 configurações de referência ────────────────────────────────────────────
const CONFIGS = [
  {
    id: 'B01',
    desc: 'WIN default — stop fixo, TP RR 2x, sem trailing',
    data: cfg({ asset:'WIN$N', tf:'5m', stopType:'fixed', stopPts:200, tpType:'rr', tpRR:2 }),
  },
  {
    id: 'B02',
    desc: 'WDO — stop candle, TP fixo, compra, entrada fechamento',
    data: cfg({ asset:'WDO$N', tf:'15m', direction:'long', entryType:'close',
                stopType:'candle', tpType:'fixed', tpPts:10 }),
  },
  {
    id: 'B03',
    desc: 'WIN — venda, stop ATR 1.5x, TP RR 3x, trailing ativo',
    data: cfg({ asset:'WIN$N', tf:'5m', direction:'short', entryType:'breakout',
                stopType:'atr', stopAtrPer:14, stopAtrMult:1.5,
                tpType:'rr', tpRR:3,
                trailing:true, trailAct:100, trailDist:100, trailStep:50 }),
  },
  {
    id: 'B04',
    desc: 'WIN — stop N candles (5), TP RR 2x, RSI condition',
    data: cfg({ asset:'WIN$N', tf:'5m', stopType:'n_candles', stopCandles:5, stopNOffset:0,
                tpType:'rr', tpRR:2,
                conditions:[{ id:'rsi', name:'IFR (RSI)', per:14, cond:'cruza acima de', val:30 }] }),
  },
  {
    id: 'B05',
    desc: 'PETR4 ação — stop fixo, capital 50k, janela horária restrita',
    data: cfg({ asset:'PETR4', market:'local', tf:'15m', tStart:'10:00', tLastEntry:'16:00',
                stopType:'fixed', stopPts:50, tpType:'rr', tpRR:2.5,
                initialCapital:50000 }),
  },
  {
    id: 'B06',
    desc: 'WDO — Fibonacci ativo, TP nível 161.8, SL nível 100',
    data: cfg({ asset:'WDO$N', tf:'5m', useFibonacci:true,
                fiboTriggerLevel:'61.8', fiboSLLevel:'100.0', fiboTPLevel:'161.8',
                stopType:'fixed', tpType:'rr', tpRR:2 }),
  },
  {
    id: 'B07',
    desc: 'WIN — parcial 50% em 200pts, trailing BAR',
    data: cfg({ asset:'WIN$N', tf:'5m', trailing:true, trailAct:200, trailDist:100, trailStep:50,
                partial:true, partPct:50, partAt:200, partMoveStop:true }),
  },
  {
    id: 'B08',
    desc: 'WIN — 2 condições AND (RSI + MACD), saída por condição ativa',
    data: cfg({ asset:'WIN$N', tf:'30m',
                conditions:[
                  { id:'rsi',  name:'IFR (RSI)', per:14, cond:'cruza acima de', val:30 },
                  { id:'macd', name:'MACD',      per:0,  cond:'MACD cruza acima do sinal', val:0 },
                ],
                exitCond:true, exitCondition:{ id:'rsi', name:'IFR (RSI)', per:14, cond:'cruza abaixo de', val:70 } }),
  },
  {
    id: 'B09',
    desc: 'WIN — datas explícitas, capital 25k, maxDailyTrades 3',
    data: cfg({ asset:'WIN$N', tf:'5m', maxDailyTrades:3,
                backtestDateFrom: new Date('2024-01-01T00:00:00.000Z'),
                backtestDateTo:   new Date('2025-12-31T00:00:00.000Z'),
                initialCapital: 25000 }),
  },
  {
    id: 'B10',
    desc: 'IND$N cheio — venda, stop ATR 2x, TP ATR 3x',
    data: cfg({ asset:'IND$N', tf:'60m', direction:'short', entryType:'close',
                stopType:'atr', stopAtrPer:14, stopAtrMult:2.0,
                tpType:'atr', tpAtrPer:14, tpAtrMult:3.0 }),
  },
];

// ── Gerar e imprimir ──────────────────────────────────────────────────────────
const baselines = {};
for (const c of CONFIGS) {
  const payload = buildPayload(c.data);
  baselines[c.id] = { desc: c.desc, payload };
  console.log(`\n=== ${c.id} — ${c.desc} ===`);
  console.log(JSON.stringify(payload, null, 2));
}

// Exporta para uso no diff pós-reskin
if (typeof module !== 'undefined') module.exports = baselines;

/**
 * Teste 8: Frontend convertBackendResult validation
 * Executa via Node.js com mock data para validar os 3 caminhos da funcao.
 */

// --- Copiar funcao do app.html ---
function convertBackendResult(result, deposit) {
  deposit = deposit || 100000;
  const metrics = result.metrics || {};
  const trades = result.trades || [];
  const equityCurve = result.equity_curve || [];

  if (trades.length > 0) {
    let v = 0, peak = 0;
    return trades.map((t, i) => {
      const pnl = (t.profit || 0) + (t.commission || 0) + (t.swap || 0);
      v += pnl;
      if (v > peak) peak = v;
      const dt = t.close_time || t.open_time || '';
      const parts = dt.split(/[.\s-]/);
      let tLabel = '';
      if (parts.length >= 2) {
        const yr = parts[0], mo = parseInt(parts[1]) - 1;
        const d = new Date(parseInt(yr), mo);
        tLabel = d.toLocaleDateString('pt-BR', {month:'short'}).replace('.','') + " '" + String(yr).slice(2);
      } else {
        tLabel = 'T' + (i+1);
      }
      return { v: Math.round(v), dd: Math.round(Math.min(0, v - peak)), pnl: Math.round(pnl), t: tLabel };
    });
  }

  if (equityCurve.length > 0) {
    let peak = 0;
    return equityCurve.map((balance, i) => {
      const v = balance - deposit;
      if (v > peak) peak = v;
      const pnl = i === 0 ? v : (balance - equityCurve[i-1]);
      return { v: Math.round(v), dd: Math.round(Math.min(0, v - peak)), pnl: Math.round(pnl), t: 'T' + (i+1) };
    });
  }

  const totalTrades = metrics.total_trades || 0;
  const winRate = (metrics.win_rate || 50) / 100;
  const avgWin = metrics.gross_profit && metrics.win_trades ? metrics.gross_profit / metrics.win_trades : 200;
  const avgLoss = metrics.gross_loss && metrics.loss_trades ? Math.abs(metrics.gross_loss) / metrics.loss_trades : 150;

  let v = 0, peak = 0;
  const eq = [];
  let s = totalTrades * 7919 + Math.round((metrics.total_net_profit || 0) * 100);
  const rng = () => { s = (s * 16807 + 0) % 2147483647; return (s & 0x7fffffff) / 2147483647; };

  for (let i = 0; i < Math.max(totalTrades, 30); i++) {
    const isWin = rng() < winRate;
    const pnl = isWin ? avgWin * (0.5 + rng()) : -avgLoss * (0.5 + rng());
    v += pnl;
    if (v > peak) peak = v;
    eq.push({ v: Math.round(v), dd: Math.round(Math.min(0, v - peak)), pnl: Math.round(pnl), t: 'T' + (i+1) });
  }
  return eq;
}

// --- Testes ---
let passed = 0;
let failed = 0;

function assert(cond, msg) {
  if (cond) { passed++; }
  else { failed++; console.log('  FAIL: ' + msg); }
}

// Teste 8a: Caminho trades (principal)
console.log('8a: Caminho trades...');
const tradeResult = {
  metrics: { total_trades: 3 },
  trades: [
    { profit: 500, commission: -10, swap: 0, close_time: '2025.01.15 10:00' },
    { profit: -200, commission: -10, swap: -5, close_time: '2025.02.20 14:30' },
    { profit: 800, commission: -10, swap: 0, close_time: '2025.03.10 09:15' },
  ]
};
const eq1 = convertBackendResult(tradeResult, 100000);
assert(eq1.length === 3, 'trades: deve ter 3 pontos');
assert(eq1[0].pnl === 490, 'trades[0].pnl = 500-10 = 490, got ' + eq1[0].pnl);
assert(eq1[0].v === 490, 'trades[0].v = 490, got ' + eq1[0].v);
assert(eq1[1].pnl === -215, 'trades[1].pnl = -200-10-5 = -215, got ' + eq1[1].pnl);
assert(eq1[1].v === 275, 'trades[1].v = 490-215 = 275, got ' + eq1[1].v);
assert(eq1[1].dd === -215, 'trades[1].dd = 275-490 = -215, got ' + eq1[1].dd);
assert(eq1[2].pnl === 790, 'trades[2].pnl = 800-10 = 790, got ' + eq1[2].pnl);
assert(eq1[2].v === 1065, 'trades[2].v = 275+790 = 1065, got ' + eq1[2].v);
assert(eq1[2].dd === 0, 'trades[2].dd = 0 (new peak), got ' + eq1[2].dd);
// Verificar labels de data
assert(typeof eq1[0].t === 'string' && eq1[0].t.length > 0, 'trades[0].t deve ter label de data');

// Teste 8b: Caminho equity_curve
console.log('8b: Caminho equity_curve...');
const ecResult = {
  metrics: {},
  trades: [],
  equity_curve: [100000, 100500, 100200, 101000]
};
const eq2 = convertBackendResult(ecResult, 100000);
assert(eq2.length === 4, 'ec: deve ter 4 pontos');
assert(eq2[0].v === 0, 'ec[0].v = 100000-100000 = 0, got ' + eq2[0].v);
assert(eq2[1].v === 500, 'ec[1].v = 500, got ' + eq2[1].v);
assert(eq2[1].pnl === 500, 'ec[1].pnl = 500, got ' + eq2[1].pnl);
assert(eq2[2].v === 200, 'ec[2].v = 200, got ' + eq2[2].v);
assert(eq2[2].dd === -300, 'ec[2].dd = 200-500 = -300, got ' + eq2[2].dd);
assert(eq2[3].v === 1000, 'ec[3].v = 1000, got ' + eq2[3].v);
assert(eq2[3].dd === 0, 'ec[3].dd = 0 (new peak), got ' + eq2[3].dd);

// Teste 8c: Caminho metricas (fallback sintetico)
console.log('8c: Caminho metricas (sintetico)...');
const metricResult = {
  metrics: { total_trades: 50, win_rate: 60, gross_profit: 10000, win_trades: 30, gross_loss: -5000, loss_trades: 20, total_net_profit: 5000 },
  trades: [],
  equity_curve: []
};
const eq3 = convertBackendResult(metricResult, 100000);
assert(eq3.length === 50, 'metrics: deve ter 50 pontos (total_trades), got ' + eq3.length);
assert(eq3.every(p => typeof p.v === 'number' && typeof p.dd === 'number' && typeof p.pnl === 'number' && typeof p.t === 'string'),
  'metrics: todos os pontos devem ter v, dd, pnl, t');
// Verificar determinismo (mesma seed = mesmo resultado)
const eq3b = convertBackendResult(metricResult, 100000);
assert(JSON.stringify(eq3) === JSON.stringify(eq3b), 'metrics: deve ser deterministico');
// dd nunca positivo
assert(eq3.every(p => p.dd <= 0), 'metrics: dd nunca positivo');

// Teste 8d: Resultado vazio
console.log('8d: Resultado vazio...');
const eq4 = convertBackendResult({}, 100000);
assert(eq4.length === 30, 'empty: fallback deve ter 30 pontos, got ' + eq4.length);

// --- Resultado ---
console.log(`\nTeste 8: ${passed} passed, ${failed} failed`);
if (failed > 0) process.exit(1);
console.log('Teste 8 PASSED - convertBackendResult validado');

"""
BacktestPro - Conversor Frontend cfg -> EA JSON

Recebe o state.cfg do app.html (formato JavaScript) e gera o JSON
no formato esperado pelo backtest_runner.py / EA.

Responsabilidades:
- Mapear conditions[0..2] para InpInd1/Cond1/Period1/Value1, etc
- Inferir InpUseOscillators/InpUseIndicators baseado nos indicadores presentes
- Mapear stopType/tpType/direction/entryType para enums do EA
- Gerar checksum para cache de resultados
- Validar que a combinacao faz sentido (SMC isolation, etc)
"""

import hashlib
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from mappings import (
    CANDLE_MAP,
    CONDITION_MAP,
    DIRECTION_MAP,
    ENTRY_TYPE_MAP,
    FIBO_DEBUG_HIGHLIGHT_MAP,
    FIBO_LEVEL_MAP,
    FIBO_TRIGGER_MODE_MAP,
    INDICATOR_MAP,
    RISK_TYPE_MAP,
    SMC_IDS,
    SMC_MAP,
    STOP_LOSS_MAP,
    TAKE_PROFIT_MAP,
    TIMEFRAME_MAP,
    TRAILING_ACTIVATION_MAP,
    TRAILING_TYPE_MAP,
    normalize_condition_text,
    resolve_candle,
    resolve_condition,
    resolve_smc,
)

logger = logging.getLogger(__name__)


# ============================================================================
# VALIDACAO
# ============================================================================

class ConversionError(Exception):
    """Erro de conversao frontend -> EA."""
    pass


class ConversionWarning:
    """Aviso nao-bloqueante."""
    def __init__(self, code, message):
        self.code = code
        self.message = message

    def __repr__(self):
        return f"[{self.code}] {self.message}"


def validate_cfg(cfg: Dict[str, Any]) -> List[ConversionWarning]:
    """
    Valida o cfg do frontend antes da conversao.

    Returns:
        Lista de avisos (warnings). Levanta ConversionError para bloqueios.
    """
    warnings = []
    conditions = cfg.get("conditions", [])

    # SMC isolation: nao pode misturar SMC com outros
    has_smc = any(c["id"] in SMC_IDS for c in conditions)
    has_non_smc = any(c["id"] not in SMC_IDS and c["id"] != "candle" for c in conditions)
    if has_smc and has_non_smc:
        raise ConversionError(
            "R33: Smart Money Concepts nao podem ser combinados com outros indicadores."
        )

    # Maximo 3 condicoes (limitacao do EA: InpInd1, InpInd2, InpInd3)
    # Candle e SMC nao contam como condicao de indicador (inputs separados)
    indicator_conds = [c for c in conditions if c["id"] not in SMC_IDS and c["id"] != "candle"]
    if len(indicator_conds) > 3:
        raise ConversionError(
            f"EA suporta no maximo 3 condicoes de indicador. Recebeu {len(indicator_conds)}."
        )

    # TP/SL nao suportados
    tp_type = cfg.get("tpType", "rr")
    if tp_type in ("fib_ext", "none"):
        warnings.append(ConversionWarning(
            "TP_NOT_SUPPORTED",
            f"Take Profit '{tp_type}' nao implementado no EA. Ignorando."
        ))

    # Trailing: validar tipo se informado
    trailing_type = cfg.get("trailingType", "")
    if cfg.get("trailing", False) and trailing_type:
        trail_info = TRAILING_TYPE_MAP.get(trailing_type)
        if not trail_info:
            warnings.append(ConversionWarning(
                "TRAILING_UNKNOWN_TYPE",
                f"Tipo de trailing '{trailing_type}' desconhecido. Usando BAR_BY_BAR."
            ))

    # Candle patterns nao suportados no EA
    candle_conds = [c for c in conditions if c["id"] == "candle"]
    for cc in candle_conds:
        cond_text = cc.get("params", {}).get("cond", "")
        resolved = resolve_candle(cond_text)
        if resolved and resolved["value"] is None:
            warnings.append(ConversionWarning(
                "CANDLE_NOT_IN_EA",
                f"Padrao '{cond_text}' nao existe no EA. Sera ignorado."
            ))

    return warnings


# ============================================================================
# CONVERSAO PRINCIPAL
# ============================================================================

def _infer_direction_from_condition(cond_text: str, indicator_id: str) -> Optional[str]:
    """
    Infere direcao (long/short/both) a partir do texto da condicao.
    Usado para SMC e candle patterns que precisam de bull/bear.
    """
    norm = normalize_condition_text(cond_text)

    # Condicoes explicitas de compra
    buy_keywords = ["acima", "compra", "alta", "bull", "superior", "rompe maxima"]
    sell_keywords = ["abaixo", "venda", "baixa", "bear", "inferior", "rompe minima"]

    for kw in buy_keywords:
        if kw in norm:
            return "long"
    for kw in sell_keywords:
        if kw in norm:
            return "short"

    return None


def _map_condition_slot(
    condition: Dict[str, Any],
    slot: int,
    direction: str,
) -> Dict[str, Any]:
    """
    Mapeia uma condicao do frontend para os inputs do EA (slot 1, 2 ou 3).

    Args:
        condition: dict com {id, name, params: {per, per2, val, cond, dev, ...}}
        slot: 1, 2 ou 3
        direction: 'long', 'short' ou 'both'

    Returns:
        dict parcial com os inputs do EA para este slot
    """
    cid = condition["id"]
    params = condition.get("params", {})
    cond_text = params.get("cond", "")

    ind_info = INDICATOR_MAP.get(cid)
    if not ind_info:
        raise ConversionError(f"Indicador '{cid}' nao encontrado no INDICATOR_MAP.")

    cond_info = resolve_condition(cid, cond_text)
    if not cond_info:
        raise ConversionError(
            f"Condicao '{cond_text}' do indicador '{cid}' nao encontrada no CONDITION_MAP."
        )

    # Determinar se eh cruzamento de medias (precisa de period2)
    is_ma_cross = cond_info.get("bidirectional", False) or cond_info["value"] in (13, 14)

    result = {}

    if slot == 1:
        result["InpInd1"] = ind_info["value"]
        result["InpCond1"] = cond_info["value"]
        result["InpPeriod1"] = params.get("per", 14)
        result["InpPeriod1b"] = params.get("per2", 0) if is_ma_cross else 0
        result["InpValue1"] = float(params.get("val", 0))
    elif slot == 2:
        result["InpUseCond2"] = True
        result["InpInd2"] = ind_info["value"]
        result["InpCond2"] = cond_info["value"]
        result["InpPeriod2"] = params.get("per", 14)
        result["InpPeriod2b"] = params.get("per2", 0) if is_ma_cross else 0
        result["InpValue2"] = float(params.get("val", 0))
    elif slot == 3:
        result["InpUseCond3"] = True
        result["InpInd3"] = ind_info["value"]
        result["InpCond3"] = cond_info["value"]
        result["InpPeriod3"] = params.get("per", 14)
        result["InpPeriod3b"] = params.get("per2", 0) if is_ma_cross else 0
        result["InpValue3"] = float(params.get("val", 0))

    return result


def convert_cfg_to_ea_params(cfg: Dict[str, Any]) -> Dict[str, Any]:
    """
    Converte state.cfg do app.html para parametros do EA.

    Args:
        cfg: Dicionario com o state.cfg do frontend. Formato:
            {
                asset: 'WIN$N', market: 'local', tf: '5m',
                tStart: '09:00', tLastEntry: '17:00', tEnd: '17:30',
                maxDailyTrades: 0,
                conditions: [{id:'rsi', name:'IFR', params:{per:14, cond:'cruza acima de', val:30}}, ...],
                direction: 'long', entryType: 'breakout', validity: 3,
                stopType: 'fixed', stopPts: 200, stopOffset: 10, stopCandles: 5,
                stopAtrPer: 14, stopAtrMult: 1.5,
                tpType: 'rr', tpPts: 400, tpRR: 2, tpAtrPer: 14, tpAtrMult: 2.0,
                trailing: false, trailAct: 100, trailDist: 100, trailStep: 50,
                partial: false, partPct: 50, partAt: 200, partMoveStop: true,
                exitCond: false, exitCondition: null
            }

    Returns:
        Dict com todos os parametros do EA resolvidos para valores numericos.
    """
    conditions = cfg.get("conditions", [])
    direction = cfg.get("direction", "long")

    # Separar condicoes por tipo
    indicator_conds = [c for c in conditions if c["id"] not in SMC_IDS and c["id"] != "candle"]
    candle_conds = [c for c in conditions if c["id"] == "candle"]
    smc_conds = [c for c in conditions if c["id"] in SMC_IDS]

    # Inferir modulos ativos
    groups_present = set()
    for c in indicator_conds:
        ind_info = INDICATOR_MAP.get(c["id"])
        if ind_info:
            groups_present.add(ind_info["group"])

    use_oscillators = "oscillator" in groups_present
    use_indicators = bool(groups_present - {"oscillator"})  # qualquer grupo nao-oscilador
    use_candle = len(candle_conds) > 0
    use_smc = len(smc_conds) > 0

    # Ativar modulo somente se ha indicadores daquele grupo
    # (a logica correta ja foi calculada acima com groups_present)

    params = {}

    # [0] Logger
    params["InpLogLevel"] = 3   # INFO
    params["InpLogOutput"] = 1  # PRINT

    # [1] Modulos Ativos
    # Calcular fibo_active antecipadamente para tratar exclusividade
    _fibo_as_trigger = cfg.get("useFibonacci", False)
    _fibo_as_sl      = cfg.get("stopType", "") == "fibo"
    _fibo_as_tp      = cfg.get("tpType",   "") == "fibo"
    _fibo_active     = _fibo_as_trigger or _fibo_as_sl or _fibo_as_tp

    # Quando Fibonacci e gatilho, substitui SMC e condicoes tradicionais
    if _fibo_as_trigger:
        use_smc = False

    params["InpUseOscillators"]   = use_oscillators
    params["InpUseIndicators"]    = use_indicators
    params["InpUseCandlePatterns"]= use_candle
    params["InpUseSmartMoney"]    = use_smc
    params["InpUseFibonacci"]     = _fibo_active

    # [2-4] Condicoes de indicador (max 3 slots)
    # Slot 1: sempre preenchido (mesmo que BP_IND_NONE)
    if len(indicator_conds) >= 1:
        params.update(_map_condition_slot(indicator_conds[0], 1, direction))
    else:
        params["InpInd1"] = 0       # BP_IND_NONE
        params["InpCond1"] = 0      # BP_COND_NONE
        params["InpPeriod1"] = 14
        params["InpPeriod1b"] = 0
        params["InpValue1"] = 0.0

    # Slot 2
    if len(indicator_conds) >= 2:
        params.update(_map_condition_slot(indicator_conds[1], 2, direction))
    else:
        params["InpUseCond2"] = False
        params["InpInd2"] = 0
        params["InpCond2"] = 0
        params["InpPeriod2"] = 14
        params["InpPeriod2b"] = 0
        params["InpValue2"] = 0.0

    # Slot 3
    if len(indicator_conds) >= 3:
        params.update(_map_condition_slot(indicator_conds[2], 3, direction))
    else:
        params["InpUseCond3"] = False
        params["InpInd3"] = 0
        params["InpCond3"] = 0
        params["InpPeriod3"] = 14
        params["InpPeriod3b"] = 0
        params["InpValue3"] = 0.0

    # [5] Entrada
    entry_info = ENTRY_TYPE_MAP.get(cfg.get("entryType", "next_open"), ENTRY_TYPE_MAP["next_open"])
    dir_info = DIRECTION_MAP.get(direction, DIRECTION_MAP["long"])
    params["InpEntryType"] = entry_info["value"]
    params["InpStopOrderBuffer"] = 1
    params["InpStopOrderExpBars"] = cfg.get("validity", 1)
    params["InpDirection"] = dir_info["value"]

    # [6] Stop Loss
    sl_type = cfg.get("stopType", "fixed")
    sl_info = STOP_LOSS_MAP.get(sl_type, STOP_LOSS_MAP["fixed"])
    params["InpSLType"] = sl_info["value"]
    params["InpSL_ATRPeriod"] = cfg.get("stopAtrPer", 14)
    params["InpSL_ATRMult"] = float(cfg.get("stopAtrMult", 1.5))
    params["InpSL_FixedPts"] = cfg.get("stopPts", 200)
    params["InpSL_Buffer"] = cfg.get("stopOffset", 5)
    params["InpSL_Min"] = 10
    params["InpSL_Max"] = 5000
    # N-candles: novo input (Fase 2 do EA)
    params["InpSL_CandlesBack"] = cfg.get("stopCandles", 1) if sl_type == "n_candles" else 1

    # [7] Take Profit
    tp_type = cfg.get("tpType", "rr")
    tp_info = TAKE_PROFIT_MAP.get(tp_type)
    if tp_info and tp_info["value"] is not None:
        params["InpTPType"] = tp_info["value"]
    else:
        # Fallback para RR se tipo nao suportado
        params["InpTPType"] = 1  # TP_RR_MULTIPLIER
        logger.warning(f"TP type '{tp_type}' nao suportado, usando RR como fallback.")

    params["InpTP_FixedPts"] = cfg.get("tpPts", 200)
    params["InpTP_RR"] = float(cfg.get("tpRR", 2.0))
    params["InpTP_ZZDepth"] = 12
    params["InpTP_ZZDeviation"] = 5
    params["InpTP_ZZBackstep"] = 3
    params["InpTP_ZZBuffer"] = 2
    params["InpTP_Min"] = 10
    params["InpTP_Max"] = 0
    params["InpTP_ATRPeriod"] = cfg.get("tpAtrPer", 14)
    params["InpTP_ATRPercent"] = float(cfg.get("tpAtrMult", 2.0)) * 100  # Frontend usa multiplicador, EA usa percentual
    params["InpTP_ATRTF"] = 16408  # PERIOD_D1

    # [8] Risco
    # Frontend nao tem seletor de risk type explicitamente, assume fixed lots para MVP
    params["InpRiskType"] = 0     # RISK_FIXED
    params["InpRiskPercent"] = 1.0
    params["InpFixedLots"] = 0.1
    params["InpInitialAlloc"] = 10000.0

    # [9] Janela de Operacao
    # tStart      = inicio da leitura de sinais  -> InpStartHour/Min
    # tLastEntry  = ultima abertura permitida     -> InpEndHour/Min
    # tEnd        = encerramento forcado          -> InpCloseHour/Min
    t_start      = cfg.get("tStart",      "09:00").split(":")
    t_last_entry = cfg.get("tLastEntry",  "17:00").split(":")
    t_end        = cfg.get("tEnd",        "17:30").split(":")
    params["InpStartHour"]  = int(t_start[0])
    params["InpStartMin"]   = int(t_start[1]) if len(t_start) > 1 else 0
    params["InpEndHour"]    = int(t_last_entry[0])
    params["InpEndMin"]     = int(t_last_entry[1]) if len(t_last_entry) > 1 else 0
    params["InpCloseHour"]  = int(t_end[0])
    params["InpCloseMin"]   = int(t_end[1]) if len(t_end) > 1 else 0
    params["InpMaxTradesPerDay"] = cfg.get("maxDailyTrades", 0)

    # [10] Candle Patterns
    bull_candle = 0  # BP_CANDLE_NONE
    bear_candle = 0
    for cc in candle_conds:
        cond_text = cc.get("params", {}).get("cond", "")
        resolved = resolve_candle(cond_text)
        if resolved and resolved["value"] is not None:
            if resolved["side"] == "bull":
                bull_candle = resolved["value"]
            elif resolved["side"] == "bear":
                bear_candle = resolved["value"]
            elif resolved["side"] == "neutral":
                # Neutros: colocar em bull slot por padrao
                bull_candle = resolved["value"]

    params["InpCandleBull"] = bull_candle
    params["InpCandleBear"] = bear_candle

    # [11] Smart Money
    smc_entry = 0  # BP_SMC_NONE
    if smc_conds:
        sc = smc_conds[0]
        cond_text = sc.get("params", {}).get("cond", "")
        smc_val = resolve_smc(cond_text, direction)
        if smc_val is not None:
            smc_entry = smc_val

    params["InpSMCEntry"] = smc_entry

    # [12] Trailing Stop
    if cfg.get("trailing", False):
        trail_type_key = cfg.get("trailingType", "bar")
        trail_info = TRAILING_TYPE_MAP.get(trail_type_key, TRAILING_TYPE_MAP["bar"])
        params["InpTrailType"] = trail_info["value"]

        act_key = cfg.get("trailingActMode", "immediate")
        act_info = TRAILING_ACTIVATION_MAP.get(act_key, TRAILING_ACTIVATION_MAP["immediate"])
        params["InpTrailActMode"] = act_info["value"]

        params["InpTrailRRBreakeven"] = float(cfg.get("trailRRBreakeven", 1.0))
        params["InpTrailRRTrailing"] = float(cfg.get("trailRRTrailing", 1.5))
        params["InpTrailStepPts"] = cfg.get("trailStep", 10)
        params["InpTrailOnlyFavorable"] = cfg.get("trailOnlyFavorable", False)
        params["InpTrailBufferTicks"] = cfg.get("trailBufferTicks", 5)
        params["InpTrailATRPeriod"] = cfg.get("trailAtrPer", 14)
        params["InpTrailATRBreakMult"] = float(cfg.get("trailAtrBreakMult", 0.0))
        params["InpTrailATRMult"] = float(cfg.get("trailAtrMult", 2.0))
        params["InpTrailMinPoints"] = cfg.get("trailMinPoints", 10)
        params["InpTrailMinProfit"] = float(cfg.get("trailMinProfit", 0.0))
    else:
        params["InpTrailType"] = 0      # TRAILING_NONE
        params["InpTrailActMode"] = 0
        params["InpTrailRRBreakeven"] = 1.0
        params["InpTrailRRTrailing"] = 1.5
        params["InpTrailStepPts"] = 10
        params["InpTrailOnlyFavorable"] = False
        params["InpTrailBufferTicks"] = 5
        params["InpTrailATRPeriod"] = 14
        params["InpTrailATRBreakMult"] = 0.0
        params["InpTrailATRMult"] = 2.0
        params["InpTrailMinPoints"] = 10
        params["InpTrailMinProfit"] = 0.0

    # [13] Saida Parcial
    if cfg.get("partial", False):
        params["InpUsePartial"] = True
        params["InpPartialPct"] = cfg.get("partPct", 50)
        params["InpPartialTriggerPts"] = cfg.get("partAt", 100)
        params["InpPartialMoveSL"] = cfg.get("partMoveStop", True)
    else:
        params["InpUsePartial"] = False
        params["InpPartialPct"] = 50
        params["InpPartialTriggerPts"] = 100
        params["InpPartialMoveSL"] = True

    # [14] Saida por Condicao
    if cfg.get("exitCond", False) and cfg.get("exitCondition"):
        exit_c = cfg["exitCondition"]
        exit_ind = INDICATOR_MAP.get(exit_c.get("id"))
        exit_cond = resolve_condition(exit_c.get("id", ""), exit_c.get("params", {}).get("cond", ""))
        if exit_ind and exit_cond:
            params["InpUseExitCond"] = True
            params["InpExitInd"] = exit_ind["value"]
            params["InpExitCond"] = exit_cond["value"]
            params["InpExitPeriod"] = exit_c.get("params", {}).get("per", 14)
            params["InpExitValue"] = float(exit_c.get("params", {}).get("val", 0))
        else:
            params["InpUseExitCond"] = False
            params["InpExitInd"] = 0
            params["InpExitCond"] = 0
            params["InpExitPeriod"] = 14
            params["InpExitValue"] = 0.0
    else:
        params["InpUseExitCond"] = False
        params["InpExitInd"] = 0
        params["InpExitCond"] = 0
        params["InpExitPeriod"] = 14
        params["InpExitValue"] = 0.0

    # [15] Fibonacci
    # Ativo como gatilho OU como referencia de SL/TP.
    # InpUseFibonacci=true quando: cfg.useFibonacci=true (gatilho) OU
    # cfg.stopType='fibo' OU cfg.tpType='fibo' (apenas SL/TP).
    # _fibo_active e _fibo_as_trigger ja foram calculados no bloco [1].
    fibo_active = _fibo_active

    if fibo_active:
        params["InpFibo_ZZDepth"]     = cfg.get("fiboZZDepth",     12)
        params["InpFibo_ZZDeviation"] = cfg.get("fiboZZDeviation",  5)
        params["InpFibo_ZZBackstep"]  = cfg.get("fiboZZBackstep",   3)

        # TriggerLevel: so relevante quando Fibonacci e gatilho; default 61.8%
        trig_level_key = cfg.get("fiboTriggerLevel", "61.8")
        trig_level_info = FIBO_LEVEL_MAP.get(trig_level_key, FIBO_LEVEL_MAP["61.8"])
        params["InpFibo_TriggerLevel"] = trig_level_info["value"]

        # TriggerMode: touch ou validation; default validation
        trig_mode_key = cfg.get("fiboTriggerMode", "validation")
        trig_mode_info = FIBO_TRIGGER_MODE_MAP.get(trig_mode_key, FIBO_TRIGGER_MODE_MAP["validation"])
        params["InpFibo_TriggerMode"] = trig_mode_info["value"]

        # SLLevel: nivel usado como SL quando InpSLType=BP_SL_FIBO; default 100%
        sl_level_key = cfg.get("fiboSLLevel", "100.0")
        sl_level_info = FIBO_LEVEL_MAP.get(sl_level_key, FIBO_LEVEL_MAP["100.0"])
        params["InpFibo_SLLevel"] = sl_level_info["value"]

        # TPLevel: nivel usado como TP quando InpTPType=BP_TP_FIBO; default 161.8%
        tp_level_key = cfg.get("fiboTPLevel", "161.8")
        tp_level_info = FIBO_LEVEL_MAP.get(tp_level_key, FIBO_LEVEL_MAP["161.8"])
        params["InpFibo_TPLevel"] = tp_level_info["value"]
    else:
        # Defaults quando modulo inativo
        params["InpFibo_ZZDepth"]      = 12
        params["InpFibo_ZZDeviation"]  = 5
        params["InpFibo_ZZBackstep"]   = 3
        params["InpFibo_TriggerLevel"] = FIBO_LEVEL_MAP["61.8"]["value"]   # 3
        params["InpFibo_TriggerMode"]  = FIBO_TRIGGER_MODE_MAP["validation"]["value"]  # 1
        params["InpFibo_SLLevel"]      = FIBO_LEVEL_MAP["100.0"]["value"]  # 5
        params["InpFibo_TPLevel"]      = FIBO_LEVEL_MAP["161.8"]["value"]  # 7

    # Debug visual: nunca exposto no frontend publico (Opcao A do backlog Ivan).
    # Worker sempre envia os defaults para o EA ter os inputs completos.
    params["InpFibo_Debug"]          = False
    params["InpFibo_DebugHighlight"] = FIBO_DEBUG_HIGHLIGHT_MAP["both"]["value"]  # 3 = BP_HL_BOTH

    return params


# ============================================================================
# CONSTRUCAO DO JSON COMPLETO (formato backtest_runner.py)
# ============================================================================

def build_backtest_json(
    cfg: Dict[str, Any],
    from_date: str = "2019.01.02",
    to_date: Optional[str] = None,
    deposit: int = 10000,
    model: int = 1,
) -> Tuple[Dict[str, Any], List[ConversionWarning]]:
    """
    Gera o JSON completo para o backtest_runner.py.

    Args:
        cfg: state.cfg do frontend
        from_date: Data inicio (default: Jan 2019)
        to_date: Data fim (default: hoje)
        deposit: Capital inicial
        model: Modelo de teste MT5 (1=Every tick)

    Returns:
        Tupla (json_config, warnings)
    """
    # Validar
    warnings = validate_cfg(cfg)

    # Converter
    ea_params = convert_cfg_to_ea_params(cfg)

    # Determinar timeframe MT5
    tf_frontend = cfg.get("tf", "5m")
    tf_info = TIMEFRAME_MAP.get(tf_frontend, TIMEFRAME_MAP["5m"])

    # Determinar moeda baseado no mercado
    market = cfg.get("market", "local")
    currency = "BRL" if market == "local" else "USD"

    if to_date is None:
        to_date = datetime.now().strftime("%Y.%m.%d")

    config = {
        "ea_name": "BacktestPro_Universal_EA",
        "symbol": cfg.get("asset", "WIN$N"),
        "timeframe": tf_info["mt5"],
        "from_date": from_date,
        "to_date": to_date,
        "deposit": deposit,
        "currency": currency,
        "leverage": 100,
        "model": model,
        "parameters": ea_params,
    }

    return config, warnings


# ============================================================================
# CHECKSUM PARA CACHE
# ============================================================================

def compute_checksum(config: Dict[str, Any]) -> str:
    """
    Gera SHA256 dos parametros relevantes para cache.

    Parametros que afetam o resultado do backtest:
    - symbol, timeframe, from_date, to_date
    - Todos os EA parameters
    - deposit (afeta position sizing se RISK_PERCENT)

    NAO inclui: ea_name, currency, leverage (nao afetam sinais)

    Returns:
        String hex SHA256 (64 chars)
    """
    # Ordenar parametros para garantir determinismo
    cache_key = {
        "symbol": config["symbol"],
        "timeframe": config["timeframe"],
        "from_date": config["from_date"],
        "to_date": config["to_date"],
        "deposit": config["deposit"],
        "model": config["model"],
        "parameters": dict(sorted(config["parameters"].items())),
    }

    serialized = json.dumps(cache_key, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


# ============================================================================
# CLI para testes
# ============================================================================

if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    # Exemplo: simular um cfg do frontend
    test_cfg = {
        "asset": "WIN$N",
        "market": "local",
        "tf": "5m",
        "tStart": "09:00",
        "tLastEntry": "17:00",
        "tEnd": "17:30",
        "maxDailyTrades": 3,
        "conditions": [
            {"id": "rsi", "name": "IFR (RSI)", "params": {"per": 14, "cond": "cruza acima de", "val": 30}},
            {"id": "sma", "name": "SMA", "params": {"per": 200, "cond": "Preco esta acima"}},
        ],
        "direction": "long",
        "entryType": "breakout",
        "validity": 3,
        "stopType": "fixed",
        "stopPts": 200,
        "stopOffset": 10,
        "stopCandles": 5,
        "stopAtrPer": 14,
        "stopAtrMult": 1.5,
        "tpType": "rr",
        "tpPts": 400,
        "tpRR": 2.0,
        "tpAtrPer": 14,
        "tpAtrMult": 2.0,
        "trailing": False,
        "partial": False,
        "exitCond": False,
        "exitCondition": None,
    }

    config, warns = build_backtest_json(test_cfg)

    print("\n=== WARNINGS ===")
    for w in warns:
        print(f"  {w}")

    print("\n=== EA PARAMS ===")
    for k, v in config["parameters"].items():
        print(f"  {k} = {v}")

    print(f"\n=== CHECKSUM ===")
    print(f"  {compute_checksum(config)}")

    print(f"\n=== FULL JSON ===")
    print(json.dumps(config, indent=2, ensure_ascii=False))

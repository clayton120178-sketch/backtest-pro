"""
BacktestPro - Tabela Canonica de Mapeamento
Fonte unica de verdade: Frontend (app.html) -> EA (BP_Constants.mqh)

Todas as conversoes Frontend->EA passam por este modulo.
Quando um enum for adicionado/alterado no EA, atualizar AQUI.
"""

# ============================================================================
# INDICADORES: frontend id -> enum EA
# ============================================================================

INDICATOR_MAP = {
    # Osciladores
    "rsi":      {"enum": "BP_IND_RSI",       "value": 1,  "group": "oscillator"},
    "stoch":    {"enum": "BP_IND_STOCH",      "value": 2,  "group": "oscillator"},
    "cci":      {"enum": "BP_IND_CCI",        "value": 3,  "group": "oscillator"},
    "williams": {"enum": "BP_IND_WILLIAMS",   "value": 4,  "group": "oscillator"},
    "macd":     {"enum": "BP_IND_MACD",       "value": 5,  "group": "oscillator"},
    # Tendencia
    "sma":      {"enum": "BP_IND_SMA",        "value": 10, "group": "trend"},
    "ema":      {"enum": "BP_IND_EMA",        "value": 11, "group": "trend"},
    "adx":      {"enum": "BP_IND_ADX",        "value": 12, "group": "trend"},
    "sar":      {"enum": "BP_IND_SAR",        "value": 13, "group": "trend"},
    "bb":       {"enum": "BP_IND_BOLLINGER",  "value": 14, "group": "trend"},
    "vwap":     {"enum": "BP_IND_VWAP",       "value": 15, "group": "trend"},
    "hilo":     {"enum": "BP_IND_HILO",       "value": 16, "group": "trend"},
    # Volume
    "avgvol":   {"enum": "BP_IND_VOLUME_MA",  "value": 21, "group": "volume"},
    "obv":      {"enum": "BP_IND_OBV",        "value": 22, "group": "volume"},
    # Volatilidade
    "atr":      {"enum": "BP_IND_ATR",        "value": 30, "group": "volatility"},
    # Preco
    "hilon":    {"enum": "BP_IND_PRICE_HIGH_N","value": 40, "group": "price"},
    "range":    {"enum": "BP_IND_PRICE_HIGH_N","value": 40, "group": "price"},  # Range usa mesmo enum internamente
    "prevday":  {"enum": "BP_IND_PREV_HIGH",  "value": 42, "group": "price"},
    "fib":      {"enum": "BP_IND_FIBONACCI",  "value": 44, "group": "price"},
    "gap":      {"enum": "BP_IND_GAP",        "value": 45, "group": "price"},
    # Candle patterns (tratados separadamente via InpCandleBull/InpCandleBear)
    "candle":   {"enum": "BP_CANDLE_PATTERN", "value": -1, "group": "candle"},
    # Smart Money (tratados separadamente via InpSMCEntry)
    "fvg":      {"enum": "BP_SMC_FVG",        "value": -1, "group": "smc"},
    "bos":      {"enum": "BP_SMC_BOS",        "value": -1, "group": "smc"},
    "choch":    {"enum": "BP_SMC_CHOCH",       "value": -1, "group": "smc"},
    "ob":       {"enum": "BP_SMC_OB",          "value": -1, "group": "smc"},
    "sweep":    {"enum": "BP_SMC_SWEEP",       "value": -1, "group": "smc"},
    "grab":     {"enum": "BP_SMC_GRAB",        "value": -1, "group": "smc"},
}

# IDs que pertencem ao Smart Money (nao combinam com outros)
SMC_IDS = {"fvg", "bos", "choch", "ob", "sweep", "grab"}


# ============================================================================
# CONDICOES: texto do frontend -> enum EA
# A chave pode conter variantes; o conversor faz lowercase+strip antes de buscar.
# ============================================================================

CONDITION_MAP = {
    # --- Osciladores genericos ---
    "cruza acima de":               {"enum": "BP_COND_CROSS_ABOVE",        "value": 1},
    "cruza abaixo de":              {"enum": "BP_COND_CROSS_BELOW",        "value": 2},
    "esta acima de":                {"enum": "BP_COND_ABOVE",              "value": 3},
    "esta abaixo de":               {"enum": "BP_COND_BELOW",              "value": 4},
    "esta acima de":                {"enum": "BP_COND_ABOVE",              "value": 3},
    "esta abaixo de":               {"enum": "BP_COND_BELOW",              "value": 4},

    # --- Medias moveis (preco vs MA) ---
    "preco cruza acima":            {"enum": "BP_COND_CROSS_ABOVE_PRICE",  "value": 7},
    "preco cruza abaixo":           {"enum": "BP_COND_CROSS_BELOW_PRICE",  "value": 8},
    "preco esta acima":             {"enum": "BP_COND_ABOVE",              "value": 3},
    "preco esta abaixo":            {"enum": "BP_COND_BELOW",              "value": 4},

    # --- Cruzamento de medias (MA rapida x MA lenta) ---
    "media curta cruza acima da longa":     {"enum": "BP_COND_MA_CROSS_ABOVE",  "value": 13},
    "media curta cruza abaixo da longa":    {"enum": "BP_COND_MA_CROSS_BELOW",  "value": 14},
    "cruzamento de medias (compra e venda)":{"enum": "BP_COND_MA_CROSS_ABOVE",  "value": 13, "bidirectional": True},

    # --- MACD ---
    "macd cruza acima do sinal":    {"enum": "BP_COND_MACD_CROSS_UP",     "value": 9},
    "macd cruza abaixo do sinal":   {"enum": "BP_COND_MACD_CROSS_DOWN",   "value": 10},
    "macd acima de zero":           {"enum": "BP_COND_MACD_ABOVE_ZERO",   "value": 11},
    "macd abaixo de zero":          {"enum": "BP_COND_MACD_BELOW_ZERO",   "value": 12},

    # --- Bollinger Bands ---
    "preco toca banda superior":    {"enum": "BP_COND_ABOVE",             "value": 3},   # Mapeado como ABOVE (toque = preco >= banda)
    "preco toca banda inferior":    {"enum": "BP_COND_BELOW",             "value": 4},   # Mapeado como BELOW (toque = preco <= banda)
    "preco cruza banda superior":   {"enum": "BP_COND_CROSS_ABOVE",       "value": 1},
    "preco cruza banda inferior":   {"enum": "BP_COND_CROSS_BELOW",       "value": 2},

    # --- VWAP ---
    "preco esta acima do vwap":     {"enum": "BP_COND_ABOVE",             "value": 3},
    "preco esta abaixo do vwap":    {"enum": "BP_COND_BELOW",             "value": 4},
    "preco cruza acima do vwap":    {"enum": "BP_COND_CROSS_ABOVE",       "value": 1},
    "preco cruza abaixo do vwap":   {"enum": "BP_COND_CROSS_BELOW",       "value": 2},

    # --- ADX ---
    # ADX usa os mesmos enums dos osciladores (ABOVE/BELOW/CROSS_ABOVE/CROSS_BELOW)
    # Ja coberto por "esta acima de", "cruza acima de", etc.

    # --- SAR Parabolico ---
    "preco esta acima do sar":      {"enum": "BP_COND_ABOVE",             "value": 3},
    "preco esta abaixo do sar":     {"enum": "BP_COND_BELOW",             "value": 4},
    "preco cruza acima do sar":     {"enum": "BP_COND_CROSS_ABOVE",       "value": 1},
    "preco cruza abaixo do sar":    {"enum": "BP_COND_CROSS_BELOW",       "value": 2},

    # --- HiLo Activator ---
    "hilo virou compra":            {"enum": "BP_COND_HILO_BUY",          "value": 15},
    "hilo virou venda":             {"enum": "BP_COND_HILO_SELL",         "value": 16},
    "hilo esta em modo compra":     {"enum": "BP_COND_HILO_BUY",          "value": 15},
    "hilo esta em modo venda":      {"enum": "BP_COND_HILO_SELL",         "value": 16},
    "hilo mudou de direcao":        {"enum": "BP_COND_HILO_CHANGED",      "value": 17},

    # --- OBV ---
    "obv esta acima da sua media":  {"enum": "BP_COND_ABOVE",             "value": 3},
    "obv esta abaixo da sua media": {"enum": "BP_COND_BELOW",             "value": 4},
    "obv cruza acima da sua media": {"enum": "BP_COND_CROSS_ABOVE",       "value": 1},
    "obv cruza abaixo da sua media":{"enum": "BP_COND_CROSS_BELOW",       "value": 2},

    # --- Volume Medio ---
    "e maior que":                  {"enum": "BP_COND_ABOVE",             "value": 3},
    "e menor que":                  {"enum": "BP_COND_BELOW",             "value": 4},

    # --- ATR ---
    "atr esta acima de x\u00d7 a media":    {"enum": "BP_COND_ABOVE",    "value": 3},
    "atr esta abaixo de x\u00d7 a media":   {"enum": "BP_COND_BELOW",    "value": 4},
    "atr cruza acima de x\u00d7 a media":   {"enum": "BP_COND_CROSS_ABOVE","value": 1},
    "atr cruza abaixo de x\u00d7 a media":  {"enum": "BP_COND_CROSS_BELOW","value": 2},

    # --- Preco: High/Low N periodos ---
    "preco rompe maxima de n periodos":     {"enum": "BP_COND_CROSS_ABOVE", "value": 1},
    "preco rompe minima de n periodos":     {"enum": "BP_COND_CROSS_BELOW", "value": 2},
    "preco esta acima da maxima de n":      {"enum": "BP_COND_ABOVE",       "value": 3},
    "preco esta abaixo da minima de n":     {"enum": "BP_COND_BELOW",       "value": 4},

    # --- Gap ---
    "gap de alta":                          {"enum": "BP_COND_ABOVE",        "value": 3},
    "gap de baixa":                         {"enum": "BP_COND_BELOW",        "value": 4},
    "gap de alta maior que":                {"enum": "BP_COND_ABOVE",        "value": 3},   # val = pontos minimos
    "gap de baixa maior que":               {"enum": "BP_COND_BELOW",        "value": 4},

    # --- Prevday ---
    "preco esta acima da maxima de ontem":  {"enum": "BP_COND_ABOVE",        "value": 3},
    "preco esta abaixo da minima de ontem": {"enum": "BP_COND_BELOW",        "value": 4},
    "preco cruza acima da maxima de ontem": {"enum": "BP_COND_CROSS_ABOVE",  "value": 1},
    "preco cruza abaixo da minima de ontem":{"enum": "BP_COND_CROSS_BELOW",  "value": 2},
    "preco esta entre maxima e minima de ontem":{"enum": "BP_COND_IN_ZONE_OB","value": 5},  # Re-usa zona

    # --- Fibonacci ---
    "preco toca nivel 23.6%":               {"enum": "BP_COND_ABOVE",        "value": 3, "fib_level": 23.6},
    "preco toca nivel 38.2%":               {"enum": "BP_COND_ABOVE",        "value": 3, "fib_level": 38.2},
    "preco toca nivel 50%":                 {"enum": "BP_COND_ABOVE",        "value": 3, "fib_level": 50.0},
    "preco toca nivel 61.8%":               {"enum": "BP_COND_ABOVE",        "value": 3, "fib_level": 61.8},
    "preco toca nivel 78.6%":               {"enum": "BP_COND_ABOVE",        "value": 3, "fib_level": 78.6},
    "preco cruza acima do nivel 61.8%":     {"enum": "BP_COND_CROSS_ABOVE",  "value": 1, "fib_level": 61.8},
    "preco cruza abaixo do nivel 61.8%":    {"enum": "BP_COND_CROSS_BELOW",  "value": 2, "fib_level": 61.8},
    "preco esta na zona 50%-61.8%":         {"enum": "BP_COND_IN_ZONE_OB",   "value": 5, "fib_level": 50.0},
    "preco esta na zona 61.8%-78.6%":       {"enum": "BP_COND_IN_ZONE_OB",   "value": 5, "fib_level": 61.8},
}


# ============================================================================
# CANDLE PATTERNS: texto do frontend -> enum EA
# NOTA: Alguns patterns existem no frontend mas NAO no EA enum atual.
#       Marcados com value=None (serao ignorados ou adicionados ao EA depois).
# ============================================================================

CANDLE_MAP = {
    # -- Bullish --
    "martelo (alta)":                {"enum": "BP_CANDLE_HAMMER",       "value": 1,    "side": "bull"},
    "martelo invertido (alta)":      {"enum": None,                     "value": None, "side": "bull"},   # TODO: adicionar ao EA
    "engolfo de alta":               {"enum": "BP_CANDLE_BULL_ENGULF",  "value": 2,    "side": "bull"},
    "estrela da manha (alta)":       {"enum": "BP_CANDLE_MORNING_STAR", "value": 3,    "side": "bull"},
    "doji da manha (alta)":          {"enum": "BP_CANDLE_MORNING_STAR", "value": 3,    "side": "bull"},   # Mapeado para morning star
    "harami de alta":                {"enum": "BP_CANDLE_BULL_HARAMI",  "value": 4,    "side": "bull"},
    "marubozu de alta":              {"enum": None,                     "value": None, "side": "bull"},   # TODO: adicionar ao EA
    "pivo de alta":                  {"enum": "BP_CANDLE_BULL_PIVOT",   "value": 7,    "side": "bull"},
    "3 soldados brancos (alta)":     {"enum": None,                     "value": None, "side": "bull"},   # TODO: adicionar ao EA
    "linha de perfuracao (alta)":    {"enum": None,                     "value": None, "side": "bull"},   # TODO: adicionar ao EA
    "fundo duplo (alta)":            {"enum": "BP_CANDLE_DOUBLE_BOTTOM","value": 6,    "side": "bull"},
    "trap de alta":                  {"enum": None,                     "value": None, "side": "bull"},   # TODO: adicionar ao EA

    # -- Bearish --
    "engolfo de baixa":              {"enum": "BP_CANDLE_BEAR_ENGULF",  "value": 11,   "side": "bear"},
    "estrela da noite (baixa)":      {"enum": "BP_CANDLE_EVENING_STAR", "value": 12,   "side": "bear"},
    "doji da noite (baixa)":         {"enum": "BP_CANDLE_EVENING_STAR", "value": 12,   "side": "bear"},   # Mapeado para evening star
    "harami de baixa":               {"enum": "BP_CANDLE_BEAR_HARAMI",  "value": 13,   "side": "bear"},
    "marubozu de baixa":             {"enum": None,                     "value": None, "side": "bear"},   # TODO: adicionar ao EA
    "pivo de baixa":                 {"enum": "BP_CANDLE_BEAR_PIVOT",   "value": 16,   "side": "bear"},
    "3 corvos negros (baixa)":       {"enum": None,                     "value": None, "side": "bear"},   # TODO: adicionar ao EA
    "cobertura de nuvem negra (baixa)":{"enum": None,                   "value": None, "side": "bear"},   # TODO: adicionar ao EA
    "topo duplo (baixa)":            {"enum": "BP_CANDLE_DOUBLE_TOP",   "value": 15,   "side": "bear"},
    "trap de baixa":                 {"enum": None,                     "value": None, "side": "bear"},   # TODO: adicionar ao EA

    # -- Neutros --
    "doji":                          {"enum": "BP_CANDLE_DOJI",         "value": 20,   "side": "neutral"},
    "spinning top":                  {"enum": "BP_CANDLE_SPINNING_TOP", "value": 21,   "side": "neutral"},
}


# ============================================================================
# SMART MONEY CONCEPTS: frontend cond -> enum EA
# ============================================================================

SMC_MAP = {
    # FVG
    "fvg detectado":                 {"enum_bull": "BP_SMC_FVG_BULL",   "val_bull": 1,
                                      "enum_bear": "BP_SMC_FVG_BEAR",   "val_bear": 2},
    "preco retorna ao fvg":          {"enum_bull": "BP_SMC_FVG_BULL",   "val_bull": 1,
                                      "enum_bear": "BP_SMC_FVG_BEAR",   "val_bear": 2},
    # BoS
    "bos detectado":                 {"enum_bull": "BP_SMC_BOS_BULL",   "val_bull": 3,
                                      "enum_bear": "BP_SMC_BOS_BEAR",   "val_bear": 4},
    # CHoCH
    "choch detectado":               {"enum_bull": "BP_SMC_CHOCH_BULL", "val_bull": 5,
                                      "enum_bear": "BP_SMC_CHOCH_BEAR", "val_bear": 6},
    # Order Block: REMOVIDO como conceito isolado.
    # OB agora e filtro de mitigacao em BoS/CHoCH via InpOB_Mitigation
    # (ver OB_MITIGATION_MAP abaixo). Valores 7/8 do enum estao reservados.

    # Liquidity Sweep: HIGH=SELL (val_bear=9), LOW=BUY (val_bull=10)
    # Logica: SWEEP_HIGH = BoS_Bull confirmado + reversao -> sinal de venda
    #         SWEEP_LOW  = BoS_Bear confirmado + reversao -> sinal de compra
    "liquidity sweep detectado":     {"enum_bull": "BP_SMC_SWEEP_LOW",  "val_bull": 10,
                                      "enum_bear": "BP_SMC_SWEEP_HIGH", "val_bear": 9},
    # Liquidity Grab: HIGH=SELL (val_bear=11), LOW=BUY (val_bull=12)
    # Logica: GRAB_HIGH = BoS_Bull falhado, rejeicao no topo -> sinal de venda
    #         GRAB_LOW  = BoS_Bear falhado, rejeicao no fundo -> sinal de compra
    "liquidity grab detectado":      {"enum_bull": "BP_SMC_GRAB_LOW",   "val_bull": 12,
                                      "enum_bear": "BP_SMC_GRAB_HIGH",  "val_bear": 11},
}


# ============================================================================
# OB MITIGATION: filtro aplicado em BoS/CHoCH via InpOB_Mitigation
# ============================================================================

OB_MITIGATION_MAP = {
    "sem filtro":      {"enum": "OB_MITIGATION_NONE",       "value": 0},
    "ob touch":        {"enum": "OB_MITIGATION_TOUCH",      "value": 1},
    "ob validation":   {"enum": "OB_MITIGATION_VALIDATION", "value": 2},
}


# ============================================================================
# STOP LOSS: frontend -> EA (CommonTypes.mqh do Framework)
# InpSLType usa ENUM_STOP_LOSS_TYPE do Framework:
#   SL_ATR=0, SL_FIXED=1, SL_GRAPHIC=2 (max/min candle + buffer)
# ============================================================================

STOP_LOSS_MAP = {
    "fixed":     {"enum": "SL_FIXED",   "value": 1},
    "hl_candle": {"enum": "SL_GRAPHIC", "value": 2},   # Max/min candle de sinal
    "n_candles": {"enum": "SL_GRAPHIC", "value": 2},   # Mesmo tipo, InpSL_CandlesBack diferencia
    "atr":       {"enum": "SL_ATR",     "value": 0},
}


# ============================================================================
# TAKE PROFIT: frontend -> EA (CommonTypes.mqh do Framework)
# InpTPType usa ENUM_TAKE_PROFIT_TYPE do Framework:
#   TP_FIXED_POINTS=0, TP_RR_MULTIPLIER=1, TP_ZIGZAG_LEVEL=2, TP_ATR=3
# ============================================================================

TAKE_PROFIT_MAP = {
    "fixed":   {"enum": "TP_FIXED_POINTS",  "value": 0},
    "rr":      {"enum": "TP_RR_MULTIPLIER", "value": 1},
    "atr":     {"enum": "TP_ATR",           "value": 3},
    # Fase futura:
    "fib_ext": {"enum": None,               "value": None},   # TODO: nao implementado no EA
    "none":    {"enum": None,               "value": None},   # TODO: nao implementado no EA
}


# ============================================================================
# DIRECAO: frontend -> EA
# ============================================================================

DIRECTION_MAP = {
    "long":  {"enum": "TRADING_BUY_ONLY",  "value": 1},
    "short": {"enum": "TRADING_SELL_ONLY",  "value": -1},
    "both":  {"enum": "TRADING_BOTH",       "value": 0},
}


# ============================================================================
# TIPO DE ENTRADA: frontend -> EA
# ============================================================================

ENTRY_TYPE_MAP = {
    "next_open":  {"enum": "BP_ENTRY_NEXT_OPEN",  "value": 0},
    "breakout":   {"enum": "BP_ENTRY_STOP_ORDER",  "value": 1},
    # sig_close removido do frontend
}


# ============================================================================
# RISK TYPE: frontend -> EA
# ============================================================================

RISK_TYPE_MAP = {
    "fixed":       {"enum": "RISK_FIXED",       "value": 0},
    "percent":     {"enum": "RISK_PERCENT",      "value": 1},
    "progression": {"enum": "RISK_PROGRESSION",  "value": 2},
}


# ============================================================================
# TIMEFRAMES: frontend display -> MT5 constante
# ============================================================================

TIMEFRAME_MAP = {
    "1m":  {"mt5": "M1",  "value": 1},
    "2m":  {"mt5": "M2",  "value": 2},
    "3m":  {"mt5": "M3",  "value": 3},
    "5m":  {"mt5": "M5",  "value": 5},
    "10m": {"mt5": "M10", "value": 10},
    "15m": {"mt5": "M15", "value": 15},
    "30m": {"mt5": "M30", "value": 30},
    "1h":  {"mt5": "H1",  "value": 16385},
    "2h":  {"mt5": "H2",  "value": 16386},
    "4h":  {"mt5": "H4",  "value": 16388},
    "D1":  {"mt5": "D1",  "value": 16408},
    "W1":  {"mt5": "W1",  "value": 32769},
}


# ============================================================================
# TRAILING STOP: frontend -> Framework (CommonTypes.mqh)
# Neste caso usamos os enums do Framework pois o EA chama TrailingStop_Create()
# ============================================================================

TRAILING_TYPE_MAP = {
    "rr":        {"enum": "TRAILING_RR_RATIO",    "value": 1},
    "bar":       {"enum": "TRAILING_BAR_BY_BAR",  "value": 2},
    "atr":       {"enum": "TRAILING_ATR",         "value": 3},
    "disabled":  {"enum": "TRAILING_NONE",         "value": 0},
}

TRAILING_ACTIVATION_MAP = {
    "immediate":       {"enum": "ACTIVATION_IMMEDIATE",       "value": 0},
    "after_profit":    {"enum": "ACTIVATION_AFTER_PROFIT",    "value": 1},
    "after_breakeven": {"enum": "ACTIVATION_AFTER_BREAKEVEN", "value": 2},
}


# ============================================================================
# HELPERS
# ============================================================================

def normalize_condition_text(text):
    """
    Normaliza texto de condicao para busca no CONDITION_MAP.
    Remove acentos comuns, lowercase, strip.
    """
    if not text:
        return ""
    t = text.lower().strip()
    # Substituicoes de acentos mais comuns no portugues
    replacements = {
        "\u00e1": "a", "\u00e0": "a", "\u00e3": "a", "\u00e2": "a",
        "\u00e9": "e", "\u00ea": "e",
        "\u00ed": "i",
        "\u00f3": "o", "\u00f4": "o", "\u00f5": "o",
        "\u00fa": "u", "\u00fc": "u",
        "\u00e7": "c",
        "\u00d7": "x",  # multiplicacao
    }
    for old, new in replacements.items():
        t = t.replace(old, new)
    return t


def resolve_condition(indicator_id, condition_text):
    """
    Resolve condicao do frontend para enum EA.

    Args:
        indicator_id: ID do indicador no frontend (ex: 'rsi', 'sma')
        condition_text: Texto da condicao (ex: 'cruza acima de')

    Returns:
        dict com 'value' (int) e metadata, ou None se nao encontrado
    """
    norm = normalize_condition_text(condition_text)
    if norm in CONDITION_MAP:
        return CONDITION_MAP[norm]

    # Fallback: tentar sem acentos/especiais (ex: "esta" vs "esta")
    # Ja normalizado acima, mas se nao encontrou, tentar variantes
    for key, val in CONDITION_MAP.items():
        if normalize_condition_text(key) == norm:
            return val

    return None


def resolve_candle(condition_text):
    """
    Resolve padrao de candle do frontend para enum EA.

    Returns:
        dict com 'value', 'side' ou None se nao suportado.
    """
    norm = normalize_condition_text(condition_text)
    if norm in CANDLE_MAP:
        return CANDLE_MAP[norm]

    for key, val in CANDLE_MAP.items():
        if normalize_condition_text(key) == norm:
            return val

    return None


def resolve_smc(condition_text, direction="long"):
    """
    Resolve conceito Smart Money para enum EA.

    Args:
        condition_text: Texto da condicao SMC
        direction: 'long' ou 'short' para escolher bull/bear

    Returns:
        int (valor do enum) ou None
    """
    norm = normalize_condition_text(condition_text)
    for key, val in SMC_MAP.items():
        if normalize_condition_text(key) == norm:
            if direction == "long":
                return val["val_bull"]
            else:
                return val["val_bear"]
    return None

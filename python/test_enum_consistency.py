"""
Teste 7: Consistencia MQL5 (BP_Constants.mqh) vs Python (mappings.py)
Verifica que todos os valores numericos de enums no Python batem com o MQL5.
"""
import re
import sys

# --- Parse BP_Constants.mqh enums ---
def parse_mqh_enums(filepath):
    """Extrai todos os enums e seus valores de BP_Constants.mqh"""
    enums = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Regex para extrair enum entries: NAME = VALUE
    for match in re.finditer(r'(BP_\w+)\s*=\s*(-?\d+)', content):
        name = match.group(1)
        value = int(match.group(2))
        enums[name] = value
    return enums


def test_indicator_map(mqh_enums):
    """Verifica INDICATOR_MAP values contra BP_Constants."""
    from mappings import INDICATOR_MAP
    errors = []
    for fid, info in INDICATOR_MAP.items():
        enum_name = info["enum"]
        py_val = info["value"]
        if py_val == -1:
            continue  # candle/smc tratados separadamente
        if enum_name in mqh_enums:
            if mqh_enums[enum_name] != py_val:
                errors.append(f"  INDICATOR {fid}: {enum_name} Python={py_val} MQL5={mqh_enums[enum_name]}")
        else:
            errors.append(f"  INDICATOR {fid}: {enum_name} NAO encontrado no MQL5")
    return errors


def test_condition_map(mqh_enums):
    """Verifica CONDITION_MAP values contra BP_Constants."""
    from mappings import CONDITION_MAP
    errors = []
    seen = set()
    for text, info in CONDITION_MAP.items():
        enum_name = info["enum"]
        py_val = info["value"]
        key = (enum_name, py_val)
        if key in seen:
            continue
        seen.add(key)
        if enum_name in mqh_enums:
            if mqh_enums[enum_name] != py_val:
                errors.append(f"  CONDITION '{text}': {enum_name} Python={py_val} MQL5={mqh_enums[enum_name]}")
        # Nota: condicoes que usam enums genericos (ABOVE, BELOW) ja estao em BP_COND_*
    return errors


def test_candle_map(mqh_enums):
    """Verifica CANDLE_MAP values contra BP_Constants."""
    from mappings import CANDLE_MAP
    errors = []
    for text, info in CANDLE_MAP.items():
        enum_name = info["enum"]
        py_val = info["value"]
        if enum_name is None or py_val is None:
            continue  # TODO items
        if enum_name in mqh_enums:
            if mqh_enums[enum_name] != py_val:
                errors.append(f"  CANDLE '{text}': {enum_name} Python={py_val} MQL5={mqh_enums[enum_name]}")
    return errors


def test_smc_map(mqh_enums):
    """Verifica SMC_MAP values contra BP_Constants."""
    from mappings import SMC_MAP
    errors = []
    for text, info in SMC_MAP.items():
        for suffix in ["bull", "bear"]:
            enum_name = info[f"enum_{suffix}"]
            py_val = info[f"val_{suffix}"]
            if enum_name in mqh_enums:
                if mqh_enums[enum_name] != py_val:
                    errors.append(f"  SMC '{text}' ({suffix}): {enum_name} Python={py_val} MQL5={mqh_enums[enum_name]}")
    return errors


def test_sl_tp_maps(mqh_enums):
    """Verifica SL/TP maps."""
    from mappings import STOP_LOSS_MAP, TAKE_PROFIT_MAP
    errors = []
    for fid, info in STOP_LOSS_MAP.items():
        enum_name = info["enum"]
        py_val = info["value"]
        if enum_name in mqh_enums:
            if mqh_enums[enum_name] != py_val:
                errors.append(f"  SL '{fid}': {enum_name} Python={py_val} MQL5={mqh_enums[enum_name]}")
    for fid, info in TAKE_PROFIT_MAP.items():
        enum_name = info["enum"]
        py_val = info["value"]
        if enum_name is None:
            continue
        if enum_name in mqh_enums:
            if mqh_enums[enum_name] != py_val:
                errors.append(f"  TP '{fid}': {enum_name} Python={py_val} MQL5={mqh_enums[enum_name]}")
    return errors


def test_trailing_maps(mqh_enums):
    """Verifica Trailing Type e Activation maps contra BP_Constants."""
    from mappings import TRAILING_TYPE_MAP, TRAILING_ACTIVATION_MAP
    errors = []
    # Trailing type: Python usa Framework enums (TRAILING_*), BP_Constants tem BP_TRAIL_*
    # Verificar que os values numericos sao iguais
    bp_trail = {
        "TRAILING_NONE": mqh_enums.get("BP_TRAIL_NONE"),
        "TRAILING_RR_RATIO": mqh_enums.get("BP_TRAIL_RR_RATIO"),
        "TRAILING_BAR_BY_BAR": mqh_enums.get("BP_TRAIL_BAR_BY_BAR"),
        "TRAILING_ATR": mqh_enums.get("BP_TRAIL_ATR"),
    }
    for fid, info in TRAILING_TYPE_MAP.items():
        fw_enum = info["enum"]  # Framework enum name
        py_val = info["value"]
        bp_val = bp_trail.get(fw_enum)
        if bp_val is not None and bp_val != py_val:
            errors.append(f"  TRAIL '{fid}': {fw_enum} Python={py_val} BP={bp_val}")

    bp_act = {
        "ACTIVATION_IMMEDIATE": mqh_enums.get("BP_ACT_IMMEDIATE"),
        "ACTIVATION_AFTER_PROFIT": mqh_enums.get("BP_ACT_AFTER_PROFIT"),
        "ACTIVATION_AFTER_BREAKEVEN": mqh_enums.get("BP_ACT_AFTER_BREAKEVEN"),
    }
    for fid, info in TRAILING_ACTIVATION_MAP.items():
        fw_enum = info["enum"]
        py_val = info["value"]
        bp_val = bp_act.get(fw_enum)
        if bp_val is not None and bp_val != py_val:
            errors.append(f"  ACT '{fid}': {fw_enum} Python={py_val} BP={bp_val}")

    return errors


if __name__ == "__main__":
    mqh_path = r"c:\Users\ivans\Documents\Claude Code\BackTestPro\mql5\Include\BacktestPro\BP_Constants.mqh"
    mqh_enums = parse_mqh_enums(mqh_path)
    print(f"Enums extraidos do MQL5: {len(mqh_enums)}")

    all_errors = []

    tests = [
        ("Indicators", test_indicator_map),
        ("Conditions", test_condition_map),
        ("Candles", test_candle_map),
        ("SMC", test_smc_map),
        ("SL/TP", test_sl_tp_maps),
        ("Trailing", test_trailing_maps),
    ]

    for name, fn in tests:
        errs = fn(mqh_enums)
        status = "PASS" if not errs else "FAIL"
        print(f"  [{status}] {name}" + (f" ({len(errs)} erros)" if errs else ""))
        all_errors.extend(errs)

    if all_errors:
        print(f"\nERROS ({len(all_errors)}):")
        for e in all_errors:
            print(e)
        sys.exit(1)
    else:
        print(f"\nTeste 7 PASSED - Todos os enums consistentes")
        sys.exit(0)

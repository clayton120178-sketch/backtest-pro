"""
BacktestPro - Backtest Runner
Transforma JSON de estrategia em .set + .ini e executa backtest no MT5.

Input:  JSON com parametros da estrategia
Output: .set + .ini no diretorio do MT5, inicia processo, monitora log

Uso:
    runner = BacktestRunner()
    result = runner.run(json_config)
    # ou
    runner.generate_files(json_config)  # so gera .set/.ini sem executar
"""

import os
import subprocess
import time
import logging
import json
import uuid
import psutil
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


# ============================================================================
# CONSTANTES
# ============================================================================

# Caminhos MT5 (mesmos do WFA Automatico)
MT5_PATH = r"C:\Program Files\MetaTrader_Teste\terminal64.exe"
MT5_GUID = "84064CA60B86A0341461272DFBBA7B87"
APPDATA = os.getenv("APPDATA", "")

# Diretorios derivados
MT5_DATA_DIR = os.path.join(APPDATA, "MetaQuotes", "Terminal", MT5_GUID)
MT5_EXPERTS_DIR = os.path.join(MT5_DATA_DIR, "MQL5", "Experts")
MT5_TESTER_DIR = os.path.join(MT5_DATA_DIR, "MQL5", "Profiles", "Tester")
MT5_LOG_DIR = os.path.join(MT5_DATA_DIR, "Tester", "logs")

# Diretorio de output para .ini/.set
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "_output")

# Timeframes MT5 (constantes oficiais)
MT5_TIMEFRAMES = {
    "M1": 1, "M2": 2, "M3": 3, "M4": 4, "M5": 5,
    "M6": 6, "M10": 10, "M12": 12, "M15": 15,
    "M20": 20, "M30": 30,
    "H1": 16385, "H2": 16386, "H3": 16387, "H4": 16388,
    "H6": 16390, "H8": 16392, "H12": 16396,
    "D1": 16408, "W1": 32769, "MN1": 49153,
}

# Mapeamento de enums MQL5 para valores numericos
# Os enums do EA usam valores numericos no .set
ENUM_MAPS = {
    # ENUM_BP_INDICATOR
    "BP_IND_NONE": 0, "BP_IND_RSI": 1, "BP_IND_STOCH": 2,
    "BP_IND_CCI": 3, "BP_IND_WILLIAMS": 4, "BP_IND_MACD": 5,
    "BP_IND_SMA": 10, "BP_IND_EMA": 11, "BP_IND_ADX": 12,
    "BP_IND_SAR": 13, "BP_IND_BOLLINGER": 14, "BP_IND_VWAP": 15,
    "BP_IND_VOLUME": 20, "BP_IND_VOLUME_MA": 21, "BP_IND_OBV": 22,
    "BP_IND_ATR": 30,
    "BP_IND_PRICE_HIGH_N": 40, "BP_IND_PRICE_LOW_N": 41,
    "BP_IND_PREV_HIGH": 42, "BP_IND_PREV_LOW": 43,
    "BP_IND_FIBONACCI": 44, "BP_IND_GAP": 45,

    # ENUM_BP_CONDITION
    "BP_COND_NONE": 0, "BP_COND_CROSS_ABOVE": 1, "BP_COND_CROSS_BELOW": 2,
    "BP_COND_ABOVE": 3, "BP_COND_BELOW": 4,
    "BP_COND_IN_ZONE_OB": 5, "BP_COND_IN_ZONE_OS": 6,
    "BP_COND_CROSS_ABOVE_PRICE": 7, "BP_COND_CROSS_BELOW_PRICE": 8,
    "BP_COND_MACD_CROSS_UP": 9, "BP_COND_MACD_CROSS_DOWN": 10,
    "BP_COND_MACD_ABOVE_ZERO": 11, "BP_COND_MACD_BELOW_ZERO": 12,
    "BP_COND_MA_CROSS_ABOVE": 13, "BP_COND_MA_CROSS_BELOW": 14,

    # ENUM_BP_ENTRY_TYPE
    "BP_ENTRY_NEXT_OPEN": 0, "BP_ENTRY_STOP_ORDER": 1,

    # ENUM_TRADING_DIRECTION
    "TRADING_BOTH": 0, "TRADING_BUY_ONLY": 1, "TRADING_SELL_ONLY": -1,

    # ENUM_BP_CANDLE_PATTERN
    "BP_CANDLE_NONE": 0,
    "BP_CANDLE_HAMMER": 1, "BP_CANDLE_BULL_ENGULF": 2,
    "BP_CANDLE_MORNING_STAR": 3, "BP_CANDLE_BULL_HARAMI": 4,
    "BP_CANDLE_BOTTOM_TAIL": 5, "BP_CANDLE_DOUBLE_BOTTOM": 6,
    "BP_CANDLE_BULL_PIVOT": 7,
    "BP_CANDLE_SHOOTING_STAR": 10, "BP_CANDLE_BEAR_ENGULF": 11,
    "BP_CANDLE_EVENING_STAR": 12, "BP_CANDLE_BEAR_HARAMI": 13,
    "BP_CANDLE_TOP_TAIL": 14, "BP_CANDLE_DOUBLE_TOP": 15,
    "BP_CANDLE_BEAR_PIVOT": 16,
    "BP_CANDLE_DOJI": 20, "BP_CANDLE_SPINNING_TOP": 21,

    # ENUM_BP_SMC_CONCEPT
    "BP_SMC_NONE": 0,
    "BP_SMC_FVG_BULL": 1, "BP_SMC_FVG_BEAR": 2,
    "BP_SMC_BOS_BULL": 3, "BP_SMC_BOS_BEAR": 4,
    "BP_SMC_CHOCH_BULL": 5, "BP_SMC_CHOCH_BEAR": 6,
    "BP_SMC_OB_BULL": 7, "BP_SMC_OB_BEAR": 8,
    "BP_SMC_SWEEP_HIGH": 9, "BP_SMC_SWEEP_LOW": 10,

    # ENUM_BP_SL_TYPE (EA - BP_Constants.mqh)
    # ATENCAO: Valores do EA, NAO do Framework (CommonTypes.mqh)!
    # EA: BP_SL_CANDLE=0, BP_SL_ATR=1, BP_SL_FIXED_PTS=2
    # Framework: SL_ATR=0, SL_FIXED=1, SL_GRAPHIC=2  (DIFERENTE!)
    "BP_SL_CANDLE": 0, "BP_SL_ATR": 1, "BP_SL_FIXED_PTS": 2,
    # Aliases legados (manter para compatibilidade com JSONs antigos)
    "SL_ATR": 1, "SL_FIXED": 2, "SL_GRAPHIC": 0,

    # ENUM_BP_TP_TYPE (EA - BP_Constants.mqh)
    # EA: BP_TP_RR=0, BP_TP_ATR=1, BP_TP_FIXED_PTS=2
    # Framework: TP_FIXED_POINTS=0, TP_RR_MULTIPLIER=1, TP_ZIGZAG_LEVEL=2, TP_ATR=3
    "BP_TP_RR": 0, "BP_TP_ATR": 1, "BP_TP_FIXED_PTS": 2,
    # Aliases legados
    "TP_FIXED": 2, "TP_RR_MULTIPLIER": 0, "TP_ZIGZAG": 2, "TP_ATR": 1,

    # ENUM_RISK_TYPE (framework)
    "RISK_FIXED": 0, "RISK_PERCENT": 1, "RISK_PROGRESSION": 2,

    # ENUM_LOG_LEVEL (framework)
    "LOG_LEVEL_ERROR": 1, "LOG_LEVEL_WARNING": 2, "LOG_LEVEL_INFO": 3,
    "LOG_LEVEL_VERBOSE": 4, "LOG_LEVEL_DEBUG": 5,

    # ENUM_LOG_OUTPUT (framework)
    "LOG_TO_PRINT": 1, "LOG_TO_FILE": 2, "LOG_TO_BOTH": 3,

    # ENUM_TIMEFRAMES (para TP_ATR)
    "PERIOD_CURRENT": 0,
    "PERIOD_M1": 1, "PERIOD_M5": 5, "PERIOD_M15": 15, "PERIOD_M30": 30,
    "PERIOD_H1": 16385, "PERIOD_H4": 16388,
    "PERIOD_D1": 16408, "PERIOD_W1": 32769, "PERIOD_MN1": 49153,
}


def resolve_enum(value):
    """Converte nome de enum para valor numerico, ou retorna o valor se ja for numerico."""
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str) and value in ENUM_MAPS:
        return ENUM_MAPS[value]
    if isinstance(value, bool):
        return 1 if value else 0
    return value


# ============================================================================
# GERADOR DE ARQUIVOS
# ============================================================================

def build_set_content(params: Dict[str, Any]) -> str:
    """
    Gera conteudo do arquivo .set a partir dos parametros.

    Formato MT5 para valores fixos (backtest simples):
        parameter_name=value

    Args:
        params: Dicionario com nome_do_input -> valor
    Returns:
        Conteudo do .set como string
    """
    lines = []
    lines.append("; BacktestPro - SET file")
    lines.append(f"; Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    for name, value in params.items():
        resolved = resolve_enum(value)
        # bool -> 0/1
        if isinstance(resolved, bool):
            resolved = 1 if resolved else 0
        lines.append(f"{name}={resolved}")

    lines.append("")
    return "\n".join(lines)


def build_ini_content(
    ea_name: str,
    symbol: str,
    timeframe: str,
    from_date: str,
    to_date: str,
    params: Dict[str, Any],
    deposit: int = 10000,
    currency: str = "BRL",
    leverage: int = 100,
    model: int = 1,
    report_file: str = "",
) -> str:
    """
    Gera conteudo do arquivo .ini para o Strategy Tester do MT5.

    Args:
        ea_name:   Nome do EA (ex: "BacktestPro_Universal_EA")
        symbol:    Simbolo (ex: "WINJ25")
        timeframe: Timeframe display (ex: "M5", "H1")
        from_date: Data inicio "YYYY.MM.DD"
        to_date:   Data fim "YYYY.MM.DD"
        params:    Dicionario com parametros do EA
        deposit:   Capital inicial
        currency:  Moeda
        leverage:  Alavancagem
        model:     Modelo de teste (1=Every tick)
    Returns:
        Conteudo do .ini como string
    """
    lines = []
    lines.append("; BacktestPro - INI file")
    lines.append(f"; Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    # Secao [Tester]
    lines.append("[Tester]")
    lines.append(f"Expert={ea_name}")
    lines.append(f"Symbol={symbol}")
    lines.append(f"Period={timeframe}")
    lines.append(f"FromDate={from_date}")
    lines.append(f"ToDate={to_date}")
    lines.append(f"Deposit={deposit}")
    lines.append(f"Currency={currency}")
    lines.append("ProfitInPips=0")
    lines.append(f"Leverage={leverage}")
    lines.append("ExecutionMode=5")
    lines.append(f"Model={model}")
    lines.append("Optimization=0")           # 0 = backtest simples (sem otimizacao)
    lines.append("OptimizationCriterion=0")
    if report_file:
        lines.append(f"Report={report_file}")
        lines.append("ReplaceReport=1")
    lines.append("ShutdownTerminal=1")        # Fecha MT5 ao terminar
    lines.append("")

    # Secao [TesterInputs] - parametros do EA com valores fixos
    lines.append("[TesterInputs]")
    for name, value in params.items():
        resolved = resolve_enum(value)
        if isinstance(resolved, bool):
            resolved = 1 if resolved else 0
        lines.append(f"{name}={resolved}")

    lines.append("")
    return "\n".join(lines)


# ============================================================================
# CONTROLE DO MT5
# ============================================================================

def is_mt5_running() -> bool:
    """Verifica se o terminal MT5 esta rodando."""
    for proc in psutil.process_iter(["name"]):
        try:
            if proc.info["name"] and "terminal64" in proc.info["name"].lower():
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return False


def shutdown_mt5():
    """Forca encerramento de todas as instancias do MT5."""
    logger.info("Encerrando instancias do MT5...")
    subprocess.run(
        ["taskkill", "/F", "/IM", "terminal64.exe"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    while is_mt5_running():
        time.sleep(1)
    logger.info("MT5 encerrado.")


def clear_tester_log():
    """Remove log do tester de hoje para garantir leitura limpa."""
    today = datetime.now().strftime("%Y%m%d")
    log_file = os.path.join(MT5_LOG_DIR, f"{today}.log")
    if os.path.exists(log_file):
        try:
            os.remove(log_file)
            logger.info(f"Log removido: {log_file}")
        except OSError as e:
            logger.warning(f"Nao foi possivel remover log: {e}")


def start_backtest(ini_path: str, timeout: int = 3600) -> bool:
    """
    Inicia o MT5 com o arquivo .ini e aguarda conclusao do backtest.

    Fluxo:
        1. Encerra MT5 se estiver rodando
        2. Limpa log do tester
        3. Inicia MT5 com /config:ini_path
        4. Aguarda inicializacao (60s)
        5. Monitora processo ate terminar ou timeout

    Args:
        ini_path: Caminho absoluto do arquivo .ini
        timeout:  Timeout em segundos (default: 3600 = 1 hora)
    Returns:
        True se backtest concluiu (MT5 fechou normalmente)
    """
    ini_path = os.path.abspath(ini_path)

    if not os.path.exists(MT5_PATH):
        logger.error(f"MT5 nao encontrado: {MT5_PATH}")
        return False

    if not os.path.exists(ini_path):
        logger.error(f"INI nao encontrado: {ini_path}")
        return False

    # 1. Cleanup
    shutdown_mt5()
    clear_tester_log()

    # 2. Comando
    cmd = [MT5_PATH, f"/config:{ini_path}"]
    logger.info(f"Iniciando MT5: {' '.join(cmd)}")

    # 3. Inicia processo
    start_time = datetime.now()
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=MT5_EXPERTS_DIR,
    )
    logger.info(f"MT5 iniciado - PID: {process.pid}")

    # 4. Aguarda inicializacao (60s em blocos de 10s)
    logger.info("Aguardando inicializacao do MT5 (60s)...")
    for i in range(6):
        time.sleep(10)
        if process.poll() is not None:
            logger.error(f"MT5 encerrou inesperadamente apos {(i+1)*10}s")
            return False
        logger.info(f"  {(i+1)*10}s - MT5 rodando (PID: {process.pid})")

    # 5. Monitora ate conclusao
    logger.info("MT5 inicializado. Monitorando backtest...")
    deadline = time.time() + timeout

    while process.poll() is None:
        if time.time() > deadline:
            logger.error(f"Timeout de {timeout}s atingido. Encerrando MT5.")
            process.kill()
            return False
        time.sleep(5)

    elapsed = (datetime.now() - start_time).total_seconds()
    logger.info(f"MT5 encerrou - return code: {process.returncode} - tempo: {elapsed:.0f}s")

    # MT5 frequentemente retorna codigos != 0 mesmo em execucoes bem sucedidas.
    # Consideramos sucesso se o processo terminou (nao foi killed por timeout).
    return True


# ============================================================================
# CLASSE PRINCIPAL
# ============================================================================

class BacktestRunner:
    """
    Orquestra a execucao de backtests no MT5.

    Input: JSON com configuracao da estrategia
    Output: Gera .set + .ini, executa MT5 e retorna resultado
    """

    def __init__(self, output_dir: str = OUTPUT_DIR):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_files(self, config: Dict[str, Any]) -> Dict[str, str]:
        """
        Gera arquivos .set e .ini a partir do JSON de configuracao.

        Args:
            config: Dicionario JSON com a estrategia. Estrutura esperada:
                {
                    "ea_name": "BacktestPro_Universal_EA",
                    "symbol": "WINJ25",
                    "timeframe": "M5",
                    "from_date": "2025.01.01",
                    "to_date": "2025.03.27",
                    "deposit": 10000,
                    "currency": "BRL",
                    "leverage": 100,
                    "model": 1,
                    "parameters": {
                        "InpLogLevel": "LOG_LEVEL_INFO",
                        "InpLogOutput": "LOG_TO_PRINT",
                        "InpUseOscillators": true,
                        "InpUseIndicators": true,
                        "InpUseCandlePatterns": false,
                        "InpUseSmartMoney": false,
                        "InpInd1": "BP_IND_RSI",
                        "InpCond1": "BP_COND_CROSS_ABOVE",
                        "InpPeriod1": 14,
                        "InpPeriod1b": 0,
                        "InpValue1": 30.0,
                        "InpUseCond2": false,
                        "InpInd2": "BP_IND_SMA",
                        "InpCond2": "BP_COND_ABOVE",
                        "InpPeriod2": 200,
                        "InpPeriod2b": 0,
                        "InpValue2": 0.0,
                        "InpUseCond3": false,
                        "InpInd3": "BP_IND_NONE",
                        "InpCond3": "BP_COND_NONE",
                        "InpPeriod3": 14,
                        "InpPeriod3b": 0,
                        "InpValue3": 0.0,
                        "InpEntryType": "BP_ENTRY_NEXT_OPEN",
                        "InpStopOrderBuffer": 1,
                        "InpStopOrderExpBars": 1,
                        "InpDirection": "TRADING_BUY_ONLY",
                        "InpSLType": "SL_GRAPHIC",
                        "InpSL_ATRPeriod": 14,
                        "InpSL_ATRMult": 1.5,
                        "InpSL_FixedPts": 100,
                        "InpSL_Buffer": 5,
                        "InpSL_Min": 10,
                        "InpSL_Max": 5000,
                        "InpTPType": "TP_RR_MULTIPLIER",
                        "InpTP_FixedPts": 200,
                        "InpTP_RR": 2.0,
                        "InpTP_ZZDepth": 12,
                        "InpTP_ZZDeviation": 5,
                        "InpTP_ZZBackstep": 3,
                        "InpTP_ZZBuffer": 2,
                        "InpTP_Min": 10,
                        "InpTP_Max": 0,
                        "InpTP_ATRPeriod": 14,
                        "InpTP_ATRPercent": 100.0,
                        "InpTP_ATRTF": "PERIOD_D1",
                        "InpRiskType": "RISK_FIXED",
                        "InpRiskPercent": 1.0,
                        "InpFixedLots": 0.1,
                        "InpInitialAlloc": 10000.0,
                        "InpStartHour": 9,
                        "InpStartMin": 0,
                        "InpEndHour": 17,
                        "InpEndMin": 30,
                        "InpMaxTradesPerDay": 0,
                        "InpCandleBull": "BP_CANDLE_NONE",
                        "InpCandleBear": "BP_CANDLE_NONE",
                        "InpSMCEntry": "BP_SMC_NONE"
                    }
                }

        Returns:
            Dict com paths: {"set_path": "...", "ini_path": "..."}
        """
        ea_name = config.get("ea_name", "BacktestPro_Universal_EA")
        symbol = config["symbol"]
        timeframe = config["timeframe"]
        from_date = config["from_date"]
        to_date = config["to_date"]
        params = config["parameters"]

        # UniqueID para identificar este backtest (evita colisao entre usuarios)
        unique_id = uuid.uuid4().hex[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"BP_{symbol}_{timeframe}_{unique_id}_{timestamp}"
        report_file = f"{base_name}.xml"

        set_path = os.path.join(self.output_dir, f"{base_name}.set")
        ini_path = os.path.join(self.output_dir, f"{base_name}.ini")

        # Gera .set
        set_content = build_set_content(params)
        with open(set_path, "w", encoding="utf-8") as f:
            f.write(set_content)
        logger.info(f".set gerado: {set_path}")

        # Gera .ini
        ini_content = build_ini_content(
            ea_name=ea_name,
            symbol=symbol,
            timeframe=timeframe,
            from_date=from_date,
            to_date=to_date,
            params=params,
            deposit=config.get("deposit", 10000),
            currency=config.get("currency", "BRL"),
            leverage=config.get("leverage", 100),
            model=config.get("model", 1),
            report_file=report_file,
        )
        with open(ini_path, "w", encoding="utf-8") as f:
            f.write(ini_content)
        logger.info(f".ini gerado: {ini_path}")

        return {
            "set_path": set_path,
            "ini_path": ini_path,
            "report_file": report_file,
            "unique_id": unique_id,
            "base_name": base_name,
        }

    def run(self, config: Dict[str, Any], timeout: int = 3600) -> Dict[str, Any]:
        """
        Gera arquivos e executa backtest no MT5.

        Args:
            config:  JSON de configuracao da estrategia
            timeout: Timeout em segundos
        Returns:
            Dict com resultado:
                {"success": bool, "set_path": str, "ini_path": str, "elapsed": float}
        """
        files = self.generate_files(config)
        start = time.time()
        success = start_backtest(files["ini_path"], timeout=timeout)
        elapsed = time.time() - start

        return {
            "success": success,
            "set_path": files["set_path"],
            "ini_path": files["ini_path"],
            "elapsed": elapsed,
        }

    def run_from_file(self, json_path: str, timeout: int = 3600) -> Dict[str, Any]:
        """
        Carrega JSON de arquivo e executa backtest.

        Args:
            json_path: Caminho do arquivo .json
            timeout:   Timeout em segundos
        Returns:
            Mesmo retorno de run()
        """
        with open(json_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        return self.run(config, timeout=timeout)


# ============================================================================
# CLI
# ============================================================================

if __name__ == "__main__":
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    if len(sys.argv) < 2:
        print("Uso: python backtest_runner.py <config.json> [--dry-run]")
        print("  --dry-run  Gera .set/.ini sem executar o MT5")
        sys.exit(1)

    json_path = sys.argv[1]
    dry_run = "--dry-run" in sys.argv

    runner = BacktestRunner()

    with open(json_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    if dry_run:
        files = runner.generate_files(config)
        print(f"\n.set: {files['set_path']}")
        print(f".ini: {files['ini_path']}")
        print("\n[DRY RUN] Arquivos gerados. MT5 nao foi iniciado.")
    else:
        result = runner.run(config)
        print(f"\nResultado: {'OK' if result['success'] else 'FALHOU'}")
        print(f"Tempo: {result['elapsed']:.0f}s")
        print(f".set: {result['set_path']}")
        print(f".ini: {result['ini_path']}")

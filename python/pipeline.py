"""
BacktestPro - Pipeline Orquestrador

Fluxo completo:
1. Recebe cfg do frontend
2. Valida combinacao de condicoes
3. Gera checksum para cache lookup
4. Verifica cache (Supabase ou local)
5. Se cache miss: converte -> gera .set/.ini -> executa MT5 -> parseia resultado
6. Salva resultado com checksum para futuros cache hits
7. Retorna JSON com metricas para o frontend

Modos de operacao:
- LOCAL:  Executa tudo localmente (Python + MT5 na mesma maquina)
- WORKER: Roda como worker na VPS, polling fila do Supabase
"""

import json
import logging
import os
import time
from datetime import datetime
from typing import Any, Dict, Optional

from backtest_runner import BacktestRunner
from cfg_to_json import build_backtest_json, compute_checksum, validate_cfg, ConversionError
from result_parser import get_backtest_result

logger = logging.getLogger(__name__)


# ============================================================================
# CACHE LOCAL (fallback quando Supabase nao esta disponivel)
# ============================================================================

CACHE_DIR = os.path.join(os.path.dirname(__file__), "_cache")


def _local_cache_path(checksum: str) -> str:
    return os.path.join(CACHE_DIR, f"{checksum}.json")


def cache_lookup_local(checksum: str) -> Optional[Dict[str, Any]]:
    """Busca resultado no cache local por checksum."""
    path = _local_cache_path(checksum)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                cached = json.load(f)
            logger.info(f"Cache HIT (local): {checksum[:12]}...")
            return cached
        except (json.JSONDecodeError, OSError):
            pass
    return None


def cache_save_local(checksum: str, result: Dict[str, Any]):
    """Salva resultado no cache local."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    path = _local_cache_path(checksum)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        logger.info(f"Cache SAVE (local): {checksum[:12]}...")
    except OSError as e:
        logger.warning(f"Erro ao salvar cache: {e}")


# ============================================================================
# PIPELINE PRINCIPAL
# ============================================================================

class BacktestPipeline:
    """
    Orquestra o fluxo completo de backtest.

    Uso:
        pipeline = BacktestPipeline()
        result = pipeline.run(frontend_cfg)
    """

    def __init__(
        self,
        output_dir: str = "",
        use_cache: bool = True,
        from_date: str = "2019.01.02",
        to_date: Optional[str] = None,
        deposit: int = 10000,
        timeout: int = 3600,
    ):
        self.use_cache = use_cache
        self.from_date = from_date
        self.to_date = to_date
        self.deposit = deposit
        self.timeout = timeout

        if output_dir:
            self.runner = BacktestRunner(output_dir)
        else:
            self.runner = BacktestRunner()

    def run(self, frontend_cfg: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executa pipeline completo.

        Args:
            frontend_cfg: state.cfg do app.html

        Returns:
            {
                "success": bool,
                "checksum": str,
                "cached": bool,         # True se veio do cache
                "warnings": [str],
                "config": dict,         # JSON enviado ao EA
                "result": {             # Metricas do backtest
                    "metrics": {...},
                    "trades": [...],
                    "equity_curve": [...]
                },
                "files": {              # Paths dos arquivos gerados
                    "set_path": str,
                    "ini_path": str,
                    "report_file": str
                },
                "elapsed": float,       # Tempo total em segundos
                "error": str            # Mensagem de erro se success=False
            }
        """
        start_time = time.time()
        response = {
            "success": False,
            "checksum": "",
            "cached": False,
            "warnings": [],
            "config": {},
            "result": None,
            "files": {},
            "elapsed": 0,
            "error": "",
        }

        # 1. Validar
        try:
            warnings = validate_cfg(frontend_cfg)
            response["warnings"] = [str(w) for w in warnings]
        except ConversionError as e:
            response["error"] = str(e)
            response["elapsed"] = time.time() - start_time
            return response

        # 2. Converter frontend cfg -> JSON EA
        try:
            config, extra_warnings = build_backtest_json(
                frontend_cfg,
                from_date=self.from_date,
                to_date=self.to_date,
                deposit=self.deposit,
            )
            response["config"] = config
            response["warnings"].extend([str(w) for w in extra_warnings])
        except (ConversionError, KeyError, ValueError) as e:
            response["error"] = f"Erro na conversao: {e}"
            response["elapsed"] = time.time() - start_time
            return response

        # 3. Checksum para cache
        checksum = compute_checksum(config)
        response["checksum"] = checksum

        # 4. Cache lookup
        if self.use_cache:
            cached = cache_lookup_local(checksum)
            if cached:
                response["success"] = True
                response["cached"] = True
                response["result"] = cached
                response["elapsed"] = time.time() - start_time
                return response

        # 5. Gerar .set + .ini e executar
        try:
            files = self.runner.generate_files(config)
            response["files"] = files
        except Exception as e:
            response["error"] = f"Erro ao gerar arquivos: {e}"
            response["elapsed"] = time.time() - start_time
            return response

        # 6. Executar MT5
        from backtest_runner import start_backtest
        success = start_backtest(files["ini_path"], timeout=self.timeout)

        if not success:
            response["error"] = "MT5 falhou ou timeout atingido."
            response["elapsed"] = time.time() - start_time
            return response

        # 7. Parsear resultado
        report_name = files.get("report_file", "")
        if report_name:
            result = get_backtest_result(report_name)
            if result:
                response["success"] = True
                response["result"] = result

                # 8. Salvar no cache
                if self.use_cache:
                    cache_save_local(checksum, result)
            else:
                response["error"] = f"Report '{report_name}' nao encontrado ou falha no parse."
        else:
            response["error"] = "Nome do report nao definido."

        response["elapsed"] = time.time() - start_time
        return response

    def dry_run(self, frontend_cfg: Dict[str, Any]) -> Dict[str, Any]:
        """
        Gera .set/.ini sem executar MT5. Util para validacao.

        Returns:
            Mesmo formato de run(), mas sem result e sem execucao.
        """
        start_time = time.time()
        response = {
            "success": True,
            "checksum": "",
            "cached": False,
            "warnings": [],
            "config": {},
            "result": None,
            "files": {},
            "elapsed": 0,
            "error": "",
        }

        try:
            warnings = validate_cfg(frontend_cfg)
            response["warnings"] = [str(w) for w in warnings]
        except ConversionError as e:
            response["success"] = False
            response["error"] = str(e)
            response["elapsed"] = time.time() - start_time
            return response

        try:
            config, extra_warnings = build_backtest_json(
                frontend_cfg,
                from_date=self.from_date,
                to_date=self.to_date,
                deposit=self.deposit,
            )
            response["config"] = config
            response["warnings"].extend([str(w) for w in extra_warnings])
        except (ConversionError, KeyError, ValueError) as e:
            response["success"] = False
            response["error"] = f"Erro na conversao: {e}"
            response["elapsed"] = time.time() - start_time
            return response

        checksum = compute_checksum(config)
        response["checksum"] = checksum

        files = self.runner.generate_files(config)
        response["files"] = files
        response["elapsed"] = time.time() - start_time
        return response


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

    # Modo 1: pipeline com cfg inline (teste)
    if len(sys.argv) < 2 or sys.argv[1] == "--test":
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

        pipeline = BacktestPipeline()
        result = pipeline.dry_run(test_cfg)

        print(f"\n{'='*60}")
        print(f"SUCCESS: {result['success']}")
        print(f"CHECKSUM: {result['checksum']}")
        print(f"CACHED: {result['cached']}")
        print(f"ELAPSED: {result['elapsed']:.3f}s")

        if result["warnings"]:
            print(f"\nWARNINGS:")
            for w in result["warnings"]:
                print(f"  {w}")

        if result["error"]:
            print(f"\nERROR: {result['error']}")

        if result["files"]:
            print(f"\nFILES:")
            for k, v in result["files"].items():
                print(f"  {k}: {v}")

        print(f"\nEA PARAMS ({len(result['config'].get('parameters', {}))} inputs):")
        for k, v in result["config"].get("parameters", {}).items():
            print(f"  {k} = {v}")

    # Modo 2: pipeline com JSON file
    elif os.path.exists(sys.argv[1]):
        json_path = sys.argv[1]
        dry_run = "--dry-run" in sys.argv

        with open(json_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)

        pipeline = BacktestPipeline()

        if dry_run:
            result = pipeline.dry_run(cfg)
        else:
            result = pipeline.run(cfg)

        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))

    else:
        print("Uso:")
        print("  python pipeline.py --test              (teste com cfg padrao)")
        print("  python pipeline.py config.json         (executa backtest)")
        print("  python pipeline.py config.json --dry-run (gera arquivos sem executar)")

"""
BacktestPro - Worker VPS

Roda na VPS Windows com MT5 instalado.
Faz polling da tabela backtests no Supabase, pega jobs 'queued',
executa o pipeline completo e salva o resultado de volta.

Fluxo:
1. Conecta ao Supabase via service_role key
2. Chama claim_backtest_job() para pegar um job atomicamente
3. Verifica cache por checksum (evita re-rodar backtests identicos)
4. Executa pipeline: cfg -> .set/.ini -> MT5 -> parse result
5. Salva resultado no Supabase (status=completed ou failed)
6. Repete polling

Uso:
    python worker.py                   # Inicia worker com polling
    python worker.py --once            # Executa um job e sai
    python worker.py --interval 5      # Polling a cada 5 segundos
"""

import json
import logging
import os
import signal
import sys
import time
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

try:
    from dotenv import load_dotenv
    # Procura .env no diretorio do script (python/) e tambem no pai (BackTestPro/)
    _script_dir = os.path.dirname(os.path.abspath(__file__))
    _parent_dir = os.path.dirname(_script_dir)
    load_dotenv(os.path.join(_script_dir, ".env"))
    load_dotenv(os.path.join(_parent_dir, ".env"))
except ImportError:
    pass  # python-dotenv opcional, pode usar vars de ambiente direto

import requests

from cfg_to_json import build_backtest_json, compute_checksum, validate_cfg, ConversionError
from pipeline import BacktestPipeline

logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURACAO
# ============================================================================

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")
WORKER_ID = os.getenv("WORKER_ID", f"vps-{uuid.uuid4().hex[:8]}")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "5"))
MAX_BACKTEST_TIMEOUT = int(os.getenv("MAX_BACKTEST_TIMEOUT", "3600"))

# Flag para shutdown graceful
_shutdown = False


def _signal_handler(sig, frame):
    global _shutdown
    logger.info("Recebido sinal de shutdown, finalizando apos job atual...")
    _shutdown = True


signal.signal(signal.SIGINT, _signal_handler)
signal.signal(signal.SIGTERM, _signal_handler)


# ============================================================================
# SUPABASE CLIENT (REST API direto, sem SDK extra)
# ============================================================================

class SupabaseClient:
    """Cliente minimalista para Supabase via REST API."""

    def __init__(self, url: str, service_key: str):
        self.url = url.rstrip("/")
        self.headers = {
            "apikey": service_key,
            "Authorization": f"Bearer {service_key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }

    def rpc(self, fn_name: str, params: Dict[str, Any] = None) -> Any:
        """Chama uma funcao RPC do Supabase."""
        resp = requests.post(
            f"{self.url}/rest/v1/rpc/{fn_name}",
            headers=self.headers,
            json=params or {},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    def get_backtest(self, backtest_id: str) -> Optional[Dict]:
        """Busca um backtest por ID."""
        resp = requests.get(
            f"{self.url}/rest/v1/backtests?id=eq.{backtest_id}&select=*",
            headers=self.headers,
            timeout=30,
        )
        resp.raise_for_status()
        rows = resp.json()
        return rows[0] if rows else None

    def update_backtest(self, backtest_id: str, data: Dict[str, Any]):
        """Atualiza campos de um backtest."""
        resp = requests.patch(
            f"{self.url}/rest/v1/backtests?id=eq.{backtest_id}",
            headers=self.headers,
            json=data,
            timeout=30,
        )
        resp.raise_for_status()

    def insert_backtest_result(
        self,
        backtest_id: str,
        result: Dict[str, Any],
        checksum: str,
        elapsed_ms: int,
    ):
        """Marca backtest como completed com resultado."""
        self.update_backtest(backtest_id, {
            "status": "completed",
            "result": result,
            "checksum": checksum,
            "completed_at": datetime.utcnow().isoformat(),
            "elapsed_ms": elapsed_ms,
        })

    def fail_backtest(self, backtest_id: str, error: str, elapsed_ms: int = 0):
        """Marca backtest como failed."""
        self.update_backtest(backtest_id, {
            "status": "failed",
            "error": error,
            "completed_at": datetime.utcnow().isoformat(),
            "elapsed_ms": elapsed_ms,
        })


# ============================================================================
# WORKER
# ============================================================================

class BacktestWorker:
    """Worker que processa backtests da fila do Supabase."""

    def __init__(self, supabase: SupabaseClient):
        self.db = supabase
        self.pipeline = BacktestPipeline(
            use_cache=True,
            timeout=MAX_BACKTEST_TIMEOUT,
        )

    def claim_job(self) -> Optional[str]:
        """Tenta pegar um job da fila. Retorna backtest_id ou None."""
        try:
            result = self.db.rpc("claim_backtest_job", {"p_worker_id": WORKER_ID})
            # RPC retorna o UUID diretamente (ou null)
            if result and result != "null":
                return str(result).strip('"')
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao clamar job: {e}")
            return None

    def process_job(self, backtest_id: str):
        """Processa um backtest completo."""
        start = time.time()

        # 1. Buscar dados do backtest
        bt = self.db.get_backtest(backtest_id)
        if not bt:
            logger.error(f"Backtest {backtest_id} nao encontrado")
            return

        frontend_cfg = bt.get("config", {})
        logger.info(f"Processando backtest {backtest_id[:8]}...")

        # 2. Converter cfg e calcular checksum
        try:
            config, warnings = build_backtest_json(frontend_cfg)
            checksum = compute_checksum(config)
        except (ConversionError, Exception) as e:
            elapsed_ms = int((time.time() - start) * 1000)
            self.db.fail_backtest(backtest_id, f"Erro na conversao: {e}", elapsed_ms)
            logger.error(f"Erro na conversao: {e}")
            return

        # 3. Cache lookup no Supabase
        try:
            cached = self.db.rpc("lookup_backtest_cache", {"p_checksum": checksum})
            if cached and cached != "null":
                elapsed_ms = int((time.time() - start) * 1000)
                self.db.insert_backtest_result(backtest_id, cached, checksum, elapsed_ms)
                logger.info(f"Cache HIT (Supabase): {checksum[:12]}... ({elapsed_ms}ms)")
                return
        except requests.exceptions.RequestException:
            pass  # Cache miss, prosseguir normalmente

        # 4. Executar pipeline completo
        try:
            result = self.pipeline.run(frontend_cfg)
        except Exception as e:
            elapsed_ms = int((time.time() - start) * 1000)
            self.db.fail_backtest(backtest_id, f"Erro no pipeline: {e}", elapsed_ms)
            logger.error(f"Erro no pipeline: {e}")
            return

        elapsed_ms = int((time.time() - start) * 1000)

        # 5. Salvar resultado
        if result["success"]:
            self.db.insert_backtest_result(
                backtest_id, result["result"], checksum, elapsed_ms
            )
            logger.info(
                f"Backtest {backtest_id[:8]} completado em {elapsed_ms}ms "
                f"(checksum={checksum[:12]}...)"
            )
        else:
            self.db.fail_backtest(backtest_id, result.get("error", "Erro desconhecido"), elapsed_ms)
            logger.warning(f"Backtest {backtest_id[:8]} falhou: {result.get('error')}")

    def run_once(self) -> bool:
        """Tenta processar um job. Retorna True se processou algo."""
        job_id = self.claim_job()
        if not job_id:
            return False
        try:
            self.process_job(job_id)
        except Exception as e:
            logger.error(f"Erro nao tratado no job {job_id}: {e}", exc_info=True)
            try:
                self.db.fail_backtest(job_id, f"Erro interno: {e}")
            except Exception:
                pass
        return True

    def run_loop(self, interval: int = 5):
        """Loop de polling infinito."""
        logger.info(f"Worker {WORKER_ID} iniciado (polling a cada {interval}s)")

        while not _shutdown:
            had_work = self.run_once()

            if _shutdown:
                break

            if not had_work:
                # Espera com check periodico do shutdown flag
                for _ in range(interval * 2):
                    if _shutdown:
                        break
                    time.sleep(0.5)
            # Se teve trabalho, volta imediatamente para pegar o proximo

        logger.info(f"Worker {WORKER_ID} encerrado.")


# ============================================================================
# CLI
# ============================================================================

def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    # Validar config
    if not SUPABASE_URL:
        logger.error("SUPABASE_URL nao definida. Configure via .env ou variavel de ambiente.")
        sys.exit(1)
    if not SUPABASE_SERVICE_KEY:
        logger.error("SUPABASE_SERVICE_KEY nao definida.")
        sys.exit(1)

    db = SupabaseClient(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    worker = BacktestWorker(db)

    # Parse args
    once = "--once" in sys.argv
    interval = POLL_INTERVAL

    for i, arg in enumerate(sys.argv):
        if arg == "--interval" and i + 1 < len(sys.argv):
            interval = int(sys.argv[i + 1])

    if once:
        logger.info("Modo --once: processando um job e saindo.")
        worker.run_once()
    else:
        worker.run_loop(interval=interval)


if __name__ == "__main__":
    main()

"""
BacktestPro - Windows Service Wrapper

Registra o worker.py como servico Windows via pywin32.

Gerenciamento:
    python worker_service.py install    # registra o servico
    python worker_service.py start      # inicia
    python worker_service.py stop       # para
    python worker_service.py restart    # reinicia
    python worker_service.py remove     # desinstala
    python worker_service.py status     # exibe status atual
    python worker_service.py debug      # roda em foreground (sem SCM)

O servico inicia automaticamente com o Windows (StartType=Automatic).
Logs: pasta Logs/ relativa ao diretorio do worker_service.py.
Rotacao: 5 MB por arquivo, 5 backups (maximo 25 MB).
"""

import logging
import logging.handlers
import os
import subprocess
import sys
import time

# ============================================================================
# LOGGING (usado tanto pelo servico quanto pelos comandos de gerenciamento)
# ============================================================================

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_LOGS_DIR = os.path.join(_SCRIPT_DIR, "Logs")
os.makedirs(_LOGS_DIR, exist_ok=True)

_LOG_FILE = os.path.join(_LOGS_DIR, "worker_service.log")

def _setup_logging():
    root = logging.getLogger()
    root.setLevel(logging.INFO)

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    rotating = logging.handlers.RotatingFileHandler(
        _LOG_FILE,
        maxBytes=5 * 1024 * 1024,   # 5 MB por arquivo
        backupCount=5,               # 5 backups = maximo 25 MB total
        encoding="utf-8",
    )
    rotating.setFormatter(fmt)
    root.addHandler(rotating)

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(fmt)
    root.addHandler(console)

_setup_logging()
logger = logging.getLogger("worker_service")


# ============================================================================
# SERVICO WINDOWS
# ============================================================================

SERVICE_NAME = "BackTestProWorker"
SERVICE_DISPLAY = "BackTestPro Worker"
SERVICE_DESCRIPTION = "Processa backtests na fila do Supabase usando MetaTrader 5."


def _get_python_exe() -> str:
    """Retorna o executavel Python real (nao pythonservice.exe)."""
    exe = sys.executable
    # Quando rodando sob SCM, sys.executable aponta para pythonservice.exe
    # Precisamos do python.exe real na mesma pasta
    if os.path.basename(exe).lower() == "pythonservice.exe":
        exe = os.path.join(os.path.dirname(exe), "python.exe")
    return exe


def _get_worker_script() -> str:
    return os.path.join(_SCRIPT_DIR, "worker.py")


try:
    import win32service
    import win32serviceutil
    import win32event
    import servicemanager

    class BackTestProService(win32serviceutil.ServiceFramework):
        _svc_name_ = SERVICE_NAME
        _svc_display_name_ = SERVICE_DISPLAY
        _svc_description_ = SERVICE_DESCRIPTION

        def __init__(self, args):
            win32serviceutil.ServiceFramework.__init__(self, args)
            self._stop_event = win32event.CreateEvent(None, 0, 0, None)
            self._process = None

        def SvcStop(self):
            logger.info("Sinal de parada recebido pelo SCM.")
            self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
            win32event.SetEvent(self._stop_event)
            if self._process and self._process.poll() is None:
                self._process.terminate()
                try:
                    self._process.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    self._process.kill()
                logger.info("Processo worker encerrado.")

        def SvcDoRun(self):
            servicemanager.LogMsg(
                servicemanager.EVENTLOG_INFORMATION_TYPE,
                servicemanager.PYS_SERVICE_STARTED,
                (self._svc_name_, ""),
            )
            logger.info(f"Servico {SERVICE_NAME} iniciado.")
            self._run_worker()
            logger.info(f"Servico {SERVICE_NAME} encerrado.")

        def _run_worker(self):
            python_exe = _get_python_exe()
            worker_script = _get_worker_script()

            while True:
                # Verifica se recebeu sinal de parada
                if win32event.WaitForSingleObject(self._stop_event, 0) == win32event.WAIT_OBJECT_0:
                    break

                logger.info(f"Iniciando worker: {python_exe} {worker_script}")
                try:
                    self._process = subprocess.Popen(
                        [python_exe, worker_script],
                        cwd=_SCRIPT_DIR,
                        stdout=open(os.path.join(_LOGS_DIR, "worker_stdout.log"), "a", encoding="utf-8"),
                        stderr=open(os.path.join(_LOGS_DIR, "worker_stderr.log"), "a", encoding="utf-8"),
                        creationflags=subprocess.CREATE_NO_WINDOW,
                    )
                except Exception as e:
                    logger.error(f"Falha ao iniciar worker: {e}")
                    # Aguarda 30s antes de tentar novamente
                    if win32event.WaitForSingleObject(self._stop_event, 30000) == win32event.WAIT_OBJECT_0:
                        break
                    continue

                # Aguarda o processo terminar ou receber sinal de parada
                while True:
                    if win32event.WaitForSingleObject(self._stop_event, 1000) == win32event.WAIT_OBJECT_0:
                        # Parada solicitada
                        if self._process.poll() is None:
                            self._process.terminate()
                            try:
                                self._process.wait(timeout=15)
                            except subprocess.TimeoutExpired:
                                self._process.kill()
                        return

                    if self._process.poll() is not None:
                        exit_code = self._process.returncode
                        logger.warning(f"Worker encerrou com codigo {exit_code}. Reiniciando em 10s...")
                        # Aguarda 10s com check de parada
                        if win32event.WaitForSingleObject(self._stop_event, 10000) == win32event.WAIT_OBJECT_0:
                            return
                        break  # Sai do loop interno para reiniciar o processo

    _PYWIN32_AVAILABLE = True

except ImportError:
    _PYWIN32_AVAILABLE = False


# ============================================================================
# COMANDOS DE GERENCIAMENTO
# ============================================================================

def _require_pywin32():
    if not _PYWIN32_AVAILABLE:
        print("ERRO: pywin32 nao instalado.")
        print("Execute: pip install pywin32")
        print("Depois execute: python -m pywin32_postinstall -install")
        sys.exit(1)


def _scm_command(*args):
    """Executa um comando via HandleCommandLine do pywin32."""
    _require_pywin32()
    old_argv = sys.argv[:]
    sys.argv = [sys.argv[0]] + list(args)
    try:
        win32serviceutil.HandleCommandLine(BackTestProService)
    finally:
        sys.argv = old_argv


def cmd_install():
    _scm_command("--startup=auto", "install")
    # Configura reinicio automatico em caso de falha (3 tentativas, 60s entre elas)
    try:
        hscm = win32service.OpenSCManager(None, None, win32service.SC_MANAGER_ALL_ACCESS)
        hs = win32service.OpenService(hscm, SERVICE_NAME, win32service.SERVICE_ALL_ACCESS)
        win32service.ChangeServiceConfig2(
            hs,
            win32service.SERVICE_CONFIG_FAILURE_ACTIONS,
            {
                "ResetPeriod": 86400,
                "RebootMsg": "",
                "Command": "",
                "Actions": [
                    (win32service.SC_ACTION_RESTART, 60000),
                    (win32service.SC_ACTION_RESTART, 60000),
                    (win32service.SC_ACTION_RESTART, 60000),
                ],
            },
        )
        win32service.CloseServiceHandle(hs)
        win32service.CloseServiceHandle(hscm)
        print("Acoes de reinicio automatico configuradas (3x, 60s entre tentativas).")
    except Exception as e:
        logger.warning(f"Nao foi possivel configurar acoes de falha: {e}")

    print("Para iniciar: python worker_service.py start")


def cmd_remove():
    _require_pywin32()
    try:
        win32serviceutil.StopService(SERVICE_NAME)
    except Exception:
        pass
    win32serviceutil.RemoveService(SERVICE_NAME)
    print(f"Servico '{SERVICE_DISPLAY}' removido.")


def cmd_start():
    _require_pywin32()
    win32serviceutil.StartService(SERVICE_NAME)
    print(f"Servico '{SERVICE_DISPLAY}' iniciado.")


def cmd_stop():
    _require_pywin32()
    win32serviceutil.StopService(SERVICE_NAME)
    print(f"Servico '{SERVICE_DISPLAY}' parado.")


def cmd_restart():
    _require_pywin32()
    win32serviceutil.RestartService(SERVICE_NAME)
    print(f"Servico '{SERVICE_DISPLAY}' reiniciado.")


def cmd_status():
    _require_pywin32()
    try:
        status = win32serviceutil.QueryServiceStatus(SERVICE_NAME)
        states = {
            1: "STOPPED",
            2: "START_PENDING",
            3: "STOP_PENDING",
            4: "RUNNING",
            5: "CONTINUE_PENDING",
            6: "PAUSE_PENDING",
            7: "PAUSED",
        }
        state_str = states.get(status[1], f"UNKNOWN({status[1]})")
        print(f"Servico '{SERVICE_DISPLAY}': {state_str}")
    except Exception as e:
        print(f"Nao foi possivel obter status: {e}")


def cmd_debug():
    """Roda o worker em modo debug (foreground, sem SCM)."""
    python_exe = _get_python_exe()
    worker_script = _get_worker_script()
    print(f"Modo debug: executando {worker_script}")
    print("Pressione Ctrl+C para encerrar.")
    try:
        subprocess.run([python_exe, worker_script], cwd=_SCRIPT_DIR)
    except KeyboardInterrupt:
        print("Encerrado pelo usuario.")


# ============================================================================
# ENTRY POINT
# ============================================================================

_COMMANDS = {
    "install": cmd_install,
    "remove": cmd_remove,
    "start": cmd_start,
    "stop": cmd_stop,
    "restart": cmd_restart,
    "status": cmd_status,
    "debug": cmd_debug,
}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        print("Uso: python worker_service.py <comando>")
        print("Comandos:", ", ".join(_COMMANDS))
        sys.exit(0)

    cmd = sys.argv[1].lower()

    if cmd in _COMMANDS:
        _COMMANDS[cmd]()
    else:
        # Delega para win32serviceutil (handles 'install', 'start', etc. via SCM internamente)
        _require_pywin32()
        win32serviceutil.HandleCommandLine(BackTestProService)

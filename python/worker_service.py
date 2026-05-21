"""
BacktestPro - Gerenciador do Worker

Gerencia o worker.py via Task Scheduler do Windows (schtasks).
Roda na sessao do usuario logado, permitindo que o MT5 (processo GUI)
seja iniciado normalmente mesmo com RDP desconectado.

Uso:
    python worker_service.py install    # cria a task e inicia
    python worker_service.py start      # inicia a task
    python worker_service.py stop       # para a task
    python worker_service.py restart    # reinicia a task
    python worker_service.py remove     # remove a task
    python worker_service.py status     # exibe status atual
    python worker_service.py debug      # roda em foreground (sem task)

A task e configurada para:
- Iniciar automaticamente no logon do usuario
- Reiniciar a cada 1 minuto se o worker encerrar (ate 3 tentativas)
- Rodar na sessao interativa (acesso ao desktop, necessario para o MT5)
"""

import logging
import logging.handlers
import os
import subprocess
import sys
import time

# ============================================================================
# LOGGING
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
        maxBytes=5 * 1024 * 1024,  # 5 MB por arquivo
        backupCount=5,              # 5 backups = maximo 25 MB total
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
# CONFIGURACAO
# ============================================================================

TASK_NAME = "BackTestProWorker"
_WORKER_SCRIPT = os.path.join(_SCRIPT_DIR, "worker.py")

# pythonw.exe roda sem janela de console — mesmo diretorio que python.exe
_PYTHON_EXE = os.path.join(
    os.path.dirname(sys.executable),
    "pythonw.exe",
)
if not os.path.exists(_PYTHON_EXE):
    _PYTHON_EXE = sys.executable  # fallback para python.exe se nao encontrar


def _run(args, check=True) -> subprocess.CompletedProcess:
    return subprocess.run(
        args,
        capture_output=True,
        text=True,
        check=check,
    )


# ============================================================================
# COMANDOS
# ============================================================================

def cmd_install():
    """Cria a task no Task Scheduler e inicia imediatamente."""
    python = _PYTHON_EXE
    script = _WORKER_SCRIPT

    # XML com InteractiveToken para rodar na sessao do usuario (necessario para MT5)
    xml = f"""<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>Processa backtests na fila do Supabase usando MetaTrader 5.</Description>
  </RegistrationInfo>
  <Triggers>
    <LogonTrigger>
      <Enabled>true</Enabled>
    </LogonTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <LogonType>S4U</LogonType>
      <RunLevel>HighestAvailable</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>
    <RestartOnFailure>
      <Interval>PT1M</Interval>
      <Count>3</Count>
    </RestartOnFailure>
    <IdleSettings>
      <StopOnIdleEnd>false</StopOnIdleEnd>
      <RestartOnIdle>false</RestartOnIdle>
    </IdleSettings>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
  </Settings>
  <Actions>
    <Exec>
      <Command>{python}</Command>
      <Arguments>"{script}"</Arguments>
      <WorkingDirectory>{_SCRIPT_DIR}</WorkingDirectory>
    </Exec>
  </Actions>
</Task>"""

    xml_path = os.path.join(_LOGS_DIR, "_task_def.xml")
    with open(xml_path, "w", encoding="utf-16") as f:
        f.write(xml)

    # Remove task anterior se existir
    _run(["schtasks", "/delete", "/tn", TASK_NAME, "/f"], check=False)

    result = _run(["schtasks", "/create", "/tn", TASK_NAME, "/xml", xml_path])
    if result.returncode != 0:
        print(f"ERRO ao criar task:\n{result.stderr}")
        sys.exit(1)

    print(f"Task '{TASK_NAME}' criada com sucesso.")
    print("Iniciando...")
    cmd_start()


def cmd_start():
    result = _run(["schtasks", "/run", "/tn", TASK_NAME], check=False)
    if result.returncode != 0:
        print(f"ERRO ao iniciar task:\n{result.stderr}")
        sys.exit(1)
    print(f"Task '{TASK_NAME}' iniciada.")


def cmd_stop():
    result = _run(["schtasks", "/end", "/tn", TASK_NAME], check=False)
    if result.returncode != 0:
        print(f"ERRO ao parar task:\n{result.stderr}")
        sys.exit(1)
    print(f"Task '{TASK_NAME}' parada.")


def cmd_restart():
    cmd_stop()
    time.sleep(2)
    cmd_start()


def cmd_remove():
    _run(["schtasks", "/end", "/tn", TASK_NAME], check=False)
    result = _run(["schtasks", "/delete", "/tn", TASK_NAME, "/f"], check=False)
    if result.returncode != 0:
        print(f"ERRO ao remover task:\n{result.stderr}")
        sys.exit(1)
    print(f"Task '{TASK_NAME}' removida.")


def cmd_status():
    result = _run(
        ["schtasks", "/query", "/tn", TASK_NAME, "/fo", "LIST"],
        check=False,
    )
    if result.returncode != 0:
        print(f"Task '{TASK_NAME}' nao encontrada.")
        return
    for line in result.stdout.splitlines():
        key = line.split(":")[0].strip().lower()
        if key in ("status", "nome da tarefa", "task name", "proximo tempo de execucao",
                   "next run time", "ultimo resultado", "last result"):
            print(line.strip())


def cmd_debug():
    """Roda o worker em foreground (sem task scheduler)."""
    print(f"Modo debug: executando {_WORKER_SCRIPT}")
    print("Pressione Ctrl+C para encerrar.")
    try:
        subprocess.run([_PYTHON_EXE, _WORKER_SCRIPT], cwd=_SCRIPT_DIR)
    except KeyboardInterrupt:
        print("Encerrado pelo usuario.")


# ============================================================================
# ENTRY POINT
# ============================================================================

_COMMANDS = {
    "install": cmd_install,
    "start": cmd_start,
    "stop": cmd_stop,
    "restart": cmd_restart,
    "remove": cmd_remove,
    "status": cmd_status,
    "debug": cmd_debug,
}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1].lower() not in _COMMANDS:
        print(__doc__)
        print("Uso: python worker_service.py <comando>")
        print("Comandos:", ", ".join(_COMMANDS))
        sys.exit(0)

    _COMMANDS[sys.argv[1].lower()]()

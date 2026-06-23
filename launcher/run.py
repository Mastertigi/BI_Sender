"""BI Notify — launcher único ("rode tudo").

Sobe toda a stack via Docker Compose (Postgres, Redis, API, worker Celery e
frontend), aplica as migrations, abre o painel no navegador e acompanha os logs.
Empacotável como BI_Notify.exe (ver build_exe.bat). Usa apenas a biblioteca
padrão — o .exe gerado fica pequeno e sem dependências.

Fechar a janela / Ctrl+C derruba a stack (docker compose down).
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path

API_HEALTH = "http://localhost:8000/health"
FRONTEND_URL = "http://localhost:5173"
HEALTH_TIMEOUT = 180  # segundos


def project_root() -> Path:
    """Raiz do projeto (onde está docker-compose.yml).

    Funciona tanto rodando como script quanto como .exe (PyInstaller).
    Procura o docker-compose.yml subindo a partir da localização do binário.
    """
    base = Path(sys.executable if getattr(sys, "frozen", False) else __file__).resolve()
    for parent in [base.parent, *base.parents]:
        if (parent / "docker-compose.yml").exists():
            return parent
    # fallback: pasta acima de launcher/
    return base.parent.parent


def log(msg: str, kind: str = "•") -> None:
    print(f"[{kind}] {msg}", flush=True)


def check_docker() -> bool:
    if shutil.which("docker") is None:
        log("Docker não encontrado no PATH. Instale o Docker Desktop.", "X")
        return False
    try:
        subprocess.run(
            ["docker", "info"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except (subprocess.CalledProcessError, OSError):
        log("Docker Desktop não está em execução. Abra-o e tente de novo.", "X")
        return False
    return True


def ensure_env(root: Path) -> None:
    env = root / ".env"
    example = root / ".env.example"
    if not env.exists() and example.exists():
        shutil.copyfile(example, env)
        log(".env criado a partir de .env.example.", "!")
        log("Edite o .env com as credenciais reais do Service Principal "
            "antes de disparar relatórios.", "!")


def compose(root: Path, *args: str, **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(["docker", "compose", *args], cwd=root, **kwargs)


def wait_health() -> bool:
    log(f"Aguardando a API ficar saudável ({API_HEALTH}) …")
    deadline = time.time() + HEALTH_TIMEOUT
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(API_HEALTH, timeout=3) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            pass
        time.sleep(3)
    return False


def main() -> int:
    root = project_root()
    log(f"Projeto: {root}")

    if not check_docker():
        input("\nPressione Enter para sair…")
        return 1

    ensure_env(root)

    log("Subindo os serviços (docker compose up --build) … pode demorar no 1º run.")
    up = compose(root, "up", "--build", "-d")
    if up.returncode != 0:
        log("Falha ao subir os containers.", "X")
        input("\nPressione Enter para sair…")
        return up.returncode

    if not wait_health():
        log("A API não respondeu a tempo. Veja os logs abaixo.", "X")
        compose(root, "logs", "--tail", "50")
        input("\nPressione Enter para sair…")
        return 1
    log("API saudável.", "✓")

    log("Aplicando migrations (alembic upgrade head) …")
    compose(root, "exec", "-T", "api", "alembic", "upgrade", "head")

    log(f"Abrindo o painel em {FRONTEND_URL}", "✓")
    webbrowser.open(FRONTEND_URL)

    print("\n" + "=" * 60)
    log("BI Notify no ar:")
    log(f"  Painel:   {FRONTEND_URL}")
    log("  API/Docs: http://localhost:8000/docs")
    log("Pressione Ctrl+C para encerrar (derruba os containers).")
    print("=" * 60 + "\n")

    try:
        # Segue os logs em primeiro plano até Ctrl+C.
        compose(root, "logs", "-f")
    except KeyboardInterrupt:
        pass
    finally:
        log("Encerrando a stack (docker compose down) …")
        compose(root, "down")
        log("Encerrado.", "✓")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Ponto de entrada do CLI: ``sync`` (pré-carrega o cache) e ``dashboard``."""

import argparse
import logging
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

from novo_f1.services.repository import Repository
from novo_f1.services.sync import sync_season

DASHBOARD_APP = Path(__file__).parent / "dashboard" / "app.py"


def build_parser() -> argparse.ArgumentParser:
    """Cria o parser de argumentos do CLI."""
    parser = argparse.ArgumentParser(
        prog="novo_f1", description="Dashboard de dados históricos da OpenF1."
    )
    subcommands = parser.add_subparsers(dest="command", required=True)

    sync = subcommands.add_parser("sync", help="Pré-carrega o cache em Parquet.")
    sync.add_argument("--year", type=int, required=True, help="Temporada (>=2023).")
    sync.add_argument(
        "--session-key", type=int, default=None, help="Sincroniza só esta sessão."
    )

    subcommands.add_parser("dashboard", help="Sobe o dashboard Streamlit.")
    return parser


def run_sync(year: int, session_key: int | None) -> int:
    """Executa o sync e imprime o resumo. Retorna o código de saída."""
    repository = Repository.from_settings()
    try:
        report = sync_season(repository, year, session_key)
    finally:
        repository.client.close()
    print(f"Sessões sincronizadas: {len(report.sessions)}")
    for endpoint, rows in sorted(report.rows.items()):
        print(f"  {endpoint}: {rows} linhas")
    print(f"Requisições HTTP: {repository.client.request_count}")
    for error in report.errors:
        print(f"  ERRO {error}", file=sys.stderr)
    return 1 if report.errors else 0


def run_dashboard() -> int:
    """Sobe o Streamlit com o app do dashboard."""
    command = [sys.executable, "-m", "streamlit", "run", str(DASHBOARD_APP)]
    return subprocess.call(command)


def main(argv: Sequence[str] | None = None) -> int:
    """Executa o CLI.

    Args:
        argv: Argumentos (padrão: ``sys.argv[1:]``).

    Returns:
        Código de saída do processo.
    """
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = build_parser().parse_args(argv)
    if args.command == "sync":
        return run_sync(args.year, args.session_key)
    return run_dashboard()


if __name__ == "__main__":
    raise SystemExit(main())

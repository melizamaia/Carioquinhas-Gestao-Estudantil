"""Conexão com o banco DuckDB de build (compartilhado entre as etapas do ETL).

O arquivo build/vagaviva.duckdb não é versionado (é reconstruído do zero pelos
scripts, a partir das bases brutas). Cada etapa acrescenta/atualiza tabelas nele:
score → fila → funil → agregados finais.
"""

from __future__ import annotations

import duckdb

import config as cfg

BUILD_DIR = cfg.PROJECT_DIR / "build"
DB_PATH = BUILD_DIR / "vagaviva.duckdb"


def connect() -> duckdb.DuckDBPyConnection:
    BUILD_DIR.mkdir(exist_ok=True)
    return duckdb.connect(str(DB_PATH))

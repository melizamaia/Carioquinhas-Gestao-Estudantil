"""Fixtures compartilhadas dos testes do ETL Vaga Viva."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import duckdb
import pytest

PROJECT_DIR = Path(__file__).resolve().parent.parent
ETL_DIR = PROJECT_DIR / "etl"
DATA_DIR = PROJECT_DIR / "data"
BUILD_DB = PROJECT_DIR / "build" / "vagaviva.duckdb"

# Permite importar config/db do pacote etl.
sys.path.insert(0, str(ETL_DIR))


def _load(nome: str) -> dict:
    return json.loads((DATA_DIR / nome).read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def painel() -> dict:
    return _load("painel.json")


@pytest.fixture(scope="session")
def fila_json() -> dict:
    return _load("fila.json")


@pytest.fixture(scope="session")
def fichas() -> dict:
    return _load("fichas_exemplo.json")


@pytest.fixture(scope="session")
def copy_json() -> dict:
    return _load("copy.json")


@pytest.fixture(scope="session")
def vagas() -> dict:
    return _load("vagas.json")


@pytest.fixture(scope="session")
def con():
    """Conexão read-only ao banco de build (tabelas score/fila/funil/...)."""
    if not BUILD_DB.exists():
        pytest.skip("build/vagaviva.duckdb ausente — rode etl/02..05 antes")
    c = duckdb.connect(str(BUILD_DB), read_only=True)
    yield c
    c.close()

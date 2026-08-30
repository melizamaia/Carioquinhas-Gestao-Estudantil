"""Caminhos e constantes compartilhadas pelo ETL do Vaga Viva.

As bases brutas NÃO ficam versionadas no repositório (são grandes e sensíveis).
Elas vivem em RAW_DIR, fora do projeto. Se rodar em outra máquina, ajuste
RAW_DIR via variável de ambiente VAGA_VIVA_RAW_DIR ou edite o default abaixo.

Os resultados agregados (poucos KB) vão para data/*.json, esses sim versionados,
prontos para serem consumidos pelo painel/ficha (Jinja2, HTML pré-renderizado).
"""

from __future__ import annotations

import os
from pathlib import Path

# Raiz do projeto (…/Carioquinhas-Gestao-Estudantil-)
PROJECT_DIR = Path(__file__).resolve().parent.parent

# Diretório das bases brutas (fora do repo). Sobrescrevível por env var.
RAW_DIR = Path(
    os.environ.get("VAGA_VIVA_RAW_DIR", "/home/mmaia/dadoscreche")
).resolve()

BASES_IC_DIR = RAW_DIR / "Bases IC_ ClassificadoseFila"
OFERECIMENTOS_DIR = RAW_DIR / "OferecimentosEvagas"

# Saídas agregadas, versionadas
DATA_DIR = PROJECT_DIR / "data"

# --- Arquivos brutos -------------------------------------------------------
# Nomes reais confirmados no dicionário de dados (README_dicionario_dados.md).
QUERY_A = BASES_IC_DIR / "01_QueryA_InscricoesPorAno.csv.gz"  # inscrições x opção
QUERY_B = BASES_IC_DIR / "02_QueryB_RespostasSocioEconomicas.csv.gz"  # respostas (4,3M)
QUERY_C = BASES_IC_DIR / "03_QueryC_PerguntasComDescricao.csv"  # catálogo + pontuação
QUERY_D = BASES_IC_DIR / "04_UnidadesEscolaresComEndereco.csv"  # unidades (SEM header)

# --- Constantes de negócio -------------------------------------------------
# Ano único de análise. A régua de pontuação mudou entre 2023 e 2024;
# nunca cruzar pontuação entre anos (dicionário Query C).
ANO_ALVO = 2025

# Valor gravado SEM cedilha e SEM til. Filtrar com acento retorna zero linhas.
SITUACAO_CANCELADO_CONFIRMACAO = "Cancelado na confirmacao"
SITUACAO_LISTA_ESPERA = "Lista de espera"
SITUACAO_CONFIRMADO = "Confirmado"

# opcao == 6 viola a regra de 5 opções (11 linhas) — descartar.
OPCAO_MAX_VALIDA = 5


def read_csv_gz_sql(path: Path, all_varchar: bool = False) -> str:
    """Trecho SQL DuckDB para ler um .csv.gz/.csv com delim=';' e UTF-8 (BOM ok)."""
    extra = ", all_varchar=true" if all_varchar else ""
    return (
        f"read_csv_auto('{path}', delim=';', header=true, "
        f"ignore_errors=false{extra})"
    )

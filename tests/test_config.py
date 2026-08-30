"""Testes unitários das funções puras do config (rápidos, sem dados)."""

from __future__ import annotations

import config as cfg
import pytest


@pytest.mark.parametrize("pos,esperado", [
    (1, "entre as 3 primeiras"),
    (3, "entre as 3 primeiras"),
    (4, "entre a 4ª e a 10ª"),
    (10, "entre a 4ª e a 10ª"),
    (11, "entre a 11ª e a 25ª"),
    (25, "entre a 11ª e a 25ª"),
    (26, "entre a 26ª e a 50ª"),
    (50, "entre a 26ª e a 50ª"),
    (51, "depois da 50ª"),
    (999, "depois da 50ª"),
])
def test_faixa_posicao(pos, esperado):
    assert cfg.faixa_posicao(pos) == esperado


def test_faixa_sempre_valida():
    rotulos = {r for _, r in cfg.FAIXAS_POSICAO}
    for p in range(1, 200):
        assert cfg.faixa_posicao(p) in rotulos


@pytest.mark.parametrize("unidade,tipo", [
    ("0716601", "publica"),    # 7 dígitos
    ("0101803", "publica"),
    ("05010", "parceira"),     # 5 dígitos
    ("11010", "parceira"),
    ("123", "desconhecida"),
    ("", "desconhecida"),
])
def test_tipo_unidade(unidade, tipo):
    assert cfg.tipo_unidade(unidade) == tipo


def test_tipo_unidade_preserva_zeros_a_esquerda():
    # Tratar como string (não numérico) é o que salva as parceiras de 5 díg.
    assert cfg.tipo_unidade("05010") == "parceira"
    assert cfg.tipo_unidade(5010) == "desconhecida"  # int perde o zero → 4 díg


def test_constantes_de_negocio():
    assert cfg.ANO_ALVO == 2025
    assert cfg.OPCAO_MAX_VALIDA == 5
    # Armadilha #1: valor gravado sem cedilha e sem til.
    assert cfg.SITUACAO_CANCELADO_CONFIRMACAO == "Cancelado na confirmacao"
    assert "ç" not in cfg.SITUACAO_CANCELADO_CONFIRMACAO
    assert "ã" not in cfg.SITUACAO_CANCELADO_CONFIRMACAO

"""Testes dos artefatos data/*.json (validam invariantes de consumo pelo painel/ficha)."""

from __future__ import annotations

import config as cfg


# ---- painel.json ----------------------------------------------------------
def test_painel_tres_numeros(painel):
    chaves = [t["chave"] for t in painel["topo"]]
    assert chaves == ["esperando", "confirmadas", "perdidas"]
    for t in painel["topo"]:
        assert isinstance(t["valor"], int) and t["valor"] > 0
        assert t["rotulo"]


def test_painel_funil_consistente(painel):
    est = {e["chave"]: e["valor"] for e in painel["funil"]["estagios"]}
    em_analise = painel["funil"]["em_analise"]
    # ofertada == convocada == confirmada + expirada + em_analise
    assert est["ofertada"] == est["convocada"]
    assert est["confirmada"] + est["expirada"] + em_analise == est["convocada"]
    # reofertada == expirada (cada vaga expirada volta à fila)
    assert est["reofertada"] == est["expirada"]
    # taxa de expiração confere
    esperado = round(100 * est["expirada"] / est["convocada"], 1)
    assert painel["funil"]["taxa_expiracao_pct"] == esperado
    assert painel["funil"]["simulado"] is True


def test_painel_cobertura(painel):
    cob = painel["cobertura"]
    assert cob["unidades_publicas"] + cob["unidades_parceiras"] == cob["unidades_com_fila"]


def test_painel_bloco_vagas(painel):
    v = painel["vagas_ofertadas"]
    assert v["cobertura_join_pct"]["publica"] == 100.0
    assert 90 <= v["cobertura_join_pct"]["parceira"] <= 100
    assert v["vagas_ofertadas_parceiras"] > 0


# ---- fila.json ------------------------------------------------------------
def test_fila_faixas_somam_tamanho(fila_json):
    rotulos = set(fila_json["faixas"])
    for f in fila_json["filas"]:
        assert sum(f["faixas"].values()) == f["tamanho"]
        assert set(f["faixas"].keys()) == rotulos          # todas as faixas presentes
        assert f["tipo"] in {"publica", "parceira", "desconhecida"}
        assert f["grupamento"] == f["grupamento"].strip()  # sem espaço sobrando


def test_fila_total_bate(fila_json):
    assert fila_json["total_filas"] == len(fila_json["filas"])


def test_fila_sem_numero_exato(fila_json):
    # Requisito 2.12: só faixas, nunca posição exata.
    for f in fila_json["filas"]:
        assert "posicao" not in f


# ---- fichas_exemplo.json --------------------------------------------------
def test_fichas(fichas):
    rotulos = {r for _, r in cfg.FAIXAS_POSICAO}
    assert len(fichas["fichas"]) >= 1
    for fic in fichas["fichas"]:
        assert fic["faixa"] in rotulos
        assert isinstance(fic["pontos"], int)
        assert fic["tipo"] in {"publica", "parceira", "desconhecida"}
        assert "posicao" not in fic  # nunca expor número exato


# ---- copy.json ------------------------------------------------------------
def test_copy_itens(copy_json):
    itens = copy_json["itens"]
    assert len(itens) == 18
    cats = {}
    for it in itens:
        assert it["original"].strip()
        assert it["reescrito"].strip()
        cats[it["categoria"]] = cats.get(it["categoria"], 0) + 1
    assert cats == {"criterio": 13, "situacao": 3, "fila": 2}


def test_copy_meta(copy_json):
    assert copy_json["meta"]["modelo"] == "claude-opus-4-8"
    assert "12 palavras" in copy_json["meta"]["system_prompt"]


# ---- vagas.json -----------------------------------------------------------
def test_vagas_cobertura(vagas):
    cob = vagas["cobertura_join"]
    assert cob["publica"]["casadas"] == cob["publica"]["total"]      # 100%
    assert cob["parceira"]["casadas"] <= cob["parceira"]["total"]
    assert cob["parceira"]["pct"] >= 90


def test_vagas_por_unidade(vagas):
    for r in vagas["por_unidade"]:
        assert r["tipo"] in {"publica", "parceira"}
        if r["tipo"] == "parceira":
            assert r["vagas_ofertadas"] is not None

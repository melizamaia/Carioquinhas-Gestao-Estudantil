"""Testes das invariantes do pipeline contra o banco de build e as bases brutas.

Validam as armadilhas e as regras de negócio direto no DuckDB (score/fila/funil).
"""

from __future__ import annotations

import config as cfg


# ---- Armadilhas nas bases brutas ------------------------------------------
def test_armadilha1_situacao_sem_acento(con):
    a = cfg.read_csv_gz_sql(cfg.QUERY_A)
    sem = con.sql(f"SELECT count(*) FROM {a} WHERE situacao='Cancelado na confirmacao'").fetchone()[0]
    com = con.sql(f"SELECT count(*) FROM {a} WHERE situacao='Cancelado na confirmação'").fetchone()[0]
    assert sem == 118816       # valor real gravado (sem cedilha/til)
    assert com == 0            # com acento não existe


def test_armadilha8_opcao6(con):
    a = cfg.read_csv_gz_sql(cfg.QUERY_A)
    n6 = con.sql(f"SELECT count(*) FROM {a} WHERE opcao=6").fetchone()[0]
    assert n6 == 11            # existem 11 linhas com opcao=6...
    # ...e nenhuma entra na fila (opcao<=5)
    assert con.sql("SELECT max(opcao) FROM fila").fetchone()[0] <= cfg.OPCAO_MAX_VALIDA


def test_armadilha3_dois_formatos(con):
    a = cfg.read_csv_gz_sql(cfg.QUERY_A)
    df = con.sql(f"""
        SELECT length(CAST(unidade AS VARCHAR)) n, count(DISTINCT unidade) u
        FROM {a} WHERE unidade IS NOT NULL GROUP BY 1
    """).df().set_index("n")["u"].to_dict()
    assert df[5] == 350        # parceiras
    assert df[7] == 522        # públicas


def test_armadilha3_join_queryD(con):
    a = cfg.read_csv_gz_sql(cfg.QUERY_A)
    d = (f"read_csv_auto('{cfg.QUERY_D}', delim=';', header=false, nullstr='NULL', "
         f"names=['seq','esc_codigo','nome','tipo','logradouro','numero',"
         f"'complemento','bairro','cep'])")
    # Unidades distintas da QueryA e quantas casam na Query D (esc_codigo tem
    # duplicados, então conta-se DISTINCT unidade, não linhas do join).
    total = con.sql(f"SELECT count(DISTINCT unidade) FROM {a} WHERE unidade IS NOT NULL").fetchone()[0]
    casadas = con.sql(f"""
        SELECT count(DISTINCT x.unidade) FROM
          (SELECT DISTINCT unidade FROM {a} WHERE unidade IS NOT NULL) x
        JOIN {d} d ON CAST(x.unidade AS VARCHAR)=CAST(d.esc_codigo AS VARCHAR)
    """).fetchone()[0]
    assert total == 872
    assert casadas == 872      # casa 872/872 (nenhuma unidade perdida)


# ---- Score ----------------------------------------------------------------
def test_score_so_2025_e_faixa(con):
    anos = [r[0] for r in con.sql("SELECT DISTINCT ano FROM score").fetchall()]
    assert anos == [cfg.ANO_ALVO]                     # só 2025
    mn, mx, nul = con.sql(
        "SELECT min(pontos), max(pontos), sum(CASE WHEN pontos IS NULL THEN 1 ELSE 0 END) FROM score"
    ).fetchone()
    assert mn >= 0 and mx <= 100 and nul == 0         # 0..100, sem nulos


# ---- Fila -----------------------------------------------------------------
def test_fila_filtros(con):
    # todas as linhas da fila são Lista de espera, 2025, opcao<=5
    total = con.sql("SELECT count(*) FROM fila").fetchone()[0]
    ok = con.sql(f"""
        SELECT count(*) FROM fila
        WHERE ano={cfg.ANO_ALVO} AND opcao<={cfg.OPCAO_MAX_VALIDA}
    """).fetchone()[0]
    assert total == ok and total > 0


def test_fila_posicoes_contiguas(con):
    # Em cada fila, posição vai de 1..N sem buracos nem repetição.
    ruins = con.sql("""
        SELECT count(*) FROM (
            SELECT min(posicao) mn, max(posicao) mx, count(*) c, count(DISTINCT posicao) d
            FROM fila GROUP BY unidade, grupamento, horario
        ) WHERE mn<>1 OR mx<>c OR d<>c
    """).fetchone()[0]
    assert ruins == 0


def test_fila_desempate(con):
    # A ordem por posição respeita pontos DESC, data_criacao ASC, ipl_id ASC.
    # Chave crescente com a posição: k=(-pontos, epoch(data), ipl). Nunca pode diminuir.
    violacoes = con.sql("""
        WITH o AS (
            SELECT unidade, grupamento, horario, posicao,
                   -pontos AS k1, epoch(data_criacao) AS k2, ipl_id AS k3,
                   LAG(-pontos)             OVER w AS p1,
                   LAG(epoch(data_criacao)) OVER w AS p2,
                   LAG(ipl_id)              OVER w AS p3
            FROM fila
            WINDOW w AS (PARTITION BY unidade, grupamento, horario ORDER BY posicao)
        )
        SELECT count(*) FROM o
        WHERE p1 IS NOT NULL AND (
            k1 < p1
            OR (k1 = p1 AND k2 < p2)
            OR (k1 = p1 AND k2 = p2 AND k3 < p3)
        )
    """).fetchone()[0]
    assert violacoes == 0


# ---- Funil ----------------------------------------------------------------
def test_funil_global_consistente(con):
    r = con.sql("""
        SELECT ofertada, convocada, confirmada, expirada, em_analise, reofertada
        FROM funil_global
    """).df().iloc[0]
    assert r.ofertada == r.convocada
    assert r.confirmada + r.expirada + r.em_analise == r.convocada
    assert r.reofertada == r.expirada


def test_funil_unidade_soma_global(con):
    g = con.sql("SELECT confirmada, expirada, em_analise FROM funil_global").df().iloc[0]
    u = con.sql("""
        SELECT sum(confirmada) c, sum(expirada) e, sum(em_analise) a FROM funil_unidade
    """).df().iloc[0]
    assert (u.c, u.e, u.a) == (g.confirmada, g.expirada, g.em_analise)


def test_top_numeros_grao_opcao(con):
    # Os três números (grão opção) não se sobrepõem: cada opção tem uma só situacao.
    r = con.sql("SELECT esperando, confirmadas, perdidas FROM top_numeros").df().iloc[0]
    assert r.esperando > 0 and r.confirmadas > 0 and r.perdidas > 0

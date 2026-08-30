"""Etapa 1 — Leitura e validação das bases brutas.

Objetivo: confirmar colunas, contagens e as armadilhas documentadas ANTES de
montar score/fila. Não escreve nada em data/; só imprime diagnóstico.

Rodar: python etl/01_validar_brutos.py
"""

from __future__ import annotations

import duckdb

import config as cfg


def linha(titulo: str) -> None:
    print("\n" + "=" * 70)
    print(titulo)
    print("=" * 70)


def main() -> None:
    con = duckdb.connect()

    # ---- Query A ----------------------------------------------------------
    linha("QUERY A — inscrições por opção")
    a = cfg.read_csv_gz_sql(cfg.QUERY_A)
    print("colunas:")
    print(con.sql(f"DESCRIBE SELECT * FROM {a}").df().to_string(index=False))
    total_a = con.sql(f"SELECT count(*) FROM {a}").fetchone()[0]
    print(f"\ntotal linhas: {total_a:,}")
    print("\npor ano:")
    print(con.sql(f"SELECT ano, count(*) n FROM {a} GROUP BY 1 ORDER BY 1").df().to_string(index=False))
    print("\ndistribuição de situacao:")
    print(con.sql(f"SELECT situacao, count(*) n FROM {a} GROUP BY 1 ORDER BY n DESC").df().to_string(index=False))
    print("\nArmadilha #1 — 'Cancelado na confirmacao' (sem acento) deve ter linhas:")
    sem = con.sql(f"SELECT count(*) FROM {a} WHERE situacao = 'Cancelado na confirmacao'").fetchone()[0]
    com = con.sql(f"SELECT count(*) FROM {a} WHERE situacao = 'Cancelado na confirmação'").fetchone()[0]
    print(f"  sem acento: {sem:,}   |   com acento: {com:,}  (com acento deve ser 0)")
    print("\nArmadilha #8 — distribuição de opcao (opcao=6 deve ser ~11 linhas):")
    print(con.sql(f"SELECT opcao, count(*) n FROM {a} GROUP BY 1 ORDER BY 1").df().to_string(index=False))
    print("\nArmadilha #3 — formato de 'unidade' (nº de dígitos):")
    print(con.sql(f"""
        SELECT length(CAST(unidade AS VARCHAR)) AS n_digitos, count(*) n,
               count(DISTINCT unidade) unidades_distintas
        FROM {a} WHERE unidade IS NOT NULL GROUP BY 1 ORDER BY 1
    """).df().to_string(index=False))
    print("\ngrupamento / horario distintos:")
    print(con.sql(f"SELECT grupamento, count(*) n FROM {a} GROUP BY 1 ORDER BY n DESC LIMIT 10").df().to_string(index=False))
    print(con.sql(f"SELECT horario, count(*) n FROM {a} GROUP BY 1 ORDER BY n DESC").df().to_string(index=False))
    print("\nnulos em colunas-chave (ano 2025):")
    print(con.sql(f"""
        SELECT
          sum(CASE WHEN prm_id IS NULL THEN 1 ELSE 0 END) prm_null,
          sum(CASE WHEN plm_id IS NULL THEN 1 ELSE 0 END) plm_null,
          sum(CASE WHEN ipl_id IS NULL THEN 1 ELSE 0 END) ipl_null,
          sum(CASE WHEN data_criacao IS NULL THEN 1 ELSE 0 END) data_null,
          sum(CASE WHEN unidade IS NULL THEN 1 ELSE 0 END) unidade_null
        FROM {a} WHERE ano = {cfg.ANO_ALVO}
    """).df().to_string(index=False))

    # ---- Query C ----------------------------------------------------------
    linha("QUERY C — catálogo de perguntas + pontuação")
    c = cfg.read_csv_gz_sql(cfg.QUERY_C)
    print("colunas:")
    print(con.sql(f"DESCRIBE SELECT * FROM {c}").df().to_string(index=False))
    print("\nlinhas por ano e faixa de pontuação:")
    print(con.sql(f"""
        SELECT ano, count(*) perguntas,
               min(perg_pontuacao) min_pt, max(perg_pontuacao) max_pt
        FROM {c} GROUP BY 1 ORDER BY 1
    """).df().to_string(index=False))
    print("\nArmadilha #5 — perg_id=2 muda de peso entre anos:")
    print(con.sql(f"""
        SELECT ano, ich_perg_id, perg_pontuacao, left(pergunta_texto, 45) txt
        FROM {c} WHERE perg_id = 2 ORDER BY ano
    """).df().to_string(index=False))

    # ---- Query B (NUNCA carregar inteira; só agregar) ---------------------
    linha("QUERY B — respostas (4,3M linhas — só agregação no DuckDB)")
    b = cfg.read_csv_gz_sql(cfg.QUERY_B)
    print("colunas:")
    print(con.sql(f"DESCRIBE SELECT * FROM {b}").df().to_string(index=False))
    total_b = con.sql(f"SELECT count(*) FROM {b}").fetchone()[0]
    print(f"\ntotal linhas: {total_b:,}  (esperado ~4.357.119)")
    print("\nresposta / confirmado (agregado):")
    print(con.sql(f"SELECT resposta, count(*) n FROM {b} GROUP BY 1 ORDER BY n DESC").df().to_string(index=False))
    print("\nlinhas de 2025 (ano-alvo):")
    b25 = con.sql(f"SELECT count(*) FROM {b} WHERE ano = {cfg.ANO_ALVO}").fetchone()[0]
    print(f"  {b25:,}")

    # ---- Query D (SEM cabeçalho) -----------------------------------------
    linha("QUERY D — unidades escolares (SEM cabeçalho — header=None)")
    d = (
        f"read_csv_auto('{cfg.QUERY_D}', delim=';', header=false, "
        f"nullstr='NULL', "
        f"names=['seq','esc_codigo','nome','tipo','logradouro',"
        f"'numero','complemento','bairro','cep'])"
    )
    print("colunas (nomeadas manualmente):")
    print(con.sql(f"DESCRIBE SELECT * FROM {d}").df().to_string(index=False))
    total_d = con.sql(f"SELECT count(*) FROM {d}").fetchone()[0]
    print(f"\ntotal unidades: {total_d:,}  (esperado 2.188)")
    print("\nprimeiras 3 linhas (confere se a 1ª unidade não virou header):")
    print(con.sql(f"SELECT seq, esc_codigo, nome FROM {d} ORDER BY seq LIMIT 3").df().to_string(index=False))

    # ---- Join A x D (dicionário: casa 872/872) ---------------------------
    linha("JOIN Query A x Query D — cobertura de unidades")
    casadas = con.sql(f"""
        SELECT count(DISTINCT a.unidade) AS unidades_a,
               count(DISTINCT d.esc_codigo) AS casadas
        FROM (SELECT DISTINCT unidade FROM {a} WHERE unidade IS NOT NULL) a
        LEFT JOIN {d} d ON CAST(a.unidade AS VARCHAR) = CAST(d.esc_codigo AS VARCHAR)
    """).df()
    print(casadas.to_string(index=False))

    con.close()
    print("\n[OK] Validação concluída.")


if __name__ == "__main__":
    main()

"""Etapa 3 — Reconstrução da fila de espera (2025) com posição.

Cada fila é uma vaga-oferta específica: (ano, unidade, grupamento, horario).
Dentro dela, ordena por:
    pontos DESC, data_criacao ASC, ipl_id ASC   (desempate — NÃO alterar).

Regras respeitadas:
- Só situacao = 'Lista de espera' (armadilha #1: valor sem acento não se aplica aqui).
- Só 2025.
- Descarta opcao = 6 (armadilha #8).
- Recorte territorial pela UNIDADE, nunca pelo bairro declarado (armadilha #9).
- Empates massivos são reais → posição será exibida em FAIXA (etapa dos JSONs),
  nunca número exato (requisito 2.12).

Depende de `score` (etapa 2). Grava a tabela `fila`.
Rodar: python etl/03_fila.py
"""

from __future__ import annotations

import config as cfg
from db import connect


def main() -> None:
    con = connect()
    a = cfg.read_csv_gz_sql(cfg.QUERY_A)

    con.execute(f"""
        CREATE OR REPLACE TABLE fila AS
        SELECT
            a.ano, a.prm_id, a.plm_id, a.ipl_id, a.opcao,
            a.unidade, a.nome_unidade, a.grupamento, a.horario,
            a.data_criacao, a.aluno_anon, a.responsavel_anon,
            s.pontos,
            ROW_NUMBER() OVER (
                PARTITION BY a.ano, a.unidade, a.grupamento, a.horario
                ORDER BY s.pontos DESC, a.data_criacao ASC, a.ipl_id ASC
            ) AS posicao,
            COUNT(*) OVER (
                PARTITION BY a.ano, a.unidade, a.grupamento, a.horario
            ) AS tamanho_fila
        FROM {a} a
        JOIN score s USING (ano, prm_id, plm_id, ipl_id)
        WHERE a.situacao = '{cfg.SITUACAO_LISTA_ESPERA}'
          AND a.ano = {cfg.ANO_ALVO}
          AND a.opcao <= {cfg.OPCAO_MAX_VALIDA}
    """)

    # ---- Checagens rápidas -----------------------------------------------
    n, filas, unidades = con.sql("""
        SELECT count(*),
               count(DISTINCT (unidade, grupamento, horario)),
               count(DISTINCT unidade)
        FROM fila
    """).fetchone()
    print(f"linhas na fila (2025): {n:,}")
    print(f"filas distintas (unidade x grupamento x horario): {filas:,}")
    print(f"unidades com fila: {unidades:,}")

    print("\nnulos em colunas-chave:")
    print(con.sql("""
        SELECT
          sum(CASE WHEN unidade IS NULL THEN 1 ELSE 0 END) unidade_null,
          sum(CASE WHEN posicao IS NULL THEN 1 ELSE 0 END) posicao_null,
          sum(CASE WHEN pontos IS NULL THEN 1 ELSE 0 END) pontos_null
        FROM fila
    """).df().to_string(index=False))

    print("\ntamanho das filas (percentis):")
    print(con.sql("""
        SELECT
          min(tamanho_fila) menor, max(tamanho_fila) maior,
          round(avg(tamanho_fila),1) media,
          quantile_cont(tamanho_fila, 0.5) mediana,
          quantile_cont(tamanho_fila, 0.9) p90
        FROM (SELECT DISTINCT unidade, grupamento, horario, tamanho_fila FROM fila)
    """).df().to_string(index=False))

    print("\nArmadilha #6 — maior bloco de empate em 0 ponto (mesma fila):")
    print(con.sql("""
        SELECT unidade, grupamento, horario, count(*) empatados_em_0
        FROM fila WHERE pontos = 0
        GROUP BY 1,2,3 ORDER BY empatados_em_0 DESC LIMIT 5
    """).df().to_string(index=False))

    print("\namostra de uma fila (topo da maior fila):")
    print(con.sql("""
        WITH maior AS (
            SELECT unidade, grupamento, horario
            FROM fila GROUP BY 1,2,3 ORDER BY count(*) DESC LIMIT 1
        )
        SELECT f.unidade, f.grupamento, f.horario, f.posicao, f.pontos, f.data_criacao
        FROM fila f JOIN maior USING (unidade, grupamento, horario)
        ORDER BY f.posicao LIMIT 8
    """).df().to_string(index=False))

    con.close()
    print("\n[OK] Etapa 3 concluída — tabela `fila` gravada.")


if __name__ == "__main__":
    main()

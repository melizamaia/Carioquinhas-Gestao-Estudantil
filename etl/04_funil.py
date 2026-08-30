"""Etapa 4 — Funil de convocação e os três números do topo (2025).

IMPORTANTE — FUNIL SIMULADO. A base não tem timestamp real de convocação/
expiração. O funil é reconstruído a partir do ESTADO FINAL de cada opção
(coluna `situacao` da Query A), não de eventos datados. Ver README.

Mapeamento de `situacao` (2025, opcao<=5) → estágio do funil de vaga:
    confirmada  : Confirmado, Ativo
    expirada    : Cancelado na confirmacao   (chamada, não confirmou)
    em_analise  : Selecionado, Selecionado da lista  (chamada, decisão pendente)
    ----------------------------------------------------------------
    convocada   = confirmada + expirada + em_analise
    ofertada    = convocada  (sem sinal separado no estado final)
    reofertada  = expirada   (cada vaga expirada volta para a fila)

Fora do funil de vaga (cancelamentos, não convocações):
    Lista de espera, Cancelado, Cancelado pelo sistema

Os TRÊS NÚMEROS DO TOPO (requisito 1.4) são reportados em grão de FAMÍLIA
(inscrições distintas), apples-to-apples:
    esperando   : famílias em 'Lista de espera'
    confirmadas : famílias com 'Confirmado'
    perdidas    : famílias com 'Cancelado na confirmacao'

Grava tabelas `funil_global`, `funil_unidade`, `top_numeros`.
Rodar: python etl/04_funil.py
"""

from __future__ import annotations

import config as cfg
from db import connect

# CASE reutilizável: situacao -> estágio do funil de vaga (ou NULL se fora dele).
BUCKET_SQL = f"""
    CASE
      WHEN situacao IN ('{cfg.SITUACAO_CONFIRMADO}', 'Ativo') THEN 'confirmada'
      WHEN situacao = '{cfg.SITUACAO_CANCELADO_CONFIRMACAO}'  THEN 'expirada'
      WHEN situacao IN ('Selecionado', 'Selecionado da lista') THEN 'em_analise'
      ELSE NULL
    END
"""


def main() -> None:
    con = connect()
    a = cfg.read_csv_gz_sql(cfg.QUERY_A)

    # Base 2025, grão opção, opcao<=5, com o bucket do funil já calculado.
    con.execute(f"""
        CREATE OR REPLACE TABLE base_funil AS
        SELECT ano, prm_id, plm_id, ipl_id, opcao,
               unidade, grupamento, horario, situacao,
               {BUCKET_SQL} AS estagio
        FROM {a}
        WHERE ano = {cfg.ANO_ALVO} AND opcao <= {cfg.OPCAO_MAX_VALIDA}
    """)

    # ---- Funil global -----------------------------------------------------
    con.execute("""
        CREATE OR REPLACE TABLE funil_global AS
        WITH c AS (
            SELECT
              sum(CASE WHEN estagio = 'confirmada' THEN 1 ELSE 0 END) AS confirmada,
              sum(CASE WHEN estagio = 'expirada'   THEN 1 ELSE 0 END) AS expirada,
              sum(CASE WHEN estagio = 'em_analise' THEN 1 ELSE 0 END) AS em_analise
            FROM base_funil
        )
        SELECT
            confirmada + expirada + em_analise AS ofertada,
            confirmada + expirada + em_analise AS convocada,
            confirmada, expirada, em_analise,
            expirada AS reofertada,
            round(100.0 * expirada / nullif(confirmada + expirada + em_analise, 0), 1)
                AS taxa_expiracao_pct
        FROM c
    """)
    print("FUNIL GLOBAL (vaga, 2025):")
    print(con.sql("SELECT * FROM funil_global").df().to_string(index=False))

    # ---- Funil por unidade (para o painel) --------------------------------
    con.execute("""
        CREATE OR REPLACE TABLE funil_unidade AS
        SELECT
            unidade,
            sum(CASE WHEN estagio = 'confirmada' THEN 1 ELSE 0 END) AS confirmada,
            sum(CASE WHEN estagio = 'expirada'   THEN 1 ELSE 0 END) AS expirada,
            sum(CASE WHEN estagio = 'em_analise' THEN 1 ELSE 0 END) AS em_analise,
            sum(CASE WHEN estagio IS NOT NULL    THEN 1 ELSE 0 END) AS convocada,
            sum(CASE WHEN estagio = 'expirada'   THEN 1 ELSE 0 END) AS reofertada
        FROM base_funil
        GROUP BY unidade
    """)
    nun = con.sql("SELECT count(*) FROM funil_unidade").fetchone()[0]
    print(f"\nfunil por unidade: {nun:,} unidades")
    print(con.sql("""
        SELECT unidade, convocada, confirmada, expirada
        FROM funil_unidade ORDER BY convocada DESC LIMIT 5
    """).df().to_string(index=False))

    # ---- Três números do topo (requisito 1.4) ----------------------------
    # Grão VAGA/opção (primário): cada opção tem uma única situacao, então os
    # três números não se sobrepõem e batem com o funil e com o README.
    # As versões distintas-por-família vão junto como campos secundários — no
    # grão família as categorias SE SOBREPÕEM (ex.: confirmou uma opção e
    # perdeu outra), por isso não somam e não servem de headline.
    con.execute(f"""
        CREATE OR REPLACE TABLE top_numeros AS
        SELECT
            -- primário (vaga/opção)
            sum(CASE WHEN situacao = '{cfg.SITUACAO_LISTA_ESPERA}' THEN 1 ELSE 0 END) AS esperando,
            sum(CASE WHEN situacao = '{cfg.SITUACAO_CONFIRMADO}' THEN 1 ELSE 0 END) AS confirmadas,
            sum(CASE WHEN situacao = '{cfg.SITUACAO_CANCELADO_CONFIRMACAO}' THEN 1 ELSE 0 END) AS perdidas,
            -- secundário (famílias distintas — informativo, com sobreposição)
            count(DISTINCT CASE WHEN situacao = '{cfg.SITUACAO_LISTA_ESPERA}'
                                THEN (prm_id, plm_id, ipl_id) END) AS familias_esperando,
            count(DISTINCT CASE WHEN situacao = '{cfg.SITUACAO_CONFIRMADO}'
                                THEN (prm_id, plm_id, ipl_id) END) AS familias_confirmadas,
            count(DISTINCT CASE WHEN situacao = '{cfg.SITUACAO_CANCELADO_CONFIRMACAO}'
                                THEN (prm_id, plm_id, ipl_id) END) AS familias_perdidas
        FROM base_funil
    """)
    print("\nTRÊS NÚMEROS DO TOPO (2025):")
    print(con.sql("SELECT esperando, confirmadas, perdidas FROM top_numeros").df().to_string(index=False))
    print("  (secundário) famílias distintas — sobrepõem, não somam:")
    print(con.sql("SELECT familias_esperando, familias_confirmadas, familias_perdidas FROM top_numeros").df().to_string(index=False))

    # ---- Checagem de consistência ----------------------------------------
    print("\nchecagem — soma dos estágios por unidade == funil global:")
    print(con.sql("""
        SELECT sum(confirmada) confirmada, sum(expirada) expirada,
               sum(em_analise) em_analise, sum(convocada) convocada
        FROM funil_unidade
    """).df().to_string(index=False))

    con.close()
    print("\n[OK] Etapa 4 concluída — funil_global, funil_unidade, top_numeros gravados.")


if __name__ == "__main__":
    main()

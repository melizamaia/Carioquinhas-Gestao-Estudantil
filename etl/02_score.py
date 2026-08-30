"""Etapa 2 — Pontuação (score) da classificação, ano-alvo 2025.

Para cada inscrição (ano, prm_id, plm_id, ipl_id) soma os pontos das perguntas
respondidas 'Sim', usando a régua de pontuação da Query C.

Regras respeitadas:
- Só 2025 (a régua mudou entre 2023 e 2024 — nunca cruzar pontuação entre anos).
- Junção Query B x Query C por (ano, ich_perg_id): ich_perg_id muda a cada ano.
- Query B tem 4,3M linhas — nunca sai do DuckDB; agrega direto no SQL.

Grava a tabela `score` no banco de build. Rodar: python etl/02_score.py
"""

from __future__ import annotations

import config as cfg
from db import connect


def main() -> None:
    con = connect()
    b = cfg.read_csv_gz_sql(cfg.QUERY_B)
    c = cfg.read_csv_gz_sql(cfg.QUERY_C)

    con.execute(f"""
        CREATE OR REPLACE TABLE score AS
        SELECT b.ano, b.prm_id, b.plm_id, b.ipl_id,
               SUM(CASE WHEN b.resposta = 'Sim' THEN c.perg_pontuacao ELSE 0 END) AS pontos
        FROM {b} b
        JOIN {c} c
          ON b.ano = c.ano AND b.ich_perg_id = c.ich_perg_id
        WHERE b.ano = {cfg.ANO_ALVO}
        GROUP BY 1, 2, 3, 4
    """)

    # ---- Checagens rápidas -----------------------------------------------
    n = con.sql("SELECT count(*) FROM score").fetchone()[0]
    print(f"inscrições pontuadas (2025): {n:,}")

    print("\nnulos e faixa de pontos:")
    print(con.sql("""
        SELECT
          sum(CASE WHEN pontos IS NULL THEN 1 ELSE 0 END) AS pontos_null,
          min(pontos) AS min_pt, max(pontos) AS max_pt,
          round(avg(pontos), 1) AS media_pt
        FROM score
    """).df().to_string(index=False))

    # Pontuação máxima teórica de 2025 = soma de todas as perg_pontuacao do ano.
    max_teorico = con.sql(f"""
        SELECT sum(perg_pontuacao) FROM {c} WHERE ano = {cfg.ANO_ALVO}
    """).fetchone()[0]
    print(f"\npontuação máxima teórica (soma da régua 2025): {max_teorico}")

    print("\ndistribuição de pontos (top 15 valores):")
    print(con.sql("""
        SELECT pontos, count(*) n
        FROM score GROUP BY 1 ORDER BY n DESC LIMIT 15
    """).df().to_string(index=False))

    print("\namostra:")
    print(con.sql("SELECT * FROM score ORDER BY pontos DESC LIMIT 5").df().to_string(index=False))

    con.close()
    print("\n[OK] Etapa 2 concluída — tabela `score` gravada.")


if __name__ == "__main__":
    main()

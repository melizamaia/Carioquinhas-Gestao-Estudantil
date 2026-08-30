"""Etapa 5 — Geração dos JSONs agregados (data/*.json) para o painel/ficha.

Consome as tabelas de build (score/fila/funil/top_numeros) e enriquece as
unidades com a Query D (join por string — resolve os dois formatos 7/5 dígitos
sem perder as parceiras) e classifica pública x parceira.

Saídas:
  data/painel.json         — três números do topo + funil + cobertura
  data/fila.json           — filas por unidade x grupamento x horário, em FAIXAS
  data/fichas_exemplo.json — famílias-exemplo para a Ficha da Família (demo)

Recorte territorial pela UNIDADE (Query D), nunca pelo bairro declarado da
família (armadilha #9). Rodar: python etl/05_gerar_jsons.py
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

import config as cfg
from db import connect

AVISO = (
    "Dados anonimizados do Claude Impact Lab (Inscrição Creche SME-RJ). "
    "Os indicadores ilustram a dinâmica do processo e não representam a realidade."
)
NOTA_FUNIL = (
    "Funil simulado sobre o estado final de cada opção (coluna situacao). "
    "A base não tem timestamp real de convocação/expiração."
)


def meta() -> dict:
    return {
        "ano": cfg.ANO_ALVO,
        "gerado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "aviso": AVISO,
    }


def salvar(nome: str, obj: dict) -> None:
    caminho = cfg.DATA_DIR / nome
    caminho.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    kb = caminho.stat().st_size / 1024
    print(f"  → {nome}  ({kb:.1f} KB)")


def construir_unidades(con) -> None:
    """Tabela de unidades enriquecida (Query D) + tipo pública/parceira."""
    d = (
        f"read_csv_auto('{cfg.QUERY_D}', delim=';', header=false, nullstr='NULL', "
        f"names=['seq','esc_codigo','nome','tipo','logradouro','numero',"
        f"'complemento','bairro','cep'])"
    )
    # A Query D tem esc_codigo duplicados (80 linhas repetidas). Deduplica para
    # UMA linha por unidade, senão o LEFT JOIN infla as filas (fan-out).
    con.execute(f"""
        CREATE OR REPLACE TABLE unidades_d AS
        SELECT unidade,
               first(nome ORDER BY seq)   AS nome,
               first(bairro ORDER BY seq) AS bairro
        FROM (
            SELECT CAST(esc_codigo AS VARCHAR) AS unidade, nome, bairro, seq
            FROM {d} WHERE esc_codigo IS NOT NULL
        )
        GROUP BY unidade
    """)
    # Registra a função de classificação como UDF para uso em SQL.
    con.create_function("tipo_unidade", cfg.tipo_unidade, ["VARCHAR"], "VARCHAR")


def gerar_painel(con) -> None:
    top = con.sql("SELECT * FROM top_numeros").df().iloc[0]
    fun = con.sql("SELECT * FROM funil_global").df().iloc[0]
    cob = con.sql("""
        SELECT count(*) linhas_na_fila,
               count(DISTINCT (unidade, grupamento, horario)) filas_distintas,
               count(DISTINCT unidade) unidades_com_fila
        FROM fila
    """).df().iloc[0]
    tipos = con.sql("""
        SELECT tipo_unidade(unidade) tipo, count(DISTINCT unidade) n
        FROM fila GROUP BY 1
    """).df().set_index("tipo")["n"].to_dict()

    painel = {
        "meta": meta(),
        "topo": [
            {"chave": "esperando", "valor": int(top.esperando),
             "rotulo": "Famílias na lista de espera"},
            {"chave": "confirmadas", "valor": int(top.confirmadas),
             "rotulo": "Vagas confirmadas"},
            {"chave": "perdidas", "valor": int(top.perdidas),
             "rotulo": "Vagas perdidas na confirmação"},
        ],
        "topo_familias_distintas": {
            "esperando": int(top.familias_esperando),
            "confirmadas": int(top.familias_confirmadas),
            "perdidas": int(top.familias_perdidas),
            "nota": "Grão família (inscrições distintas). Categorias se sobrepõem, não somam.",
        },
        "funil": {
            "simulado": True,
            "nota": NOTA_FUNIL,
            "taxa_expiracao_pct": float(fun.taxa_expiracao_pct),
            "estagios": [
                {"chave": "ofertada", "rotulo": "Ofertada", "valor": int(fun.ofertada)},
                {"chave": "convocada", "rotulo": "Convocada", "valor": int(fun.convocada)},
                {"chave": "confirmada", "rotulo": "Confirmada", "valor": int(fun.confirmada)},
                {"chave": "expirada", "rotulo": "Expirada", "valor": int(fun.expirada)},
                {"chave": "reofertada", "rotulo": "Reofertada", "valor": int(fun.reofertada)},
            ],
            "em_analise": int(fun.em_analise),
        },
        "cobertura": {
            "linhas_na_fila": int(cob.linhas_na_fila),
            "filas_distintas": int(cob.filas_distintas),
            "unidades_com_fila": int(cob.unidades_com_fila),
            "unidades_publicas": int(tipos.get("publica", 0)),
            "unidades_parceiras": int(tipos.get("parceira", 0)),
        },
    }
    salvar("painel.json", painel)


def gerar_fila(con) -> None:
    # fila é pequena (16k linhas) — pode ir para pandas. NUNCA a QueryB.
    df = con.sql("""
        SELECT f.unidade, tipo_unidade(f.unidade) AS tipo,
               COALESCE(d.nome, f.nome_unidade) AS nome,
               d.bairro AS bairro,
               trim(f.grupamento) AS grupamento, f.horario, f.posicao, f.tamanho_fila
        FROM fila f
        LEFT JOIN unidades_d d USING (unidade)
    """).df()
    df["faixa"] = df["posicao"].apply(cfg.faixa_posicao)

    rotulos = [r for _, r in cfg.FAIXAS_POSICAO]
    filas = []
    chaves = ["unidade", "tipo", "nome", "bairro", "grupamento", "horario"]
    for chave, grupo in df.groupby(chaves, dropna=False):
        contagem = grupo["faixa"].value_counts().to_dict()
        filas.append({
            "unidade": chave[0],
            "tipo": chave[1],
            "nome": None if chave[2] is None or str(chave[2]) == "nan" else chave[2],
            "bairro": None if chave[3] is None or str(chave[3]) == "nan" else chave[3],
            "grupamento": chave[4],
            "horario": chave[5],
            "tamanho": int(grupo.shape[0]),
            "faixas": {r: int(contagem.get(r, 0)) for r in rotulos},
        })
    filas.sort(key=lambda x: x["tamanho"], reverse=True)

    salvar("fila.json", {
        "meta": meta(),
        "faixas": rotulos,
        "total_filas": len(filas),
        "filas": filas,
    })


def gerar_fichas_exemplo(con) -> None:
    """Famílias-exemplo cobrindo faixas diferentes, para a Ficha da Família."""
    # Pega uma família de cada faixa dentro da maior fila, para variar as posições.
    df = con.sql("""
        WITH maior AS (
            SELECT unidade, grupamento, horario
            FROM fila GROUP BY 1,2,3 ORDER BY count(*) DESC LIMIT 1
        )
        SELECT f.aluno_anon, f.responsavel_anon,
               f.unidade, tipo_unidade(f.unidade) AS tipo,
               COALESCE(d.nome, f.nome_unidade) AS nome, d.bairro,
               trim(f.grupamento) AS grupamento, f.horario, f.pontos, f.posicao, f.tamanho_fila
        FROM fila f
        JOIN maior USING (unidade, grupamento, horario)
        LEFT JOIN unidades_d d USING (unidade)
        ORDER BY f.posicao
    """).df()

    escolhidas, faixas_vistas = [], set()
    for _, r in df.iterrows():
        fx = cfg.faixa_posicao(int(r.posicao))
        if fx in faixas_vistas:
            continue
        faixas_vistas.add(fx)
        escolhidas.append({
            "familia": r.responsavel_anon,
            "crianca": r.aluno_anon,
            "unidade": r.unidade,
            "tipo": r.tipo,
            "nome_unidade": None if r.nome is None or str(r.nome) == "nan" else r.nome,
            "bairro": None if r.bairro is None or str(r.bairro) == "nan" else r.bairro,
            "grupamento": r.grupamento,
            "horario": r.horario,
            "pontos": int(r.pontos),
            "faixa": fx,
            "tamanho_fila": int(r.tamanho_fila),
        })

    salvar("fichas_exemplo.json", {"meta": meta(), "fichas": escolhidas})


def main() -> None:
    cfg.DATA_DIR.mkdir(exist_ok=True)
    con = connect()
    construir_unidades(con)
    print("Gerando JSONs:")
    gerar_painel(con)
    gerar_fila(con)
    gerar_fichas_exemplo(con)
    con.close()
    print("\n[OK] Etapa 5 concluída.")


if __name__ == "__main__":
    main()

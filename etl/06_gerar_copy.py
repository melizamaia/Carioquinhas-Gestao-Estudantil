"""Etapa 6 — Geração de texto da Ficha da Família via Claude API (build-time).

Reescreve os textos burocráticos do formulário (critérios de classificação de
2025 + mensagens de situação/fila) em linguagem simples, para uma mãe com baixa
escolaridade. Guarda pares antes/depois em data/copy.json (para o slide do pitch).

RODAR SÓ EM BUILD, NUNCA EM RUNTIME. É idempotente: só chama a API para textos
novos ou alterados (cache pelo texto original em data/copy.json).

Requer ANTHROPIC_API_KEY no .env (nunca hardcoded). Modelo: claude-opus-4-8.
Rodar: python etl/06_gerar_copy.py
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone

from dotenv import load_dotenv

import config as cfg

MODELO = "claude-opus-4-8"

SYSTEM_PROMPT = (
    "Reescreva textos de formulário público para uma mãe com baixa escolaridade. "
    "Frases de no máximo 12 palavras. Zero siglas. Zero jargão. Voz ativa, "
    "segunda pessoa. Números em algarismo. Responda apenas com o texto reescrito."
)

# Mensagens de situação/fila da Ficha da Família (originais em linguagem oficial).
TEXTOS_SITUACAO = [
    {
        "chave": "situacao_lista_espera",
        "categoria": "situacao",
        "original": ("Sua inscrição encontra-se em lista de espera, aguardando a "
                     "disponibilização de vaga na unidade escolar pleiteada."),
    },
    {
        "chave": "situacao_cancelado_confirmacao",
        "categoria": "situacao",
        "original": ("Inscrição cancelada em decorrência do não comparecimento para "
                     "confirmação da matrícula dentro do prazo estipulado."),
    },
    {
        "chave": "situacao_confirmado",
        "categoria": "situacao",
        "original": "Matrícula confirmada com êxito na unidade escolar de destino.",
    },
    {
        "chave": "explica_faixa_posicao",
        "categoria": "fila",
        "original": ("Sua colocação na fila de classificação é apresentada em faixa "
                     "aproximada, em virtude da existência de empates na pontuação."),
    },
    {
        "chave": "explica_pontuacao",
        "categoria": "fila",
        "original": ("A pontuação é atribuída conforme os critérios socioeconômicos "
                     "declarados e validados no ato da inscrição."),
    },
]


def carregar_criterios() -> list[dict]:
    """Os 13 critérios de classificação de 2025 (perguntas da Query C)."""
    import duckdb

    con = duckdb.connect()
    c = cfg.read_csv_gz_sql(cfg.QUERY_C)
    rows = con.sql(f"""
        SELECT perg_ordemVisualizacao AS ordem, perg_pontuacao AS pontos,
               pergunta_texto AS texto
        FROM {c} WHERE ano = {cfg.ANO_ALVO} ORDER BY ordem
    """).df()
    con.close()
    itens = []
    for _, r in rows.iterrows():
        itens.append({
            "chave": f"criterio_{int(r.ordem)}",
            "categoria": "criterio",
            "pontos": int(r.pontos),
            "original": r.texto.strip(),
        })
    return itens


def carregar_cache() -> dict[str, dict]:
    """Mapa original->item já reescrito, para não chamar a API de novo."""
    caminho = cfg.DATA_DIR / "copy.json"
    if not caminho.exists():
        return {}
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    return {it["original"]: it for it in dados.get("itens", [])}


def main() -> None:
    load_dotenv(cfg.PROJECT_DIR / ".env")
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("[ERRO] ANTHROPIC_API_KEY não encontrada.", file=sys.stderr)
        print("Crie o arquivo .env (veja .env.example) com sua chave e rode de novo.",
              file=sys.stderr)
        sys.exit(1)

    import anthropic

    client = anthropic.Anthropic(api_key=api_key)

    itens = carregar_criterios() + TEXTOS_SITUACAO
    cache = carregar_cache()

    print(f"{len(itens)} textos a processar (modelo {MODELO}):")
    resultado = []
    novos, reaproveitados = 0, 0
    for it in itens:
        anterior = cache.get(it["original"])
        if anterior and anterior.get("reescrito"):
            it["reescrito"] = anterior["reescrito"]
            reaproveitados += 1
            print(f"  = {it['chave']} (cache)")
        else:
            resp = client.messages.create(
                model=MODELO,
                max_tokens=300,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": it["original"]}],
            )
            it["reescrito"] = "".join(
                b.text for b in resp.content if b.type == "text"
            ).strip()
            novos += 1
            print(f"  + {it['chave']}")
            print(f"      antes:  {it['original'][:60]}...")
            print(f"      depois: {it['reescrito']}")
        resultado.append(it)

    saida = {
        "meta": {
            "ano": cfg.ANO_ALVO,
            "gerado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "modelo": MODELO,
            "system_prompt": SYSTEM_PROMPT,
            "nota": "Textos reescritos via Claude API em build. Pares antes/depois.",
        },
        "itens": resultado,
    }
    caminho = cfg.DATA_DIR / "copy.json"
    caminho.write_text(json.dumps(saida, ensure_ascii=False, indent=2), encoding="utf-8")
    kb = caminho.stat().st_size / 1024
    print(f"\n[OK] copy.json gravado ({kb:.1f} KB). "
          f"novos={novos}, cache={reaproveitados}")


if __name__ == "__main__":
    main()

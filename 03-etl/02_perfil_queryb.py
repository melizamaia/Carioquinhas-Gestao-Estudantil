#!/usr/bin/env python3
"""
Query B (4.357.119 respostas) cruzada com o desfecho da Query A.

Pergunta central: a família declara um critério de vulnerabilidade e consegue
comprovar? E quando não comprova, o que acontece com a vaga?

Passo 1 — lê a Query A e monta o desfecho de cada inscrição (343k chaves).
Passo 2 — varre a Query B em streaming, agregando por pergunta/ano.

Uso: python3 03-etl/02_perfil_queryb.py
"""

import csv
import gzip
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DIR = BASE / "01-dados/dadoscreche/Bases IC_ ClassificadoseFila"
QA = DIR / "01_QueryA_InscricoesPorAno.csv.gz"
QB = DIR / "02_QueryB_RespostasSocioEconomicas.csv.gz"
QC = DIR / "03_QueryC_PerguntasComDescricao.csv"
SAIDA = BASE / "03-etl/saida"
SAIDA.mkdir(parents=True, exist_ok=True)

csv.field_size_limit(10_000_000)

# desfechos que interessam
MATRICULOU = "Confirmado"
PERDEU_NA_CONFIRMACAO = "Cancelado na confirmacao"
ESPERA = "Lista de espera"


def main():
    # ------------------------------------------------------------------
    # PASSO 0 — catálogo de perguntas (Query C)
    # ------------------------------------------------------------------
    catalogo = {}          # (ano, ich_perg_id) -> dict
    pontuacao_ano = defaultdict(dict)
    with open(QC, encoding="utf-8-sig", newline="") as fh:
        for r in csv.DictReader(fh, delimiter=";"):
            chave = (r["ano"], r["ich_perg_id"])
            catalogo[chave] = {
                "perg_id": r["perg_id"],
                "texto": r["pergunta_texto"].strip(),
                "pontos": int(r["perg_pontuacao"] or 0),
            }
            pontuacao_ano[r["ano"]][r["perg_id"]] = int(r["perg_pontuacao"] or 0)

    print(f"catálogo: {len(catalogo)} instâncias de pergunta")

    # ------------------------------------------------------------------
    # PASSO 1 — desfecho por inscrição, a partir da Query A
    # ------------------------------------------------------------------
    print("lendo Query A para montar desfechos...")
    desfecho = {}      # (ano,prm,plm,ipl) -> 'matriculou' | 'perdeu' | 'espera' | 'outro'
    n_opcoes = Counter()
    with gzip.open(QA, mode="rt", encoding="utf-8-sig", newline="") as fh:
        sits = defaultdict(Counter)
        for linha in csv.DictReader(fh, delimiter=";"):
            k = (linha["ano"], linha["prm_id"], linha["plm_id"], linha["ipl_id"])
            sits[k][linha["situacao"].strip()] += 1
            n_opcoes[k] += 1
    for k, c in sits.items():
        if c.get(MATRICULOU):
            desfecho[k] = "matriculou"
        elif c.get(PERDEU_NA_CONFIRMACAO):
            desfecho[k] = "perdeu_na_confirmacao"
        elif c.get(ESPERA):
            desfecho[k] = "lista_de_espera"
        else:
            desfecho[k] = "outro"
    del sits
    print(f"  {len(desfecho):,} inscrições com desfecho".replace(",", "."))

    # ------------------------------------------------------------------
    # PASSO 2 — varredura da Query B
    # ------------------------------------------------------------------
    print("varrendo Query B (4,36M linhas)...")
    total = 0
    sem_correspondencia = 0
    # por (ano, perg_id): declarou / declarou_e_confirmou / confirmou_sem_declarar
    declarou = Counter()
    declarou_confirmou = Counter()
    confirmou_sem_declarar = Counter()
    respondeu = Counter()

    # desfecho x se comprovou algum critério declarado
    # inscricao -> [n_declarados, n_confirmados]
    perfil_insc = defaultdict(lambda: [0, 0])

    combo = Counter()   # (resposta, confirmado) -> n
    anos_vistos = Counter()

    with gzip.open(QB, mode="rt", encoding="utf-8-sig", newline="") as fh:
        for linha in csv.DictReader(fh, delimiter=";"):
            total += 1
            ano = linha["ano"]
            k = (ano, linha["prm_id"], linha["plm_id"], linha["ipl_id"])
            pid = catalogo.get((ano, linha["ich_perg_id"]), {}).get("perg_id", "?")
            resp = (linha["resposta"] or "").strip()
            conf = (linha["confirmado"] or "").strip()

            anos_vistos[ano] += 1
            combo[(resp, conf)] += 1
            respondeu[(ano, pid)] += 1

            if resp == "Sim":
                declarou[(ano, pid)] += 1
                perfil_insc[k][0] += 1
                if conf == "Sim":
                    declarou_confirmou[(ano, pid)] += 1
                    perfil_insc[k][1] += 1
            elif conf == "Sim":
                confirmou_sem_declarar[(ano, pid)] += 1

            if k not in desfecho:
                sem_correspondencia += 1

    print(f"  {total:,} linhas lidas".replace(",", "."))

    # ------------------------------------------------------------------
    # RELATÓRIO
    # ------------------------------------------------------------------
    P = print
    P("\n" + "=" * 90)
    P("QUERY B — DECLARAR vs COMPROVAR")
    P("=" * 90)

    P(f"\n[1] INTEGRIDADE")
    P(f"  linhas: {total:,}".replace(",", "."))
    P(f"  respostas sem inscrição correspondente na Query A: {sem_correspondencia:,}".replace(",", "."))
    P(f"  linhas por ano: " + "  ".join(f"{a}={n:,}".replace(",", ".") for a, n in sorted(anos_vistos.items())))

    P(f"\n[2] COMBINAÇÕES resposta × confirmado")
    for (r, c), n in combo.most_common():
        P(f"  resposta={r!r:<6} confirmado={c!r:<6} {n:>10,}  {100*n/total:>5.1f}%".replace(",", "."))

    P("\n[3] TAXA DE COMPROVAÇÃO POR CRITÉRIO E ANO")
    P("    (de tudo que a família DECLAROU, quanto foi efetivamente confirmado)")
    anos = sorted(anos_vistos)
    # ordena perguntas por peso no último ano
    pids = sorted({p for (_, p) in declarou}, key=lambda p: -max(
        pontuacao_ano[a].get(p, 0) for a in anos))
    for pid in pids:
        texto = next((v["texto"] for v in catalogo.values() if v["perg_id"] == pid), "?")
        P(f"\n  perg_id={pid} · {texto[:76]}")
        for a in anos:
            d = declarou[(a, pid)]
            dc = declarou_confirmou[(a, pid)]
            if d == 0:
                continue
            pts = pontuacao_ano[a].get(pid, 0)
            taxa = 100 * dc / d
            alerta = "  <<< PERDA ALTA" if taxa < 50 else ""
            P(f"    {a} ({pts:>3}pt)  declarou {d:>7,}  comprovou {dc:>7,}  = {taxa:>5.1f}%{alerta}".replace(",", "."))

    # ------------------------------------------------------------------
    P("\n" + "=" * 90)
    P("[4] O NÚMERO DA TESE — comprovação documental × desfecho da vaga")
    P("=" * 90)

    # cruza: entre quem declarou ao menos 1 critério, comparar quem comprovou tudo,
    # comprovou em parte, e não comprovou nada
    faixas = defaultdict(Counter)   # faixa -> desfecho -> n
    for k, (nd, nc) in perfil_insc.items():
        if nd == 0:
            continue
        if nc == 0:
            faixa = "nao_comprovou_nada"
        elif nc < nd:
            faixa = "comprovou_em_parte"
        else:
            faixa = "comprovou_tudo"
        faixas[faixa][desfecho.get(k, "sem_desfecho")] += 1

    ordem = ["comprovou_tudo", "comprovou_em_parte", "nao_comprovou_nada"]
    desf_cols = ["matriculou", "perdeu_na_confirmacao", "lista_de_espera", "outro"]
    P(f"\n  {'':<22}" + "".join(f"{d:>24}" for d in desf_cols) + f"{'total':>12}")
    for faixa in ordem:
        c = faixas[faixa]
        tot = sum(c.values())
        if not tot:
            continue
        linha_txt = f"  {faixa:<22}"
        for d in desf_cols:
            linha_txt += f"{c[d]:>14,} ({100*c[d]/tot:>4.1f}%)".replace(",", ".")
        linha_txt += f"{tot:>12,}".replace(",", ".")
        P(linha_txt)

    # taxa de matrícula por faixa — a manchete
    P("\n  → TAXA DE MATRÍCULA POR CAPACIDADE DE COMPROVAR:")
    for faixa in ordem:
        c = faixas[faixa]
        tot = sum(c.values())
        if tot:
            P(f"     {faixa:<22} {100*c['matriculou']/tot:>5.1f}% matricularam   (n={tot:,})".replace(",", "."))

    # ------------------------------------------------------------------
    resumo = {
        "total_linhas_queryb": total,
        "sem_correspondencia": sem_correspondencia,
        "combinacoes_resposta_confirmado": {f"{r}|{c}": n for (r, c), n in combo.items()},
        "taxa_comprovacao": {
            f"{a}|{p}": {
                "declarou": declarou[(a, p)],
                "comprovou": declarou_confirmou[(a, p)],
                "pontos": pontuacao_ano[a].get(p, 0),
                "texto": next((v["texto"] for v in catalogo.values() if v["perg_id"] == p), "?"),
            }
            for (a, p) in sorted(declarou)
        },
        "desfecho_por_faixa_comprovacao": {
            f: dict(c) for f, c in faixas.items()
        },
    }
    destino = SAIDA / "perfil_queryb.json"
    destino.write_text(json.dumps(resumo, ensure_ascii=False, indent=2), encoding="utf-8")
    P(f"\n✓ resumo salvo em {destino.relative_to(BASE)}")


if __name__ == "__main__":
    main()

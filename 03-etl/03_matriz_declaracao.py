#!/usr/bin/env python3
"""
Matriz 2x2 completa (declarou × confirmado) por pergunta e ano.

Serve para separar duas leituras que o agregado confunde:
  (a) a família declarou e não conseguiu comprovar   -> barreira documental
  (b) o sistema confirmou sem a família declarar     -> validação automática (RMI)

Sem isso, não dá para afirmar qual dos dois números vai para o pitch.

Uso: python3 03-etl/03_matriz_declaracao.py
"""

import csv
import gzip
import json
from collections import Counter, defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DIR = BASE / "01-dados/dadoscreche/Bases IC_ ClassificadoseFila"
QB = DIR / "02_QueryB_RespostasSocioEconomicas.csv.gz"
QC = DIR / "03_QueryC_PerguntasComDescricao.csv"
SAIDA = BASE / "03-etl/saida"
SAIDA.mkdir(parents=True, exist_ok=True)

csv.field_size_limit(10_000_000)


def main():
    catalogo, pontos = {}, defaultdict(dict)
    with open(QC, encoding="utf-8-sig", newline="") as fh:
        for r in csv.DictReader(fh, delimiter=";"):
            catalogo[(r["ano"], r["ich_perg_id"])] = r["perg_id"]
            pontos[r["ano"]][r["perg_id"]] = int(r["perg_pontuacao"] or 0)
            catalogo.setdefault("txt_" + r["perg_id"], r["pergunta_texto"].strip())

    matriz = defaultdict(Counter)   # (ano, perg_id) -> Counter[(resp, conf)]
    with gzip.open(QB, mode="rt", encoding="utf-8-sig", newline="") as fh:
        for linha in csv.DictReader(fh, delimiter=";"):
            ano = linha["ano"]
            pid = catalogo.get((ano, linha["ich_perg_id"]), "?")
            matriz[(ano, pid)][
                ((linha["resposta"] or "").strip(), (linha["confirmado"] or "").strip())
            ] += 1

    P = print
    P("=" * 104)
    P("MATRIZ DECLAROU × CONFIRMADO — por pergunta e ano")
    P("=" * 104)
    P("  SS = declarou e foi confirmado      SN = declarou e NÃO foi confirmado (barreira documental)")
    P("  NS = NÃO declarou mas foi confirmado (validação automática)   NN = não declarou, não confirmado")

    # ordena por peso máximo
    pids = sorted({p for (_, p) in matriz},
                  key=lambda p: -max(pontos[a].get(p, 0) for a in pontos))

    resumo = {}
    for pid in pids:
        texto = catalogo.get("txt_" + pid, "?")
        P(f"\n  perg_id={pid} · {texto[:88]}")
        P(f"    {'ano':<6}{'pt':>4}  {'SS':>8} {'SN':>8} {'NS':>9} {'NN':>10}   "
          f"{'taxa compro.':>13} {'% autom.':>9}")
        for ano in sorted(pontos):
            c = matriz.get((ano, pid))
            if not c:
                continue
            ss = c[("Sim", "Sim")]
            sn = c[("Sim", "Nao")]
            ns = c[("Nao", "Sim")]
            nn = c[("Nao", "Nao")]
            tot_conf = ss + ns
            taxa = 100 * ss / (ss + sn) if (ss + sn) else 0
            autom = 100 * ns / tot_conf if tot_conf else 0
            P(f"    {ano:<6}{pontos[ano].get(pid,0):>4}  {ss:>8,} {sn:>8,} {ns:>9,} {nn:>10,}   "
              f"{taxa:>12.1f}% {autom:>8.1f}%".replace(",", "."))
            resumo[f"{ano}|{pid}"] = {
                "pontos": pontos[ano].get(pid, 0), "texto": texto,
                "declarou_confirmou": ss, "declarou_nao_confirmou": sn,
                "nao_declarou_confirmou": ns, "nao_nao": nn,
                "taxa_comprovacao": round(taxa, 1),
                "pct_confirmacoes_automaticas": round(autom, 1),
            }

    # ---------- leitura agregada por ano ----------
    P("\n" + "=" * 104)
    P("AGREGADO POR ANO — a quebra de 2021 para 2022")
    P("=" * 104)
    P(f"  {'ano':<6} {'SS':>10} {'SN':>10} {'NS':>10} {'NN':>12}  {'taxa compro.':>13}")
    por_ano = defaultdict(Counter)
    for (ano, pid), c in matriz.items():
        for k, v in c.items():
            por_ano[ano][k] += v
    for ano in sorted(por_ano):
        c = por_ano[ano]
        ss, sn, ns, nn = c[("Sim","Sim")], c[("Sim","Nao")], c[("Nao","Sim")], c[("Nao","Nao")]
        taxa = 100 * ss / (ss + sn) if (ss + sn) else 0
        P(f"  {ano:<6} {ss:>10,} {sn:>10,} {ns:>10,} {nn:>12,}  {taxa:>12.1f}%".replace(",", "."))

    (SAIDA / "matriz_declaracao.json").write_text(
        json.dumps(resumo, ensure_ascii=False, indent=2), encoding="utf-8")
    P(f"\n✓ salvo em 03-etl/saida/matriz_declaracao.json")


if __name__ == "__main__":
    main()

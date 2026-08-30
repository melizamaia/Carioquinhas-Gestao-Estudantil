#!/usr/bin/env python3
"""
Quem é conferido, e qual o tamanho da distorção na ordem da fila.

Três perguntas:
  (1) As 4.894 inscrições conferidas em bloco têm perfil diferente? Matriculam mais?
  (2) A chance de ser conferido depende do território / da unidade escolhida?
  (3) Se a pontuação fosse verificada, quanto a fila mudaria de ordem?

Foco em 2025 (régua vigente: CadÚnico = 51 pt de ~100).

Uso: python3 03-etl/04_distorcao_da_fila.py
"""

import csv
import gzip
import json
from collections import Counter, defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DIR = BASE / "01-dados/dadoscreche/Bases IC_ ClassificadoseFila"
QA = DIR / "01_QueryA_InscricoesPorAno.csv.gz"
QB = DIR / "02_QueryB_RespostasSocioEconomicas.csv.gz"
QC = DIR / "03_QueryC_PerguntasComDescricao.csv"
QD = DIR / "04_UnidadesEscolaresComEndereco.csv"
SAIDA = BASE / "03-etl/saida"
SAIDA.mkdir(parents=True, exist_ok=True)
ANO = "2025"

csv.field_size_limit(10_000_000)


def main():
    # ---------- régua de pontuação de 2025 ----------
    pontos = {}          # ich_perg_id -> pontos
    texto = {}
    with open(QC, encoding="utf-8-sig", newline="") as fh:
        for r in csv.DictReader(fh, delimiter=";"):
            if r["ano"] == ANO:
                pontos[r["ich_perg_id"]] = int(r["perg_pontuacao"] or 0)
                texto[r["ich_perg_id"]] = r["pergunta_texto"].strip()
    total_possivel = sum(pontos.values())
    print(f"régua {ANO}: {len(pontos)} perguntas, {total_possivel} pontos possíveis")

    # ---------- unidades ----------
    bairro_unidade = {}
    nome_unidade = {}
    with open(QD, encoding="utf-8-sig", newline="") as fh:
        for r in csv.reader(fh, delimiter=";"):
            if len(r) >= 8:
                cod = r[1].strip()
                nome_unidade[cod] = r[2].strip()
                b = r[7].strip()
                bairro_unidade[cod] = b if b and b != "NULL" else "(sem bairro)"

    # ---------- Query A: desfecho, unidade de 1a opção ----------
    print("lendo Query A...")
    desfecho, primeira_unidade, n_opcoes = {}, {}, Counter()
    sits = defaultdict(Counter)
    with gzip.open(QA, mode="rt", encoding="utf-8-sig", newline="") as fh:
        for l in csv.DictReader(fh, delimiter=";"):
            if l["ano"] != ANO:
                continue
            k = (l["prm_id"], l["plm_id"], l["ipl_id"])
            sits[k][l["situacao"].strip()] += 1
            n_opcoes[k] += 1
            if l["opcao"] == "1":
                primeira_unidade[k] = l["unidade"].strip()
    for k, c in sits.items():
        if c.get("Confirmado"):
            desfecho[k] = "matriculou"
        elif c.get("Cancelado na confirmacao"):
            desfecho[k] = "perdeu_na_confirmacao"
        elif c.get("Lista de espera"):
            desfecho[k] = "lista_de_espera"
        else:
            desfecho[k] = "outro"
    print(f"  {len(desfecho):,} inscrições em {ANO}".replace(",", "."))

    # ---------- Query B: pontuação declarada x verificada ----------
    print("lendo Query B...")
    pt_declarado = Counter()
    pt_confirmado = Counter()
    n_perg = Counter()
    n_conf = Counter()
    with gzip.open(QB, mode="rt", encoding="utf-8-sig", newline="") as fh:
        for l in csv.DictReader(fh, delimiter=";"):
            if l["ano"] != ANO:
                continue
            k = (l["prm_id"], l["plm_id"], l["ipl_id"])
            p = pontos.get(l["ich_perg_id"], 0)
            n_perg[k] += 1
            if l["resposta"].strip() == "Sim":
                pt_declarado[k] += p
            if l["confirmado"].strip() == "Sim":
                pt_confirmado[k] += p
                n_conf[k] += 1

    inscricoes = list(n_perg)
    P = print
    P("\n" + "=" * 92)
    P(f"DISTORÇÃO DA FILA — {ANO}")
    P("=" * 92)

    # ---------- (1) perfil de quem é conferido ----------
    def grupo(k):
        c, n = n_conf[k], n_perg[k]
        if c == 0:
            return "nunca conferida"
        if c == n:
            return "conferida em bloco"
        return "conferida em parte"

    P("\n[1] PERFIL POR GRUPO DE CONFERÊNCIA")
    g_desf = defaultdict(Counter)
    g_pts = defaultdict(list)
    g_opc = defaultdict(list)
    for k in inscricoes:
        g = grupo(k)
        g_desf[g][desfecho.get(k, "sem_desfecho")] += 1
        g_pts[g].append(pt_declarado[k])
        g_opc[g].append(n_opcoes.get(k, 0))

    cols = ["matriculou", "perdeu_na_confirmacao", "lista_de_espera", "outro"]
    P(f"  {'grupo':<22}{'n':>8}  " + "".join(f"{c:>22}" for c in cols) +
      f"{'pt.declarado méd':>18}{'opções méd':>12}")
    for g in ("nunca conferida", "conferida em bloco", "conferida em parte"):
        c = g_desf[g]
        tot = sum(c.values())
        if not tot:
            continue
        linha = f"  {g:<22}{tot:>8,}  ".replace(",", ".")
        for col in cols:
            linha += f"{c[col]:>13,} ({100*c[col]/tot:>4.1f}%)".replace(",", ".")
        media_pt = sum(g_pts[g]) / len(g_pts[g])
        media_op = sum(g_opc[g]) / len(g_opc[g])
        linha += f"{media_pt:>18.1f}{media_op:>12.2f}"
        P(linha)

    # ---------- (2) território ----------
    P("\n[2] A CONFERÊNCIA DEPENDE DA UNIDADE ESCOLHIDA?")
    por_unid = defaultdict(lambda: [0, 0])   # unidade -> [total, conferidas]
    por_bairro = defaultdict(lambda: [0, 0])
    for k in inscricoes:
        u = primeira_unidade.get(k)
        if not u:
            continue
        conferida = 1 if n_conf[k] > 0 else 0
        por_unid[u][0] += 1
        por_unid[u][1] += conferida
        b = bairro_unidade.get(u, "(desconhecido)")
        por_bairro[b][0] += 1
        por_bairro[b][1] += conferida

    taxas = [(c / t, t, u) for u, (t, c) in por_unid.items() if t >= 50]
    taxas.sort(reverse=True)
    P(f"  unidades com ao menos 50 inscrições de 1ª opção: {len(taxas)}")
    if taxas:
        P("\n  MAIOR taxa de conferência:")
        for taxa, t, u in taxas[:8]:
            P(f"    {taxa*100:>5.1f}%  ({t:>4} insc.)  {nome_unidade.get(u,u)[:52]}")
        P("\n  MENOR taxa de conferência:")
        for taxa, t, u in taxas[-8:]:
            P(f"    {taxa*100:>5.1f}%  ({t:>4} insc.)  {nome_unidade.get(u,u)[:52]}")
        zeradas = sum(1 for taxa, _, _ in taxas if taxa == 0)
        P(f"\n  unidades com ZERO conferência: {zeradas} de {len(taxas)}")

    bt = [(c / t, t, b) for b, (t, c) in por_bairro.items() if t >= 200]
    bt.sort(reverse=True)
    if bt:
        P(f"\n  por bairro da unidade (≥200 inscrições) — maior e menor:")
        for taxa, t, b in bt[:5]:
            P(f"    {taxa*100:>5.1f}%  ({t:>5} insc.)  {b}")
        P("    ...")
        for taxa, t, b in bt[-5:]:
            P(f"    {taxa*100:>5.1f}%  ({t:>5} insc.)  {b}")

    # ---------- (3) distorção da ordem ----------
    P("\n[3] TAMANHO DA DISTORÇÃO — pontuação declarada vs verificada")
    dec = sorted(inscricoes, key=lambda k: -pt_declarado[k])
    ver = sorted(inscricoes, key=lambda k: -pt_confirmado[k])
    pos_dec = {k: i for i, k in enumerate(dec)}
    pos_ver = {k: i for i, k in enumerate(ver)}
    n = len(inscricoes)

    desloc = [abs(pos_dec[k] - pos_ver[k]) for k in inscricoes]
    desloc.sort()
    P(f"  inscrições: {n:,}".replace(",", "."))
    P(f"  deslocamento de posição entre as duas ordenações:")
    P(f"    mediana: {desloc[n//2]:,} posições".replace(",", "."))
    P(f"    média:   {sum(desloc)/n:,.0f} posições".replace(",", "."))
    P(f"    p90:     {desloc[int(n*0.9)]:,} posições".replace(",", "."))
    grandes = sum(1 for d in desloc if d > n * 0.1)
    P(f"  inscrições que se deslocam mais de 10% da fila: {grandes:,} ({100*grandes/n:.1f}%)".replace(",", "."))

    P(f"\n  pontuação média declarada:  {sum(pt_declarado[k] for k in inscricoes)/n:>6.1f} de {total_possivel}")
    P(f"  pontuação média verificada: {sum(pt_confirmado[k] for k in inscricoes)/n:>6.1f} de {total_possivel}")

    # quantos declararam pontuação alta sem nenhuma conferência
    alto = [k for k in inscricoes if pt_declarado[k] >= 51]
    alto_sem = [k for k in alto if n_conf[k] == 0]
    P(f"\n  inscrições com 51+ pontos declarados (≥ metade da régua): {len(alto):,}".replace(",", "."))
    P(f"    dessas, SEM nenhuma conferência: {len(alto_sem):,} ({100*len(alto_sem)/len(alto):.1f}%)".replace(",", "."))

    resumo = {
        "ano": ANO,
        "pontos_possiveis": total_possivel,
        "inscricoes": n,
        "perfil_conferencia": {g: dict(c) for g, c in g_desf.items()},
        "media_pontos_declarados": round(sum(pt_declarado[k] for k in inscricoes)/n, 2),
        "media_pontos_verificados": round(sum(pt_confirmado[k] for k in inscricoes)/n, 2),
        "deslocamento_mediano": desloc[n//2],
        "deslocamento_p90": desloc[int(n*0.9)],
        "pct_desloca_mais_de_10pct": round(100*grandes/n, 1),
        "alta_pontuacao_declarada": len(alto),
        "alta_pontuacao_sem_conferencia": len(alto_sem),
        "unidades_zero_conferencia": zeradas if taxas else None,
        "unidades_avaliadas": len(taxas),
    }
    (SAIDA / "distorcao_fila.json").write_text(
        json.dumps(resumo, ensure_ascii=False, indent=2), encoding="utf-8")
    P("\n✓ salvo em 03-etl/saida/distorcao_fila.json")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Perfilamento e limpeza da Query A (837.179 opções de inscrição, 2021-2025).

Roda com stdlib pura — sem pandas, sem duckdb.
Objetivo: (1) mapear sujeira e outliers, (2) testar as hipóteses que sustentam o pitch.

Uso: python3 03-etl/01_perfil_querya.py
"""

import csv
import gzip
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
ARQ = BASE / "01-dados/dadoscreche/Bases IC_ ClassificadoseFila/01_QueryA_InscricoesPorAno.csv.gz"
SAIDA = BASE / "03-etl/saida"
SAIDA.mkdir(parents=True, exist_ok=True)

csv.field_size_limit(10_000_000)


def barra(n, total, largura=40):
    cheio = int(largura * n / total) if total else 0
    return "█" * cheio + "·" * (largura - cheio)


def main():
    if not ARQ.exists():
        sys.exit(f"Arquivo não encontrado: {ARQ}")

    # --- acumuladores ---
    total = 0
    nulos = Counter()
    vazios = Counter()
    cardinalidade = defaultdict(set)
    situacao_por_ano = defaultdict(Counter)
    situacao_geral = Counter()
    por_ano = Counter()

    # chave da inscrição = (ano, prm_id, plm_id, ipl_id)
    opcoes_por_inscricao = Counter()
    situacoes_por_inscricao = defaultdict(Counter)
    # aluno -> ano -> situacoes
    aluno_ano_situacoes = defaultdict(Counter)
    aluno_ano_unidades = defaultdict(set)

    opcao_valores = Counter()
    idade_anos = Counter()
    linhas_duplicadas = Counter()
    unidades = set()
    bairros = Counter()
    horario = Counter()
    grupamento = Counter()

    with gzip.open(ARQ, mode="rt", encoding="utf-8-sig", newline="") as fh:
        leitor = csv.DictReader(fh, delimiter=";")
        colunas = leitor.fieldnames
        for linha in leitor:
            total += 1

            for col in colunas:
                v = linha[col]
                if v is None:
                    nulos[col] += 1
                elif v.strip() == "" or v.strip().upper() == "NULL":
                    vazios[col] += 1

            ano = linha["ano"]
            sit = (linha["situacao"] or "").strip()
            por_ano[ano] += 1
            situacao_geral[sit] += 1
            situacao_por_ano[ano][sit] += 1

            # cardinalidade amostrada (evita estourar memória em colunas de alta card.)
            for col in ("ano", "prm_id", "plm_id", "opcao", "horario",
                        "grupamento", "sexo_crianca", "situacao"):
                if len(cardinalidade[col]) < 500:
                    cardinalidade[col].add(linha[col])

            insc = (ano, linha["prm_id"], linha["plm_id"], linha["ipl_id"])
            opcoes_por_inscricao[insc] += 1
            situacoes_por_inscricao[insc][sit] += 1

            aluno = linha["aluno_anon"]
            aluno_ano_situacoes[(aluno, ano)][sit] += 1
            aluno_ano_unidades[(aluno, ano)].add(linha["unidade"])

            opcao_valores[linha["opcao"]] += 1
            unidades.add(linha["unidade"])
            b = (linha["bairro"] or "").strip()
            bairros[b if b else "(vazio)"] += 1
            horario[(linha["horario"] or "").strip()] += 1
            grupamento[(linha["grupamento"] or "").strip()] += 1

            # idade da criança no ano do processo
            nasc = (linha["nascimento_aluno_anomes"] or "").strip()
            if len(nasc) >= 4 and nasc[:4].isdigit():
                idade_anos[int(ano) - int(nasc[:4])] += 1
            else:
                idade_anos["(sem data)"] += 1

            # duplicata exata de grão: mesma inscrição + mesma opção
            linhas_duplicadas[(insc, linha["opcao"])] += 1

    # ---------------------------------------------------------------
    # RELATÓRIO
    # ---------------------------------------------------------------
    P = print
    P("=" * 78)
    P(f"PERFIL — QUERY A  ({total:,} linhas)".replace(",", "."))
    P("=" * 78)

    P("\n[1] COLUNAS E AUSÊNCIAS")
    P(f"{'coluna':<28} {'vazios':>10} {'%':>7}")
    P("-" * 50)
    for col in colunas:
        v = vazios[col] + nulos[col]
        P(f"{col:<28} {v:>10,} {100*v/total:>6.2f}%".replace(",", "."))

    P("\n[2] LINHAS POR ANO")
    for ano in sorted(por_ano):
        n = por_ano[ano]
        P(f"  {ano}  {n:>8,}  {barra(n, max(por_ano.values()))}".replace(",", "."))

    P("\n[3] SITUAÇÃO — GERAL")
    for sit, n in situacao_geral.most_common():
        P(f"  {sit:<28} {n:>8,}  {100*n/total:>5.1f}%".replace(",", "."))

    P("\n[4] SITUAÇÃO POR ANO (%)")
    sits = [s for s, _ in situacao_geral.most_common()]
    P(f"  {'situacao':<28} " + " ".join(f"{a:>7}" for a in sorted(situacao_por_ano)))
    for sit in sits:
        linha_txt = f"  {sit:<28} "
        for ano in sorted(situacao_por_ano):
            tot_ano = por_ano[ano]
            pct = 100 * situacao_por_ano[ano][sit] / tot_ano if tot_ano else 0
            linha_txt += f"{pct:>6.1f}% "
        P(linha_txt)

    # ---------------------------------------------------------------
    P("\n" + "=" * 78)
    P("OUTLIERS E SUJEIRA")
    P("=" * 78)

    P("\n[5] OPÇÕES POR INSCRIÇÃO (regra de negócio: máximo 5)")
    dist_op = Counter(opcoes_por_inscricao.values())
    total_insc = len(opcoes_por_inscricao)
    for k in sorted(dist_op):
        marca = "  <<< ACIMA DA REGRA" if k > 5 else ""
        P(f"  {k} opções: {dist_op[k]:>7,} inscrições  {100*dist_op[k]/total_insc:>5.1f}%{marca}".replace(",", "."))
    acima = sum(v for k, v in dist_op.items() if k > 5)
    P(f"  → inscrições com mais de 5 opções: {acima:,} ({100*acima/total_insc:.2f}%)".replace(",", "."))

    P("\n[6] VALORES DO CAMPO 'opcao'")
    for v, n in sorted(opcao_valores.items(), key=lambda x: (len(x[0]), x[0])):
        marca = "  <<< FORA DE 1-5" if not (v.isdigit() and 1 <= int(v) <= 5) else ""
        P(f"  opcao={v:<4} {n:>8,}{marca}".replace(",", "."))

    P("\n[7] IDADE DA CRIANÇA NO ANO DO PROCESSO (creche = 0 a 3 anos)")
    for k in sorted(idade_anos, key=lambda x: (isinstance(x, str), x)):
        n = idade_anos[k]
        marca = ""
        if isinstance(k, int) and (k < 0 or k > 4):
            marca = "  <<< FORA DA FAIXA"
        P(f"  {str(k):>10} anos: {n:>8,}  {100*n/total:>5.1f}%{marca}".replace(",", "."))

    P("\n[8] DUPLICATAS DE GRÃO (mesma inscrição + mesma opção)")
    dups = {k: v for k, v in linhas_duplicadas.items() if v > 1}
    P(f"  chaves duplicadas: {len(dups):,}".replace(",", "."))
    P(f"  linhas excedentes: {sum(v-1 for v in dups.values()):,}".replace(",", "."))

    P("\n[9] CARDINALIDADE / DOMÍNIOS")
    P(f"  unidades distintas: {len(unidades):,}".replace(",", "."))
    P(f"  bairros distintos:  {len(bairros):,}".replace(",", "."))
    P(f"  horario: {dict(horario)}")
    P(f"  grupamentos distintos: {len(grupamento)}")
    for g, n in grupamento.most_common(12):
        P(f"    {g!r:<28} {n:>8,}".replace(",", "."))

    P("\n[10] BAIRROS — TOP 10 e ausências")
    for b, n in bairros.most_common(10):
        P(f"  {b:<28} {n:>8,}".replace(",", "."))

    # ---------------------------------------------------------------
    P("\n" + "=" * 78)
    P("HIPÓTESES DO PITCH")
    P("=" * 78)

    # H1 — multiplicidade: aluno confirma em 1 unidade, demais opções caem
    P("\n[H1] EFEITO MULTIPLICIDADE — quantas vagas cada criança trava")
    alunos_com_confirmado = 0
    vagas_travadas = 0
    travadas_por_ano = Counter()
    confirmados_por_ano = Counter()
    dist_travadas = Counter()
    multi_confirmado = 0
    for (aluno, ano), sits in aluno_ano_situacoes.items():
        conf = sits.get("Confirmado", 0)
        if conf >= 1:
            alumas = sum(sits.values())
            alunos_com_confirmado += 1
            confirmados_por_ano[ano] += 1
            excedente = alumas - 1  # a criança ocupa 1 vaga; as demais opções travaram
            vagas_travadas += excedente
            travadas_por_ano[ano] += excedente
            dist_travadas[alumas] += 1
            if conf > 1:
                multi_confirmado += 1

    P(f"  crianças com ao menos 1 'Confirmado': {alunos_com_confirmado:,}".replace(",", "."))
    P(f"  opções adicionais que essas crianças ocupavam: {vagas_travadas:,}".replace(",", "."))
    if alunos_com_confirmado:
        P(f"  média de opções por criança confirmada: {(vagas_travadas/alunos_com_confirmado)+1:.2f}")
    P(f"  ANOMALIA — crianças com mais de 1 'Confirmado' no mesmo ano: {multi_confirmado:,}".replace(",", "."))
    P("\n  vagas travadas por ano:")
    for ano in sorted(travadas_por_ano):
        P(f"    {ano}: {travadas_por_ano[ano]:>7,} travadas  ({confirmados_por_ano[ano]:,} crianças confirmadas)".replace(",", "."))

    # H2 — não comparecimento / falha na confirmação
    P("\n[H2] NÃO-COMPARECIMENTO — 'Cancelado na confirmacao'")
    ncf = situacao_geral.get("Cancelado na confirmacao", 0)
    P(f"  total de opções: {ncf:,} ({100*ncf/total:.1f}% de todas as linhas)".replace(",", "."))
    P("  por ano:")
    for ano in sorted(situacao_por_ano):
        n = situacao_por_ano[ano]["Cancelado na confirmacao"]
        conf = situacao_por_ano[ano]["Confirmado"]
        base_ = n + conf
        taxa = 100 * n / base_ if base_ else 0
        P(f"    {ano}: {n:>7,}  |  confirmadas {conf:>7,}  |  taxa de perda {taxa:>5.1f}%".replace(",", "."))

    # H2b — crianças que só têm cancelamento na confirmação (nunca matricularam)
    so_perdeu = 0
    for (aluno, ano), sits in aluno_ano_situacoes.items():
        if sits.get("Cancelado na confirmacao", 0) > 0 and sits.get("Confirmado", 0) == 0:
            so_perdeu += 1
    P(f"\n  crianças-ano que tiveram cancelamento na confirmação e NENHUMA matrícula: {so_perdeu:,}".replace(",", "."))
    P("  → é o universo de famílias que foram chamadas e ficaram sem a vaga.")

    # H3 — composição de situações dentro de uma inscrição
    P("\n[H3] PADRÕES DE DESFECHO POR INSCRIÇÃO (top 12 combinações)")
    padroes = Counter()
    for insc, sits in situacoes_por_inscricao.items():
        chave = " + ".join(f"{k}×{v}" for k, v in sorted(sits.items()))
        padroes[chave] += 1
    for p, n in padroes.most_common(12):
        P(f"  {n:>7,}  {p}".replace(",", "."))

    # ---------------------------------------------------------------
    # arquivo de resumo para as próximas etapas
    resumo = {
        "total_linhas": total,
        "total_inscricoes": total_insc,
        "unidades_distintas": len(unidades),
        "por_ano": dict(por_ano),
        "situacao_geral": dict(situacao_geral),
        "situacao_por_ano": {a: dict(c) for a, c in situacao_por_ano.items()},
        "vazios_por_coluna": {c: vazios[c] + nulos[c] for c in colunas},
        "opcoes_por_inscricao_dist": {str(k): v for k, v in dist_op.items()},
        "inscricoes_acima_de_5_opcoes": acima,
        "duplicatas_de_grao": len(dups),
        "h1_criancas_confirmadas": alunos_com_confirmado,
        "h1_vagas_travadas": vagas_travadas,
        "h1_travadas_por_ano": dict(travadas_por_ano),
        "h1_confirmados_por_ano": dict(confirmados_por_ano),
        "h1_anomalia_multi_confirmado": multi_confirmado,
        "h2_cancelado_na_confirmacao": ncf,
        "h2_por_ano": {a: situacao_por_ano[a]["Cancelado na confirmacao"]
                       for a in situacao_por_ano},
        "h2_criancas_sem_vaga_apos_chamada": so_perdeu,
        "idade_fora_da_faixa": sum(n for k, n in idade_anos.items()
                                   if isinstance(k, int) and (k < 0 or k > 4)),
    }
    destino = SAIDA / "perfil_querya.json"
    destino.write_text(json.dumps(resumo, ensure_ascii=False, indent=2), encoding="utf-8")
    P(f"\n✓ resumo salvo em {destino.relative_to(BASE)}")


if __name__ == "__main__":
    main()

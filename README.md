# Vaga Viva — Grupo 18

**Claude Impact Lab Rio 2** · Hackathon SME-Rio · 30/08/2026
Meliza Maia · Rodrigo Pita · Thiago Duque · Renata Ribeiro

Desafio: **Inteligência na Fila da Creche**. Rede pública com vagas ociosas e fila de espera ao mesmo tempo, sobre 5 anos de dados reais (2021–2025, 837 mil opções de inscrição, 872 unidades).

---

## A tese

A vaga vai a sorteio não porque ninguém foi chamado, mas porque **a família chamada não foi alcançada nem compreendeu a exigência a tempo**. O sorteio é o sintoma; a comunicação é a doença.

Os números saem da base oficial (ver [`03-etl/ACHADOS.md`](03-etl/ACHADOS.md)):

- **26,8%** das vagas oferecidas em 2025 se perderam na etapa de confirmação (era 49% em 2021)
- **44.041 crianças** foram chamadas em algum ano e ficaram sem nenhuma vaga
- **32.751 famílias** declararam estar no CadÚnico em 2025 e não conseguiram comprovar — critério que vale **51 dos ~100 pontos** da classificação, e que o poder público já registra
- **337.870 posições** ficaram ocupadas por crianças que se matricularam em outra unidade (a classificação roda por unidade, não por CPF)

---

## Estrutura

| Pasta | Conteúdo |
|---|---|
| `00-desafio/` | [`briefing.md`](00-desafio/briefing.md) (regras do hackathon), [`briefing-sme.md`](00-desafio/briefing-sme.md) (briefing oficial da SME), [`equipe-e-abordagem.md`](00-desafio/equipe-e-abordagem.md) (notas e diagramas do time), `imagens/` |
| `01-dados/` | [`sobre-os-dados.md`](01-dados/sobre-os-dados.md) — descrição da base oficial. Os dados brutos são clonados do repositório da SME e não versionados aqui |
| `02-projeto/` | [`PRD.md`](02-projeto/PRD.md) (requisitos) e [`PLANO.md`](02-projeto/PLANO.md) (plano de execução do dia) |
| `03-etl/` | Análise da base: scripts de perfilamento e [`ACHADOS.md`](03-etl/ACHADOS.md) com regras de limpeza e resultados |

## Reproduzir a análise

```bash
git clone https://github.com/CIT-SME-RJ/dadoscreche.git 01-dados/dadoscreche
python3 03-etl/01_perfil_querya.py      # perfil, outliers e hipóteses do funil de vaga
python3 03-etl/02_perfil_queryb.py      # comprovação documental cruzada com o desfecho
python3 03-etl/03_matriz_declaracao.py  # matriz declarou × confirmado, por critério e ano
```

Só biblioteca padrão do Python — sem pandas, sem instalação. A base inteira (837 mil + 4,36 milhões de linhas) roda em cerca de 30 segundos. Saídas em `03-etl/saida/`.

---

## Pendências da entrega

- [ ] Link da aplicação publicada
- [ ] Arquitetura da solução e como o Claude foi usado
- [ ] Vídeo demo de 60s

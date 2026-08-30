<<<<<<< HEAD
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
=======
# Vaga Viva — Trilho A: Dados (ETL + geração de texto)

Pipeline que lê as bases brutas da Inscrição Creche (SME-RJ, Claude Impact Lab
Rio) e produz agregados em `data/*.json` para o painel e a Ficha da Família
(HTML pré-renderizado com Jinja2), além dos textos reescritos em linguagem
simples via Claude API.

Toda a leitura pesada é feita em **DuckDB**; a QueryB (4,3M linhas) nunca é
carregada inteira em pandas — sempre agregada antes. As etapas 2→5/7 compartilham
um banco de build em `build/vagaviva.duckdb` (não versionado, reconstruível).

## Estrutura

```
etl/
  config.py                 # caminhos, constantes, faixa_posicao(), tipo_unidade()
  db.py                     # conexão com o banco de build
  01_validar_brutos.py      # validação + checagem das 9 armadilhas
  02_score.py               # tabela score (2025)
  03_fila.py                # tabela fila com posição/desempate
  04_funil.py               # funil simulado + 3 números do topo
  05_gerar_jsons.py         # painel.json, fila.json, fichas_exemplo.json
  06_gerar_copy.py          # copy.json (Claude API, só em build)
  07_vagas_oferecimento.py  # vagas.json + augmenta painel.json (join dos 2 formatos)
tests/                      # suíte pytest (42 testes)
data/                       # saídas agregadas (versionadas)
build/                      # banco DuckDB de build (git-ignored)
```

As bases brutas ficam **fora do repo** (grandes/sensíveis), em
`OferecimentosEvagas/` e `Bases IC_ ClassificadoseFila/` sob `VAGA_VIVA_RAW_DIR`.

## Como rodar

```bash
pip install -r requirements.txt          # duckdb, pandas, pyarrow, openpyxl, anthropic, dotenv, pytest
export VAGA_VIVA_RAW_DIR=/home/mmaia/dadoscreche   # onde estão as bases brutas

python etl/01_validar_brutos.py          # validação (não escreve nada)
python etl/02_score.py                   # tabela score (2025)
python etl/03_fila.py                    # tabela fila com posição/desempate
python etl/04_funil.py                   # funil simulado + 3 números do topo
python etl/05_gerar_jsons.py             # painel.json, fila.json, fichas_exemplo.json
python etl/07_vagas_oferecimento.py      # vagas.json + augmenta painel.json (após 05)

# Geração de texto — SÓ EM BUILD, nunca em runtime. Requer .env com ANTHROPIC_API_KEY.
python etl/06_gerar_copy.py              # copy.json (pares antes/depois)
```

## Testes

```bash
pytest -q                                # 42 testes, ~4s
```

- `tests/test_config.py` — funções puras (faixas de posição, tipo de unidade 7/5 díg, constantes).
- `tests/test_outputs.py` — invariantes dos `data/*.json` (funil consistente, faixas somam o tamanho da fila, nunca expõe posição exata, 18 textos no copy, cobertura do join).
- `tests/test_pipeline.py` — armadilhas e regras direto no DuckDB (situação sem acento, `opcao=6` fora da fila, dois formatos de unidade, score só 2025 e 0–100, posições contíguas, **desempate `pontos↓/data↑/ipl↑`**, consistência do funil).

## Saídas (`data/`)

| Arquivo | Conteúdo |
|---|---|
| `painel.json` | Três números do topo (req. 1.4); funil de vaga; cobertura; bloco de vagas ofertadas |
| `fila.json` | 822 filas (unidade × grupamento × horário) com posição em **faixa** (req. 2.12) |
| `fichas_exemplo.json` | Famílias-exemplo para a Ficha da Família |
| `vagas.json` | Vagas ofertadas (parceiras) e matrículas por unidade, via join dos 2 formatos |
| `copy.json` | 18 textos reescritos via Claude API (13 critérios + 5 mensagens), com antes/depois |

## Resultados 2025 (dados anonimizados — ver aviso)

**Três números do topo:** 16.345 famílias na lista de espera · 48.688 vagas
confirmadas · 17.838 vagas perdidas na confirmação.

**Funil de vaga:** ofertada/convocada 66.697 → confirmada 48.699 · expirada
17.838 · em análise 160 · reofertada 17.838. **Taxa de expiração ≈ 26,7%.**

**Cobertura:** 476 unidades com fila (244 públicas + 232 parceiras), 822 filas,
16.335 linhas na fila.

## Join dos dois formatos de unidade (etapa 7)

`etl/07_vagas_oferecimento.py` lê os `OferecimentosEvagas/*.xlsx` (openpyxl
`read_only`/`data_only`) e cruza com `QueryA.unidade` resolvendo os dois formatos:

- **7 dígitos = pública** → `zfill(7)` casa com `Designacao` (totalalunos): **488/488 (100%)**
- **5 dígitos = parceira** → `CRE(2) + últimos 3 do CÓDIGO SGA` casa com Parceiras: **343/348 (98,6%)**

As 5 parceiras não casadas estão ausentes do snapshot de maio/2025 (lacuna de dado,
não erro de join). Vagas ofertadas (`Meta`) só existem para parceiras; para públicas
o arquivo traz matrículas/turmas, não capacidade ofertada.

## ⚠️ Funil de convocação é SIMULADO

A base **não tem timestamp real de convocação/expiração**. O funil é
reconstruído a partir do **estado final** de cada opção (coluna `situacao` da
Query A, 2025), não de eventos datados. Mapeamento (ver `etl/04_funil.py`):

- `confirmada` = `Confirmado` + `Ativo`
- `expirada` = `Cancelado na confirmacao` (convocada, não confirmou no prazo)
- `em_analise` = `Selecionado` + `Selecionado da lista`
- `convocada` = `ofertada` = confirmada + expirada + em_analise
- `reofertada` = `expirada` (cada vaga expirada volta para a fila)

`Cancelado` e `Cancelado pelo sistema` ficam fora do funil de vaga (são
cancelamentos, não convocações).

## Régua de pontuação: só 2025

A régua mudou entre 2023 e 2024 (ex.: deficiência caiu de 100 → 25 pontos).
Todo o ETL roda **apenas sobre 2025** — pontuação nunca é cruzada entre anos.

## Armadilhas da base tratadas (confirmadas em `01_validar_brutos.py` e nos testes)

1. `situacao = 'Cancelado na confirmacao'` — **sem cedilha e sem til** (118.816 linhas; com acento = 0).
2. `04_UnidadesEscolaresComEndereco.csv` **não tem cabeçalho** — lido com `header=false`.
3. `unidade` tem dois formatos: **7 díg = pública**, **5 díg = parceira**. Tratada como STRING (nunca numérica) para não perder as 350 parceiras. Casa 872/872 com a Query D — que tem 80 `esc_codigo` duplicados, então o enriquecimento deduplica para 1 linha por unidade (senão o join infla a fila).
4. Funil simulado sobre o estado final (sem timestamp real) — ver acima.
5. Régua muda entre anos — só 2025.
6. Empates massivos (ex.: 95 famílias com 0 ponto na mesma fila) → posição exibida em faixa. Desempate: `pontos DESC, data_criacao ASC, ipl_id ASC`.
7. 2021 excluído de conferências (`confirmado` não é comparável entre anos) — irrelevante aqui, pois rodamos só 2025.
8. `opcao = 6` descartada (11 linhas, viola a regra de 5 opções).
9. Recorte territorial pela **unidade** (Query D), nunca pelo bairro declarado da família.

## Geração de texto

`etl/06_gerar_copy.py` usa a Claude API (`claude-opus-4-8`), lendo
`ANTHROPIC_API_KEY` do `.env` (nunca hardcoded; `.env` está no `.gitignore`).
System prompt: reescrever formulário público para mãe com baixa escolaridade —
frases de até 12 palavras, sem siglas, sem jargão, voz ativa, segunda pessoa.
É idempotente (cacheia pelo texto original) e roda **só em build**.

Exemplos (antes → depois):

- *"A criança é público-alvo da educação especial?"* → **"Sua filha ou seu filho tem deficiência?"**
- *"A criança pertence a família monoparental?"* → **"Você cria seu filho sozinha, sem a ajuda de um parceiro?"**

> Aviso: os dados são anonimizados e os indicadores ilustram a dinâmica do
> processo — **não representam a realidade**.
>>>>>>> origin/main

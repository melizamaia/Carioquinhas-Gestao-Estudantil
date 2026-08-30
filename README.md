<h1 align="center">Vaga Viva</h1>

<p align="center">
  <strong>Inteligência na Fila da Creche</strong><br>
  Grupo 18 · Claude Impact Lab Rio 2 · Hackathon SME-Rio · 30/08/2026
</p>

<p align="center">
  <a href="app/entrada.html"><img alt="protótipo" src="https://img.shields.io/badge/prot%C3%B3tipo-abre%20sem%20servidor-0B3B5C"></a>
  <img alt="python" src="https://img.shields.io/badge/python-DuckDB%20%2B%20pandas-3776AB">
  <img alt="testes" src="https://img.shields.io/badge/testes-42%20pytest-2E7D32">
  <a href="LICENSE"><img alt="licença" src="https://img.shields.io/badge/licen%C3%A7a-MIT-lightgrey"></a>
</p>

---

Sistema que acompanha a vaga de creche municipal do momento em que ela é oferecida
até a matrícula, e **devolve à fila toda vaga que trava sem decisão**.

Existe porque **uma em cada quatro vagas oferecidas se perde na etapa de confirmação** —
não por falta de vaga, e não porque ninguém foi chamado.

## A tese

A vaga vai a sorteio não porque ninguém foi chamado, mas porque **a família chamada
não foi alcançada nem compreendeu a exigência a tempo**. O sorteio é o sintoma;
a comunicação é a doença.

Os números saem da base oficial — 2021–2025, 837 mil opções de inscrição, 872 unidades
(memória de cálculo em [`03-etl/ACHADOS.md`](03-etl/ACHADOS.md)):

| | |
|---|---|
| **26,7%** | das vagas oferecidas em 2025 se perderam na etapa de confirmação (era 47,9% em 2022) |
| **44.041** | crianças foram chamadas em algum ano e ficaram sem nenhuma vaga |
| **32.751** | famílias declararam CadÚnico em 2025 e não comprovaram — critério que vale **51 dos ~100 pontos** e que o poder público **já registra** |
| **337.870** | posições ocupadas por crianças matriculadas em outra unidade — **2,76 por criança** (a classificação roda por unidade, não por CPF) |
| **90%** | das inscrições de 2025 tiveram a pontuação aceita **sem nenhum critério conferido** |

## A solução

Cinco telas, um ciclo. O vocabulário de cada peça está em [`CONTEXT.md`](CONTEXT.md) —
nenhum termo técnico chega à tela da família.

| Tela | Para quem | O que resolve |
|---|---|---|
| [`app/entrada.html`](app/entrada.html) | todos | Quem trabalha na Prefeitura entra com conta; quem está fora entra por link |
| [`app/painel.html?perfil=sme`](app/painel.html) | Secretaria | Os três números, o funil e as unidades que nunca conferiram uma inscrição |
| [`app/painel.html?perfil=cre`](app/painel.html) | Coordenadoria | O mesmo recorte, limitado ao território da CRE |
| [`app/painel.html?perfil=unidade`](app/painel.html) | Creche / EDI | Só as **exceções** do dia — quem respondeu que vai, some da tela |
| [`app/familia.html?token=demo-b`](app/familia.html) | Família | Ficha por link, com leitura em voz alta, prova de inscrição e decisão em dois passos |
| [`app/agente.html`](app/agente.html) | Agente comunitário | Acionamento territorial **no dia 1**, não depois das três tentativas falharem |

**Cascata** é a peça central: uma criança matriculada libera de uma vez todas as
posições que ocupava em outras unidades, e a próxima família é convocada na hora.

### Rodar a demonstração

Tudo abre com duplo clique, **sem servidor e sem build**:

```bash
xdg-open app/entrada.html      # ou index.html, que redireciona para lá
```

O roteiro de 90 segundos, os tokens de família e os quatro casos de borda
(`prazo_vencido`, `vaga_ocupada`, `ja_respondeu`, `confirmado`) estão em
[`DEMO.md`](DEMO.md).

## Arquitetura

```
bases brutas (fora do repo)          build (Python)                     runtime (sem servidor)
┌──────────────────────────┐   ┌──────────────────────────────┐   ┌────────────────────────┐
│ QueryA  837 mil linhas   │   │ etl/01 → 07   DuckDB         │   │ app/*.html             │
│ QueryB  4,36 mi linhas   ├──►│ agrega antes de virar pandas ├──►│ lê data/*.json         │
│ QueryD  unidades         │   │                              │   │ dados.js               │
│ Oferecimentos*.xlsx      │   │ etl/06  Claude API (só build)│   │                        │
└──────────────────────────┘   └──────────────────────────────┘   └────────────────────────┘
                                     build/vagaviva.duckdb              sql/policies.sql
                                     (não versionado)                  (RLS por perfil/território)
```

Três decisões que sustentam o resto:

1. **Nada de LLM em runtime.** A Claude API roda uma vez, em build, e o resultado
   é texto estático em `data/copy.json`. A família nunca espera um modelo responder.
2. **A leitura pesada é DuckDB.** A QueryB (4,3 milhões de linhas) nunca é carregada
   inteira em pandas — sempre agregada antes.
3. **O agregado histórico não vai para o banco.** Só o que muda enquanto alguém
   usa (convocação, tentativa, resposta) tem tabela em [`sql/policies.sql`](sql/policies.sql).

### Acesso

Duas formas de entrar, e não são o mesmo sistema com permissões diferentes:

| | Quem | Como |
|---|---|---|
| **Com conta** | SME · CRE · unidade | RLS por perfil e território |
| **Com link** | família · agente comunitário | token na URL, sem cadastro |

O agente cai no segundo grupo por razão institucional, não técnica: ACS é da
Secretaria de Saúde, CRAS é da Assistência Social — nenhum dos dois teria
credencial da Educação, nem em produção.

## Estrutura do repositório

| Pasta | Conteúdo |
|---|---|
| `00-desafio/` | [`briefing.md`](00-desafio/briefing.md) (regras do hackathon), [`briefing-sme.md`](00-desafio/briefing-sme.md) (briefing oficial da SME), [`equipe-e-abordagem.md`](00-desafio/equipe-e-abordagem.md), `imagens/` |
| `01-dados/` | [`sobre-os-dados.md`](01-dados/sobre-os-dados.md). Os dados brutos são clonados do repositório da SME e **não versionados** |
| `02-projeto/` | [`PRD.md`](02-projeto/PRD.md), [`PLANO.md`](02-projeto/PLANO.md), [`ROADMAP.md`](02-projeto/ROADMAP.md), [`CONTRATO-DADOS.md`](02-projeto/CONTRATO-DADOS.md), `mockup.html` |
| `03-etl/` | Análise exploratória da base + [`ACHADOS.md`](03-etl/ACHADOS.md) (regras de limpeza e resultados) |
| `etl/` | Pipeline de produção dos agregados (DuckDB) |
| `data/` | Saídas agregadas — **versionadas**, é o que o app lê |
| `app/` | As cinco telas, HTML/CSS/JS puro |
| `sql/` | Esquema de runtime e políticas de acesso |
| `tests/` | Suíte pytest (42 testes) |
| `build/` | Banco DuckDB de build (git-ignored, reconstruível) |

## Reproduzir

### Análise exploratória (só biblioteca padrão)

```bash
git clone https://github.com/CIT-SME-RJ/dadoscreche.git 01-dados/dadoscreche
python3 03-etl/01_perfil_querya.py       # perfil, outliers e hipóteses do funil de vaga
python3 03-etl/02_perfil_queryb.py       # comprovação documental cruzada com o desfecho
python3 03-etl/03_matriz_declaracao.py   # matriz declarou × confirmado, por critério e ano
python3 03-etl/04_distorcao_da_fila.py   # pontuação declarada × verificada
```

Sem pandas, sem instalação. A base inteira roda em ~30 segundos; saídas em `03-etl/saida/`.

### Pipeline de produção

```bash
pip install -r requirements.txt                     # duckdb, pandas, pyarrow, openpyxl, anthropic, dotenv, pytest
export VAGA_VIVA_RAW_DIR=/caminho/para/dadoscreche  # onde estão as bases brutas

python etl/01_validar_brutos.py          # validação + checagem das 9 armadilhas (não escreve nada)
python etl/02_score.py                   # tabela score (2025)
python etl/03_fila.py                    # tabela fila com posição/desempate
python etl/04_funil.py                   # funil simulado + 3 números do topo
python etl/05_gerar_jsons.py             # painel.json, fila.json, fichas_exemplo.json
python etl/07_vagas_oferecimento.py      # vagas.json + augmenta painel.json (depois do 05)
```

Geração de texto, **só em build** — requer `.env` com `ANTHROPIC_API_KEY`
(ver [`.env.example`](.env.example)):

```bash
python etl/06_gerar_copy.py              # copy.json (pares antes/depois)
```

As bases brutas ficam **fora do repo** (grandes e sensíveis), em
`OferecimentosEvagas/` e `Bases IC_ ClassificadoseFila/` sob `VAGA_VIVA_RAW_DIR`.

### Testes

```bash
pytest -q                                # 42 testes, ~4s
```

- [`tests/test_config.py`](tests/test_config.py) — funções puras: faixas de posição, tipo de unidade (7/5 dígitos), constantes.
- [`tests/test_outputs.py`](tests/test_outputs.py) — invariantes dos `data/*.json`: funil consistente, faixas somam o tamanho da fila, **nunca expõe posição exata**, 18 textos no copy, cobertura do join.
- [`tests/test_pipeline.py`](tests/test_pipeline.py) — armadilhas e regras direto no DuckDB: situação sem acento, `opcao=6` fora da fila, dois formatos de unidade, score só 2025 e 0–100, posições contíguas, desempate `pontos↓ / data↑ / ipl↑`.

## Saídas (`data/`)

| Arquivo | Conteúdo |
|---|---|
| `painel.json` | Três números do topo; funil de vaga; cobertura; bloco de vagas ofertadas |
| `fila.json` | 822 filas (unidade × grupamento × horário), posição sempre em **faixa** |
| `fichas_exemplo.json` | Famílias-exemplo para a Ficha da Família |
| `vagas.json` | Vagas ofertadas (parceiras) e matrículas por unidade, via join dos 2 formatos |
| `convocacoes.json` · `unidades.json` · `indicadores.json` | Estado de demonstração das telas |
| `copy.json` | 18 textos reescritos via Claude API (13 critérios + 5 mensagens), com antes/depois |

### Resultados 2025

**Três números do topo:** 16.345 famílias na lista de espera · 48.688 vagas
confirmadas · 17.838 vagas perdidas na confirmação.

**Funil de vaga:** ofertada/convocada 66.697 → confirmada 48.699 · expirada 17.838 ·
em análise 160 · reofertada 17.838. **Taxa de expiração 26,7%.**

**Cobertura:** 476 unidades com fila (244 públicas + 232 parceiras), 822 filas,
16.335 linhas na fila.

## Como o Claude foi usado

**Em build, no produto:** [`etl/06_gerar_copy.py`](etl/06_gerar_copy.py) usa a Claude API
(`claude-opus-4-8`) para reescrever o formulário público em linguagem simples — frases de
até 12 palavras, sem siglas, sem jargão, voz ativa, segunda pessoa. É idempotente (cacheia
pelo texto original) e a chave vem do `.env`, nunca hardcoded.

- *"A criança é público-alvo da educação especial?"* → **"Sua filha ou seu filho tem deficiência?"**
- *"A criança pertence a família monoparental?"* → **"Você cria seu filho sozinha, sem a ajuda de um parceiro?"**

**No processo:** Claude Code para o perfilamento das duas bases (é dele o achado das
armadilhas listadas abaixo), a suíte de testes e a modelagem de RLS.

## Notas metodológicas

Ditas antes de perguntarem — as mesmas notas aparecem na tela do painel.

<details>
<summary><strong>⚠️ O funil de convocação é SIMULADO</strong></summary>

A base **não tem timestamp real de convocação/expiração**. O funil é reconstruído a
partir do **estado final** de cada opção (coluna `situacao` da Query A, 2025), não de
eventos datados. Mapeamento (ver [`etl/04_funil.py`](etl/04_funil.py)):

- `confirmada` = `Confirmado` + `Ativo`
- `expirada` = `Cancelado na confirmacao` (convocada, não confirmou no prazo)
- `em_analise` = `Selecionado` + `Selecionado da lista`
- `convocada` = `ofertada` = confirmada + expirada + em_analise
- `reofertada` = `expirada` (cada vaga expirada volta para a fila)

`Cancelado` e `Cancelado pelo sistema` ficam **fora** do funil de vaga — são
cancelamentos, não convocações.
</details>

<details>
<summary><strong>Régua de pontuação: só 2025</strong></summary>

A régua mudou entre 2023 e 2024 (ex.: deficiência caiu de 100 → 25 pontos). Todo o ETL
roda **apenas sobre 2025**; pontuação nunca é cruzada entre anos.
</details>

<details>
<summary><strong>Join dos dois formatos de unidade</strong></summary>

[`etl/07_vagas_oferecimento.py`](etl/07_vagas_oferecimento.py) lê os
`OferecimentosEvagas/*.xlsx` (openpyxl `read_only`/`data_only`) e cruza com
`QueryA.unidade` resolvendo os dois formatos:

- **7 dígitos = pública** → `zfill(7)` casa com `Designacao`: **488/488 (100%)**
- **5 dígitos = parceira** → `CRE(2) + últimos 3 do CÓDIGO SGA` casa com Parceiras: **343/348 (98,6%)**

As 5 parceiras não casadas estão ausentes do snapshot de maio/2025 — lacuna de dado, não
erro de join. Vagas ofertadas (`Meta`) só existem para parceiras; para públicas o arquivo
traz matrículas/turmas, não capacidade ofertada.
</details>

<details>
<summary><strong>As 9 armadilhas da base, e o que fizemos com cada uma</strong></summary>

Confirmadas em [`etl/01_validar_brutos.py`](etl/01_validar_brutos.py) e travadas nos testes.

1. `situacao = 'Cancelado na confirmacao'` — **sem cedilha e sem til** (118.816 linhas; com acento = 0).
2. `04_UnidadesEscolaresComEndereco.csv` **não tem cabeçalho** — lido com `header=false`.
3. `unidade` tem dois formatos: **7 díg = pública**, **5 díg = parceira**. Tratada como STRING (nunca numérica) para não perder as 350 parceiras. Casa 872/872 com a Query D — que tem 80 `esc_codigo` duplicados, então o enriquecimento deduplica para 1 linha por unidade (senão o join infla a fila).
4. Funil simulado sobre o estado final, sem timestamp real.
5. Régua muda entre anos — só 2025.
6. Empates massivos (ex.: 95 famílias com 0 ponto na mesma fila) → posição exibida em **faixa**. Desempate: `pontos DESC, data_criacao ASC, ipl_id ASC`.
7. 2021 excluído de conferências (`confirmado` não é comparável entre anos).
8. `opcao = 6` descartada (11 linhas, viola a regra de 5 opções).
9. Recorte territorial pela **unidade** (Query D), nunca pelo bairro declarado da família.
</details>

> **Aviso:** os dados são anonimizados e os indicadores ilustram a dinâmica do
> processo — **não representam a realidade**.

## Equipe

| | Nome | GitHub |
|---|---|---|
| <img src="https://github.com/melizamaia.png" width="48" height="48" alt=""> | **Meliza Maia** | [@melizamaia](https://github.com/melizamaia) |
| <img src="https://github.com/ribeirore.png" width="48" height="48" alt=""> | **Renata Ribeiro** | [@ribeirore](https://github.com/ribeirore) |
| <img src="https://github.com/rodrigorrpita-coder.png" width="48" height="48" alt=""> | **Rodrigo Pita** | [@rodrigorrpita-coder](https://github.com/rodrigorrpita-coder) |
| <img src="https://github.com/Duque455.png" width="48" height="48" alt=""> | **Thiago Duque** | [@Duque455](https://github.com/Duque455) |

## Pendências da entrega

- [ ] Link da aplicação publicada
- [ ] Vídeo demo de 60s

## Licença

[MIT](LICENSE).

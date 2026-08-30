# Achados da análise exploratória — Query A, B e C

Rodado em 30/08, sobre a base oficial (837.179 opções de inscrição, 4.357.119 respostas, 2021–2025).
Scripts: `01_perfil_querya.py`, `02_perfil_queryb.py`, `03_matriz_declaracao.py`. Saídas em `saida/`.

---

## 1. Regras de limpeza (aplicar antes de qualquer número)

| # | Problema | Tamanho | Decisão |
|---|---|---|---|
| L1 | **O campo `confirmado` de 2021 não é comparável com os demais anos** | taxa de comprovação 88,9% em 2021 contra 10,8% em 2022 | **Excluir 2021** de toda análise de comprovação documental. Série confiável: 2022–2025 |
| L2 | Inscrições com mais de 5 opções (viola a regra do processo) | 5 inscrições, 11 linhas com `opcao=6` | Descartar as linhas de `opcao=6` |
| L3 | Crianças com mais de um `Confirmado` no mesmo ano | 741 casos | Sinalizar, **não tratar como dupla matrícula**. O briefing da SME avisa que, sem CPF/DNV/NIS, a anonimização agrupa por nome + data de nascimento e pode fundir crianças diferentes sob o mesmo código. Parte desses 741 é colisão de identidade, não vaga duplicada |
| L4 | Data de nascimento posterior ao processo | 3 registros (idade −3) | Descartar |
| L5 | `CEP` e `bairro` vazios | 23.6k linhas (2,8%) | Manter, mas excluir de recortes territoriais |
| L6 | Campo `bairro` com 1.367 valores distintos (o Rio tem ~164 bairros oficiais) | — | Normalizar por unidade escolar, não por bairro declarado |
| L7 | Régua de pontuação reescrita entre 2023 e 2024 | das 13 perguntas de 2023, só 3 seguem em 2024 | Nunca montar série temporal de pontuação sem normalizar |

**Não há duplicata de grão** (mesma inscrição + mesma opção): 0 ocorrências. A chave `(ano, prm_id, plm_id, ipl_id, opcao)` é limpa.
**Não há nulo** em nenhuma coluna crítica — só `CEP` e `bairro`.

---

## 2. O que a base confirma

### 2.1 A vaga é oferecida e a família não completa a confirmação

Situação `Cancelado na confirmacao` — a vaga foi para a família e não virou matrícula:

| Ano | Perdidas na confirmação | Confirmadas | **Taxa de perda** |
|---|---:|---:|---:|
| 2021 | 27.992 | 29.166 | **49,0%** |
| 2022 | 32.046 | 34.893 | **47,9%** |
| 2023 | 22.031 | 28.329 | **43,7%** |
| 2024 | 18.909 | 51.494 | **26,9%** |
| 2025 | 17.838 | 48.688 | **26,8%** |

**44.041 crianças** foram chamadas em algum ano e terminaram sem nenhuma vaga porque a confirmação não se completou.

O problema melhorou (49% → 27%) e continua enorme: **uma em cada quatro vagas oferecidas ainda se perde na etapa de confirmação.**

### 2.2 Efeito multiplicidade — a classificação roda por unidade, não por CPF

- 191.741 crianças com matrícula confirmada
- ocupavam **337.870 opções adicionais** em outras unidades
- média de **2,76 posições por criança matriculada**

O padrão aparece cru: 24.380 inscrições terminam exatamente em `Cancelado pelo sistema × 4 + Confirmado × 1` — a criança pega uma vaga e o sistema derruba as outras quatro.

*Ressalva honesta:* a base não tem timestamp de cancelamento, só a data de criação da inscrição. Podemos afirmar **quantas posições foram ocupadas**, não por quantos dias.

### 2.3 A fila é ordenada por autodeclaração que ninguém confere

**Este é o achado central do projeto.** Ele corrige uma leitura anterior nossa: não é que as
famílias tentam comprovar e falham — é que **a comprovação não acontece**.

Distribuição da confirmação por inscrição, 2025 (71.930 inscrições):

| Situação | Inscrições | % |
|---|---:|---:|
| **Nenhum critério confirmado** | 64.675 | **89,9%** |
| **Todos os 13 critérios confirmados de uma vez** | 4.894 | 6,8% |
| Confirmação parcial (conferência real, critério a critério) | 2.361 | 3,3% |

Um número quase idêntico de confirmações aparece em perguntas sem nenhuma relação entre si
— refugiado (5.254), deficiência (5.140), monoparental (4.590), ex-presidiário (5.001).
Validação real por critério não produz isso. É **marcação em bloco**: o campo `confirmado`
não registra "este critério foi validado", registra "esta inscrição passou por conferência".
E 9 em cada 10 nunca passaram.

Isso bate com o que a SME informou no briefing: **não há validação das informações dadas para
pontuação, não é possível anexar documento na inscrição online, e a régua é redefinida a cada
processo seletivo.**

**Consequência:** a pontuação que ordena a fila de 45 mil crianças é autodeclarada, não
anexável e não verificada em 90% dos casos. Isso produz dois erros ao mesmo tempo:

1. **É trivial de fraudar.** Marcar "Sim" em tudo não custa nada e não é checado. Quem entende
   o jogo sobe na fila.
2. **A vulnerabilidade real não é capturada.** Quem não entende o formulário marca "Não" e
   afunda, mesmo tendo direito ao ponto — e é exatamente a população de baixo letramento que
   a política pretende priorizar.

Some-se a régua que muda todo ano (das 13 perguntas de 2023, só 3 sobrevivem em 2024; o
CadÚnico salta de 25 para 51 pontos entre 2024 e 2025): a família não tem como aprender o
processo, porque o processo não se repete.

**O CadÚnico é a prova da saída.** Vale 51 dos ~100 pontos em 2025, 35.141 famílias o
declararam, e é um registro que o poder público **já possui** — acessível pelo Registro
Municipal Integrado. Não há razão para perguntar à família algo que o Estado já sabe.

---

### 2.4 Volume declarado (leitura antiga, mantida como referência)

Matriz declarou × comprovou, por ano (2021 excluído por L1):

| Ano | Declarou e comprovou | **Declarou e NÃO comprovou** | Taxa de comprovação |
|---|---:|---:|---:|
| 2022 | 4.214 | 34.885 | 10,8% |
| 2023 | 3.840 | 40.066 | 8,7% |
| 2024 | 12.098 | **140.268** | 7,9% |
| 2025 | 10.519 | **121.155** | 8,0% |

**Recorte do CadÚnico — o critério que vale 51 dos ~100 pontos em 2025:**

| Ano | Peso | Declararam | Comprovaram | **Perderam o critério** | Taxa |
|---|---:|---:|---:|---:|---:|
| 2024 | 25 pt | 38.234 | 2.949 | **35.285** | 7,7% |
| 2025 | 51 pt | 35.141 | 2.390 | **32.751** | 6,8% |

**Atenção à interpretação.** Estas colunas medem volume declarado, não capacidade de comprovar.
À luz de 2.3, "declarou e não comprovou" significa **"declarou e ninguém conferiu"** — não
"tentou provar e falhou". Usar estes números com a redação antiga cai na primeira pergunta do
jurado. O que se pode afirmar: em 2025, 35.141 famílias declararam CadÚnico e 32.751 dessas
declarações seguiram sem qualquer verificação, num critério que vale metade da pontuação.

---

### 2.5 A conferência depende de qual creche a família escolheu

Taxa de conferência por unidade de 1ª opção, 2025 (556 unidades com ao menos 50 inscrições):

| | Taxa |
|---|---:|
| CM RAÍZES DO SALGUEIRO | 90,6% |
| CM VIDIGAL | 86,4% |
| CP CRECHE COMUNITÁRIA MUNDO MÁGICO | 78,9% |
| ... | |
| CM TIA AUTA · CM DIREITOS HUMANOS · CP CRECHE GIZ COLORIDO | **0,0%** |

**48 das 556 unidades não conferiram uma única inscrição.**

Por bairro da unidade, a distância é de 27 vezes:

| Bairro | Taxa | Inscrições |
|---|---:|---:|
| Penha | 32,5% | 612 |
| Pedra de Guaratiba | 28,6% | 273 |
| Méier | 25,7% | 303 |
| ... | | |
| Jardim América | 1,8% | 493 |
| **Higienópolis** | **1,2%** | 325 |

Duas famílias com a mesma situação social têm chances completamente diferentes de ter o
critério conferido — e a variável que decide é **em qual creche elas clicaram**. Não há
padrão de renda óbvio: as maiores taxas aparecem em creches comunitárias e de favela
(Salgueiro, Vidigal), o que sugere prática local da unidade, não política de rede.

### 2.6 Matricula-se sem nenhum critério conferido

Desfecho por grupo de conferência, 2025:

| Grupo | Inscrições | Matriculou | Pontuação declarada média |
|---|---:|---:|---:|
| Nunca conferida | 64.675 | **66,8%** | 28,2 |
| Conferida em bloco | 4.894 | 73,3% | 18,4 |
| Conferida em parte | 2.361 | 80,0% | 32,4 |

**43.205 crianças se matricularam em 2025 sem que nenhum dos critérios que as classificou
fosse conferido.** A conferência não é pré-requisito da matrícula em nenhum momento do fluxo.

### 2.7 A distância entre o declarado e o verificado

| | Pontos (de 100) |
|---|---:|
| Pontuação média **declarada** | **27,7** |
| Pontuação média **verificada** | **7,9** |

**35.141 inscrições reivindicam 51 pontos ou mais** — metade ou mais da régua. Dessas,
**32.347 (92%) não tiveram nenhuma conferência.**

> **Ressalva metodológica.** O script também compara a ordem da fila declarada com a ordem
> verificada e encontra deslocamento mediano de 18.208 posições. **Não usar esse número no
> pitch:** como 90% das inscrições têm pontuação verificada zero, o ranking "verificado" é
> quase todo empate, e o deslocamento é em boa parte artefato do desempate. Os números
> sólidos são a média declarada × verificada e o recorte dos 51+ pontos.

---

## 3. O que a base NÃO confirma — e não vamos afirmar

**Não comprovar o critério não reduz a chance de matrícula de forma relevante.** Cruzamento feito:

| Capacidade de comprovar | Taxa de matrícula | n |
|---|---:|---:|
| Comprovou tudo | 63,6% | 37.820 |
| Comprovou em parte | 68,9% | 2.767 |
| Não comprovou nada | 61,3% | 157.389 |

Diferença de 2,3 pontos. **Não existe base para dizer "quem não comprova perde a vaga".**

A leitura correta é outra: não comprovar é a **norma** (157 mil contra 38 mil), então a falha documental não elimina ninguém — ela **desordena a fila inteira**. A classificação deixa de medir vulnerabilidade e passa a medir capacidade de navegar a burocracia. Isso é o que vamos afirmar, e só isso.

Também **não sai da base**: dias de vaga ociosa (não há timestamp de convocação nem de expiração), motivo do não-comparecimento, e qualquer dado de professor ou material.

**Capacidade instalada — correção.** Existe dado de lotação (aluno/turma em `totaalunoscreche`, vagas em `Parceiras`), mas é monitoramento mensal, com defasagem de ~1 mês e origem distinta da base de inscrição: não fecha com o grão da fila. O módulo de recursos fica fora **por decisão de escopo, não por ausência de dado** — e é assim que se responde ao júri.

---

## 4. Consequência para o produto

1. **O número de abertura do pitch** é a taxa de perda na confirmação: *uma em cada quatro vagas oferecidas se perde porque a família não completa a confirmação — 44.041 crianças chamadas ficaram sem vaga.*
2. **O número que explica a causa** é a ausência de verificação: *90% das inscrições de 2025 tiveram a pontuação aceita sem que nenhum critério fosse conferido. A fila é ordenada por um formulário que ninguém checa e cuja régua muda todo ano.*
3. **O número da ineficiência estrutural** é a multiplicidade: *cada criança matriculada ocupava 2,76 posições.*
4. O módulo de recursos continua fora — **por decisão de escopo**, não por ausência de dado (ver seção 3).

**A virada de produto que estes achados exigem:** parar de pedir à família que declare o que o
Estado já sabe. O CadÚnico vale 51 pontos e está no Registro Municipal Integrado. Puxar o dado
na origem resolve os dois erros com uma medida só — fecha a porta da fraude *e* remove a
barreira de letramento, porque a família deixa de precisar entender a pergunta para receber o
ponto a que tem direito.

A tela da família muda de acordo: em vez de perguntar *"você está no CadÚnico?"*, ela informa
*"encontramos seu Cadastro Único — você tem 51 pontos"*, e pede confirmação apenas do que não
puder ser verificado na origem.

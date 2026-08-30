# PRD — Vaga Viva

**Grupo 18** · Claude Impact Lab Rio 2 · 30/08/2026
Meliza Maia · Rodrigo Pita · Thiago Duque · Renata Ribeiro

> Versão 2 — reescrita após a análise exploratória da base. O que mudou: a tese saiu de
> "a família não consegue comprovar" para "**ninguém confere, e a régua muda todo ano**".
> Evidência em [`03-etl/ACHADOS.md`](../03-etl/ACHADOS.md).

---

## 1. O problema

A rede municipal do Rio tem vaga ociosa em creche e fila de espera ao mesmo tempo. Cinco anos
de dados (2021–2025), 837 mil opções de inscrição, 872 unidades, 45 mil famílias por processo.

O diagnóstico corrente é que falta um algoritmo de alocação. Não é o caso. O que a base mostra
são três falhas encadeadas.

### a) A fila é ordenada por um formulário que ninguém confere

A pontuação que define a ordem de 45 mil crianças é **autodeclarada**. A inscrição online **não
aceita anexo**. E a verificação, na prática, não acontece: em 2025, **89,9% das inscrições não
tiveram nenhum critério conferido**. Das que tiveram, a maioria foi carimbada em bloco — todos
os 13 critérios de uma vez — e não critério a critério.

Isso produz dois erros ao mesmo tempo, em direções opostas:

- **É trivial fraudar.** Marcar "Sim" em tudo não custa nada e não é checado. Quem entende o
  jogo sobe na fila.
- **A vulnerabilidade real não é capturada.** Quem não entende o formulário marca "Não" e
  afunda, mesmo tendo direito ao ponto. É exatamente a população de baixo letramento que a
  política existe para priorizar.

Some-se a régua reescrita a cada processo seletivo: das 13 perguntas de 2023, apenas 3
sobrevivem em 2024, e o CadÚnico salta de 25 para 51 pontos entre 2024 e 2025. **A família não
tem como aprender o processo, porque o processo não se repete.**

E quando a conferência acontece, ela é uma loteria territorial: a taxa varia de **32,5% na
Penha a 1,2% em Higienópolis**, e **48 de 556 unidades não conferiram uma única inscrição**.
A variável que decide se a família é conferida é **em qual creche ela clicou**. O resultado
final: **43.205 crianças se matricularam em 2025 sem que nenhum dos critérios que as
classificou fosse conferido** — a pontuação média declarada é 27,7 de 100, a verificada é 7,9.

### b) A convocação perde uma em cada quatro vagas oferecidas

Quando a vaga finalmente chega à família, ela se perde na etapa de confirmação em **26,8% dos
casos (2025)** — era 49% em 2021. **44.041 crianças** foram chamadas em algum ano e terminaram
sem nenhuma vaga porque a confirmação não se completou.

O contato é manual: uma tentativa por dia, três dias, telefone/e-mail/WhatsApp/SMS. Contatos
desatualizados, nenhum rastro, nenhuma visibilidade de quantas vagas estão paradas agora.

### c) Cada criança trava várias vagas ao mesmo tempo

A classificação roda **por unidade, não por CPF**. As 191.741 crianças matriculadas ocupavam
**337.870 posições adicionais** em outras unidades — 2,76 posições por criança. O padrão
aparece cru na base: 24.380 inscrições terminam em `Cancelado pelo sistema × 4 + Confirmado × 1`.

### A oportunidade

O critério mais pesado de 2025 — CadÚnico, **51 dos ~100 pontos** — é um registro que o poder
público **já possui**, acessível pelo Registro Municipal Integrado. Não há razão para perguntar
à família algo que o Estado já sabe.

**Puxar o dado na origem fecha a porta da fraude e remove a barreira de letramento com uma
única medida.** Essa é a espinha dorsal do produto.

---

## 2. Quem usa

Quatro perfis, com hierarquia de acesso. Cada um enxerga o mínimo necessário para agir — não é
detalhe de implementação, é requisito de LGPD e do desenho institucional.

| Perfil | Quem é | Escopo de dados | O que faz |
|---|---|---|---|
| **SME** | Secretaria, nível rede | 872 unidades, todas as CREs | Enxerga ociosidade e distorção da fila, prioriza |
| **CRE** | Coordenadoria Regional | Só as unidades do seu território | Acompanha fila e vagas paradas da região |
| **Unidade** | Diretora/secretária da creche ou EDI | Só a própria unidade | Registra contato, confere o que falta, confirma matrícula, escala |
| **Família** | Responsável pela criança | Só a própria inscrição | Vê pontuação, posição, prazo, o que levar; confirma |

**Regra de minimização:** a unidade vê nome, responsável, contato, prazo e pendências. **Não vê**
os critérios sensíveis declarados (violência doméstica, uso de drogas no núcleo familiar,
familiar ex-presidiário). Esses ficam na SME, que é quem valida na origem.

---

## 3. A solução

Três módulos sobre uma camada de acesso.

### Módulo 1 — Painel de vaga (gestor)

Cada vaga convocada é um card com estado e relógio:

```
Ofertada → Convocada → Aguardando família (3 dias) →
Conferida → Matriculada
          ↘ Expirada → Escalada → Reofertada
```

Mostra o rastro das tentativas de contato, dias restantes, e o que falta. Semáforo por urgência.
A mesma tela, filtrada pelo escopo do perfil.

**Indicador novo, vindo da análise:** *distorção da fila* — quanto a ordem atual difere da ordem
que existiria se a pontuação fosse verificada na origem.

### Módulo 2 — Ficha da Família ← **o diferencial**

Substitui o formulário autodeclarado por uma ficha que **já chega preenchida com o que o Estado
sabe**, e pergunta apenas o que não pode ser verificado na origem.

Inverte a pergunta:

| Hoje | Proposta |
|---|---|
| "Sua família está inscrita no CadÚnico?" | "Encontramos seu Cadastro Único. **Você tem 51 pontos.**" |
| "A criança tem alguma deficiência?" | "O sistema de saúde confirma este critério. Nada a fazer." |
| *(sem anexo possível)* | "Falta só isto: **foto da certidão de nascimento**." |

E comunica em linguagem que quem lê pouco consegue usar: uma informação por bloco, botão de
ouvir em voz alta, checklist com ícone grande, prazo em dia da semana, um único botão de ação.

### Módulo 3 — Escalada comunitária

Quando as três tentativas de contato falham, a vaga **não vai direto para reoferta**. Entra em
escalada: busca ativa pela rede local do território (CRAS, agente comunitário de saúde, unidade
de saúde da família), via as microáreas da SME. A vaga só passa adiante depois que a família foi
comprovadamente alcançada.

---

## 4. Requisitos

**P0** entra hoje · **P1** se der tempo · **P2** documentado como próximo passo.

### Painel de vaga

| # | Requisito | Prio |
|---|---|---|
| 1.1 | Vagas convocadas como cards, com estado e dias restantes | P0 |
| 1.2 | Semáforo (verde ≥2 dias, amarelo 1 dia, vermelho vence hoje/venceu) | P0 |
| 1.3 | Filtro por CRE e por unidade | P0 |
| 1.4 | Três números no topo, calculados da base real | P0 |
| 1.5 | Indicador de distorção da fila (declarado × verificável) | P1 |
| 1.6 | Rastro das tentativas de contato no card | P1 |
| 1.7 | Registrar nova tentativa / marcar item conferido | P1 |
| 1.8 | Agrupamento "vence amanhã" no topo | P2 |

### Ficha da Família

| # | Requisito | Prio |
|---|---|---|
| 2.1 | Tela sem login, por link com token da inscrição | P0 |
| 2.2 | Blocos na ordem: pontuação → vaga → prazo → o que falta → ação | P0 |
| 2.3 | **Critérios já verificados na origem vêm marcados, sem pergunta** | P0 |
| 2.4 | Botão "ouvir" lendo a página em voz alta em pt-BR (Web Speech API) | P0 |
| 2.5 | Checklist do que falta, com ícone por item | P0 |
| 2.6 | Prazo em dia da semana + data + contagem ("faltam 2 dias — até sexta, 5 de setembro") | P0 |
| 2.7 | Botão único de confirmação | P0 |
| 2.8 | Envio de foto do documento pelo celular (resolve o "não dá para anexar") | P1 |
| 2.9 | Endereço da creche com botão de abrir no mapa | P1 |
| 2.10 | "Não vou conseguir ir" — aciona a unidade em vez de perder a vaga em silêncio | P1 |
| 2.11 | Versão imprimível de 1 página para o agente comunitário levar na mão | P2 |

### Escalada comunitária

| # | Requisito | Prio |
|---|---|---|
| 3.1 | Botão "Escalar", habilitado após 3 tentativas registradas | P0 |
| 3.2 | Mostrar o território/microárea de destino do encaminhamento | P0 |
| 3.3 | Estado "Em escalada" no funil, distinto de "Expirada" | P0 |
| 3.4 | Registro de quem escalou e quando | P1 |

### Hierarquia de acesso

| # | Requisito | Prio |
|---|---|---|
| 4.1 | Seletor de perfil que refiltra a tela de verdade | P0 |
| 4.2 | Critérios sensíveis ocultos no perfil Unidade | P0 |
| 4.3 | Políticas RLS escritas e versionadas em `sql/policies.sql` | P0 |
| 4.4 | RLS aplicada no Supabase | P1 |
| 4.5 | SSO pelo Registro Municipal Integrado | P2 — documentado |

---

## 5. A régua de linguagem e acessibilidade

Requisito de produto, não preferência de estilo. Tela da família que quebre uma destas regras
volta para reescrita.

**Linguagem**
- Frase de no máximo 12 palavras
- Zero siglas — nenhuma, nem CRE, nem EDI, nem SME
- Zero jargão: não existe "convocação", "deferimento", "comprovação de critério", "dias úteis",
  "unidade escolar". Vira: "vaga", "você conseguiu", "leve estes papéis", "até sexta, dia 5", "creche"
- Voz ativa, segunda pessoa, imperativo na ação
- Números em algarismo

**Visual**
- Corpo a partir de 20px, título a partir de 32px
- Alvo de toque mínimo de 48px
- Contraste mínimo 7:1 (AAA)
- Uma ação por tela — nunca dois botões concorrendo
- Ícone sempre com palavra ao lado
- Sem scroll horizontal, sem modal, sem tooltip, sem hover como única pista

**Técnico**
- Funciona em Android 8, tela de 360px, 3G
- Página abaixo de 200KB
- Conteúdo essencial legível sem JavaScript
- Áudio pela Web Speech API nativa — sem biblioteca, sem API paga

**Teste de aceitação:** uma pessoa de fora lê a tela uma vez e diz, sem ajuda, para onde ir, até
quando, e o que levar. Se precisa reler ou perguntar, a tela falhou.

---

## 6. Dados e métricas

Fonte: `github.com/CIT-SME-RJ/dadoscreche` — UTF-8 com BOM, separador `;`, unidades sem cabeçalho.
Perfilamento completo e regras de limpeza em [`03-etl/ACHADOS.md`](../03-etl/ACHADOS.md).

### Os três números do topo

1. **Uma em cada quatro vagas oferecidas se perde na confirmação** (26,8% em 2025; 49% em 2021).
   44.041 crianças chamadas ficaram sem vaga.
2. **90% das inscrições de 2025 tiveram a pontuação aceita sem nenhuma conferência.** A fila é
   ordenada por um formulário que ninguém checa e cuja régua muda todo ano.
3. **Cada criança matriculada ocupava 2,76 posições** — 337.870 vagas travadas por multiplicidade.

### Regras de limpeza obrigatórias

| Regra | Efeito |
|---|---|
| **Excluir 2021** de qualquer análise de conferência | O campo `confirmado` de 2021 não é comparável (88,9% contra 10,8% em 2022) |
| Descartar `opcao = 6` | 11 linhas, viola a regra de 5 opções |
| Não chamar as 741 duplas de "matrícula duplicada" | Parte é colisão de anonimização (nome + data de nascimento) |
| Recorte territorial pela unidade, nunca pelo bairro declarado | 1.367 valores distintos num município de ~164 bairros |
| Nunca cruzar pontuação entre anos sem normalizar | Régua reescrita entre 2023 e 2024 |

### O que não medimos, e por quê

Não há dado de professor, material ou capacidade instalada — por isso **não existe módulo de
recursos**. Não há timestamp de convocação ou expiração — por isso **não afirmamos "dias de vaga
ociosa"**, apenas quantas posições foram ocupadas. Não há base para dizer que quem não comprova
perde a vaga: a taxa de matrícula é 61,3% para quem não teve nada conferido e 63,6% para quem
teve tudo. **A falha documental não elimina ninguém — ela desordena a fila inteira.**

---

## 7. Fora do escopo

| Item | Motivo |
|---|---|
| Módulo de recursos / RH | Ausência total de dado na base |
| Disparo real de SMS/WhatsApp | Exige integração institucional; mostramos o gatilho e o conteúdo |
| Integração ao vivo com o RMI | Demonstramos o conceito com dado da própria base |
| Autenticação real | Modelada em SQL; demo usa seletor de perfil |
| Geolocalização precisa | Base anonimiza endereço até bairro |
| Reescrita do algoritmo de classificação | Não é o gargalo |

---

## 8. Riscos

| Risco | Plano B |
|---|---|
| ETL não alimenta o app até as 14h | JSON pré-agregado no repo, app lê estático. Decisão automática, sem debate |
| Supabase consome tempo demais | Mesmo plano B; políticas ficam versionadas como entrega de engenharia |
| Tela da família fica bonita mas ainda burocrática | Passada de linguagem às 15h, com a régua da seção 5 na mão |
| Jurado questionar a leitura do `confirmado` | Resposta pronta: a evidência é a marcação em bloco (89,9% zero, 6,8% todos os 13) |
| Escopo estoura | P1 e P2 caem inteiros. P0 é intocável |

---

## 9. Critérios de pronto

- [ ] App publicado, abrindo em aba anônima
- [ ] Repositório público
- [ ] Painel com estados de vaga e filtro por CRE, ligado em dado real
- [ ] Ficha da família passando na régua da seção 5, com áudio funcionando
- [ ] Critérios verificáveis na origem aparecendo já marcados
- [ ] Botão de escalada visível e explicado
- [ ] Seletor de perfil trocando o escopo de dados de verdade
- [ ] `sql/policies.sql` no repo
- [ ] README com equipe, resumo, arquitetura, uso do Claude, link
- [ ] Vídeo de 60s
- [ ] **Teste da vizinha aprovado**
- [ ] E-mail com "Grupo 18" no assunto e no corpo

---

## 10. O argumento do pitch, em três frases

A vaga de creche é distribuída por uma pontuação que a própria família declara, que não aceita
anexo, e que em 90% dos casos ninguém confere — com a régua reescrita a cada ano.
Isso é fácil de fraudar para quem entende o jogo, e é intransponível para quem tem pouca
escolaridade: a mãe que tem direito ao ponto marca "não" porque não entendeu a pergunta.
O Vaga Viva puxa da origem o que o poder público já sabe, pergunta à família só o que falta em
linguagem que ela consegue usar, e mostra ao gestor cada vaga parada antes que ela volte para o sorteio.

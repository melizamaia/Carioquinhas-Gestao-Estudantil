# Grupo 18 — Match perfeito: Inteligência na inscrição de creche

Fonte: Notion (notas do briefing).

## Equipe

Grupo 18: Meliza Maia, Rodrigo Pita, Thiago Duque e Renata Ribeiro

## Ângulo escolhido

**Match perfeito: Inteligência na inscrição de creche** — foco no problema de acesso à creche (0–3 anos).

## Contexto levantado no briefing

- Famílias comprovam vulnerabilidade social via documentação: Cadastro Único, Bolsa Família, histórico de violência, entre outros.
- Existem 13 critérios de pontuação usados na classificação (não foram citados/detalhados na call). Os mais importantes mencionados:
  - Cadastro Único
  - Bolsa Família
  - Pequenos Cariocas
- Observar as CREs (Coordenadorias Regionais de Educação) e a geografia das creches em relação à localidade das famílias.
- Critério de classificação: até 5 opções de vaga por CPF/inscrição.
- Avaliação é feita por vulnerabilidade social.

## A dor central (oportunidade do projeto)

Cada criança é convocada com **até 5 opções de vaga**, mas o responsável só escolhe **uma**. Há uma janela de **3 dias de alocação** por criança — nesse período a vaga fica ociosa, sem chamar outra criança da fila para ocupá-la caso a família não responda a tempo.

→ Esse é o gap que o projeto pode atacar: reduzir a ociosidade de vaga durante a janela de decisão da família.

## Diagramas do briefing (slides da Prefeitura/SME)

Fotos originais em [`imagens/`](imagens/).

### A Jornada do Cidadão

Foto: [`imagens/jornada-do-cidadao.jpg`](imagens/jornada-do-cidadao.jpg)

1. **Inscrição no matrícula.rio:** CPF obrigatório com validação da Receita Federal + 5 opções por unidade
2. **Comprovação dos critérios de vulnerabilidade** nas unidades + validação de parte dos critérios via Registro Municipal Integrado
3. **Classificação** em data publicada no Diário Oficial + resultados no site
4. **Confirmação de matrícula** na unidade escolhida
5. **Lista de espera publicada:** períodos de 3 dias para convocação

### O fluxo de inscrição: sistemas

Foto: [`imagens/fluxo-inscricao-sistemas.jpg`](imagens/fluxo-inscricao-sistemas.jpg)

1. **Planejamento de Matrícula:** site de planejamento com a organização da rede entre o ano atual x seguinte
2. **Site de Matrícula:** recebe as vagas que serão ofertadas para o processo de inscrição
3. **Inscrição Creche:** as inscrições realizadas no site são exportadas para o processo de classificação e convocação
4. Antes do período de classificação, as inscrições são analisadas e os critérios via Registro Municipal Integrado são confirmados utilizando o datalake
5. **Classificação:** em data publicada em DO, o sistema executa o script de classificação, gerando uma lista de classificados e espera por unidade

Referência citada no slide: Registro Municipal Integrado → https://docs.dados.rio/rmi/overview

### Eixo 2 — Inscrição e Classificação: onde a lógica quebra hoje

Slide da Prefeitura/SME apresentado no evento. 5 etapas do fluxo atual:

1. Família se inscreve e escolhe até 5 unidades + declara os critérios no site (Matrícula Rio)
2. Leva a documentação em uma das unidades escolhidas para comprovar parte dos critérios
3. A creche confirma manualmente no sistema + SME confirma os critérios: CadÚnico e Bolsa Família
4. Pontuação é registrada no sistema > classificação é realizada e as vagas são priorizadas e distribuídas
5. O ano inicia com vagas ociosas + convocação manual + contatos desatualizados + convocação demorada

**Onde o fluxo quebra (texto do slide):**

> O ponto crítico do fluxo está na escolha das 5 unidades pelo responsável, feita sem qualquer critério de distância ou território, o que resulta em opções inviáveis e, consequentemente, em futuros cancelamentos. Além disso, o processo de classificação é orientado pela total de escolhas por unidade, e não por CPF, o que gera lacunas e pontos cegos na convocação. O sistema classifica as opções simultaneamente: ofertando até 5 vagas para o mesmo CPF.

→ Isso reforça e detalha a dor central do projeto (seção acima): a raiz do problema não é só a janela de 3 dias parada — é que a escolha das 5 unidades já nasce sem lógica geográfica, e a classificação roda por unidade em vez de por CPF, o que trava a convocação em cadeia.

### Eixo 3 — Convocação: hoje ainda é manual e lento

Foto: [`imagens/eixo3-convocacao.jpg`](imagens/eixo3-convocacao.jpg)

Linha do tempo da convocação, quando surge uma vaga:

1. **Contato da escola:** 1 tentativa por dia, durante 3 dias consecutivos, em horários diferentes (telefone, e-mail, WhatsApp ou SMS)
2. **Prazo da família:** 3 dias úteis para comparecer e confirmar a vaga na unidade
3. **Possível extensão:** mais 1 dia útil, mediante justificativa apresentada dentro do prazo original

**Onde a agilidade falta (texto do slide):**

> Não localizar a família ou não obter resposta a tempo retira a criança da lista e passa a vaga adiante. É um fluxo manual e repetitivo, tentativa a tentativa, com potencial claro de automação e rastreio.

→ Esse é o outro lado da mesma dor: mesmo depois de resolver a alocação (Eixo 2), a convocação em si é manual, sem rastreio e lenta — é onde a vaga fica ociosa de fato.

## Base de dados

Vamos receber a base de dados oficial da secretaria — dados são reais. Repositório: https://github.com/CIT-SME-RJ/dadoscreche/ (ver [01-dados/sobre-os-dados.md](../01-dados/sobre-os-dados.md)).

Notas do briefing: **falta dados** em algum ponto do processo (mencionado sem detalhe — checar com os mentores o que exatamente falta) e há uma nota sobre **gasto de créditos** (da API/Claude, provavelmente — sem detalhe numérico capturado).

## Entrega — atenção a uma diferença com o README oficial do repo

O briefing do Notion diz que a entrega aceita: **GitHub, ou aplicação online rodando, site acessado, ou vídeo de até 5 minutos com captura de tela**.

O README oficial do repositório (`taicor-ai/claude-impact-lab-rio-2`) pede vídeo de **60s**, obrigatório só se a aplicação não estiver publicada.

**Essas duas fontes não batem** (5 min vs 60s) — vale confirmar com a organização qual vale, mas por segurança, mirar no vídeo de 60s (o mais restritivo) e ter a aplicação publicada como plano principal.

## Critérios de nota (igual ao briefing oficial)

- Impacto: 40%
- Produto: 20%
- Engenharia: 20%
- Ideia: 10%
- Apresentação: 10%

Último commit: 16h30. 5 finalistas, 6 minutos, depois perguntas.

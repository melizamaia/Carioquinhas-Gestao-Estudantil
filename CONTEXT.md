# Vaga Viva

Sistema que acompanha a vaga de creche municipal do momento em que ela é oferecida até a matrícula, e devolve à fila toda vaga que trava sem decisão. Existe porque uma em cada quatro vagas oferecidas se perde na etapa de confirmação.

## Linguagem

### O ciclo da vaga

**Convocação**:
A chamada de uma família para ocupar uma vaga específica numa unidade.
_Evite_: chamamento, oferta

**Resposta**:
O que a família diz pelo link com token: que vai, que quer outra data, ou que não vai. É nosso termo, criado neste projeto — não existe no processo atual, onde só há silêncio ou comparecimento.
_Evite_: confirmação (é outra coisa, ver abaixo), aceite, retorno

**Confirmação**:
O ato presencial na creche, com os documentos na mão. É da SME e não mexemos nele: `Cancelado na confirmacao` na base significa que a família foi convocada e este ato não aconteceu.
_Evite_: usar para o clique no link

**Matrícula**:
O desfecho: a criança ocupa a vaga.

**Devolução**:
A vaga volta para a fila e a próxima família é convocada. Tem três portas: matrícula da criança em outra unidade, recusa explícita, ou prazo vencido sem que ninguém alcance a família.
_Evite_: reoferta, sorteio, liberação

**Cascata**:
A devolução disparada por matrícula. Uma criança matriculada libera de uma vez todas as posições que ela ocupava em outras unidades — em média 2,76.
_Evite_: desduplicação, limpeza

### Quem alcança a família

**Acionamento territorial**:
O aviso que vai para a microárea da SME (CRAS, agente comunitário de saúde, unidade de saúde da família) no mesmo momento da convocação, não depois das tentativas falharem.
_Evite_: escalada, encaminhamento

**Busca ativa**:
A ida presencial do agente até a família, liberada depois de três tentativas de contato sem resposta.
_Evite_: visita, diligência

**Tentativa**:
Um contato registrado com a família por qualquer canal. O rastro de tentativas é o que hoje não existe.

### A fila

**Pontuação declarada**:
A soma dos critérios que a família marcou no formulário. Ordena a fila hoje. Em 2025, 90% das inscrições nunca tiveram nenhum critério conferido.

**Pontuação verificada**:
A mesma soma, contando só o que passou por conferência. Média de 7,9 contra 27,7 da declarada.

**Distorção da fila**:
A distância entre a ordem declarada e a ordem verificada.

**Faixa**:
Como a posição na fila é comunicada à família — "entre as 30 primeiras". Nunca número exato, porque o desempate é por data de inscrição e a precisão seria falsa.
_Evite_: posição, colocação, lugar

### Quem usa

**Unidade**:
A creche ou EDI. É quem age sobre a criança: registra tentativa, confere documento, confirma matrícula.
_Evite_: escola, unidade escolar (jargão proibido na tela da família)

**CRE**:
Coordenadoria Regional de Educação. Enxerga as unidades do seu território.

**Exceção**:
Um caso que precisa de uma pessoa da unidade. É o que aparece no painel dela — quem respondeu que vai, some.

## Vocabulário proibido na tela da família

Nenhum termo desta página aparece para a família. Lá não existe convocação, confirmação, deferimento, unidade escolar, dias úteis, nem sigla alguma. Vira: vaga, você conseguiu, leve estes papéis, até sexta dia 5, creche. A régua completa está na seção 5 do [PRD](./02-projeto/PRD.md).

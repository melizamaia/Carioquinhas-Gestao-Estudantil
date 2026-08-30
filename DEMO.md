# Roteiro da demonstração — Vaga Viva

**Grupo 18** · Claude Impact Lab Rio 2 · 30/08/2026

Tudo abre com duplo clique, sem servidor. Comece sempre por `app/entrada.html`.

---

## Os links

| Tela | Endereço |
|---|---|
| **Entrada** — "Quem é você?" | `app/entrada.html` |
| Painel · creche | `app/painel.html?perfil=unidade` |
| Painel · coordenadoria | `app/painel.html?perfil=cre` |
| Painel · secretaria | `app/painel.html?perfil=sme` |
| Ficha da família | `app/familia.html?token=demo-b` |
| Agente comunitário | `app/agente.html` |

## Os tokens da família

| Token | Caso | O que mostra |
|---|---|---|
| `demo-b` | Prazo em 2 dias, faltam 3 documentos | O caso base. Pontuação já confirmada pelo Cadastro Único, checklist, decisão em dois passos |
| `demo-f` | Prazo termina hoje | A urgência dita em palavra, não em cor |

## Os quatro casos de borda

Acrescente `&estado=` ao link da família:

| Endereço | O que mostra |
|---|---|
| `familia.html?token=demo-b&estado=prazo_vencido` | Não dá erro: diz que o prazo passou e oferece caminho |
| `familia.html?token=demo-b&estado=vaga_ocupada` | Nunca mostra vaga que já foi. Diz o que houve e a posição na fila agora |
| `familia.html?token=demo-b&estado=ja_respondeu` | Pode mudar de ideia enquanto a vaga não foi devolvida |
| `familia.html?token=demo-b&estado=confirmado` | A tela depois do "sim" |

---

## O caminho de 90 segundos

**1 · Entrada (10s)**
Abra `app/entrada.html`. Leia em voz alta a diferença entre os dois grupos.
> "Quem trabalha na Prefeitura entra com conta. Quem está fora entra por link. O agente comunitário é da Saúde: ele não teria credencial da Educação nem em produção."

**2 · Secretaria (15s)**
Clique em **Secretaria**. Os três números, e a tabela.
> "Uma em cada quatro vagas oferecidas se perde na confirmação. E estas três creches nunca conferiram uma única inscrição."

Aponte a **nota metodológica**. Dita antes de perguntarem, ela vira maturidade. Descoberta pelo júri, vira buraco.

**3 · Creche (20s)**
Volte por "Trocar de perfil" e entre como **Creche**.
> "A diretora não vê 40 casos. Vê 6, e só o que precisa dela hoje."

O card do alto: **2 vagas devolvidas pela cascata**.
> "A Criança 3391-C se matriculou em outra creche. As posições que ela travava aqui voltaram para a fila na hora. Cada criança matriculada ocupava 2,76 posições: são 337.870 vagas travadas no Rio."

Clique em **Convocar as 2**.

**4 · Família (30s) — ligue o som**
Abra `familia.html?token=demo-b` no celular.
> "Isto é o que a mãe recebe."

Toque em **Ouvir esta página**. Deixe as quatro frases tocarem inteiras, sem falar por cima.

Aponte a linha de prova: *"Você inscreveu a criança nesta creche em 12 de março."*
> "É isso que faz ela confiar no link. Um brasão qualquer copia."

Toque em **Não vou conseguir** → **Quero ir, mas em outro dia** → escolha uma data.
> "Hoje esta mãe simplesmente sumiria, e a vaga venceria em silêncio."

**5 · Agente (15s)**
Abra `app/agente.html`.
> "A rede é avisada no primeiro dia, não depois das três tentativas. Com janela de 3 dias, avisar o agente no dia 3 é avisar quando a vaga já venceu."

Toque em **Encontrei a família**.

---

## O que dizer se perguntarem

**"Vocês disparam WhatsApp de verdade?"**
Não, e o gargalo não é enviar: é não saber se chegou. O que entregamos é o motor — cadência, conteúdo, registro e regra de escalada. A conversa acontece na ficha, que é nossa. E o link diz o que hoje ninguém sabe: se a família abriu.

**"Como vocês puxam o CadÚnico?"**
Nesta demonstração, da própria base, e a tela declara isso. Em produção é o Registro Municipal Integrado. O ponto é que o dado já é do poder público: não há razão para perguntar à família algo que o Estado já sabe.

**"De onde vem o relógio de 3 dias?"**
O desfecho de cada inscrição é real. A janela é reconstruída pela regra do processo, porque a base não tem carimbo de hora de convocação nem de expiração. Está escrito na tela.

**"E a autenticação?"**
Modelada em `sql/policies.sql`, com RLS por perfil e território, e acesso por token para quem não tem conta. A demonstração usa a tela de entrada no lugar do login — e não pedimos senha de propósito: uma tela com a marca da Prefeitura pedindo senha, num protótipo, é um formulário que ninguém deveria preencher.

**"Por que não tem módulo de recursos?"**
Existe dado de lotação, mas é monitoramento mensal, com defasagem de um mês e origem distinta da base de inscrição. Não fecha com o grão da fila e não é o gargalo. Ficou fora por decisão, não por ausência de dado.

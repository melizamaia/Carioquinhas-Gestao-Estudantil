# Contrato de dados — back ⇄ front

**Grupo 18 · 30/08/2026 · congelado às 13h45**
Back: Renata e Meliza · Front: Rodrigo e Thiago

> **O front não espera o back.** Os arquivos em `data/` já existem com dado falso e o formato
> definitivo. Rodrigo e Thiago constroem contra eles agora. Quando o ETL terminar, o back
> **substitui o conteúdo** dos mesmos arquivos, com as mesmas chaves — e nada quebra.
>
> Se uma chave precisar mudar, avisa no canal antes de mudar. Só isso.

---

## 1. Por que congelar o formato antes do ETL

O formato sai dos fluxos, não do dado. Ele já está decidido: o que a família responde, o que a
unidade vê, o que conta como exceção. Nada disso depende de a agregação ficar pronta.

Se o front esperar, às 15h existem números lindos e nenhuma tela. Se o back atrasar, o app roda
com dado falso e ninguém percebe na demo — os arquivos são idênticos em estrutura.

**Consequência prática:** o gate das 14h do roadmap deixa de ser uma decisão dramática. Vira
troca de arquivo.

---

## 2. Os quatro arquivos

| Arquivo | Quem consome | Vira o quê |
|---|---|---|
| `data/unidades.json` | painel | filtro de CRE e unidade, nome nas telas |
| `data/convocacoes.json` | painel **e** ficha | os cards, e uma página por token |
| `data/indicadores.json` | painel | os três números do topo e o ranking da SME |
| `data/copy.json` | ficha, tela do agente | todo texto que a família lê ou ouve |

Todos já estão no repositório, preenchidos. **Abra e olhe antes de programar qualquer coisa.**

---

## 3. A máquina de estados

Um campo só, `estado`, e ele é a fonte da verdade:

```
proposta ──[unidade confirma]──> aguardando
                                      │
                    ┌─────────────────┼─────────────────┐
                    │                 │                 │
              respondeu_vou      (sem resposta)      recusou
                    │                 │                 │
              matriculada          vencida          devolvida
                    │                 │                 │
                    └──── devolve as outras ────────────┘
                              (cascata)
```

Valores válidos: `proposta` · `aguardando` · `respondeu_vou` · `matriculada` · `vencida` · `recusou` · `devolvida`

**`aberta_em` não é estado, é fato.** É o carimbo de quando a família abriu o link. É o que separa
"abriu e não respondeu" de "nunca abriu" — as duas exceções mais importantes do painel. `null`
significa que nunca abriu.

---

## 4. O motor: uma função, três portas

Isto é o coração do sistema. Escrever uma vez, chamar de três lugares.

```
devolver(convocacao_id, motivo)
  motivo ∈ { 'cascata', 'recusa', 'prazo' }

  1. marca a convocação como devolvida
  2. pega as próximas da fila daquela unidade + grupamento + turno
  3. cria as novas linhas com estado = 'proposta'   ← não convoca sozinho
```

E a que dispara a cascata:

```
matricular(convocacao_id)
  1. marca como matriculada
  2. para toda outra convocação do mesmo aluno_anon que não esteja finalizada:
       devolver(id, 'cascata')
```

**Por que `proposta` e não convocação direta:** convocar cidadão é ato com responsável. O sistema
propõe, a unidade confirma em um clique. É o que uma secretaria aceita, e é a resposta pronta se
o júri perguntar quem responde pela convocação.

**É também onde a cascata aparece na tela.** Nas creches que recebem as vagas de volta, surge a
exceção `pronta_para_convocar`. Sem isso a cascata só existiria na creche que matriculou — que é
justamente onde ela não importa.

---

## 5. A exceção é calculada no back, não no front

O front **não** reimplementa esta regra. O back entrega o campo `excecao` pronto.

| `excecao` | Quando | O que a unidade faz |
|---|---|---|
| `nao_abriu` | `aguardando` e `aberta_em` é null há 1+ dia | busca ativa |
| `abriu_sem_resposta` | `aguardando`, `aberta_em` preenchido, `resposta` null | liga |
| `pediu_data` | `resposta` = `outra_data` | aceita a data |
| `recusou` | `resposta` = `nao_vou` | libera em 1 clique |
| `vencendo_hoje` | `prazo_em` = hoje e sem resposta | busca ativa |
| `pronta_para_convocar` | `estado` = `proposta` | convoca |
| `null` | tudo em ordem | some da tela |

Quem tem `excecao: null` **não aparece** no painel da unidade: vira a linha de contagem no topo.

---

## 6. Supabase — só o que é escrita em runtime

O agregado histórico não vai para o banco. Só o que muda enquanto alguém usa.

```sql
create table convocacao (
  id            uuid primary key default gen_random_uuid(),
  token         text unique,
  aluno_anon    text not null,
  unidade_id    text not null,
  grupamento    text,
  turno         text,
  prazo_em      date,
  estado        text not null default 'proposta',
  aberta_em     timestamptz,
  criado_em     timestamptz not null default now()
);

create table resposta (
  id             uuid primary key default gen_random_uuid(),
  convocacao_id  uuid references convocacao(id),
  valor          text not null check (valor in ('vou','outra_data','nao_vou')),
  data_escolhida date,
  criado_em      timestamptz not null default now()
);

create table tentativa (
  id             uuid primary key default gen_random_uuid(),
  convocacao_id  uuid references convocacao(id),
  canal          text,
  resultado      text,
  criado_em      timestamptz not null default now()
);

create table devolucao (
  id             uuid primary key default gen_random_uuid(),
  convocacao_id  uuid references convocacao(id),
  motivo         text not null check (motivo in ('cascata','recusa','prazo')),
  criado_em      timestamptz not null default now()
);

create index on convocacao (unidade_id, estado);
create index on convocacao (aluno_anon);
create index on resposta (convocacao_id);
```

`resposta` é tabela, não coluna, de propósito: a família pode mudar de ideia, e o caso de borda 3
(duas pessoas com o mesmo link) exige saber que houve duas. **Vale a última; a unidade vê todas.**

### Acesso — dois modos, não quatro perfis

| Modo | Quem | Como |
|---|---|---|
| **Com conta** | SME · CRE · unidade | RLS por perfil e escopo territorial |
| **Com link** | família · agente comunitário | token na URL, sem conta |

O agente comunitário entra pelo mesmo mecanismo da família, e isso não é atalho: **ACS é da
Saúde, CRAS é da Assistência Social.** Não são da Educação e não teriam credencial da SME nem em
produção. Um padrão, dois públicos.

Escrever em `sql/policies.sql` e commitar mesmo que não chegue a rodar — vale ponto de engenharia.

---

## 7. Quem faz o quê

**Meliza — a agregação**
1. DuckDB: score, fila, funil, join de unidade (cuidado com os dois formatos de `unidade`)
2. Gerar `unidades.json` e `indicadores.json` a partir de 2025
3. Derivar `convocacoes.json` do estado final real, aplicando a regra da seção 5
4. A função `devolver` / `matricular`, em SQL ou Python

**Renata — a linguagem e o banco**
1. Criar as tabelas no Supabase pela interface, com o SQL da seção 6
2. `sql/policies.sql`
3. **`copy.json`** — é seu, e é o que decide se a tela passa no teste da vizinha. O roteiro de
   áudio de 4 frases por token é o item mais importante do arquivo
4. `DEMO.md` com os tokens escolhidos
5. Conferir toda saída contra a régua da seção 5 do PRD: 12 palavras, zero sigla, zero jargão

---

## 8. Ordem, com relógio

| Hora | O quê | Trava alguém? |
|---|---|---|
| **13h45** | Contrato congelado, `data/*.json` no repo | ✅ destrava o front agora |
| 13h45–14h15 | Tabelas no Supabase + `policies.sql` | não |
| 13h45–15h00 | ETL: agregação e derivação | não |
| 14h15–15h00 | `copy.json` completo, com os áudios | trava a ficha final |
| **15h00** | **Corte:** o que estiver pronto substitui o falso. O que não estiver, fica falso | — |
| 15h00–15h30 | `DEMO.md` + conferência de linguagem | não |

**A regra do corte das 15h:** ninguém troca arquivo depois disso. Dado falso numa demo que roda é
infinitamente melhor que dado real numa demo que quebra.

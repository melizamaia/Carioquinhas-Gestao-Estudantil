# Roadmap Final — Vaga Viva

**Grupo 18** · Claude Impact Lab Rio 2 · 30/08/2026 · 11h30 → 16h30
Meliza Maia · Rodrigo Pita · Thiago Duque · Renata Ribeiro

> Escopo congelado. Só entra o que cabe em 5 horas e roda ao vivo.
> O que ficou de fora está na seção 7 — com o motivo, para ninguém reabrir a discussão às 15h.

---

## 1. O produto em uma frase

A vaga de creche é distribuída por uma pontuação que a família declara, que não aceita anexo e que em 90% dos casos ninguém confere. O Vaga Viva mostra ao gestor cada vaga parada antes que ela expire, aciona a rede do território no primeiro dia, libera automaticamente as vagas que uma criança trava em outras unidades, e fala com a família em linguagem que ela consegue usar.

---

## 2. Escopo congelado

### Módulo 1 — Painel de vaga (gestor)

| # | Requisito |
|---|---|
| 1.1 | Vagas convocadas como cards, com estado e dias restantes |
| 1.2 | Semáforo: verde ≥2 dias · amarelo 1 dia · vermelho vence hoje/venceu |
| 1.3 | Filtro por CRE e por unidade |
| 1.4 | Três números no topo, calculados da base real |
| 1.6 | Rastro das tentativas de contato no card |
| 1.7 | Registrar tentativa · marcar item conferido |
| **1.9** | **Liberação em cascata: ao matricular, as posições da criança em outras unidades são liberadas automaticamente** |

### Módulo 2 — Ficha da Família

| # | Requisito |
|---|---|
| 2.1 | Tela sem login, por link com token |
| 2.2 | Blocos na ordem: pontuação → vaga → prazo → o que falta → ação |
| 2.3 | Critérios verificados na origem já vêm marcados, sem pergunta |
| 2.4 | Botão "ouvir", lendo a página em pt-BR (Web Speech API) |
| 2.5 | Checklist do que falta, com ícone por item |
| 2.6 | Prazo em dia da semana + data + contagem |
| 2.7 | Botão único de confirmação |
| **2.12** | **Posição na fila em faixa ("entre as 30 primeiras"), nunca número exato** |
| **2.13** | **Texto das telas gerado pelo Claude em tempo de build, segundo a régua da seção 5** |

### Módulo 3 — Acionamento territorial

| # | Requisito |
|---|---|
| **3.5** | **Aviso territorial para ACS/CRAS da microárea, disparado no T0 junto com os canais digitais** |
| 3.1 | Botão **Busca ativa**, habilitado após 3 tentativas registradas |
| 3.2 | Mostrar a microárea de destino do encaminhamento |
| 3.3 | Estados distintos: `Rede acionada` · `Em busca ativa` · `Expirada` |

### Módulo 4 — Hierarquia de acesso

| # | Requisito |
|---|---|
| 4.1 | Seletor de perfil que refiltra a tela de verdade (SME · CRE · Unidade · Família) |
| 4.2 | Critérios sensíveis ocultos no perfil Unidade |
| 4.3 | Políticas RLS escritas e versionadas em `sql/policies.sql` |

### Se sobrar tempo, nesta ordem

1. **1.5** Indicador de distorção da fila (declarado × verificável)
2. **2.8** Envio de foto do documento pelo celular
3. **2.10** "Não vou conseguir ir" aciona a unidade
4. **4.4** RLS efetivamente aplicada no Supabase (as políticas já estarão versionadas)
5. **2.9** Endereço da creche com botão de mapa

---

## 3. Fluxo da vaga

```
Ofertada → Convocada
             │
             ├─ T0    SMS · e-mail · WhatsApp (simulados)  ─┐
             │        Aviso territorial ACS/CRAS  ──────────┤ simultâneos
             │                                              │
             ├─ +1d   2ª tentativa                          │
             ├─ +2d   3ª tentativa                          │
             ├─ +3d   Busca ativa presencial (botão)        │
             │                                              │
             └─ resposta em qualquer canal ─────────────────┘ encerra todos
                        │
                        ├─ Conferida → Matriculada
                        │                  └─ LIBERAÇÃO EM CASCATA
                        │                     (posições em outras unidades)
                        └─ prazo vencido → Expirada → Reofertada
```

Duas regras que definem o produto:

**A rede é avisada no primeiro dia, não no último.** A família que não responde ao digital é justamente aquela cujo canal digital está quebrado. Com janela de 3 dias, avisar o ACS depois de 3 tentativas é avisar quando a vaga já expirou.

**Matricular em um lugar libera os outros.** As 191.741 crianças matriculadas em 2025 ocupavam 337.870 posições adicionais. A liberação é uma função sobre `aluno_anon`, que é estável entre unidades e entre os 5 anos da base.

---

## 4. Arquitetura

```
BUILD (roda no notebook, versionado no repo)
  base .csv.gz → DuckDB → agregações → data/*.json  (poucos KB)
  Claude API → textos em linguagem simples → data/copy.json
  gerador → HTML pré-renderizado por token
        │
        └─ git push
                │
RUNTIME
  Render Static Site   ← grátis, sem cold start
    ├─ /painel/            HTML + JSON embutido (funciona sem JS)
    ├─ /familia/{token}/   HTML pré-renderizado
    └─ JS progressivo:     filtro · áudio · confirmação
                              └─→ Supabase (escrita + RLS)
```

Três decisões que sustentam isso:

- **Estático, não SPA.** O requisito de conteúdo legível sem JavaScript e a página abaixo de 200KB inviabilizam uma SPA. HTML pré-renderizado atende os dois de graça.
- **Static site, não web service.** O plano gratuito do Render hiberna em 15 minutos e leva 30 a 60 segundos para acordar. Static sites não hibernam. Isso elimina o maior risco da apresentação.
- **Claude em tempo de build.** A chave não vai para produção, não há latência nem custo na demo, e a tela funciona mesmo se a API estiver fora na hora da apresentação.

---

## 5. Stack — tudo gratuito, sem cartão

| Camada | Ferramenta | Cuidado |
|---|---|---|
| Leitura da base | **DuckDB** | Lê `.csv.gz` direto. `delim=';'`, UTF-8 com BOM |
| Manipulação | **pandas** + **pyarrow** | QueryB tem 4,3M linhas — agregue no DuckDB, não carregue |
| Excel | **openpyxl** | `data_only=True`, senão vêm fórmulas |
| Shapefile → GeoJSON | **mapshaper.org** | No navegador. Evita instalar GDAL |
| Banco + RLS | **Supabase Free** | 500 MB. Pausa após 7 dias sem atividade |
| CSS | **Pico.css** (~10KB) ou CSS puro | Nada de Tailwind CDN |
| Fontes | **System font stack** | 0 KB. Google Fonts pesa em 3G |
| Mapa (P1) | **Leaflet** + tiles **CARTO Positron** | Base clara ajuda no contraste 7:1 |
| Áudio | **Web Speech API** nativa | Voz pt-BR varia por aparelho — teste no celular da demo |
| IA | **Claude API** | Só em build |
| Deploy | **Render Static Site** | Ilimitado, sem cold start |
| Keep-alive | **UptimeRobot Free** | Evita a pausa do Supabase |
| Repo | **GitHub** | Público |
| Diagrama | **Mermaid** | Renderiza no README do GitHub |
| Contraste | **WebAIM Contrast Checker** | Meta: 7:1 |
| A11y + peso | **Lighthouse** (Chrome DevTools) | Meta: ≥95 |
| 360px + 3G | **DevTools** → Device Toolbar + Slow 4G | |
| Vídeo | **OBS Studio** ou gravador do sistema | |

---

## 6. Cronograma

| Horário | O que | Gate |
|---|---|---|
| **11h30–11h45** | Contas em paralelo, um por pessoa | **Deploy de um `index.html` no ar, com o repo ainda vazio** |
| **11h45–13h00** | ETL: score, fila, funil, joins, `data/*.json` | JSON no repo |
| 13h00–13h20 | Almoço | — |
| **13h20–14h30** | Painel ‖ Ficha da Família, em paralelo | **14h00: se o ETL não alimentar o app, congela o JSON e segue** |
| **14h30–15h00** | Liberação em cascata + acionamento no T0 | Fluxo ponta a ponta roda |
| **15h00–15h30** | Passada de linguagem + Lighthouse + contraste | Accessibility ≥95 |
| **15h30–15h50** | README, `sql/policies.sql`, diagrama, `DEMO.md` | Checklist da seção 9 |
| **15h50–16h20** | Ensaio 2× + gravação do vídeo | Vídeo exportado |
| **16h20–16h30** | Push final + e-mail com "Grupo 18" no assunto | Enviado |

**Grave o vídeo mesmo com o deploy funcionando.** É a apólice contra o wi-fi da sala.

### Contas das 11h30 (15 minutos, um por pessoa)

| Trilho | Tarefa | Pronto quando |
|---|---|---|
| A | Repo público + README esqueleto + `.env.example` | Push feito |
| B | Supabase: projeto criado, URL e anon key no canal do time | Chave compartilhada |
| C | Render: static site apontado para o repo | Deploy verde |
| D | Claude API testada com um curl | Resposta 200 |

### Divisão do sprint

| Trilho | Responsabilidade |
|---|---|
| **A — Dados** | ETL, score, fila, joins de unidade, `data/*.json`, os três números do topo |
| **B — Painel** | Módulo 1 completo, incluindo cascata e estados do funil |
| **C — Família** | Módulo 2, régua de linguagem, áudio, acessibilidade |
| **D — Plataforma** | Supabase, `policies.sql`, seletor de perfil, deploy, README, vídeo |

Ajustem pelos perfis do time. O que não pode acontecer é dois trilhos no mesmo arquivo.

---

## 7. Fora do escopo — decidido, não em aberto

| Item | Motivo |
|---|---|
| Disparo real de SMS/WhatsApp | Exige integração institucional. O sandbox do Twilio ainda obriga cada destinatário a enviar um código antes de receber qualquer coisa. Mostramos o gatilho e o conteúdo da mensagem |
| Módulo de recursos / RH | **Existe dado de lotação** (aluno/turma em `totaalunoscreche`, vagas em `Parceiras`), mas é monitoramento mensal com defasagem de ~1 mês e origem distinta da base de inscrição. Não fecha com o grão da fila e não é o gargalo. **Fora por decisão, não por ausência de dado** |
| Integração ao vivo com o RMI | Demonstramos o conceito com dado da própria base |
| Autenticação real | Modelada em SQL; a demo usa seletor de perfil |
| Geolocalização **da família** | A base anonimiza o endereço até bairro. Localização **de unidade e microárea** é dado aberto e é usada |
| Reescrita do algoritmo de classificação | Não é o gargalo |
| Versão imprimível, agrupamento "vence amanhã", SSO | Cortados por tempo, documentados como próximo passo |

---

## 8. Armadilhas da base — leia antes de escrever o ETL

| O que | Consequência |
|---|---|
| `situacao` = **"Cancelado na confirmacao"**, sem cedilha e sem til | Filtrar com acento devolve zero linhas |
| `04_UnidadesEscolares` **não tem cabeçalho** | `header=None`, senão perde a primeira unidade |
| `QueryA.unidade` tem **dois formatos** | 7 dígitos = pública (`zfill(7)` → `DESIGNACAO`) · 5 dígitos = parceira (`CRE` + últimos 3 do `CÓDIGO SGA`). Só pela Query D vocês perdem **352 unidades e 149.092 linhas**, sem erro nenhum |
| **Não há timestamp** de convocação ou expiração | O funil é simulado sobre o estado final. Declarar isso no README |
| A régua mudou entre 2023 e 2024 | Rodar tudo sobre **2025**. Nunca cruzar pontuação entre anos |
| Empates massivos na fila | 95 famílias com 0 ponto na mesma unidade. Desempate explícito: `pontos DESC, data_criacao ASC, ipl_id ASC`. Por isso posição é faixa, não número |
| **Excluir 2021** de análise de conferência | O campo `confirmado` de 2021 não é comparável (88,9% contra 10,8% em 2022) |
| Descartar `opcao = 6` | 11 linhas, viola a regra de 5 opções |
| Recorte territorial **pela unidade**, nunca pelo bairro declarado | 1.367 valores distintos num município de ~164 bairros |
| Excel com fórmulas | `data_only=True` no openpyxl |

### Reconstrução da fila — validado, 2,4s no DuckDB

```python
con.sql("""
create table score as
select b.ano, b.prm_id, b.plm_id, b.ipl_id,
       sum(case when b.resposta='Sim' then c.perg_pontuacao else 0 end) as pontos
from b join c on b.ano = c.ano and b.ich_perg_id = c.ich_perg_id
group by 1,2,3,4
""")

con.sql("""
create table fila as
select a.*, s.pontos,
       row_number() over (
         partition by a.ano, a.unidade, a.grupamento, a.horario
         order by s.pontos desc, a.data_criacao asc, a.ipl_id asc
       ) as posicao
from a join score s using (ano, prm_id, plm_id, ipl_id)
where a.situacao = 'Lista de espera'
""")
```

---

## 9. Pronto quando

**Entrega**
- [ ] App publicado, abrindo em aba anônima
- [ ] Repositório público
- [ ] README com equipe, resumo, arquitetura, uso do Claude, link
- [ ] `sql/policies.sql` no repo
- [ ] `DEMO.md` com os três tokens
- [ ] Vídeo de 60s
- [ ] E-mail com "Grupo 18" no assunto e no corpo

**Funcional**
- [ ] Painel com estados de vaga e filtro por CRE, em dado real
- [ ] Ficha da Família passando na régua de linguagem, com áudio funcionando
- [ ] Critérios verificáveis na origem aparecendo já marcados
- [ ] Acionamento territorial visível no T0, distinto da busca ativa
- [ ] Confirmar matrícula libera as outras posições da criança
- [ ] Seletor de perfil trocando o escopo de dados de verdade

**Técnico**
- [ ] Lighthouse Accessibility ≥ 95 na Ficha da Família
- [ ] Página da família < 200KB transferidos
- [ ] Contraste 7:1 conferido em todas as combinações
- [ ] Testada em 360px com throttling Slow 4G
- [ ] Áudio testado no celular da demo
- [ ] Conteúdo essencial legível com JavaScript desativado
- [ ] Keep-alive ativo no Supabase
- [ ] **Teste da vizinha aprovado**

---

## 10. Dados de demonstração

Escolher agora, gravar em `DEMO.md`:

| Token | Caso | Mostra |
|---|---|---|
| `demo-a` | Alta pontuação, CadÚnico verificado na origem, prazo hoje | "Você tem 51 pontos. Nada a fazer." |
| `demo-b` | Falta um documento, prazo em 2 dias | Checklist e prazo em linguagem simples |
| `demo-c` | 3 tentativas falhas, rede acionada desde o T0 | Os dois trilhos do acionamento |

## 11. Roteiro do vídeo — 60s

| Tempo | Cena |
|---|---|
| 0–10s | Os três números do topo do painel |
| 10–25s | Card vencendo hoje → 3 tentativas falhas → rede já acionada desde o T0 |
| 25–40s | Ficha da Família (`demo-b`), **com o áudio tocando** |
| 40–50s | Confirmar matrícula → outras posições acendem como liberadas |
| 50–60s | Seletor de perfil: mesma tela, escopo de CRE, critérios sensíveis ocultos |

Os dois momentos que nenhum outro grupo vai ter são o áudio tocando e a cascata de liberação. Se faltar tempo no vídeo, corta-se o resto.

---

## 12. O pitch, em três frases

A vaga de creche é distribuída por uma pontuação que a própria família declara, que não aceita anexo, e que em 90% dos casos ninguém confere — com a régua reescrita a cada ano. Isso é fácil de fraudar para quem entende o jogo e intransponível para quem tem pouca escolaridade: a mãe que tem direito ao ponto marca "não" porque não entendeu a pergunta. O Vaga Viva puxa da origem o que o poder público já sabe, pergunta à família só o que falta em linguagem que ela consegue usar, aciona a rede do território no primeiro dia, e devolve à fila cada vaga que uma criança trava em outra unidade.
segue
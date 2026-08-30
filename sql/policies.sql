-- ============================================================
-- Vaga Viva — esquema e políticas de acesso
-- Grupo 18 · Claude Impact Lab Rio 2 · 30/08/2026
--
-- Duas formas de entrar, e elas não são o mesmo sistema com
-- permissões diferentes:
--
--   COM CONTA   SME · CRE · unidade      RLS por perfil e território
--   COM LINK    família · agente         token na URL, sem cadastro
--
-- O agente comunitário cai no segundo grupo por razão institucional,
-- não técnica: ACS é da Secretaria de Saúde, CRAS é da Assistência
-- Social. Nenhum dos dois teria credencial da Educação, nem em produção.
-- ============================================================

-- ------------------------------------------------------------
-- 1. Tabelas de runtime
--    O agregado histórico não entra aqui: ele é lido de data/*.json,
--    gerado em build. No banco fica só o que muda enquanto alguém usa.
-- ------------------------------------------------------------

create table if not exists unidade (
  id          text primary key,          -- '02.22.001'
  nome        text not null,
  cre         text not null,
  bairro      text,
  microarea   text
);

create table if not exists convocacao (
  id          uuid primary key default gen_random_uuid(),
  token       text unique,               -- o acesso da família. null enquanto 'proposta'
  aluno_anon  text not null,
  unidade_id  text not null references unidade(id),
  grupamento  text,
  turno       text,
  prazo_em    date,
  estado      text not null default 'proposta'
              check (estado in ('proposta','aguardando','respondeu_vou',
                                'matriculada','vencida','recusou','devolvida')),
  aberta_em   timestamptz,               -- quando a família abriu o link. null = nunca abriu
  criado_em   timestamptz not null default now(),
  origem_convocacao_id uuid references convocacao(id) -- de qual convocação esta nasceu (cascata). null = original
);

-- resposta é tabela, não coluna: a família pode mudar de ideia, e duas
-- pessoas com o mesmo link podem responder diferente. Vale a última;
-- a unidade vê todas.
create table if not exists resposta (
  id             uuid primary key default gen_random_uuid(),
  convocacao_id  uuid not null references convocacao(id) on delete cascade,
  valor          text not null check (valor in ('vou','outra_data','nao_vou')),
  data_escolhida date,
  criado_em      timestamptz not null default now()
);

create table if not exists tentativa (
  id             uuid primary key default gen_random_uuid(),
  convocacao_id  uuid not null references convocacao(id) on delete cascade,
  canal          text check (canal in ('whatsapp','sms','email','telefone','presencial')),
  resultado      text,
  criado_em      timestamptz not null default now()
);

create table if not exists devolucao (
  id             uuid primary key default gen_random_uuid(),
  convocacao_id  uuid not null references convocacao(id) on delete cascade,
  motivo         text not null check (motivo in ('cascata','recusa','prazo')),
  criado_em      timestamptz not null default now()
);

create table if not exists acionamento (
  id             uuid primary key default gen_random_uuid(),
  convocacao_id  uuid not null references convocacao(id) on delete cascade,
  microarea      text not null,
  token_agente   text,                   -- o acesso do agente comunitário
  estado         text not null default 'acionada'
                 check (estado in ('acionada','em_busca_ativa','encontrada','nao_encontrada')),
  criado_em      timestamptz not null default now()
);

-- perfis de quem tem conta
create table if not exists operador (
  user_id     uuid primary key,          -- auth.users.id
  perfil      text not null check (perfil in ('sme','cre','unidade')),
  cre         text,                      -- obrigatório para perfil 'cre'
  unidade_id  text references unidade(id)-- obrigatório para perfil 'unidade'
);

-- fila: leitura, importada do ETL (score + posição + desempate — a mesma
-- regra de data/fila.json). Não é estado que muda por interação, é
-- populada por import em lote. proxima_da_fila() é quem lê daqui.
create table if not exists fila (
  unidade_id  text not null references unidade(id),
  grupamento  text not null,
  turno       text not null,
  aluno_anon  text not null,
  posicao     integer not null,
  primary key (unidade_id, grupamento, turno, posicao)
);

create index if not exists ix_convocacao_unidade_estado on convocacao (unidade_id, estado);
create index if not exists ix_convocacao_aluno          on convocacao (aluno_anon);
create index if not exists ix_convocacao_token          on convocacao (token);
create index if not exists ix_resposta_convocacao       on resposta (convocacao_id);
create index if not exists ix_acionamento_token         on acionamento (token_agente);
create index if not exists ix_fila_unidade              on fila (unidade_id, grupamento, turno, posicao);

-- ------------------------------------------------------------
-- 2. Funções de perfil
-- ------------------------------------------------------------

create or replace function perfil_atual() returns text
language sql stable security definer set search_path = public as $$
  select perfil from operador where user_id = auth.uid()
$$;

create or replace function cre_atual() returns text
language sql stable security definer set search_path = public as $$
  select cre from operador where user_id = auth.uid()
$$;

create or replace function unidade_atual() returns text
language sql stable security definer set search_path = public as $$
  select unidade_id from operador where user_id = auth.uid()
$$;

-- Escopo territorial: a regra única que define o que cada conta enxerga.
create or replace function enxerga_unidade(alvo text) returns boolean
language sql stable security definer set search_path = public as $$
  select case perfil_atual()
    when 'sme'     then true
    when 'cre'     then exists (select 1 from unidade u
                                 where u.id = alvo and u.cre = cre_atual())
    when 'unidade' then alvo = unidade_atual()
    else false
  end
$$;

-- ------------------------------------------------------------
-- 3. O motor: uma função, três portas
--    Devolver a vaga e propor a próxima da fila. Chamada por
--    cascata, por recusa e por prazo vencido.
-- ------------------------------------------------------------

-- A fila real mora em `fila` (importada do ETL, não escrita por
-- interação). Único lugar que sabe lê-la para devolver(): pula quem já
-- tem convocação aberta na mesma vaga, para não convocar a mesma
-- criança duas vezes pela mesma posição.
create or replace function proxima_da_fila(
  p_unidade text, p_grupamento text, p_turno text, p_n integer default 1
) returns table (aluno_anon text)
language sql stable security definer set search_path = public as $$
  select f.aluno_anon
  from fila f
  where f.unidade_id = p_unidade
    and f.grupamento = p_grupamento
    and f.turno = p_turno
    and not exists (
      select 1 from convocacao c
      where c.aluno_anon = f.aluno_anon
        and c.unidade_id = f.unidade_id
        and c.grupamento = f.grupamento
        and c.turno = f.turno
        and c.estado not in ('devolvida', 'recusou', 'vencida')
    )
  order by f.posicao asc
  limit p_n;
$$;

create or replace function devolver(p_convocacao uuid, p_motivo text, p_origem uuid default null)
returns void language plpgsql security definer set search_path = public as $$
declare v_unidade text; v_grup text; v_turno text;
begin
  update convocacao set estado = 'devolvida' where id = p_convocacao
    returning unidade_id, grupamento, turno into v_unidade, v_grup, v_turno;

  insert into devolucao (convocacao_id, motivo) values (p_convocacao, p_motivo);

  -- Nasce como 'proposta', nunca já convocada: convocar cidadão é ato
  -- com responsável. O sistema propõe, a unidade confirma em 1 clique.
  -- origem_convocacao_id é o rastro da cascata: sem ele a unidade que
  -- recebe a vaga de volta não tem como explicar de onde ela veio.
  insert into convocacao (aluno_anon, unidade_id, grupamento, turno, estado, origem_convocacao_id)
  select f.aluno_anon, v_unidade, v_grup, v_turno, 'proposta', p_origem
  from proxima_da_fila(v_unidade, v_grup, v_turno, 1) f;
end $$;

create or replace function matricular(p_convocacao uuid)
returns void language plpgsql security definer set search_path = public as $$
declare v_aluno text; r record;
begin
  update convocacao set estado = 'matriculada' where id = p_convocacao
    returning aluno_anon into v_aluno;

  -- A cascata: uma matrícula devolve todas as outras posições da criança.
  -- Média de 2,76 posições por matriculado, 337.870 travadas em 2025.
  for r in select id from convocacao
           where aluno_anon = v_aluno and id <> p_convocacao
             and estado not in ('matriculada','devolvida','recusou','vencida')
  loop
    perform devolver(r.id, 'cascata', p_convocacao);
  end loop;
end $$;

-- ------------------------------------------------------------
-- 4. RLS
-- ------------------------------------------------------------

alter table unidade     enable row level security;
alter table convocacao  enable row level security;
alter table resposta    enable row level security;
alter table tentativa   enable row level security;
alter table devolucao   enable row level security;
alter table acionamento enable row level security;
alter table operador    enable row level security;
alter table fila        enable row level security;

-- unidade: catálogo, legível por qualquer conta autenticada
create policy unidade_leitura on unidade
  for select to authenticated using (true);

-- fila: catálogo (importado do ETL), mesma regra de unidade
create policy fila_leitura on fila
  for select to authenticated using (true);

-- operador: cada conta lê apenas o próprio registro
create policy operador_proprio on operador
  for select to authenticated using (user_id = auth.uid());

-- convocação: escopo territorial do perfil
create policy convocacao_leitura on convocacao
  for select to authenticated using (enxerga_unidade(unidade_id));

create policy convocacao_escrita on convocacao
  for update to authenticated using (enxerga_unidade(unidade_id))
                            with check (enxerga_unidade(unidade_id));

-- tentativa e acionamento: seguem a convocação
create policy tentativa_leitura on tentativa
  for select to authenticated using (exists (
    select 1 from convocacao c where c.id = convocacao_id and enxerga_unidade(c.unidade_id)));

create policy tentativa_registro on tentativa
  for insert to authenticated with check (exists (
    select 1 from convocacao c where c.id = convocacao_id and enxerga_unidade(c.unidade_id)));

create policy acionamento_leitura on acionamento
  for select to authenticated using (exists (
    select 1 from convocacao c where c.id = convocacao_id and enxerga_unidade(c.unidade_id)));

create policy resposta_leitura on resposta
  for select to authenticated using (exists (
    select 1 from convocacao c where c.id = convocacao_id and enxerga_unidade(c.unidade_id)));

create policy devolucao_leitura on devolucao
  for select to authenticated using (exists (
    select 1 from convocacao c where c.id = convocacao_id and enxerga_unidade(c.unidade_id)));

-- ------------------------------------------------------------
-- 5. Minimização — o ponto de LGPD que vale no pitch
--
--    A unidade age sobre a criança, mas NÃO precisa saber por que ela
--    pontuou. Critérios sensíveis (violência doméstica, uso de drogas
--    no núcleo familiar, familiar ex-presidiário) ficam fora do alcance
--    dela: quem valida na origem é a Secretaria.
--
--    Por isso a pontuação e os critérios não moram em `convocacao`.
--    A unidade recebe uma visão sem eles.
-- ------------------------------------------------------------

create or replace view convocacao_unidade
with (security_invoker = true) as
  select c.id, c.token, c.aluno_anon, c.unidade_id, c.grupamento, c.turno,
         c.prazo_em, c.estado, c.aberta_em, c.criado_em,
         -- rastro da cascata: de qual criança/unidade a vaga voltou.
         -- Nunca pontuação nem critério — isso não entra aqui em nenhuma versão.
         oc.aluno_anon as origem_aluno,
         ou.nome       as origem_unidade
  from convocacao c
  left join convocacao oc on oc.id = c.origem_convocacao_id
  left join unidade ou    on ou.id = oc.unidade_id;

-- ------------------------------------------------------------
-- 6. Acesso por link, sem conta
--
--    Família e agente comunitário não têm usuário. O token é a
--    credencial, e ele abre exatamente uma convocação — nunca uma
--    lista, nunca uma busca. Implementado como função security
--    definer chamada por RPC, e não como policy de tabela: assim
--    não existe caminho para enumerar tokens.
-- ------------------------------------------------------------

create or replace function ficha_por_token(p_token text)
returns table (
  aluno_anon text, unidade_nome text, bairro text, grupamento text,
  prazo_em date, estado text
) language sql security definer set search_path = public as $$
  update convocacao set aberta_em = coalesce(aberta_em, now())
   where token = p_token;              -- abrir o link já é o registro de que chegou
  select c.aluno_anon, u.nome, u.bairro, c.grupamento, c.prazo_em, c.estado
  from convocacao c join unidade u on u.id = c.unidade_id
  where c.token = p_token;
$$;

create or replace function responder(p_token text, p_valor text, p_data date default null)
returns void language plpgsql security definer set search_path = public as $$
declare v_id uuid; v_estado text;
begin
  select id, estado into v_id, v_estado from convocacao where token = p_token;
  if v_id is null then raise exception 'link inválido'; end if;

  -- Caso de borda 2: pode mudar de ideia enquanto a vaga não foi devolvida.
  if v_estado in ('devolvida','matriculada','vencida') then
    raise exception 'esta vaga já foi encerrada';
  end if;

  insert into resposta (convocacao_id, valor, data_escolhida)
  values (v_id, p_valor, p_data);

  -- A recusa NÃO devolve sozinha. Ela marca, e a unidade libera em 1
  -- clique. Sem isso, quem tiver o link recusa a vaga da família.
  -- Mesmo assim a vaga volta em horas, e não em três dias.
  update convocacao
     set estado = case p_valor when 'vou' then 'respondeu_vou'
                               when 'nao_vou' then 'recusou'
                               else estado end
   where id = v_id;
end $$;

revoke all on function ficha_por_token(text) from public;
revoke all on function responder(text, text, date) from public;
grant execute on function ficha_por_token(text) to anon;
grant execute on function responder(text, text, date) to anon;

-- ------------------------------------------------------------
-- 7. O que fica de fora, e por quê
--
--  · SSO pelo Registro Municipal Integrado — é o passo seguinte;
--    a tabela `operador` é o ponto de encaixe.
--  · Auditoria de leitura — em produção é obrigatória para dado de
--    criança. Não cabia em 5 horas.
--  · Rotação e expiração de token — hoje o token vale enquanto a
--    convocação existe. Em produção precisa de prazo próprio.
--  · Sincronização de `fila` — hoje é import em lote (mesmo cálculo do
--    ETL). Sem pipeline automático: se a fila mudar, alguém reimporta.
-- ------------------------------------------------------------

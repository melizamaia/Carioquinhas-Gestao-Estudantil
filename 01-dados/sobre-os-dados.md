# Dados do desafio

Fonte: https://github.com/CIT-SME-RJ/dadoscreche

Dados anonimizados de inscrição em creches do Rio (2021–2025), 343.308 inscrições em 872 unidades. Não baixei os arquivos ainda (são grandes) — clonar o repo direto nesta pasta quando for mexer nos dados.

## Estrutura do repositório de dados

```
dadoscreche/
├── Bases IC_ ClassificadoseFila/
│   ├── 01_QueryA_InscricoesPorAno.csv.gz       (837.179 linhas — inscrições por ano)
│   ├── 02_QueryB_RespostasSocioEconomicas.csv.gz (4.357.119 linhas — respostas do questionário socioeconômico)
│   ├── 03_QueryC_PerguntasComDescricao.csv      (65 linhas — catálogo de perguntas/pontuação)
│   └── README_dicionario_dados.md               (dicionário de dados)
├── OferecimentosEvagas/                          (oferta de vagas)
├── Microáreas_SME_revisãoIPP/                    (microáreas)
├── NascidosvivosRJ.xlsx                          (nascidos vivos — referência de demanda)
```

## Pontos de atenção

- Encoding UTF-8 com BOM, separador `;`
- Diretório de unidades (872 unidades) não tem cabeçalho — usar `header=None`
- 221 de 4,36M respostas não têm inscrição correspondente; 8.162 inscrições (2,4%) sem resposta registrada
- Pontuação de classificação muda por ano (ex.: peso de deficiência caiu de 100 para 25 pontos entre 2023–2024)
- Aviso do próprio dataset: indicadores gerados não representam a realidade — anonimização generaliza data de nascimento (ano-mês) e endereço (nível de bairro)

## Como puxar os dados

```
git clone https://github.com/CIT-SME-RJ/dadoscreche.git
```

## Dados disponibilizados (slide oficial do evento)

Foto: [`../00-desafio/imagens/dados-disponibilizados.jpg`](../00-desafio/imagens/dados-disponibilizados.jpg). Confirma os números do repo — base cobre os processos seletivos de 2021 a 2025 (SME-Rio); crianças e responsáveis são identificados por código anônimo.

| Tabela | Descrição | Quant. |
|---|---|---|
| Inscrições por opção | Cada opção de creche escolhida dentro de uma inscrição, com unidade, turno e situação | 837.179 |
| Respostas socioeconômicas | Respostas ao questionário de critérios de vulnerabilidade | ± 436 MB (não totalizado) |
| Perguntas por processo | Catálogo de critérios e pontuação vigente em cada processo seletivo | 65 |
| Unidades escolares | Cadastro de creches e EDIs, com endereço e tipo de gestão | 2.188 |

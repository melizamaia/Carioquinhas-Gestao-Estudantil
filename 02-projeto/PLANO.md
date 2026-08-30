# Plano de desenvolvimento — Grupo 18

> **Superado às 11h30 por [`ROADMAP.md`](./ROADMAP.md).**
>
> Este arquivo continha o plano da manhã, escrito antes da análise exploratória fechar
> ([`03-etl/ACHADOS.md`](../03-etl/ACHADOS.md)). Ficou desatualizado em três pontos que
> importam, e por isso foi esvaziado em vez de mantido:
>
> - **Os três números do pitch mudaram.** Os antigos ("dias de vaga ociosa", "taxa de
>   não-comparecimento") não saem da base — não há timestamp de convocação nem de expiração.
> - **A stack mudou.** Saiu Next.js na Vercel, entrou site estático no Render, com o ETL em
>   DuckDB e o texto gerado pelo Claude em tempo de build.
> - **O motivo de cortar o módulo de recursos mudou.** Existe dado de lotação; o corte é por
>   decisão de escopo, não por ausência de dado. A redação antiga cairia na primeira pergunta
>   do júri.
>
> **Documentos vivos:**
> - [`PRD.md`](./PRD.md) — o problema, a solução, os requisitos, a régua de linguagem
> - [`ROADMAP.md`](./ROADMAP.md) — escopo congelado, cronograma, stack, armadilhas do ETL
> - [`../03-etl/ACHADOS.md`](../03-etl/ACHADOS.md) — a evidência por trás de cada número

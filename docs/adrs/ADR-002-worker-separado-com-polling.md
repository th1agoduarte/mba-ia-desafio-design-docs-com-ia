# ADR-002: Worker em processo separado, lendo a outbox por polling a cada 2 segundos

## Status

Aceito

- **Data:** reunião técnica de quinta-feira, 09:00 (registro em 2026-11-15)
- **Decisores:** Larissa, Diego, Bruno; Marcos validou a latência
- **Relacionados:** [ADR-001](ADR-001-outbox-no-mysql.md), [ADR-003](ADR-003-retry-com-backoff-e-dlq.md)

## Contexto

Com a outbox ([ADR-001](ADR-001-outbox-no-mysql.md)), alguém precisa ler os eventos pendentes e fazer as chamadas HTTP. Requisitos:

1. Os clientes consideram "tempo real" qualquer coisa abaixo de 10 segundos ([09:02] Marcos).
2. A entrega não pode morrer junto com a API: "se a API reinicia, perde o worker" ([09:11] Diego).
3. Mesma stack e mesmo banco ([09:11] Bruno; [09:11] Diego).

O MySQL não tem um mecanismo de notificação para processos externos equivalente ao `LISTEN/NOTIFY` do Postgres. Triggers do MySQL só executam SQL ([09:09] Diego).

## Decisão

- **Polling em loop a cada 2 segundos:** busca os eventos pendentes mais antigos em batch pequeno, processa e marca ([09:08], [09:09] Diego). Registrado como decisão: "Worker em polling, 2s" ([09:10] Larissa). Marcos confirmou que serve ([09:10] Marcos).
- **Processo separado da API:**
  - nova entry-point `src/worker.ts` (novo), no mesmo molde de `src/server.ts`, e script `npm run worker` ([09:11] Larissa; [09:28] Bruno);
  - a lógica de processamento fica dentro do módulo, em `src/modules/webhooks/webhook.worker.ts` (novo) ([09:28] Bruno).
- **Mesmo banco, PrismaClient próprio:** "PrismaClient é por processo. Mesmo banco, mesma DATABASE_URL, mas instância nova" ([09:30] Bruno). O worker importa `src/config/database.ts`, que cria uma instância por processo.
- **Uma única instância do worker.** A ordem de entrega por `order_id` segue o `created_at` da outbox. Não há garantia de ordem global ([09:12] Diego). Isso fica documentado como **limitação conhecida** ([09:13] Larissa), e os clientes não pediram ordem global ([09:14] Marcos).

## Alternativas Consideradas

| ID | Alternativa | Por que foi descartada |
|---|---|---|
| ADR-002-ALT-01 | **Trigger no banco** para acordar o worker de forma reativa ([09:09] Bruno) | Trigger do MySQL não notifica processo externo. Seria preciso improvisar (escrever em arquivo, chamar um endpoint), o que "fica esquisito". Polling de 2 s já atende o requisito de < 10 s ([09:09] Diego) |
| ADR-002-ALT-02 | **Worker dentro do processo da API** (implícito na exigência de [09:11] Diego) | Um restart ou deploy da API para a entrega. "Só não pode ser o mesmo processo" ([09:11] Diego) |
| ADR-002-ALT-03 | **Vários workers em paralelo** ([09:12] Diego) | Perde a ordem por `order_id`. Escalar com particionamento por `order_id` ou lock pessimista é "problema do futuro" ([09:13] Diego) |

## Consequências

**Positivas**
- Atende os < 10 s com folga: no pior caso, o evento espera um ciclo de 2 s antes da primeira tentativa ([09:10] Larissa).
- Deploys e restarts da API não afetam a entrega, e vice-versa ([09:11] Diego).
- Implementação simples, sem dependência nova ([09:29] Bruno, sobre não adicionar nada novo).

**Negativas**
- Consultas ao banco a cada 2 s mesmo sem eventos (custo baixo, graças ao índice por status, [09:08] Diego).
- Um único worker é ponto único de falha da *entrega*. Não há perda de dados: os eventos acumulam na outbox até o worker voltar.
- A ordem por pedido depende de rodar uma instância só. Escalar horizontalmente exige uma nova decisão (ver [RFC](../RFC.md#6-questões-em-aberto)).

**Trade-off:** trocamos reatividade instantânea e escala horizontal por simplicidade operacional e ordem por pedido, dentro do limite de 10 s pedido pelos clientes.

## Referências

- Transcrição: [09:08]–[09:14], [09:28], [09:30]
- Código: `src/server.ts` (modelo de bootstrap e shutdown), `src/config/database.ts`, `package.json` (scripts)

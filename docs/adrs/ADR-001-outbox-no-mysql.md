# ADR-001: Padrão Outbox no MySQL existente, na mesma transação da mudança de status

## Status

Aceito

- **Data:** reunião técnica de quinta-feira, 09:00 (registro em 2026-11-15)
- **Decisores:** Larissa (Tech Lead), Diego (Plataforma), Bruno (Pedidos)
- **Relacionados:** [ADR-002](ADR-002-worker-separado-com-polling.md), [ADR-005](ADR-005-at-least-once-com-x-event-id.md), [ADR-007](ADR-007-payload-snapshot-na-insercao.md)

## Contexto

Três clientes B2B querem ser avisados quando o status dos pedidos deles muda. Hoje eles fazem polling em `GET /orders` ([09:00] Marcos). A mudança de status acontece em `OrderService.changeStatus` (`src/modules/orders/order.service.ts`), dentro de um `prisma.$transaction` que já faz bastante coisa:
- valida a transição na máquina de estados de `src/modules/orders/order.status.ts`;
- debita ou repõe estoque;
- atualiza `orders`;
- grava `order_status_history`.

Bruno descreveu essa transação como "pesada" ([09:04] Bruno).

Precisamos de um mecanismo que:
1. não deixe uma chamada HTTP a um cliente lento travar mudanças de status de outros pedidos ([09:04] Bruno);
2. não exija desfazer a mudança de status quando o cliente está fora do ar ([09:04] Bruno);
3. garanta que todo status confirmado gere um evento, e que nenhum evento exista para um status que sofreu rollback ([09:06] Diego, [09:40] Bruno).

O time é pequeno e não quer operar infraestrutura nova ([09:07] Diego).

## Decisão

Adotar o **padrão Outbox no MySQL que a aplicação já usa** ([09:06] Diego; "Tá decidido então: outbox em MySQL", [09:08] Larissa):

- Dentro da mesma transação de `changeStatus`, uma linha é inserida na tabela `webhook_outbox`. Se essa inserção falhar, a transação inteira sofre rollback: "não pode ter caso de status mudar e evento não sair" ([09:40] Bruno; "Essencial", [09:41] Diego).
- A tabela tem índice por status (pendente, processando, falhou, entregue) e por `created_at` ([09:08] Diego).
- Um processo separado lê a outbox e faz as chamadas HTTP. Essa parte está em [ADR-002](ADR-002-worker-separado-com-polling.md).
- A inserção é feita por uma função que recebe o client da transação corrente, `publishWebhookEvent(tx, order, fromStatus, toStatus)` ([09:41] Bruno; "função pura recebendo o tx", [09:41] Diego).
- Só entra na outbox o evento que algum webhook do customer quer receber. O filtro é aplicado na inserção ([09:34] Bruno; [09:34] Diego).

O detalhamento da tabela e da função está no [FDD](../FDD.md#4-modelo-de-dados).

## Alternativas Consideradas

| ID | Alternativa | Por que foi descartada |
|---|---|---|
| ADR-001-ALT-01 | **Disparo síncrono** da chamada HTTP dentro de `changeStatus` ([09:03] Larissa) | Um cliente lento trava a transação e as mudanças de status de outros pedidos. Com o cliente fora do ar, não dá para fazer rollback da mudança de status ([09:04] Bruno). "Síncrono está fora de questão" ([09:06] Diego) |
| ADR-001-ALT-02 | **Redis Streams** ou fila equivalente ([09:07] Larissa) | Exige subir e operar infraestrutura nova. Para um time pequeno, Redis Cluster é *overengineering* ([09:07] Diego). Além disso, publicar num sistema externo fora da transação SQL perde a atomicidade que a outbox dá de graça |

## Consequências

**Positivas**
- Atomicidade: o evento existe se, e somente se, a mudança de status foi confirmada ([09:06] Diego).
- Nenhuma infraestrutura nova: mesmo MySQL, mesmo Prisma, mesma `DATABASE_URL` ([09:07] Diego, [09:30] Bruno).
- A latência da API de pedidos deixa de depender dos clientes, porque a chamada HTTP sai do caminho da requisição ([09:04] Bruno).

**Negativas**
- A transação de `changeStatus` ganha uma leitura (webhooks ativos do customer) e uma escrita a mais ([09:40] Bruno).
- A tabela cresce continuamente. O arquivamento de linhas entregues ("depois de 30 dias ou assim") ficou **fora do escopo** desta feature ([09:08] Diego).
- A entrega deixa de ser imediata: depende do intervalo do worker ([ADR-002](ADR-002-worker-separado-com-polling.md)).

**Trade-off:** aceitamos uma transação de status um pouco maior e uma tabela que cresce, em troca de consistência garantida entre pedido e evento sem operar infraestrutura nova.

## Referências

- Transcrição: [09:03]–[09:08], [09:34], [09:40]–[09:41]
- Código: `src/modules/orders/order.service.ts` (`changeStatus`), `prisma/schema.prisma`

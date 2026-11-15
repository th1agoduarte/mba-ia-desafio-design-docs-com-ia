# ADR-007: Payload do evento renderizado (snapshot) no momento da inserção na outbox

## Status

Aceito

- **Data:** reunião técnica de quinta-feira, conversa final após a saída de Marcos e Sofia (registro em 2026-11-15)
- **Decisores:** Larissa, Diego, Bruno
- **Relacionados:** [ADR-001](ADR-001-outbox-no-mysql.md), [ADR-005](ADR-005-at-least-once-com-x-event-id.md)

## Contexto

O evento da outbox pode ser enviado segundos ou horas depois da mudança de status: o polling é de 2 s e o retry chega a ~15 h ([ADR-002](ADR-002-worker-separado-com-polling.md), [ADR-003](ADR-003-retry-com-backoff-e-dlq.md)). Nesse intervalo o pedido pode mudar de novo. Bruno perguntou se a outbox guarda o payload já renderizado ou só o `order_id`, para renderizar na hora do envio ([09:51] Bruno).

O payload combinado é JSON enxuto, com estes campos ([09:43] Diego):
- `event_id`;
- `event_type` (ex.: `order.status_changed`);
- `timestamp` ISO 8601;
- `order_id`, `order_number`, `customer_id`;
- `from_status`, `to_status`;
- campos básicos do pedido, como `total_cents`.

Não leva os itens do pedido: quem quiser detalhes consulta `GET /orders/:id` ([09:43] Diego; [09:44] Bruno).

## Decisão

**O payload é renderizado e gravado na outbox no momento da inserção,** dentro da transação de `changeStatus`. Assim, o evento reflete o estado do pedido no instante da mudança de status ([09:52] Larissa; "snapshot na inserção", [09:52] Diego; "Decidido", [09:52] Bruno).

## Alternativas Consideradas

| ID | Alternativa | Por que foi descartada |
|---|---|---|
| ADR-007-ALT-01 | **Guardar só o `order_id` e renderizar no envio** ([09:51] Bruno) | Se o pedido mudar depois, o evento passa a descrever um estado posterior ao da transição que ele anuncia, o "caso esquisito" ([09:52] Larissa). Em retentativas, o mesmo `X-Event-Id` poderia chegar com conteúdos diferentes, o que quebra a deduplicação do [ADR-005](ADR-005-at-least-once-com-x-event-id.md) |

## Consequências

**Positivas**
- Cada evento é um fato imutável: retentativas e replay reenviam exatamente o mesmo conteúdo com o mesmo `X-Event-Id`.
- O worker não precisa ler `orders` no envio. Basta a linha da outbox, o que simplifica e reduz consultas.
- A assinatura HMAC é calculada sobre o snapshot serializado ([ADR-004](ADR-004-hmac-sha256-com-secret-por-endpoint.md)).

**Negativas**
- A linha da outbox fica maior, porque guarda o JSON completo em vez de um id. É um efeito pequeno, já que o payload é enxuto ([09:43] Diego), mas soma ao crescimento da tabela, cujo arquivamento ficou fora do escopo ([09:08] Diego).
- A renderização acontece dentro da transação de status e acrescenta um pouco de trabalho a ela ([ADR-001](ADR-001-outbox-no-mysql.md)).

**Trade-off:** aceitamos linhas maiores e um pouco mais de trabalho na transação, em troca de eventos imutáveis e coerentes com a garantia at-least-once.

## Referências

- Transcrição: [09:43]–[09:44], [09:51]–[09:52]
- Código: `src/modules/orders/order.service.ts` (o `order` lido no início de `changeStatus` já traz `orderNumber`, `customerId` e `totalCents`, conforme `prisma/schema.prisma`)

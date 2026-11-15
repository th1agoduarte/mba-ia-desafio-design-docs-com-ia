# ADR-005: Garantia de entrega at-least-once, com X-Event-Id para deduplicação no cliente

## Status

Aceito

- **Data:** reunião técnica de quinta-feira, 09:00 (registro em 2026-11-15)
- **Decisores:** Diego, Larissa; Sofia registrou a ressalva; Marcos assumiu a comunicação aos clientes
- **Relacionados:** [ADR-001](ADR-001-outbox-no-mysql.md), [ADR-003](ADR-003-retry-com-backoff-e-dlq.md), [ADR-007](ADR-007-payload-snapshot-na-insercao.md)

## Contexto

Com outbox, worker e retry ([ADR-001](ADR-001-outbox-no-mysql.md), [ADR-002](ADR-002-worker-separado-com-polling.md), [ADR-003](ADR-003-retry-com-backoff-e-dlq.md)), um mesmo evento pode ser enviado mais de uma vez. Dois exemplos:
- o cliente processou a requisição, mas respondeu depois do timeout de 10 s ([09:42] Diego);
- o worker caiu entre o envio e a marcação como entregue.

Precisamos dizer explicitamente aos clientes que garantia oferecemos e como eles lidam com duplicatas.

## Decisão

- **Garantia at-least-once.** O cliente pode receber o mesmo evento duas vezes e precisa estar preparado para isso ([09:24] Diego).
- **Cada evento leva um `X-Event-Id`:** um UUID gerado quando o evento entra na outbox, único por evento. O cliente deduplica por esse id ([09:25] Diego).
- **Comunicação ao cliente:** Marcos documenta isso com destaque no portal de desenvolvedor ([09:26] Marcos).

Decisão fechada em "At-least-once com X-Event-Id pra dedup do lado do cliente. Decisão" ([09:26] Larissa).

O id é gerado na inserção e fica gravado no snapshot do evento ([ADR-007](ADR-007-payload-snapshot-na-insercao.md)). Por isso as retentativas reenviam o **mesmo** `X-Event-Id`. O replay da DLQ também mantém o id, conforme proposta do FDD, que é coerente com "único por evento".

## Alternativas Consideradas

| ID | Alternativa | Por que foi descartada |
|---|---|---|
| ADR-005-ALT-01 | **Exactly-once** ([09:25] Diego) | Exigiria coordenação dos dois lados e "fica muito mais complexo". At-least-once com event_id resolve a grande maioria dos casos e é o que Stripe e GitHub fazem ([09:25] Diego) |
| ADR-005-ALT-02 | **At-most-once**, sem retentativas. Não discutida na reunião: contraponto natural | Contradiz a decisão de retry do [ADR-003](ADR-003-retry-com-backoff-e-dlq.md): um cliente fora do ar perderia eventos |

## Consequências

**Positivas**
- Nenhum evento confirmado se perde por falha transitória. Em último caso, ele fica na DLQ ([ADR-003](ADR-003-retry-com-backoff-e-dlq.md)).
- Modelo simples do nosso lado e familiar para quem já integra com Stripe ou GitHub ([09:25] Diego).

**Negativas**
- **Transfere responsabilidade para o cliente,** que precisa implementar a deduplicação ([09:25] Sofia).
- Um cliente que ignora o `X-Event-Id` pode processar duplicado. A mitigação é a documentação no portal ([09:26] Marcos).

**Trade-off:** trocamos a garantia mais forte (exactly-once) por um modelo simples e padrão de mercado, aceitando que a deduplicação é responsabilidade do cliente.

## Referências

- Transcrição: [09:24]–[09:26], [09:42]
- Código: `prisma/schema.prisma` (ids `uuid()`), `package.json` (dependência `uuid` já presente)

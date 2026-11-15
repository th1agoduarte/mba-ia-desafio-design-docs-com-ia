# Architectural Decision Records

Este diretório armazena os ADRs (Architectural Decision Records) do projeto. Cada decisão arquitetural relevante fica num arquivo próprio, nomeado no formato `ADR-NNN-titulo-em-kebab-case.md`, que é o formato exigido pelo desafio. Os ADRs seguem uma variante do MADR com as seções Status, Contexto, Decisão, Alternativas Consideradas e Consequências.

ADRs da feature **Sistema de Webhooks de Notificação de Pedidos**, decididos na reunião registrada em [`TRANSCRICAO.md`](../../TRANSCRICAO.md):

| ADR | Decisão | Status |
|---|---|---|
| [ADR-001](ADR-001-outbox-no-mysql.md) | Padrão Outbox no MySQL, na mesma transação do `changeStatus` | Aceito |
| [ADR-002](ADR-002-worker-separado-com-polling.md) | Worker em processo separado, com polling de 2 s | Aceito |
| [ADR-003](ADR-003-retry-com-backoff-e-dlq.md) | Retry com backoff 1m/5m/30m/2h/12h e DLQ em tabela separada | Aceito (interpretação a confirmar) |
| [ADR-004](ADR-004-hmac-sha256-com-secret-por-endpoint.md) | HMAC-SHA256, secret por endpoint e rotação com 24 h de convivência | Aceito |
| [ADR-005](ADR-005-at-least-once-com-x-event-id.md) | At-least-once com `X-Event-Id` | Aceito |
| [ADR-006](ADR-006-reuso-dos-padroes-do-projeto.md) | Reuso dos padrões existentes do projeto | Aceito |
| [ADR-007](ADR-007-payload-snapshot-na-insercao.md) | Payload renderizado (snapshot) na inserção | Aceito |

A proposta consolidada está no [RFC](../RFC.md) e a especificação de implementação está no [FDD](../FDD.md).

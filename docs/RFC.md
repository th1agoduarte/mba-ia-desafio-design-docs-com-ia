# RFC-001: Sistema de Webhooks de Notificação de Pedidos

## 1. Metadados

| Campo | Valor |
|---|---|
| **Autor** | Thiago Duarte, consolidando a reunião técnica conduzida por Larissa (Tech Lead) |
| **Status** | Em revisão |
| **Data** | 2026-11-15 (a reunião de origem foi numa quinta-feira às 09:00; a transcrição não registra o dia) |
| **Revisores** | Larissa (Tech Lead), Marcos (Product Manager), Bruno (Engenheiro Pleno, Pedidos), Diego (Engenheiro Sênior, Plataforma), Sofia (Engenheira de Segurança) |
| **Documentos** | [PRD](PRD.md), produto · [FDD](FDD.md), implementação · [ADRs](adrs/README.md), decisões · [Tracker](TRACKER.md), origem de cada item |

## 2. Resumo executivo (TL;DR)

Propomos notificar os clientes B2B por **webhooks de saída** a cada mudança de status de pedido.

- **Registro do evento:** o evento é gravado numa **outbox no MySQL**, na mesma transação que muda o status.
- **Entrega:** um **worker em processo separado** lê a outbox a cada **2 s** e faz a chamada HTTP.
- **Garantia:** entrega **at-least-once**, com `X-Event-Id` para deduplicação.
- **Segurança:** assinatura **HMAC-SHA256 com secret por endpoint**, rotacionável com 24 h de convivência.
- **Falhas:** **retry com backoff** de 1m/5m/30m/2h/12h; esgotadas as tentativas, o evento vai para uma **DLQ** com replay manual por um admin.
- **Implementação:** tudo reaproveita os padrões que o OMS já tem.

Não há infraestrutura nova. A estimativa é de **três sprints**, incluindo a revisão de segurança.

## 3. Contexto e problema

Atlas Comercial, MaxDistribuição e Nova Cargo pediram formalmente para ser notificados quando o status dos pedidos muda. Hoje eles fazem polling em `GET /orders`, o que deixa a integração lenta e cara. A Atlas sinalizou que pode migrar para um concorrente se a solução não sair até o fim do trimestre ([09:00] Marcos). Para eles, "tempo real" é qualquer coisa abaixo de 10 s ([09:02] Marcos). O fluxo é só de saída ([09:02] Marcos; [09:03] Sofia).

O OMS (Node.js + TypeScript, Express, Prisma/MySQL) não tem nenhum mecanismo de eventos, filas ou notificação externa. A mudança de status é feita em `OrderService.changeStatus` (`src/modules/orders/order.service.ts`), numa transação que:
- valida a máquina de estados (`src/modules/orders/order.status.ts`);
- movimenta estoque;
- grava `orders` e `order_status_history`.

Bruno descreveu essa transação como "pesada" ([09:04] Bruno). O problema é publicar esses eventos para sistemas externos sem tornar essa transação dependente da disponibilidade dos clientes, e sem perder ou inventar eventos.

## 4. Proposta técnica

Visão geral. O detalhamento de tabelas, contratos e erros fica no [FDD](FDD.md).

```
 API (src/server.ts)                          Worker (src/worker.ts, novo)
 PATCH /orders/:id/status                      a cada 2 s
   └─ changeStatus ─ transação ─┐                │
        orders / history        │                ▼
        webhook_outbox  ◄───────┘      lê pendentes ─► assina (HMAC) ─► POST https://cliente
                                                  │            ├─ 2xx  → entregue
                                                  │            └─ erro → retry (backoff) ─► DLQ
 CRUD de webhooks, rotação de secret,             ▼
 histórico de entregas, replay da DLQ (ADMIN)   webhook_deliveries / webhook_dead_letter
```

| ID | Proposta | Decisão |
|---|---|---|
| RFC-PROP-01 | **Outbox transacional:** `changeStatus` grava o evento na outbox dentro da própria transação. Se essa gravação falhar, a mudança de status sofre rollback | [ADR-001](adrs/ADR-001-outbox-no-mysql.md) |
| RFC-PROP-02 | **Filtro na origem:** o evento só entra na outbox se algum webhook ativo do customer assina aquele status | [ADR-001](adrs/ADR-001-outbox-no-mysql.md) |
| RFC-PROP-03 | **Worker separado:** processo próprio com polling de 2 s, PrismaClient próprio no mesmo banco e uma única instância, o que preserva a ordem por pedido | [ADR-002](adrs/ADR-002-worker-separado-com-polling.md) |
| RFC-PROP-04 | **Resiliência:** timeout de 10 s por chamada, até 5 retentativas com backoff de 1m/5m/30m/2h/12h (leitura a confirmar, RFC-Q-07), e depois DLQ com replay manual restrito a ADMIN | [ADR-003](adrs/ADR-003-retry-com-backoff-e-dlq.md) |
| RFC-PROP-05 | **Autenticidade:** HMAC-SHA256 sobre o corpo, com secret gerada pela plataforma para cada endpoint, rotação com 24 h de convivência e `https` obrigatório | [ADR-004](adrs/ADR-004-hmac-sha256-com-secret-por-endpoint.md) |
| RFC-PROP-06 | **Semântica de entrega:** at-least-once, com `X-Event-Id` estável entre retentativas | [ADR-005](adrs/ADR-005-at-least-once-com-x-event-id.md) |
| RFC-PROP-07 | **Evento imutável:** payload enxuto, sem itens, gravado como snapshot na inserção | [ADR-007](adrs/ADR-007-payload-snapshot-na-insercao.md) |
| RFC-PROP-08 | **Padrões do projeto:** módulo `src/modules/webhooks` (novo), erros `AppError` com prefixo `WEBHOOK_`, Pino, `errorMiddleware`, Zod e `requireRole` | [ADR-006](adrs/ADR-006-reuso-dos-padroes-do-projeto.md) |
| RFC-PROP-09 | **Superfície de API para o cliente:** cadastrar, editar, remover e listar webhooks por customer; rotacionar a secret; consultar as últimas 100 entregas. Para o admin: replay da DLQ | [09:31]–[09:36]; contratos no [FDD §6](FDD.md#6-contratos-públicos) |

**Prazo** ([09:46] Larissa):
- modelagem de outbox e DLQ: 1 sprint;
- worker e retry: 1 sprint;
- CRUD e histórico de entregas: ½ sprint;
- integração com pedidos e testes ponta a ponta: ½ sprint;
- HMAC e validações: o restante;
- revisão de segurança da Sofia: pelo menos 2 dias úteis antes do deploy ([09:46] Sofia).

Total: **três sprints**.

## 5. Alternativas consideradas

| ID | Alternativa | Trade-off que levou ao descarte | Origem |
|---|---|---|---|
| RFC-ALT-01 | **Chamada HTTP síncrona** dentro de `changeStatus` | Seria a solução mais simples e imediata, mas acopla a transação de status à latência e à disponibilidade de cada cliente. Um cliente lento trava outros pedidos, e um cliente fora do ar não pode desfazer uma mudança de status | [09:04] Bruno; [09:06] Diego |
| RFC-ALT-02 | **Redis Streams** ou outra fila dedicada | Daria mais throughput e reatividade, mas exige subir e operar infraestrutura nova. Para um time pequeno é *overengineering*, e publicar fora da transação SQL perde a atomicidade da outbox | [09:07] Larissa; [09:07] Diego |
| RFC-ALT-03 | **Trigger do banco** para acordar o worker | Seria mais reativo que o polling, mas o MySQL não tem `LISTEN/NOTIFY` e trigger não notifica processo externo. Os contornos possíveis são frágeis, e 2 s de polling já cumprem os < 10 s | [09:09] Bruno; [09:09] Diego |
| RFC-ALT-04 | **Exactly-once** | Seria mais confortável para o cliente, mas exige coordenação dos dois lados e muito mais complexidade. At-least-once com id de evento é o padrão de mercado | [09:25] Diego |
| RFC-ALT-05 | **Retry indefinido** ou **só 3 tentativas** | O retry indefinido deixa eventos pendurados para sempre. Com 3 tentativas, uma indisponibilidade de manhã se esgota em ~30 min, e já houve manutenção de 2 h | [09:15] Diego; [09:16] Bruno; [09:16] Diego |
| RFC-ALT-06 | **Secret global** da plataforma | Seria mais simples de gerenciar, mas o vazamento de uma secret comprometeria todos os clientes | [09:21] Sofia |

O registro detalhado de cada alternativa está nos ADRs correspondentes.

## 6. Questões em aberto

**Levantadas na reunião e não decididas ou adiadas**

| ID | Questão | Situação | Origem |
|---|---|---|---|
| RFC-Q-01 | **Rate limiting de saída:** 50 pedidos mudando em 1 minuto geram 50 chamadas ao cliente | Fora do escopo. Vamos observar e implementar se virar problema | [09:38] Diego; [09:39] Larissa |
| RFC-Q-02 | **Aviso ao cliente por e-mail** quando o webhook falha repetidamente | Próxima fase, depois de medir o impacto | [09:37] Marcos; [09:37] Larissa |
| RFC-Q-03 | **Escalar além de um worker** (particionar por `order_id` ou usar lock pessimista) | "Problema do futuro". A limitação de ordem está documentada | [09:13] Diego; [09:13] Larissa |
| RFC-Q-04 | **Endurecer a permissão do CRUD** de webhooks, hoje aberto a qualquer usuário autenticado | "Por enquanto sim. Mais pra frente a gente pode endurecer" | [09:37] Sofia |
| RFC-Q-05 | **`customer_id` no body ou no path** | A reunião deixou as duas opções. O FDD propõe o path em `/customers/:customerId/webhooks` | [09:32] Larissa |
| RFC-Q-06 | **Arquivamento das linhas entregues** da outbox ("30 dias ou assim") | Fora do escopo desta feature | [09:08] Diego |

**Lacunas identificadas ao consolidar a reunião com o código** (para a sessão de revisão que Larissa vai marcar com Bruno e Diego, [09:50] Larissa)

| ID | Questão | Por que importa |
|---|---|---|
| RFC-Q-07 | **"5 tentativas" quer dizer 5 envios ou 5 retentativas?** | Os 5 intervalos (1m/5m/30m/2h/12h) e a janela de "quase 15 horas" ([09:17] Diego) só fecham com 5 retentativas depois do envio inicial. Mas o resumo final da reunião ([09:48] Larissa) repete "total 5 tentativas", o que favorece a leitura de 5 envios. O FDD adota a leitura de 5 retentativas, que precisa ser confirmada |
| RFC-Q-08 | **Ordem por pedido durante o retry** | A ordem por `order_id` ([09:12] Diego) só vale sem falhas. Se o evento A está em backoff, o evento B do mesmo pedido pode sair antes. Bloquear B alonga a fila; não bloquear quebra a ordem. Nada foi decidido |
| RFC-Q-09 | **Assinatura durante as 24 h de convivência** | A reunião decidiu que a secret antiga continua válida ([09:21] Sofia), mas não definiu como o cliente recebe as duas assinaturas. Há uma proposta no FDD |
| RFC-Q-10 | **Armazenamento da secret em repouso** | HMAC exige a secret recuperável, então não dá para guardar só o hash. A forma de proteger a secret fica para a revisão de segurança da Sofia ([09:46] Sofia) |
| RFC-Q-11 | **Como o admin descobre o id do item da DLQ** | Só o replay foi especificado ([09:18] Diego). Não há endpoint de listagem da DLQ |
| RFC-Q-12 | **`X-Timestamp` fora da assinatura** | O HMAC cobre só os bytes do corpo ([09:22] Sofia), mas o `X-Timestamp` foi pedido para o cliente detectar replay ([09:44] Diego). Sem entrar na assinatura (ou sem o cliente usar o `timestamp` do corpo, que é assinado), o header pode ser trocado. Decidir na revisão de segurança da Sofia |

## 7. Impacto e riscos

**Impacto nos componentes existentes**
- `OrderService.changeStatus` passa a fazer uma consulta e uma inserção a mais na transação.
- O app ganha um novo router e novas tabelas no `prisma/schema.prisma`.
- Passa a existir um segundo processo para operar: `npm run worker` ([09:11] Larissa).
- A API pública de pedidos não muda.

| ID | Risco de arquitetura | Prob. | Impacto | Mitigação |
|---|---|---|---|---|
| RFC-RISK-01 | Falha na inserção da outbox derruba a mudança de status (efeito colateral do acoplamento transacional) | Baixa | Alto | Comportamento desejado ([09:40] Bruno). Inserção simples e coberta por teste de rollback |
| RFC-RISK-02 | Worker parado: eventos acumulam e a latência estoura os 10 s | Média | Médio | Sem perda (estão na outbox). Monitorar o backlog e a idade do evento mais antigo |
| RFC-RISK-03 | Polling de 2 s gera carga constante no MySQL compartilhado | Baixa | Baixo | Consulta por índice de status, em batch pequeno ([09:08] Diego) |
| RFC-RISK-04 | Rajadas de eventos para o mesmo cliente sem rate limiting | Média | Médio | Observar (RFC-Q-01). Métricas de envio por customer no FDD |
| RFC-RISK-05 | Ordem por pedido perdida com retry ou ao escalar workers | Média | Baixo | Limitação documentada. Os clientes não exigem ordem global ([09:14] Marcos). RFC-Q-03 e RFC-Q-08 |

## 8. Decisões relacionadas

- [ADR-001: Outbox no MySQL](adrs/ADR-001-outbox-no-mysql.md)
- [ADR-002: Worker separado com polling de 2 s](adrs/ADR-002-worker-separado-com-polling.md)
- [ADR-003: Retry com backoff e DLQ](adrs/ADR-003-retry-com-backoff-e-dlq.md)
- [ADR-004: HMAC-SHA256 com secret por endpoint](adrs/ADR-004-hmac-sha256-com-secret-por-endpoint.md)
- [ADR-005: At-least-once com X-Event-Id](adrs/ADR-005-at-least-once-com-x-event-id.md)
- [ADR-006: Reuso dos padrões do projeto](adrs/ADR-006-reuso-dos-padroes-do-projeto.md)
- [ADR-007: Payload snapshot na inserção](adrs/ADR-007-payload-snapshot-na-insercao.md)

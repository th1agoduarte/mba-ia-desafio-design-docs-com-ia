# FDD — Sistema de Webhooks de Notificação de Pedidos

| Campo | Valor |
|---|---|
| **Feature** | Webhooks de saída para mudanças de status de pedido |
| **Status** | Pronto para implementação, com as questões RFC-Q-07 a RFC-Q-11 a fechar na revisão |
| **Base** | [RFC-001](RFC.md) e [ADR-001 a ADR-007](adrs/README.md) |
| **Data** | 2026-11-15 |

**Convenções deste documento**
- **(novo)** marca arquivo, tabela ou script que **ainda não existe** e será criado pela feature. Todo caminho sem essa marca existe hoje no repositório.
- **Proposta: não discutido** marca escolha de implementação que a reunião não definiu. É um ponto de partida, não uma decisão, e fica sujeita à revisão com Larissa, Bruno e Diego ([09:50] Larissa).
- `[hh:mm] Nome` remete à transcrição. O [Tracker](TRACKER.md) liga cada ID deste documento à sua origem.

---

## 1. Contexto e motivação técnica

A aplicação não tem nenhum mecanismo de eventos, fila ou notificação externa. Os clientes B2B fazem polling em `GET /api/v1/orders` para saber se o status mudou ([09:00] Marcos).

O ponto de mudança de status é único: `OrderService.changeStatus` em `src/modules/orders/order.service.ts`. O método abre um `prisma.$transaction` e, em sequência:
1. lê o pedido com os itens (linhas 132–135);
2. valida a transição com `canTransition` (`src/modules/orders/order.status.ts`);
3. debita ou repõe estoque (linhas 151–156);
4. atualiza `orders` (linha 158);
5. grava `order_status_history` (linhas 159–167).

Publicar o evento nesse ponto, de forma atômica e sem chamada HTTP dentro da transação, é o núcleo técnico da feature ([ADR-001](adrs/ADR-001-outbox-no-mysql.md)).

## 2. Objetivos técnicos

| ID | Objetivo | Origem |
|---|---|---|
| FDD-OBJ-01 | Toda mudança de status confirmada gera evento para os webhooks que a assinam. Nenhum evento é gerado para uma mudança que sofreu rollback | [09:06] Diego; [09:40] Bruno |
| FDD-OBJ-02 | Primeira tentativa de entrega em menos de 10 s após o commit (polling de 2 s) | [09:02] Marcos; [09:10] Larissa |
| FDD-OBJ-03 | A transação de status nunca espera uma chamada HTTP | [09:04] Bruno |
| FDD-OBJ-04 | Nenhum evento se perde por indisponibilidade do cliente: ele é entregue ou vai para a DLQ, de onde pode ser reenviado | [09:15] Diego; [09:18] Diego |
| FDD-OBJ-05 | O cliente consegue validar origem e integridade (HMAC) e deduplicar (`X-Event-Id`) | [09:20] Sofia; [09:25] Diego |
| FDD-OBJ-06 | Nenhuma dependência ou infraestrutura nova: reuso dos padrões do projeto | [09:07] Diego; [09:30] Larissa |

## 3. Escopo e exclusões

**Incluso:**
- tabelas da feature e migration;
- função `publishWebhookEvent` integrada a `changeStatus`;
- worker com polling, retry e DLQ;
- endpoints de CRUD de webhook, rotação de secret, histórico de entregas e replay da DLQ;
- assinatura HMAC;
- validações (https, filtro de status);
- logs e métricas.

**Excluído** (com origem):

| Exclusão | Origem |
|---|---|
| Webhooks de entrada (cliente → plataforma) | [09:02] Marcos; [09:03] Sofia |
| E-mail de aviso ao cliente quando o webhook falha (próxima fase) | [09:37] Larissa |
| Rate limiting de saída (observar e decidir depois) | [09:39] Larissa |
| Dashboard ou painel visual (projeto separado do time de frontend) | [09:40] Larissa |
| Arquivamento das linhas entregues da outbox | [09:08] Diego |
| Múltiplos workers, particionamento ou lock pessimista | [09:13] Diego |
| Exactly-once | [09:25] Diego |
| Itens do pedido no payload | [09:43] Diego |
| Restringir o CRUD a papéis específicos (por enquanto, qualquer autenticado) | [09:37] Sofia |

## 4. Modelo de dados

Quatro tabelas novas em `prisma/schema.prisma`, criadas por uma migration (novo) via `npm run db:migrate`. As convenções do schema atual foram mantidas:
- ids `String @id @default(uuid()) @db.Char(36)`, porque "tudo é uuid" ([09:51] Larissa);
- `createdAt` e `updatedAt`;
- `@@map` em snake_case;
- `@@index` explícitos.

```prisma
enum WebhookOutboxStatus {   // "pendente, processando, falhou, entregue" [09:08] Diego
  PENDING
  PROCESSING
  FAILED
  DELIVERED
}

enum WebhookDeliveryResult {
  SUCCESS
  FAILURE
}

model WebhookEndpoint {          // url + secret + customer_id + estado ativo [09:21] Bruno/Sofia
  id                      String    @id @default(uuid()) @db.Char(36)
  customerId              String    @db.Char(36)
  url                     String    @db.VarChar(2048)
  secret                  String    @db.VarChar(128)   // ver RFC-Q-10 (proteção em repouso)
  previousSecret          String?   @db.VarChar(128)   // válida até previousSecretExpiresAt [09:21] Sofia
  previousSecretExpiresAt DateTime?
  statuses                Json                         // lista de OrderStatus assinados [09:33] Marcos
  active                  Boolean   @default(true)
  createdAt               DateTime  @default(now())
  updatedAt               DateTime  @updatedAt

  customer    Customer            @relation(fields: [customerId], references: [id])
  outbox      WebhookOutbox[]
  deliveries  WebhookDelivery[]
  deadLetters WebhookDeadLetter[]

  @@index([customerId])
  @@map("webhook_endpoints")
}

model WebhookOutbox {
  id                String              @id @default(uuid()) @db.Char(36)
  eventId           String              @db.Char(36)       // X-Event-Id; repete em retry e replay [09:25] Diego
  webhookEndpointId String              @db.Char(36)
  orderId           String              @db.Char(36)       // sem FK: OrderService.delete apaga pedidos CANCELLED
  eventType         String              @db.VarChar(64)    // "order.status_changed" [09:43] Diego
  payload           Json                                   // snapshot [09:52] Larissa/Diego
  status            WebhookOutboxStatus @default(PENDING)
  attempts          Int                 @default(0)        // retentativas já realizadas (0 = só a inicial)
  nextAttemptAt     DateTime            @default(now())
  lastError         String?             @db.VarChar(500)
  deliveredAt       DateTime?
  createdAt         DateTime            @default(now())
  updatedAt         DateTime            @updatedAt

  endpoint    WebhookEndpoint    @relation(fields: [webhookEndpointId], references: [id], onDelete: Cascade)
  deliveries  WebhookDelivery[]
  deadLetter  WebhookDeadLetter?

  @@index([status])        // [09:08] Diego
  @@index([createdAt])     // [09:08] Diego
  @@index([webhookEndpointId])
  @@index([orderId])
  @@map("webhook_outbox")
}

model WebhookDelivery {          // histórico de entregas [09:34] Marcos
  id                String                @id @default(uuid()) @db.Char(36)
  outboxId          String                @db.Char(36)
  webhookEndpointId String                @db.Char(36)
  eventId           String                @db.Char(36)
  attemptNumber     Int                                  // 1 = inicial, 2..6 = retentativas
  result            WebhookDeliveryResult
  httpStatus        Int?
  durationMs        Int                                  // "tempo de resposta" [09:34] Marcos
  errorCode         String?               @db.VarChar(64) // WEBHOOK_* (seção 7)
  responseBody      String?               @db.Text        // truncado; proposta: não discutido (seção 8)
  createdAt         DateTime              @default(now())

  outbox   WebhookOutbox   @relation(fields: [outboxId], references: [id], onDelete: Cascade)
  endpoint WebhookEndpoint @relation(fields: [webhookEndpointId], references: [id], onDelete: Cascade)

  @@index([webhookEndpointId, createdAt])
  @@map("webhook_deliveries")
}

model WebhookDeadLetter {        // "payload, motivo da falha e timestamp" [09:18] Diego
  id                String    @id @default(uuid()) @db.Char(36)
  outboxId          String    @db.Char(36)   // sem @unique: um evento reenviado que falha de novo ganha outra linha
  webhookEndpointId String    @db.Char(36)
  eventId           String    @db.Char(36)
  payload           Json
  failureReason     String    @db.VarChar(500)
  failedAt          DateTime  @default(now())
  replayedAt        DateTime?
  replayedById      String?   @db.Char(36)                // auditoria do replay [09:36] Sofia

  outbox   WebhookOutbox   @relation(fields: [outboxId], references: [id], onDelete: Cascade)
  endpoint WebhookEndpoint @relation(fields: [webhookEndpointId], references: [id], onDelete: Cascade)

  @@index([failedAt])
  @@map("webhook_dead_letter")
  @@index([outboxId])
}
```

No model `Customer` existente, entra a relação inversa `webhookEndpoints WebhookEndpoint[]`.

Decisões de modelagem:
- **Uma linha de outbox por endpoint de destino.**
  - **Motivo:** status, retry, DLQ e o header `X-Webhook-Id` ([09:44] Sofia) são todos por destino.
  - **Consequência:** dois webhooks do mesmo customer que assinam o mesmo status geram duas linhas, cada uma com seu `eventId`, porque é a unidade que o cliente deduplica por endpoint.
  - Proposta: não discutido.
- **`statuses` como JSON.** O filtro é feito em memória, sobre os poucos endpoints de um customer, dentro de `publishWebhookEvent`. Proposta: não discutido.
- **`WebhookEndpoint` sem `deletedAt`.** O `DELETE` remove a linha, e o cascade leva junto outbox, entregas e DLQ do endpoint. É o mesmo padrão de `onDelete: Cascade` que `OrderItem` e `OrderStatusHistory` já usam no schema. Risco em FDD-RISK-05.

## 5. Fluxos detalhados

### FDD-FLUXO-01: Criação do evento na outbox (dentro de `changeStatus`)

```
PATCH /api/v1/orders/:id/status
  └─ OrderController.changeStatus → OrderService.changeStatus
       prisma.$transaction(async (tx) => {
         1. findUnique(order + items)          (existente)
         2. valida from/to, canTransition       (existente)
         3. debita/repõe estoque                (existente)
         4. tx.order.update(status = to)        (existente)
         5. tx.orderStatusHistory.create(...)   (existente)
         6. await publishWebhookEvent(tx, order, from, to)   ◄── NOVO
         7. findUnique(refreshed) e retorno     (existente)
       })
```

`publishWebhookEvent` fica em `src/modules/webhooks/webhook.publisher.ts` (novo). É uma função que recebe o `tx`, sem repository injetado ([09:41] Bruno; [09:41] Diego):

```ts
export async function publishWebhookEvent(
  tx: Prisma.TransactionClient,
  order: Pick<Order, 'id' | 'orderNumber' | 'customerId' | 'totalCents'>,
  fromStatus: OrderStatus,
  toStatus: OrderStatus,
): Promise<number> {
  const endpoints = await tx.webhookEndpoint.findMany({
    where: { customerId: order.customerId, active: true },
  });
  const targets = endpoints.filter((e) => (e.statuses as OrderStatus[]).includes(toStatus));
  if (targets.length === 0) return 0;               // filtro na inserção [09:34] Bruno

  const occurredAt = new Date().toISOString();       // timestamp ISO 8601 [09:43] Diego
  await tx.webhookOutbox.createMany({
    data: targets.map((endpoint) => {
      const eventId = uuidv4();                      // pacote uuid já existente
      return {
        eventId,
        webhookEndpointId: endpoint.id,
        orderId: order.id,
        eventType: 'order.status_changed',
        payload: {                                   // snapshot [09:52]
          event_id: eventId,
          event_type: 'order.status_changed',
          timestamp: occurredAt,
          order_id: order.id,
          order_number: order.orderNumber,
          from_status: fromStatus,
          to_status: toStatus,
          customer_id: order.customerId,
          total_cents: order.totalCents,
        },
      };
    }),
  });
  return targets.length;
}
```

Regras:
- **Falha na inserção:** qualquer exceção propaga e desfaz a transação inteira. A resposta é `500 INTERNAL_SERVER_ERROR` pelo `errorMiddleware` e o status não muda ([09:40] Bruno).
- **Sem endpoint interessado:** nenhuma linha é criada e a mudança de status segue normalmente ([09:34] Bruno).
- **Criação de pedido não gera evento.** `OrderService.create` cria o pedido já em `PENDING` sem passar por `changeStatus`, e a reunião tratou só a mudança de status ([09:40] Bruno).
- **Mesma transação, só o insert a mais:** o limite de 64 KB **não** é checado aqui, para que um payload anômalo nunca impeça uma mudança de status. Ele é checado no worker (FDD-FLUXO-02, passo 3).

### FDD-FLUXO-02: Processamento pelo worker

`src/worker.ts` (novo) é a entry-point e segue o molde de `src/server.ts`: bootstrap, `logger.info('webhook_worker_started')` e shutdown em `SIGINT`/`SIGTERM` com `prisma.$disconnect()`. A lógica fica em `src/modules/webhooks/webhook.worker.ts` (novo) ([09:28] Bruno).

1. **Na inicialização:** move para `PENDING` as linhas que ficaram em `PROCESSING` (resultado de uma queda no meio de um envio). Com um único worker ([09:12] Diego), nenhuma outra instância pode estar processando essas linhas. O reenvio é coberto pela garantia at-least-once ([ADR-005](adrs/ADR-005-at-least-once-com-x-event-id.md)).
2. **A cada `WEBHOOK_POLL_INTERVAL_MS` (2000 ms)** ([09:09] Diego), busca um batch:
   `findMany({ where: { status: 'PENDING', nextAttemptAt: { lte: now } }, orderBy: { createdAt: 'asc' }, take: WEBHOOK_WORKER_BATCH_SIZE, include: { endpoint: true } })`.
   - A reunião fixou só "batch pequeno" ([09:08] Diego). O tamanho é configurável. Proposta: não discutido.
   - Marca as linhas do batch como `PROCESSING`.
3. **Para cada evento:**
   - a. Se o endpoint estiver inativo: vai para a DLQ com `WEBHOOK_ENDPOINT_INACTIVE`, sem retry.
   - b. Serializa o `payload` (é o corpo exato a ser assinado e enviado). Se passar de `WEBHOOK_MAX_PAYLOAD_BYTES` (65536), vai para a DLQ com `WEBHOOK_PAYLOAD_TOO_LARGE`, sem retry e sem truncar ([09:23] Sofia; [09:24] Diego; [09:24] Larissa).
   - c. Sem secret utilizável: vai para a DLQ com `WEBHOOK_SECRET_REQUIRED`.
   - d. Assina e envia (FDD-CONTRATO-08) com `fetch` e `AbortSignal.timeout(WEBHOOK_HTTP_TIMEOUT_MS)` (10000 ms) ([09:42] Diego).
   - e. Grava uma linha em `webhook_deliveries` com resultado, `httpStatus`, `durationMs`, `errorCode` e corpo de resposta truncado.
   - f. Resposta `2xx`: `status = DELIVERED` e `deliveredAt = now`. Qualquer outra coisa (timeout, erro de rede, resposta não 2xx) segue para FDD-FLUXO-03. A reunião não diferenciou 4xx de 5xx. Proposta: não discutido.
4. **Ordem e paralelismo:**
   - eventos do **mesmo `orderId`** são enviados em série, na ordem de `createdAt` ([09:12] Diego);
   - eventos de pedidos diferentes podem ir em paralelo dentro do batch, para que um cliente lento (até 10 s) não atrase os outros.

   Proposta: não discutido. Ver FDD-RISK-01.

### FDD-FLUXO-03: Retry com backoff

O cronograma vem de [ADR-003](adrs/ADR-003-retry-com-backoff-e-dlq.md) e adota a leitura de 5 retentativas depois do envio inicial, **a confirmar em RFC-Q-07**:

| Envio | `attempts` antes do envio | Quando acontece |
|---|---|---|
| 1 (inicial) | 0 | próximo ciclo do worker (≤ 2 s após o commit) |
| 2 | 1 | 1 min após a falha do envio 1 |
| 3 | 2 | 5 min após a falha do envio 2 |
| 4 | 3 | 30 min após a falha do envio 3 |
| 5 | 4 | 2 h após a falha do envio 4 |
| 6 | 5 | 12 h após a falha do envio 5 |
| — | 5 | falha do envio 6 → DLQ (`WEBHOOK_MAX_ATTEMPTS_EXCEEDED`) |

Na falha:
- se `attempts < 5`: `attempts += 1`, `nextAttemptAt = now + BACKOFF[attempts - 1]`, `status = PENDING` e `lastError = <código>`;
- se `attempts = 5`: FDD-FLUXO-04.

`BACKOFF = [1m, 5m, 30m, 2h, 12h]` fica numa constante do módulo (`webhook.constants.ts`, novo). Janela total: ~14 h 36 min ([09:17] Diego).

### FDD-FLUXO-04: Envio para a DLQ

Em uma única transação:
1. cria uma **nova** linha em `webhook_dead_letter` com `outboxId`, `eventId`, `payload`, `failureReason` (código e mensagem) e `failedAt` ([09:18] Diego). Um evento que volta a falhar depois de um replay ganha outra linha, que pode ser reenviada de novo; por isso `outboxId` não é único (só indexado);
2. marca a outbox como `FAILED`.

Log `webhook_event_dead_lettered` em nível `warn`. Não há aviso ao cliente: e-mail é da próxima fase ([09:37] Larissa).

### FDD-FLUXO-05: Replay manual da DLQ

`POST /api/v1/admin/webhooks/dead-letter/:id/replay`, com `authenticate` e `requireRole('ADMIN')` ([09:36] Larissa):
1. Busca a DLQ pelo id. Se não existir: `WEBHOOK_DEAD_LETTER_NOT_FOUND`.
2. Se `replayedAt` já estiver preenchido: `WEBHOOK_DEAD_LETTER_ALREADY_REPLAYED`.
3. Se o endpoint estiver inativo: `WEBHOOK_ENDPOINT_INACTIVE`.
4. Numa transação:
   - a linha original da outbox volta para `status = PENDING`, `attempts = 0`, `nextAttemptAt = now` e `lastError = null`. O **`eventId` é mantido**, para o cliente deduplicar ([ADR-005](adrs/ADR-005-at-least-once-com-x-event-id.md)). Proposta: não discutido;
   - na DLQ: `replayedAt = now` e `replayedById = req.user.id`.
5. Log `webhook_dead_letter_replayed` em `info`, com `userId`, `deadLetterId`, `eventId` e `webhookId`. É a auditoria pedida em [09:36] Sofia.

O evento volta ao FLUXO-02 com o ciclo de tentativas completo.

### FDD-FLUXO-06: Rotação de secret

`POST /api/v1/webhooks/:id/rotate-secret` ([09:21] Sofia):
1. Gera uma secret nova com `crypto.randomBytes(32).toString('hex')`. O tamanho da secret é proposta: não discutido e fica para a revisão da Sofia ([09:46] Sofia).
2. `previousSecret = secret atual`, `previousSecretExpiresAt = now + 24 h` e `secret = nova`.
3. Uma nova rotação dentro das 24 h descarta a secret mais antiga imediatamente: só existem duas válidas por vez. Proposta: não discutido.
4. Responde com a secret nova. É a única vez, além da criação, em que a secret sai pela API ([09:31] Marcos).
5. Log `webhook_secret_rotated`, sem o valor da secret.

**Assinatura durante a convivência** (proposta: não discutido, ver RFC-Q-09): enquanto `previousSecretExpiresAt > now`, o header leva as duas assinaturas, a nova primeiro: `X-Signature: sha256=<hmac_nova>,sha256=<hmac_antiga>`. Assim, um cliente que ainda valida com a antiga continua aceitando ([09:21] Sofia).

## 6. Contratos públicos

Todas as rotas ficam sob `/api/v1`, como as demais (`src/app.ts`, linha 67). Os endpoints de configuração usam `authenticate` (Bearer JWT). JSON da API em camelCase, como no resto do projeto (ex.: `customerId`, `toStatus` em `order.schemas.ts`). Os erros usam o envelope de `src/middlewares/error.middleware.ts`:

```json
{ "error": { "code": "WEBHOOK_NOT_FOUND", "message": "Webhook not found" } }
```

Respostas comuns a todos os endpoints autenticados, vindas de middlewares existentes e por isso fora da matriz `WEBHOOK_`:
- `401 UNAUTHORIZED`: token ausente ou inválido;
- `400 VALIDATION_ERROR`: parâmetros malformados, como um id que não é UUID.

O `customer_id` vai no **path**, e não no JWT ([09:32] Larissa). A escolha entre body e path está em RFC-Q-05.

### FDD-CONTRATO-01: `POST /api/v1/customers/:customerId/webhooks`: cadastrar webhook

Fonte: [09:31] Marcos; [09:33] Marcos.

Request:
```http
POST /api/v1/customers/3f6c1a2e-8d4b-4c1e-9a7f-2b5d8e9c0a11/webhooks
Authorization: Bearer <jwt>
Content-Type: application/json

{
  "url": "https://hooks.atlas.example/oms/orders",
  "statuses": ["SHIPPED", "DELIVERED"]
}
```

Response `201 Created`. A `secret` aparece **somente** aqui e na rotação:
```json
{
  "id": "9b2e7c4d-1f3a-4e5b-8c6d-7a8b9c0d1e2f",
  "customerId": "3f6c1a2e-8d4b-4c1e-9a7f-2b5d8e9c0a11",
  "url": "https://hooks.atlas.example/oms/orders",
  "statuses": ["SHIPPED", "DELIVERED"],
  "active": true,
  "secret": "4f9d2c7a1b8e6f3d0a5c9e2b7d4f1a8c6e3b0d9f2a7c5e1b8d4f6a3c0e9b2d7f",
  "createdAt": "2026-11-20T13:58:02.114Z",
  "updatedAt": "2026-11-20T13:58:02.114Z"
}
```

| Status | Quando |
|---|---|
| 201 | Criado |
| 400 | `VALIDATION_ERROR`, com `details` contendo `WEBHOOK_INVALID_URL` (URL não `https`) ou `WEBHOOK_INVALID_EVENT_FILTER` |
| 401 | Sem token válido |
| 404 | `WEBHOOK_CUSTOMER_NOT_FOUND` |

Validação (`webhook.schemas.ts`, novo):
- `url`: `z.string().url().max(2048)` mais um refine de protocolo `https:` ([09:23] Sofia);
- `statuses`: array não vazio e sem repetição de `OrderStatus`, **exceto `PENDING`**. Nenhuma transição em `src/modules/orders/order.status.ts` leva a `PENDING`, então esse filtro nunca dispararia. É uma regra derivada do código. Proposta: não discutido.

### FDD-CONTRATO-02: `GET /api/v1/customers/:customerId/webhooks`: listar webhooks do customer

Fonte: [09:33] Bruno. Usa a paginação de `src/shared/http/response.ts` (`paginated`), com `page` e `pageSize` como em `listOrdersQuerySchema`.

Request:
```http
GET /api/v1/customers/3f6c1a2e-8d4b-4c1e-9a7f-2b5d8e9c0a11/webhooks?page=1&pageSize=20
Authorization: Bearer <jwt>
```

Response `200 OK` (sem `secret`):
```json
{
  "data": [
    {
      "id": "9b2e7c4d-1f3a-4e5b-8c6d-7a8b9c0d1e2f",
      "customerId": "3f6c1a2e-8d4b-4c1e-9a7f-2b5d8e9c0a11",
      "url": "https://hooks.atlas.example/oms/orders",
      "statuses": ["SHIPPED", "DELIVERED"],
      "active": true,
      "previousSecretExpiresAt": null,
      "createdAt": "2026-11-20T13:58:02.114Z",
      "updatedAt": "2026-11-20T13:58:02.114Z"
    }
  ],
  "pagination": { "page": 1, "pageSize": 20, "total": 1, "totalPages": 1 }
}
```

| Status | Quando |
|---|---|
| 200 | Lista, possivelmente vazia |
| 401 | Sem token válido |
| 404 | `WEBHOOK_CUSTOMER_NOT_FOUND` |

### FDD-CONTRATO-03: `PATCH /api/v1/webhooks/:id`: editar webhook

Fonte: [09:33] Bruno. Corpo parcial, com pelo menos um campo entre `url`, `statuses` e `active`. As mesmas validações do CONTRATO-01 se aplicam.

Request:
```http
PATCH /api/v1/webhooks/9b2e7c4d-1f3a-4e5b-8c6d-7a8b9c0d1e2f
Authorization: Bearer <jwt>
Content-Type: application/json

{ "statuses": ["PROCESSING", "SHIPPED", "DELIVERED", "CANCELLED"] }
```

Response `200 OK`: o webhook atualizado, no mesmo formato de um item do CONTRATO-02, sem `secret`.
```json
{
  "id": "9b2e7c4d-1f3a-4e5b-8c6d-7a8b9c0d1e2f",
  "customerId": "3f6c1a2e-8d4b-4c1e-9a7f-2b5d8e9c0a11",
  "url": "https://hooks.atlas.example/oms/orders",
  "statuses": ["PROCESSING", "SHIPPED", "DELIVERED", "CANCELLED"],
  "active": true,
  "previousSecretExpiresAt": null,
  "createdAt": "2026-11-20T13:58:02.114Z",
  "updatedAt": "2026-11-20T14:10:45.330Z"
}
```

| Status | Quando |
|---|---|
| 200 | Atualizado |
| 400 | `VALIDATION_ERROR` (corpo vazio, `WEBHOOK_INVALID_URL` ou `WEBHOOK_INVALID_EVENT_FILTER` em `details`) |
| 401 | Sem token válido |
| 404 | `WEBHOOK_NOT_FOUND` |

O novo filtro vale para as próximas mudanças de status. Eventos já gravados na outbox não são refiltrados, porque o filtro é aplicado na inserção ([09:34] Bruno).

### FDD-CONTRATO-04: `DELETE /api/v1/webhooks/:id`: remover webhook

Fonte: [09:33] Bruno.

Request:
```http
DELETE /api/v1/webhooks/9b2e7c4d-1f3a-4e5b-8c6d-7a8b9c0d1e2f
Authorization: Bearer <jwt>
```

Response `204 No Content`, sem corpo, igual ao `DELETE /orders/:id` existente.

| Status | Quando |
|---|---|
| 204 | Removido. Eventos pendentes, histórico e DLQ do endpoint são apagados em cascata (FDD-RISK-05) |
| 401 | Sem token válido |
| 404 | `WEBHOOK_NOT_FOUND` |

### FDD-CONTRATO-05: `POST /api/v1/webhooks/:id/rotate-secret`: rotacionar secret

Fonte: [09:21] Sofia. O caminho é proposta: não discutido.

Request:
```http
POST /api/v1/webhooks/9b2e7c4d-1f3a-4e5b-8c6d-7a8b9c0d1e2f/rotate-secret
Authorization: Bearer <jwt>
```

Response `200 OK`:
```json
{
  "id": "9b2e7c4d-1f3a-4e5b-8c6d-7a8b9c0d1e2f",
  "secret": "b71e0c94d3a25f86e1c07b49a2d83f5e6c19a07d42b8e3f5a6c01d97e2b4f83a",
  "previousSecretExpiresAt": "2026-11-21T14:10:00.000Z"
}
```

| Status | Quando |
|---|---|
| 200 | Nova secret gerada. A anterior vale por mais 24 h |
| 401 | Sem token válido |
| 404 | `WEBHOOK_NOT_FOUND` |

### FDD-CONTRATO-06: `GET /api/v1/webhooks/:id/deliveries`: histórico de entregas

Fonte: [09:34] Marcos ("últimos 100 webhooks..., sucesso/falha, payload, response, tempo de resposta").

Request:
```http
GET /api/v1/webhooks/9b2e7c4d-1f3a-4e5b-8c6d-7a8b9c0d1e2f/deliveries?limit=100
Authorization: Bearer <jwt>
```

`limit` aceita de 1 a 100, com padrão 100. A ordem é decrescente por `createdAt`. Usar `limit` em vez de `page`/`pageSize` (`src/shared/http/response.ts`) segue o pedido de "últimos 100" ([09:34] Marcos) e é proposta: não discutido. Response `200 OK`:
```json
{
  "data": [
    {
      "id": "c4d5e6f7-a8b9-4c0d-9e1f-2a3b4c5d6e7f",
      "eventId": "7b0c9e2a-4d1f-4a8b-9c3e-5f6a7b8c9d0e",
      "attemptNumber": 2,
      "result": "SUCCESS",
      "httpStatus": 200,
      "durationMs": 412,
      "errorCode": null,
      "responseBody": "{\"received\":true}",
      "payload": {
        "event_id": "7b0c9e2a-4d1f-4a8b-9c3e-5f6a7b8c9d0e",
        "event_type": "order.status_changed",
        "timestamp": "2026-11-20T14:03:12.481Z",
        "order_id": "0d1e2f3a-4b5c-4d6e-8f7a-9b0c1d2e3f4a",
        "order_number": "ORD-000123",
        "from_status": "PROCESSING",
        "to_status": "SHIPPED",
        "customer_id": "3f6c1a2e-8d4b-4c1e-9a7f-2b5d8e9c0a11",
        "total_cents": 45990
      },
      "createdAt": "2026-11-20T14:04:14.902Z"
    },
    {
      "id": "b3c4d5e6-f7a8-4b9c-8d0e-1f2a3b4c5d6e",
      "eventId": "7b0c9e2a-4d1f-4a8b-9c3e-5f6a7b8c9d0e",
      "attemptNumber": 1,
      "result": "FAILURE",
      "httpStatus": null,
      "durationMs": 10000,
      "errorCode": "WEBHOOK_DELIVERY_TIMEOUT",
      "responseBody": null,
      "payload": { "event_id": "7b0c9e2a-4d1f-4a8b-9c3e-5f6a7b8c9d0e", "...": "..." },
      "createdAt": "2026-11-20T14:03:24.511Z"
    }
  ]
}
```

| Status | Quando |
|---|---|
| 200 | Histórico, possivelmente vazio |
| 400 | `VALIDATION_ERROR` (`limit` fora de 1–100) |
| 401 | Sem token válido |
| 404 | `WEBHOOK_NOT_FOUND` |

### FDD-CONTRATO-07: `POST /api/v1/admin/webhooks/dead-letter/:id/replay`: replay da DLQ

Fonte: [09:18] Diego; [09:35] Diego; [09:36] Sofia. Exige `authenticate` e `requireRole('ADMIN')`.

Request:
```http
POST /api/v1/admin/webhooks/dead-letter/e1f2a3b4-c5d6-4e7f-8a9b-0c1d2e3f4a5b/replay
Authorization: Bearer <jwt de usuário ADMIN>
```

Response `202 Accepted`. O evento volta para a outbox, e a entrega é assíncrona:
```json
{
  "deadLetterId": "e1f2a3b4-c5d6-4e7f-8a9b-0c1d2e3f4a5b",
  "outboxId": "a9b8c7d6-e5f4-4a3b-9c2d-1e0f9a8b7c6d",
  "eventId": "7b0c9e2a-4d1f-4a8b-9c3e-5f6a7b8c9d0e",
  "status": "PENDING",
  "replayedAt": "2026-11-21T09:12:40.330Z",
  "replayedById": "5a6b7c8d-9e0f-4a1b-8c2d-3e4f5a6b7c8d"
}
```

| Status | Quando |
|---|---|
| 202 | Evento recolocado como pendente |
| 401 | Sem token válido |
| 403 | `FORBIDDEN` (usuário não é ADMIN), resposta do `requireRole` existente |
| 404 | `WEBHOOK_DEAD_LETTER_NOT_FOUND` |
| 409 | `WEBHOOK_DEAD_LETTER_ALREADY_REPLAYED` ou `WEBHOOK_ENDPOINT_INACTIVE` |

### FDD-CONTRATO-08: requisição de saída (o que o cliente recebe)

Fonte: payload [09:43] Diego; headers [09:44] Diego e [09:44] Sofia.

```http
POST https://hooks.atlas.example/oms/orders
Content-Type: application/json
X-Event-Id: 7b0c9e2a-4d1f-4a8b-9c3e-5f6a7b8c9d0e
X-Webhook-Id: 9b2e7c4d-1f3a-4e5b-8c6d-7a8b9c0d1e2f
X-Timestamp: 2026-11-20T14:03:13.902Z
X-Signature: sha256=5d41402abc4b2a76b9719d911017c592ae7f1c3b9d2e8a6f4c0b7e1d3a9f2c58

{"event_id":"7b0c9e2a-4d1f-4a8b-9c3e-5f6a7b8c9d0e","event_type":"order.status_changed","timestamp":"2026-11-20T14:03:12.481Z","order_id":"0d1e2f3a-4b5c-4d6e-8f7a-9b0c1d2e3f4a","order_number":"ORD-000123","from_status":"PROCESSING","to_status":"SHIPPED","customer_id":"3f6c1a2e-8d4b-4c1e-9a7f-2b5d8e9c0a11","total_cents":45990}
```

| Header | Conteúdo | Origem |
|---|---|---|
| `X-Event-Id` | UUID do evento, igual ao `event_id` do corpo. Repete em retry e replay | [09:25] Diego |
| `X-Signature` | `sha256=` + HMAC-SHA256 em hex dos **bytes exatos do corpo**, com a secret do endpoint. O prefixo `sha256=` é proposta: não discutido | [09:20] Sofia; [09:22] Sofia |
| `X-Timestamp` | Momento do envio (ISO 8601), pedido para o cliente detectar replay attack ([09:44] Diego). **Atenção:** a assinatura cobre só o corpo ([09:22] Sofia), então quem intercepta a requisição pode trocar este header; sozinho, ele não protege contra replay (RFC-Q-12) | [09:44] Diego |
| `X-Webhook-Id` | Id do endpoint cadastrado | [09:44] Sofia |
| `Content-Type` | `application/json` | [09:44] Diego |

Semântica:
- `timestamp`, no corpo, é o momento da mudança de status (snapshot). `X-Timestamp` é o momento deste envio.
- `order_number` segue o formato `ORD-000123` gerado por `reserveOrderNumber` (`order.service.ts`).
- O cliente deve responder `2xx` em até 10 s. Qualquer outra resposta conta como falha e gera retry.

## 7. Matriz de erros

Todos os erros do módulo estendem `AppError` (`src/shared/errors/app-error.ts`), no molde de `InsufficientStockError` em `src/shared/errors/http-errors.ts`, e ficam em `src/modules/webhooks/webhook.errors.ts` (novo).

Erros que nascem de validação Zod passam pelo `validate` existente, que converte todo `ZodError` em `400 VALIDATION_ERROR` (`src/middlewares/validate.middleware.ts`, linhas 26–31). Por isso o código `WEBHOOK_*` chega ao cliente em `error.details[].message`:
```json
{ "error": { "code": "VALIDATION_ERROR", "message": "Validation failed",
  "details": [ { "path": "url", "message": "WEBHOOK_INVALID_URL: url must use https" } ] } }
```

Os erros do worker não têm resposta HTTP para a nossa API. Eles são gravados em `webhook_deliveries.errorCode`, em `webhook_dead_letter.failureReason` e nos logs.

| ID | Código | HTTP | Onde aparece | Quando ocorre | Ação |
|---|---|---|---|---|---|
| FDD-ERR-01 | `WEBHOOK_NOT_FOUND` | 404 | `error.code` | Id de webhook inexistente em PATCH, DELETE, rotate-secret ou deliveries ([09:28] Bruno) | Cliente confere o id |
| FDD-ERR-02 | `WEBHOOK_INVALID_URL` | 400 | `details[].message` | URL inválida ou não `https` ([09:23] Sofia; [09:28] Bruno) | Cliente cadastra uma URL `https` |
| FDD-ERR-03 | `WEBHOOK_INVALID_EVENT_FILTER` | 400 | `details[].message` | `statuses` vazio, repetido, inexistente ou `PENDING` ([09:33] Marcos; a regra do `PENDING` deriva de `order.status.ts`. Proposta: não discutido) | Cliente corrige a lista |
| FDD-ERR-04 | `WEBHOOK_CUSTOMER_NOT_FOUND` | 404 | `error.code` | `customerId` do path inexistente ([09:32] Larissa) | Cliente confere o customer |
| FDD-ERR-05 | `WEBHOOK_SECRET_REQUIRED` | worker | delivery, DLQ, log | Endpoint sem secret utilizável no momento de assinar ([09:28] Bruno) | DLQ sem retry. Admin investiga e faz replay |
| FDD-ERR-06 | `WEBHOOK_PAYLOAD_TOO_LARGE` | worker | delivery, DLQ, log | Corpo serializado > 64 KB ([09:23] Sofia; [09:24] Larissa) | DLQ sem retry e sem truncar. Indica bug |
| FDD-ERR-07 | `WEBHOOK_DELIVERY_TIMEOUT` | worker | delivery, log | Sem resposta em 10 s ([09:42] Diego) | Retry com backoff |
| FDD-ERR-08 | `WEBHOOK_DELIVERY_FAILED` | worker | delivery, log | Erro de rede/TLS ou resposta não 2xx ([09:15] Diego) | Retry com backoff |
| FDD-ERR-09 | `WEBHOOK_MAX_ATTEMPTS_EXCEEDED` | worker | DLQ, log | Falha da última retentativa ([09:15] Diego) | DLQ. Replay manual |
| FDD-ERR-10 | `WEBHOOK_ENDPOINT_INACTIVE` | 409 / worker | `error.code`, DLQ | Envio ou replay para endpoint desativado (proposta: não discutido) | Reativar via PATCH e fazer replay |
| FDD-ERR-11 | `WEBHOOK_DEAD_LETTER_NOT_FOUND` | 404 | `error.code` | Id de DLQ inexistente no replay ([09:18] Diego) | Admin confere o id |
| FDD-ERR-12 | `WEBHOOK_DEAD_LETTER_ALREADY_REPLAYED` | 409 | `error.code` | Replay repetido do mesmo item (proposta: não discutido) | Acompanhar o evento pela outbox ou pelas entregas |

## 8. Estratégias de resiliência

| ID | Estratégia | Valor | Origem |
|---|---|---|---|
| FDD-RES-01 | Timeout por chamada HTTP | 10 s (`AbortSignal.timeout`) | [09:42] Diego |
| FDD-RES-02 | Retry com backoff exponencial | 1m, 5m, 30m, 2h, 12h (5 retentativas, RFC-Q-07) | [09:17] Diego; [09:17] Larissa |
| FDD-RES-03 | Fallback: DLQ persistida + replay manual ADMIN | `webhook_dead_letter` | [09:18] Diego; [09:36] Larissa |
| FDD-RES-04 | Atomicidade evento ↔ status | Outbox na mesma transação. Rollback mútuo | [09:06] Diego; [09:40] Bruno |
| FDD-RES-05 | Isolamento de falhas | Worker em processo próprio. Queda da API não para a entrega e vice-versa | [09:11] Diego |
| FDD-RES-06 | Recuperação após queda do worker | `PROCESSING` → `PENDING` no start. Reenvio coberto por at-least-once | [09:24] Diego |
| FDD-RES-07 | Erros não transitórios não são retentados | Payload > 64 KB, endpoint inativo e secret ausente vão direto para a DLQ | [09:23] Sofia (para 64 KB). Demais casos: proposta: não discutido |
| FDD-RES-08 | Limite do corpo de resposta guardado | `responseBody` truncado em `WEBHOOK_RESPONSE_BODY_MAX_BYTES`. Proposta: não discutido | [09:34] Marcos (pede "response") |
| FDD-RES-09 | Shutdown gracioso | `SIGINT`/`SIGTERM`: termina o envio em andamento, para o loop e chama `prisma.$disconnect()` (molde de `src/server.ts`) | `src/server.ts` |

O fallback para o cliente é consultar `GET /api/v1/orders/:id`, que continua disponível ([09:43] Diego). Aviso por e-mail fica para a próxima fase ([09:37] Larissa).

## 9. Observabilidade

O projeto não tem biblioteca de métricas nem de tracing distribuído (`package.json`: só `pino` e `pino-http`), e a reunião decidiu não adicionar nada novo ([09:29] Bruno). Por isso, métricas e tracing são **derivados de logs estruturados do Pino e das tabelas da feature**. Adotar Prometheus ou OpenTelemetry não foi discutido e fica fora deste escopo.

**Logs.** Usam o `logger` de `src/shared/logger/index.ts`, em JSON com `service` e `env`, e nomes de evento em snake_case, como os existentes `server_started` e `http_request`.

| ID | Evento | Nível | Campos | Origem |
|---|---|---|---|---|
| FDD-OBS-01 | `webhook_event_enqueued` | debug | `orderId`, `eventId`, `webhookId`, `toStatus` | [09:40] Bruno |
| FDD-OBS-02 | `webhook_delivery_succeeded` / `webhook_delivery_failed` | info / warn | `eventId`, `webhookId`, `orderId`, `attemptNumber`, `httpStatus`, `durationMs`, `errorCode` | [09:34] Marcos |
| FDD-OBS-03 | `webhook_event_dead_lettered` | warn | `eventId`, `webhookId`, `customerId`, `failureReason` | [09:18] Diego |
| FDD-OBS-04 | `webhook_dead_letter_replayed` | info | `userId`, `deadLetterId`, `eventId`, `webhookId` (auditoria) | [09:36] Sofia |
| FDD-OBS-05 | `webhook_secret_rotated` | info | `webhookId`, `userId`, nunca o valor | [09:21] Sofia; [09:22] Diego |
| FDD-OBS-06 | `webhook_worker_tick` | debug | `batchSize`, `pendingCount`, `oldestPendingAgeMs`, `durationMs` | [09:09] Diego |

`redactPaths` do logger ganha `'*.secret'` e `'*.previousSecret'`, para que um objeto de endpoint logado por engano não vaze a secret. Já houve vazamento de secret em log de cliente ([09:22] Diego).

**Métricas** (derivadas):

| ID | Métrica | Como medir | Meta ou uso |
|---|---|---|---|
| FDD-OBS-07 | Latência até a 1ª tentativa | `webhook_deliveries.createdAt` (`attemptNumber = 1`) − `webhook_outbox.createdAt` | < 10 s ([09:02] Marcos) |
| FDD-OBS-08 | Backlog e idade do pendente mais antigo | `pendingCount` e `oldestPendingAgeMs` do tick | Alerta se a idade passar de 10 s de forma sustentada (worker parado ou lento) |
| FDD-OBS-09 | Taxa de sucesso e falha por endpoint; duração das chamadas | `webhook_deliveries` agrupado por `webhookEndpointId` e `result`; `durationMs` | Saúde de cada integração |
| FDD-OBS-10 | Entradas na DLQ por dia | `webhook_dead_letter.failedAt` | Dado para decidir o e-mail da próxima fase ("depois que a gente medir o impacto", [09:37] Larissa) |
| FDD-OBS-11 | Envios por customer por minuto | `webhook_deliveries` agrupado por minuto | Dado para decidir o rate limiting ([09:39] Diego; [09:39] Larissa) |

**Tracing** (correlação):
- **FDD-OBS-12:** cada log do fluxo carrega `orderId`, `eventId`, `webhookId` e, no worker, `outboxId` e `attemptNumber`. A linha `http_request` de `request-logger.middleware.ts` já registra o `path` com o id do pedido e o `requestId`. Assim, um evento é rastreável desde a requisição `PATCH /orders/:id/status` até cada tentativa de entrega.
- O cliente informa `X-Event-Id` e `X-Webhook-Id` ao suporte, e isso leva direto ao histórico (CONTRATO-06).
- Propagar o `requestId` da API para dentro da outbox exigiria mudar a assinatura de `changeStatus`, o que não foi discutido.

## 10. Integração com o sistema existente

| ID | Arquivo (existente) | Como o módulo de webhooks se integra |
|---|---|---|
| FDD-INT-01 | `src/modules/orders/order.service.ts` | `changeStatus` (linhas 126–179) ganha **uma chamada**, `await publishWebhookEvent(tx, order, from, to)`, logo após `tx.orderStatusHistory.create` (linha 159) e antes do `findUnique` final. Usa o mesmo `tx` do `$transaction` (o tipo `TxClient`, linha 24, já existe). O `order` lido na linha 132 tem `id`, `orderNumber`, `customerId` e `totalCents`. Construtor e composição não mudam ([09:41] Bruno) |
| FDD-INT-02 | `src/modules/orders/order.status.ts` | Fonte da verdade dos status válidos para o filtro. Os status assinaveis são os destinos possíveis no mapa `transitions` (todos, exceto `PENDING`). O schema de webhooks reaproveita `OrderStatus` e o mapa, sem duplicar a lista |
| FDD-INT-03 | `src/shared/errors/app-error.ts` e `src/shared/errors/http-errors.ts` | As classes de `webhook.errors.ts` (novo) estendem `AppError`, como `InsufficientStockError`, com `errorCode` `WEBHOOK_*` ([09:28] Bruno). `src/shared/errors/index.ts` não precisa mudar: os erros são exportados pelo próprio módulo |
| FDD-INT-04 | `src/middlewares/error.middleware.ts` | **Sem alteração.** Já serializa qualquer `AppError` como `{ error: { code, message, details } }` e trata `ZodError` e Prisma `P2002`/`P2025` ([09:29] Bruno) |
| FDD-INT-05 | `src/middlewares/validate.middleware.ts` | **Sem alteração.** Valida body, params e query com os schemas de `webhook.schemas.ts` (novo). Por converter `ZodError` em `VALIDATION_ERROR`, os códigos `WEBHOOK_INVALID_URL` e `WEBHOOK_INVALID_EVENT_FILTER` vão na `message` do refine (seção 7) |
| FDD-INT-06 | `src/middlewares/auth.middleware.ts` | `authenticate` em todas as rotas do módulo. `requireRole('ADMIN')` no replay ([09:36] Larissa), como já é feito em `src/modules/users/user.routes.ts`. `req.user.id` alimenta `replayedById` e o log de auditoria |
| FDD-INT-07 | `src/shared/logger/index.ts` | Reuso do `logger` na API e no worker. Única mudança: incluir `'*.secret'` e `'*.previousSecret'` em `redactPaths` |
| FDD-INT-08 | `src/config/env.ts` | O `envSchema` ganha variáveis com default: `WEBHOOK_POLL_INTERVAL_MS=2000`, `WEBHOOK_HTTP_TIMEOUT_MS=10000`, `WEBHOOK_MAX_PAYLOAD_BYTES=65536`, `WEBHOOK_WORKER_BATCH_SIZE` e `WEBHOOK_RESPONSE_BODY_MAX_BYTES` (os dois últimos: proposta: não discutido) |
| FDD-INT-09 | `src/config/database.ts` | O worker importa `prisma` deste módulo. Como é outro processo Node, obtém a própria instância de `PrismaClient` com a mesma `DATABASE_URL` ([09:30] Bruno) |
| FDD-INT-10 | `src/server.ts` | Modelo para `src/worker.ts` (novo): `bootstrap()`, logs `*_started`, handlers `SIGINT`/`SIGTERM` com `prisma.$disconnect()` e `logger.fatal` + `process.exit(1)` em falha de bootstrap ([09:11] Larissa) |
| FDD-INT-11 | `src/app.ts` e `src/routes/index.ts` | `buildControllers` instancia `WebhookRepository`, `WebhookService` e `WebhookController` (novos). O tipo `Controllers` ganha `webhooks`, e `buildApiRouter` monta o router do módulo: `/customers/:customerId/webhooks`, `/webhooks` e `/admin/webhooks` |
| FDD-INT-12 | `prisma/schema.prisma` | 4 models e 2 enums novos (seção 4) e a relação `webhookEndpoints` em `Customer`. Migration nova em `prisma/migrations/` |
| FDD-INT-13 | `package.json` | Scripts `worker` (`tsx watch --env-file=.env src/worker.ts`) e `worker:start` (`node --env-file=.env dist/worker.js`), no molde de `dev`/`start` ([09:11] Larissa). Nenhuma dependência nova |
| FDD-INT-14 | `tests/setup.ts` e `tests/helpers/factories.ts` | O `beforeEach` precisa limpar `webhookDeadLetter`, `webhookDelivery`, `webhookOutbox` e `webhookEndpoint` antes de `customer` (FK). Os testes usam `bootstrapAuthenticatedUser('ADMIN')` e `createTestCustomer` já existentes |
| FDD-INT-15 | `src/shared/http/response.ts` | `paginated()` e `buildPagination()` na listagem de webhooks (CONTRATO-02) |

Trecho da mudança em `changeStatus`:

```ts
      await tx.orderStatusHistory.create({ /* ... existente ... */ });

      await publishWebhookEvent(tx, order, from, to);   // novo: mesma transação

      const refreshed = await tx.order.findUnique({ /* ... existente ... */ });
```

**Arquivos novos**

| Arquivo (novo) | Conteúdo |
|---|---|
| `src/worker.ts` | Entry-point do worker |
| `src/modules/webhooks/webhook.worker.ts` | Loop de polling, envio, retry e DLQ |
| `src/modules/webhooks/webhook.publisher.ts` | `publishWebhookEvent(tx, …)` |
| `src/modules/webhooks/webhook.signer.ts` | Assinatura HMAC-SHA256 (`node:crypto`) |
| `src/modules/webhooks/webhook.controller.ts` | Handlers HTTP no padrão `RequestHandler` + `try/next(err)` |
| `src/modules/webhooks/webhook.service.ts` | Regras de CRUD, rotação, histórico e replay |
| `src/modules/webhooks/webhook.repository.ts` | Acesso Prisma às 4 tabelas |
| `src/modules/webhooks/webhook.routes.ts` | Routers, `authenticate`, `requireRole('ADMIN')` e `validate` |
| `src/modules/webhooks/webhook.schemas.ts` | Schemas Zod |
| `src/modules/webhooks/webhook.errors.ts` | Erros `WEBHOOK_*` |
| `src/modules/webhooks/webhook.constants.ts` | `BACKOFF`, `MAX_RETRIES = 5` e `EVENT_TYPE` |
| `tests/webhooks.test.ts` | Testes de API e integração (seção 12) |

## 11. Dependências e compatibilidade

| Item | Situação |
|---|---|
| Node.js ≥ 20 (`package.json`, `engines`) | `fetch` e `AbortSignal.timeout` nativos para as chamadas HTTP: sem cliente HTTP novo |
| `node:crypto` | HMAC-SHA256 e geração de secret: sem dependência nova |
| `uuid` 11.0.3, `zod` 3.23.8, `pino` 9.5.0, `@prisma/client` 5.22.0 | Já instalados e reutilizados ([09:29] Bruno) |
| MySQL 8.0 (`docker-compose.yml`) | Suporta colunas `JSON`, usadas em `payload` e `statuses` |
| Migration | Só aditiva (tabelas novas e uma relação nova em `Customer`), sem alterar colunas existentes |
| API existente | Nenhum contrato muda. `PATCH /orders/:id/status` mantém request e response. Só o tempo da transação aumenta um pouco |
| Deploy | Dois processos: API (`npm start`) e worker (`npm run worker:start`). Se o worker não subir, os eventos acumulam na outbox sem perda |
| Revisão de segurança | Pelo menos 2 dias úteis da Sofia antes do deploy, com foco em HMAC e geração de secret ([09:46] Sofia) |

## 12. Critérios de aceite técnicos

| ID | Critério | Como verificar |
|---|---|---|
| FDD-CA-01 | Mudança de status para um status assinado cria uma linha `PENDING` na outbox na mesma transação | Teste de integração em `tests/webhooks.test.ts` (novo) |
| FDD-CA-02 | Se a inserção na outbox falhar, o status e o histórico do pedido não mudam | Teste forçando erro em `publishWebhookEvent` |
| FDD-CA-03 | Status não assinado, ou customer sem webhook ativo, não cria linha na outbox | Teste de integração |
| FDD-CA-04 | O worker entrega em até 10 s após o commit, com os headers `X-Event-Id`, `X-Signature`, `X-Timestamp`, `X-Webhook-Id` e `Content-Type` | Teste com servidor HTTP local de captura |
| FDD-CA-05 | A assinatura confere com `HMAC-SHA256(secret, corpo)` calculado pelo teste | Teste do `webhook.signer.ts` (novo) |
| FDD-CA-06 | Timeout de 10 s e resposta não 2xx geram retry nos intervalos de 1m/5m/30m/2h/12h. Após a última falha, o evento vai para a DLQ | Teste com relógio controlado (`vi.useFakeTimers`) |
| FDD-CA-07 | Payload acima de 64 KB não é enviado e vai para a DLQ com `WEBHOOK_PAYLOAD_TOO_LARGE` | Teste unitário |
| FDD-CA-08 | URL `http://` é recusada com `400` e `WEBHOOK_INVALID_URL` em `details` | Teste de API |
| FDD-CA-09 | Replay sem ADMIN retorna `403`. Com ADMIN, retorna `202`, recoloca o evento como `PENDING` com o mesmo `eventId` e loga `userId` | Teste de API |
| FDD-CA-10 | Após a rotação, envios levam as duas assinaturas por 24 h e só a nova depois disso | Teste com relógio controlado |
| FDD-CA-11 | `GET /webhooks/:id/deliveries` retorna no máximo 100 itens, do mais recente para o mais antigo, com resultado, payload, resposta e duração | Teste de API |
| FDD-CA-12 | A secret nunca aparece em logs nem em respostas, exceto na criação e na rotação | Teste do logger e revisão da Sofia |
| FDD-CA-13 | Os testes existentes (`tests/orders.test.ts`, `tests/auth.test.ts`) continuam passando | `npm test` |

## 13. Riscos e mitigação

| ID | Risco de implementação | Prob. | Impacto | Mitigação |
|---|---|---|---|---|
| FDD-RISK-01 | *Head-of-line blocking*: um cliente que sempre estoura os 10 s atrasa o batch | Média | Médio | Paralelismo entre pedidos diferentes (FLUXO-02, passo 4) e métrica de idade do pendente mais antigo (OBS-08) |
| FDD-RISK-02 | Linhas presas em `PROCESSING` após uma queda do worker | Média | Baixo | Recuperação no start (RES-06). Exige garantir que só uma instância rode ([09:12] Diego) |
| FDD-RISK-03 | Duas instâncias do worker rodando por engano (deploy errado) geram envios duplicados e fora de ordem | Baixa | Médio | Documentar no runbook. At-least-once tolera duplicatas. Escala horizontal segue como RFC-Q-03 |
| FDD-RISK-04 | Secret vazar em log ou em resposta | Baixa | Alto | `redactPaths` (INT-07), DTOs sem `secret`, CA-12 e revisão da Sofia ([09:46] Sofia) |
| FDD-RISK-05 | `DELETE` do webhook apaga em cascata o histórico e a DLQ do endpoint | Média | Baixo | Comportamento documentado no contrato. Para manter o histórico, o cliente pode usar `PATCH active=false`. Reavaliar na revisão |
| FDD-RISK-06 | Evento posterior do mesmo pedido é entregue antes de um evento em backoff | Média | Baixo | Limitação registrada (RFC-Q-08). `timestamp` e `from_status`/`to_status` no corpo permitem ao cliente detectar a inversão |
| FDD-RISK-07 | Transação de `changeStatus` fica mais lenta com a leitura dos endpoints e o insert | Baixa | Baixo | Índice `customerId` em `webhook_endpoints`. `createMany` em uma ida ao banco |

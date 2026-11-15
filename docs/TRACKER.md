# Tracker de Rastreabilidade

Cada linha liga um item dos documentos à sua origem:
- **TRANSCRICAO:** a fala em [`TRANSCRICAO.md`](../TRANSCRICAO.md), no formato `[hh:mm] Nome`;
- **CODIGO:** o arquivo real do repositório.

Quando um item tem as duas origens, a fonte primária é a transcrição, e o arquivo aparece no resumo. Itens que o próprio documento marca como **proposta: não discutido** aparecem com o tipo "Proposta (não discutida)" e apontam para a fala que criou a necessidade. Esses itens não são decisões da reunião.

Cobertura: todos os IDs definidos em PRD, RFC, FDD e ADRs têm linha aqui. `make check` confere isso automaticamente: que todo ID dos documentos está no tracker, que todo `[hh:mm] Nome` existe na transcrição e que todo caminho de código existe no repositório.

| ID | Documento | Tipo | Conteúdo (resumo) | Fonte | Localização |
|---|---|---|---|---|---|
| ADR-001 | docs/adrs/ADR-001-outbox-no-mysql.md | Decisão | Outbox no MySQL existente, inserida na mesma transação da mudança de status | TRANSCRICAO | [09:06] Diego; [09:08] Larissa |
| ADR-001-ALT-01 | docs/adrs/ADR-001-outbox-no-mysql.md | Alternativa descartada | Disparo HTTP síncrono no service de orders: trava a transação e impede rollback coerente | TRANSCRICAO | [09:03] Larissa; [09:04] Bruno; [09:06] Diego |
| ADR-001-ALT-02 | docs/adrs/ADR-001-outbox-no-mysql.md | Alternativa descartada | Redis Streams ou fila: infra nova, overengineering para time pequeno | TRANSCRICAO | [09:07] Larissa; [09:07] Diego |
| ADR-002 | docs/adrs/ADR-002-worker-separado-com-polling.md | Decisão | Worker em processo separado (src/worker.ts), com polling de 2 s e uma instância | TRANSCRICAO | [09:09] Diego; [09:10] Larissa; [09:11] Diego; [09:11] Larissa |
| ADR-002-ALT-01 | docs/adrs/ADR-002-worker-separado-com-polling.md | Alternativa descartada | Trigger do banco para acordar o worker: MySQL não tem LISTEN/NOTIFY | TRANSCRICAO | [09:09] Bruno; [09:09] Diego |
| ADR-002-ALT-02 | docs/adrs/ADR-002-worker-separado-com-polling.md | Alternativa descartada | Worker dentro do processo da API: restart da API pararia a entrega | TRANSCRICAO | [09:11] Diego |
| ADR-002-ALT-03 | docs/adrs/ADR-002-worker-separado-com-polling.md | Alternativa descartada | Vários workers em paralelo: perde a ordem por order_id; "problema do futuro" | TRANSCRICAO | [09:12] Diego; [09:13] Diego |
| ADR-003 | docs/adrs/ADR-003-retry-com-backoff-e-dlq.md | Decisão | 5 tentativas com backoff 1m/5m/30m/2h/12h, DLQ em tabela separada e replay ADMIN | TRANSCRICAO | [09:15] Diego; [09:17] Larissa; [09:18] Diego; [09:36] Larissa |
| ADR-003-ALT-01 | docs/adrs/ADR-003-retry-com-backoff-e-dlq.md | Alternativa descartada | Retry indefinido: evento pendurado para sempre | TRANSCRICAO | [09:15] Diego |
| ADR-003-ALT-02 | docs/adrs/ADR-003-retry-com-backoff-e-dlq.md | Alternativa descartada | 3 tentativas: esgota em ~30 min, menos que uma manutenção de 2 h | TRANSCRICAO | [09:16] Bruno; [09:16] Diego |
| ADR-003-ALT-03 | docs/adrs/ADR-003-retry-com-backoff-e-dlq.md | Alternativa descartada | Marcar "failed" na própria outbox em vez de tabela de DLQ | TRANSCRICAO | [09:17] Larissa; [09:18] Diego |
| ADR-004 | docs/adrs/ADR-004-hmac-sha256-com-secret-por-endpoint.md | Decisão | HMAC-SHA256 sobre o corpo, secret por endpoint, rotação com 24 h e https obrigatório | TRANSCRICAO | [09:20] Sofia; [09:21] Sofia; [09:22] Sofia; [09:23] Sofia |
| ADR-004-ALT-01 | docs/adrs/ADR-004-hmac-sha256-com-secret-por-endpoint.md | Alternativa descartada | Secret global da plataforma: "se vaza uma, vaza tudo" | TRANSCRICAO | [09:21] Sofia |
| ADR-004-ALT-02 | docs/adrs/ADR-004-hmac-sha256-com-secret-por-endpoint.md | Alternativa descartada | Rotação sem convivência (contraponto implícito, não discutido): o cliente ficaria sem tempo de migrar | TRANSCRICAO | [09:21] Sofia |
| ADR-005 | docs/adrs/ADR-005-at-least-once-com-x-event-id.md | Decisão | At-least-once com X-Event-Id (UUID gerado na outbox) para dedup no cliente | TRANSCRICAO | [09:24] Diego; [09:25] Diego; [09:26] Larissa |
| ADR-005-ALT-01 | docs/adrs/ADR-005-at-least-once-com-x-event-id.md | Alternativa descartada | Exactly-once: exige coordenação dos dois lados, muito mais complexo | TRANSCRICAO | [09:25] Diego |
| ADR-005-ALT-02 | docs/adrs/ADR-005-at-least-once-com-x-event-id.md | Alternativa descartada | At-most-once (contraponto não discutido): contradiz a política de retry | TRANSCRICAO | [09:15] Diego |
| ADR-006 | docs/adrs/ADR-006-reuso-dos-padroes-do-projeto.md | Decisão | Reuso de módulos, AppError, prefixo WEBHOOK_, Pino, errorMiddleware, Zod e requireRole | TRANSCRICAO | [09:27] Bruno; [09:28] Bruno; [09:29] Bruno; [09:30] Larissa |
| ADR-006-ALT-01 | docs/adrs/ADR-006-reuso-dos-padroes-do-projeto.md | Alternativa descartada | Injetar repository no OrderService: substituído por função que recebe o tx | TRANSCRICAO | [09:41] Bruno; [09:41] Diego |
| ADR-006-ALT-02 | docs/adrs/ADR-006-reuso-dos-padroes-do-projeto.md | Alternativa descartada | Infra própria do módulo (logger, erros): duplicaria o que existe | TRANSCRICAO | [09:29] Bruno |
| ADR-007 | docs/adrs/ADR-007-payload-snapshot-na-insercao.md | Decisão | Payload renderizado e gravado (snapshot) na inserção da outbox | TRANSCRICAO | [09:52] Larissa; [09:52] Diego; [09:52] Bruno |
| ADR-007-ALT-01 | docs/adrs/ADR-007-payload-snapshot-na-insercao.md | Alternativa descartada | Guardar só order_id e renderizar no envio: evento refletiria estado posterior | TRANSCRICAO | [09:51] Bruno; [09:52] Larissa |
| RFC-PROP-01 | docs/RFC.md | Proposta técnica | Outbox transacional em changeStatus, com rollback mútuo | TRANSCRICAO | [09:06] Diego; [09:40] Bruno |
| RFC-PROP-02 | docs/RFC.md | Proposta técnica | Filtro por status na inserção: só entra se algum webhook assina | TRANSCRICAO | [09:34] Bruno; [09:34] Diego |
| RFC-PROP-03 | docs/RFC.md | Proposta técnica | Worker separado, polling de 2 s, PrismaClient próprio, instância única | TRANSCRICAO | [09:10] Larissa; [09:11] Diego; [09:30] Bruno |
| RFC-PROP-04 | docs/RFC.md | Proposta técnica | Timeout 10 s, 5 retentativas com backoff, DLQ e replay ADMIN | TRANSCRICAO | [09:42] Diego; [09:17] Larissa; [09:36] Larissa |
| RFC-PROP-05 | docs/RFC.md | Proposta técnica | HMAC-SHA256, secret por endpoint gerada pela plataforma, rotação 24 h, https | TRANSCRICAO | [09:22] Sofia; [09:23] Sofia; [09:31] Marcos |
| RFC-PROP-06 | docs/RFC.md | Proposta técnica | At-least-once com X-Event-Id estável entre retentativas | TRANSCRICAO | [09:26] Larissa |
| RFC-PROP-07 | docs/RFC.md | Proposta técnica | Payload enxuto, sem itens, snapshot na inserção | TRANSCRICAO | [09:43] Diego; [09:52] Diego |
| RFC-PROP-08 | docs/RFC.md | Proposta técnica | Módulo src/modules/webhooks (novo) no padrão do projeto, erros WEBHOOK_ | TRANSCRICAO | [09:27] Bruno; [09:29] Larissa; [09:30] Larissa |
| RFC-PROP-09 | docs/RFC.md | Proposta técnica | API: CRUD por customer, rotação, histórico (100) e replay admin | TRANSCRICAO | [09:31] Marcos; [09:33] Bruno; [09:34] Marcos; [09:35] Diego |
| RFC-ALT-01 | docs/RFC.md | Trade-off | Síncrono: simples, mas acopla a transação à latência e à disponibilidade do cliente | TRANSCRICAO | [09:04] Bruno; [09:06] Diego |
| RFC-ALT-02 | docs/RFC.md | Trade-off | Redis Streams: mais reativo, mas infra nova e sem atomicidade com o SQL | TRANSCRICAO | [09:07] Larissa; [09:07] Diego |
| RFC-ALT-03 | docs/RFC.md | Trade-off | Trigger do banco: reativo, mas MySQL não notifica processo externo | TRANSCRICAO | [09:09] Bruno; [09:09] Diego |
| RFC-ALT-04 | docs/RFC.md | Trade-off | Exactly-once: mais confortável ao cliente, porém complexo demais | TRANSCRICAO | [09:25] Diego |
| RFC-ALT-05 | docs/RFC.md | Trade-off | Retry indefinido ou 3 tentativas: pendura eventos ou esgota cedo demais | TRANSCRICAO | [09:15] Diego; [09:16] Bruno; [09:16] Diego |
| RFC-ALT-06 | docs/RFC.md | Trade-off | Secret global: mais simples, mas um vazamento compromete todos | TRANSCRICAO | [09:21] Sofia |
| RFC-Q-01 | docs/RFC.md | Questão em aberto | Rate limiting de saída: observar e decidir depois | TRANSCRICAO | [09:38] Diego; [09:39] Larissa |
| RFC-Q-02 | docs/RFC.md | Questão em aberto | Aviso por e-mail em falhas repetidas: próxima fase | TRANSCRICAO | [09:37] Marcos; [09:37] Larissa |
| RFC-Q-03 | docs/RFC.md | Questão em aberto | Escala além de um worker (partição por order_id ou lock) | TRANSCRICAO | [09:13] Diego; [09:13] Larissa |
| RFC-Q-04 | docs/RFC.md | Questão em aberto | Endurecer permissões do CRUD de webhooks | TRANSCRICAO | [09:37] Sofia |
| RFC-Q-05 | docs/RFC.md | Questão em aberto | customer_id no body ou no path | TRANSCRICAO | [09:32] Larissa |
| RFC-Q-06 | docs/RFC.md | Questão em aberto | Arquivamento das linhas entregues da outbox | TRANSCRICAO | [09:08] Diego |
| RFC-Q-07 | docs/RFC.md | Ambiguidade | "5 tentativas" × 5 intervalos × "quase 15 horas": 5 envios ou 5 retentativas? | TRANSCRICAO | [09:15] Diego; [09:17] Diego; [09:17] Larissa |
| RFC-Q-08 | docs/RFC.md | Questão em aberto | Ordem por pedido quando um evento está em backoff | TRANSCRICAO | [09:12] Diego |
| RFC-Q-09 | docs/RFC.md | Questão em aberto | Como assinar durante as 24 h de convivência de duas secrets | TRANSCRICAO | [09:21] Sofia |
| RFC-Q-10 | docs/RFC.md | Questão em aberto | Proteção da secret em repouso (HMAC exige a secret recuperável) | TRANSCRICAO | [09:46] Sofia |
| RFC-Q-11 | docs/RFC.md | Questão em aberto | Descoberta do id da DLQ: só o replay foi especificado | TRANSCRICAO | [09:18] Diego |
| RFC-RISK-01 | docs/RFC.md | Risco | Falha na inserção da outbox derruba a mudança de status (desejado) | TRANSCRICAO | [09:40] Bruno; [09:41] Diego |
| RFC-RISK-02 | docs/RFC.md | Risco | Worker parado: backlog cresce e latência passa de 10 s | TRANSCRICAO | [09:11] Diego; [09:02] Marcos |
| RFC-RISK-03 | docs/RFC.md | Risco | Polling de 2 s gera carga constante no MySQL | TRANSCRICAO | [09:08] Diego; [09:09] Diego |
| RFC-RISK-04 | docs/RFC.md | Risco | Rajadas para um mesmo cliente sem rate limiting | TRANSCRICAO | [09:38] Diego |
| RFC-RISK-05 | docs/RFC.md | Risco | Ordem por pedido perdida com retry ou mais workers | TRANSCRICAO | [09:12] Diego; [09:14] Marcos |
| FDD-OBJ-01 | docs/FDD.md | Objetivo técnico | Evento se e somente se a mudança de status foi confirmada | TRANSCRICAO | [09:06] Diego; [09:40] Bruno |
| FDD-OBJ-02 | docs/FDD.md | Objetivo técnico | Primeira tentativa em < 10 s (polling de 2 s) | TRANSCRICAO | [09:02] Marcos; [09:10] Larissa |
| FDD-OBJ-03 | docs/FDD.md | Objetivo técnico | Transação de status nunca espera HTTP | TRANSCRICAO | [09:04] Bruno |
| FDD-OBJ-04 | docs/FDD.md | Objetivo técnico | Nenhum evento perdido: entregue ou na DLQ | TRANSCRICAO | [09:15] Diego; [09:18] Diego |
| FDD-OBJ-05 | docs/FDD.md | Objetivo técnico | Cliente valida HMAC e deduplica por X-Event-Id | TRANSCRICAO | [09:20] Sofia; [09:25] Diego |
| FDD-OBJ-06 | docs/FDD.md | Restrição | Nenhuma dependência ou infra nova | TRANSCRICAO | [09:07] Diego; [09:30] Larissa |
| FDD-FLUXO-01 | docs/FDD.md | Fluxo | publishWebhookEvent(tx, …) após o history em changeStatus (src/modules/orders/order.service.ts), com filtro e rollback | TRANSCRICAO | [09:40] Bruno; [09:41] Bruno; [09:34] Bruno |
| FDD-FLUXO-02 | docs/FDD.md | Fluxo | Worker: recuperação no start, batch a cada 2 s, envio com timeout de 10 s, histórico | TRANSCRICAO | [09:08] Diego; [09:09] Diego; [09:28] Bruno; [09:42] Diego |
| FDD-FLUXO-03 | docs/FDD.md | Fluxo | Retry: tabela de envios 1 a 6 com 1m/5m/30m/2h/12h e DLQ após o 6º | TRANSCRICAO | [09:17] Diego; [09:17] Larissa |
| FDD-FLUXO-04 | docs/FDD.md | Fluxo | DLQ: grava payload, motivo e data; outbox FAILED | TRANSCRICAO | [09:18] Diego |
| FDD-FLUXO-05 | docs/FDD.md | Fluxo | Replay: ADMIN, volta a PENDING com o mesmo eventId, auditoria em log | TRANSCRICAO | [09:18] Diego; [09:36] Sofia; [09:36] Larissa |
| FDD-FLUXO-06 | docs/FDD.md | Fluxo | Rotação: nova secret, anterior válida 24 h, duas assinaturas (proposta) | TRANSCRICAO | [09:21] Sofia |
| FDD-CONTRATO-01 | docs/FDD.md | Contrato | POST /api/v1/customers/:customerId/webhooks: url + statuses → 201 com secret | TRANSCRICAO | [09:31] Marcos; [09:32] Larissa; [09:33] Marcos |
| FDD-CONTRATO-02 | docs/FDD.md | Contrato | GET /api/v1/customers/:customerId/webhooks: lista paginada sem secret | TRANSCRICAO | [09:33] Bruno |
| FDD-CONTRATO-03 | docs/FDD.md | Contrato | PATCH /api/v1/webhooks/:id: edição parcial; filtro vale para eventos futuros | TRANSCRICAO | [09:33] Bruno; [09:34] Bruno |
| FDD-CONTRATO-04 | docs/FDD.md | Contrato | DELETE /api/v1/webhooks/:id → 204 | TRANSCRICAO | [09:33] Bruno |
| FDD-CONTRATO-05 | docs/FDD.md | Contrato | POST /api/v1/webhooks/:id/rotate-secret → nova secret e expiração da anterior | TRANSCRICAO | [09:21] Sofia |
| FDD-CONTRATO-06 | docs/FDD.md | Contrato | GET /api/v1/webhooks/:id/deliveries: até 100, com resultado, payload, resposta e duração | TRANSCRICAO | [09:34] Marcos |
| FDD-CONTRATO-07 | docs/FDD.md | Contrato | POST /api/v1/admin/webhooks/dead-letter/:id/replay: ADMIN → 202 | TRANSCRICAO | [09:18] Diego; [09:35] Diego; [09:36] Sofia |
| FDD-CONTRATO-08 | docs/FDD.md | Contrato | Requisição de saída: payload snake_case e headers X-Event-Id, X-Signature, X-Timestamp, X-Webhook-Id, Content-Type | TRANSCRICAO | [09:43] Diego; [09:44] Diego; [09:44] Sofia |
| FDD-ERR-01 | docs/FDD.md | Erro | WEBHOOK_NOT_FOUND (404) | TRANSCRICAO | [09:28] Bruno |
| FDD-ERR-02 | docs/FDD.md | Erro | WEBHOOK_INVALID_URL (400, em details): URL não https | TRANSCRICAO | [09:23] Sofia; [09:28] Bruno |
| FDD-ERR-03 | docs/FDD.md | Proposta (não discutida) | WEBHOOK_INVALID_EVENT_FILTER (400): lista vazia ou inválida; a recusa de PENDING deriva de order.status.ts | TRANSCRICAO | [09:33] Marcos |
| FDD-ERR-04 | docs/FDD.md | Erro | WEBHOOK_CUSTOMER_NOT_FOUND (404) | TRANSCRICAO | [09:32] Larissa |
| FDD-ERR-05 | docs/FDD.md | Erro | WEBHOOK_SECRET_REQUIRED (worker): endpoint sem secret utilizável | TRANSCRICAO | [09:28] Bruno |
| FDD-ERR-06 | docs/FDD.md | Erro | WEBHOOK_PAYLOAD_TOO_LARGE (worker): > 64 KB, sem truncar | TRANSCRICAO | [09:23] Sofia; [09:24] Diego; [09:24] Larissa |
| FDD-ERR-07 | docs/FDD.md | Erro | WEBHOOK_DELIVERY_TIMEOUT (worker): sem resposta em 10 s | TRANSCRICAO | [09:42] Diego |
| FDD-ERR-08 | docs/FDD.md | Erro | WEBHOOK_DELIVERY_FAILED (worker): rede ou não 2xx | TRANSCRICAO | [09:15] Diego |
| FDD-ERR-09 | docs/FDD.md | Erro | WEBHOOK_MAX_ATTEMPTS_EXCEEDED (worker) → DLQ | TRANSCRICAO | [09:15] Diego |
| FDD-ERR-10 | docs/FDD.md | Proposta (não discutida) | WEBHOOK_ENDPOINT_INACTIVE: envio ou replay para endpoint desativado ("estado ativo") | TRANSCRICAO | [09:21] Bruno |
| FDD-ERR-11 | docs/FDD.md | Erro | WEBHOOK_DEAD_LETTER_NOT_FOUND (404) | TRANSCRICAO | [09:18] Diego |
| FDD-ERR-12 | docs/FDD.md | Proposta (não discutida) | WEBHOOK_DEAD_LETTER_ALREADY_REPLAYED (409) | TRANSCRICAO | [09:18] Diego |
| FDD-RES-01 | docs/FDD.md | Requisito Não Funcional | Timeout de 10 s por chamada HTTP | TRANSCRICAO | [09:42] Diego |
| FDD-RES-02 | docs/FDD.md | Requisito Não Funcional | Backoff exponencial 1m/5m/30m/2h/12h | TRANSCRICAO | [09:17] Diego; [09:17] Larissa |
| FDD-RES-03 | docs/FDD.md | Requisito Não Funcional | Fallback: DLQ persistida e replay manual ADMIN | TRANSCRICAO | [09:18] Diego; [09:36] Larissa |
| FDD-RES-04 | docs/FDD.md | Requisito Não Funcional | Atomicidade evento ↔ status | TRANSCRICAO | [09:06] Diego; [09:40] Bruno |
| FDD-RES-05 | docs/FDD.md | Requisito Não Funcional | Isolamento: worker em processo próprio | TRANSCRICAO | [09:11] Diego |
| FDD-RES-06 | docs/FDD.md | Proposta (não discutida) | Recuperação PROCESSING → PENDING no start, coberta por at-least-once | TRANSCRICAO | [09:24] Diego; [09:12] Diego |
| FDD-RES-07 | docs/FDD.md | Requisito Não Funcional | Erros não transitórios (64 KB etc.) vão direto à DLQ, sem retry | TRANSCRICAO | [09:23] Sofia |
| FDD-RES-08 | docs/FDD.md | Proposta (não discutida) | responseBody truncado em limite configurável | TRANSCRICAO | [09:34] Marcos |
| FDD-RES-09 | docs/FDD.md | Requisito Não Funcional | Shutdown gracioso do worker no molde do servidor | CODIGO | src/server.ts |
| FDD-OBS-01 | docs/FDD.md | Observabilidade | Log webhook_event_enqueued | TRANSCRICAO | [09:40] Bruno; [09:29] Bruno |
| FDD-OBS-02 | docs/FDD.md | Observabilidade | Logs de entrega com attemptNumber, httpStatus, durationMs e errorCode | TRANSCRICAO | [09:34] Marcos |
| FDD-OBS-03 | docs/FDD.md | Observabilidade | Log webhook_event_dead_lettered | TRANSCRICAO | [09:18] Diego |
| FDD-OBS-04 | docs/FDD.md | Observabilidade | Log de auditoria do replay com userId | TRANSCRICAO | [09:36] Sofia |
| FDD-OBS-05 | docs/FDD.md | Observabilidade | Log de rotação sem o valor da secret; redact de secret | TRANSCRICAO | [09:21] Sofia; [09:22] Diego |
| FDD-OBS-06 | docs/FDD.md | Observabilidade | Log webhook_worker_tick com backlog e idade | TRANSCRICAO | [09:09] Diego |
| FDD-OBS-07 | docs/FDD.md | Métrica | Latência até a 1ª tentativa < 10 s | TRANSCRICAO | [09:02] Marcos |
| FDD-OBS-08 | docs/FDD.md | Métrica | Backlog e idade do pendente mais antigo (alerta > 10 s) | TRANSCRICAO | [09:02] Marcos; [09:11] Diego |
| FDD-OBS-09 | docs/FDD.md | Métrica | Sucesso e falha por endpoint; duração das chamadas | TRANSCRICAO | [09:34] Marcos |
| FDD-OBS-10 | docs/FDD.md | Métrica | Entradas na DLQ por dia (insumo para o e-mail da próxima fase) | TRANSCRICAO | [09:37] Larissa |
| FDD-OBS-11 | docs/FDD.md | Métrica | Envios por customer por minuto (insumo para o rate limiting) | TRANSCRICAO | [09:38] Diego; [09:39] Larissa |
| FDD-OBS-12 | docs/FDD.md | Observabilidade | Tracing por correlação orderId/eventId/webhookId com o requestId do log http_request | CODIGO | src/middlewares/request-logger.middleware.ts |
| FDD-INT-01 | docs/FDD.md | Integração | changeStatus chama publishWebhookEvent com o mesmo tx, após o history | CODIGO | src/modules/orders/order.service.ts |
| FDD-INT-02 | docs/FDD.md | Integração | Status assináveis = destinos do mapa transitions (sem PENDING) | CODIGO | src/modules/orders/order.status.ts |
| FDD-INT-03 | docs/FDD.md | Integração | Erros WEBHOOK_* estendem AppError, como InsufficientStockError | CODIGO | src/shared/errors/http-errors.ts |
| FDD-INT-04 | docs/FDD.md | Integração | errorMiddleware sem alteração: já serializa AppError | CODIGO | src/middlewares/error.middleware.ts |
| FDD-INT-05 | docs/FDD.md | Integração | validate sem alteração: ZodError → VALIDATION_ERROR, código WEBHOOK_ em details | CODIGO | src/middlewares/validate.middleware.ts |
| FDD-INT-06 | docs/FDD.md | Integração | authenticate e requireRole('ADMIN') no replay | CODIGO | src/middlewares/auth.middleware.ts |
| FDD-INT-07 | docs/FDD.md | Integração | Logger Pino reutilizado; redact de secret e previousSecret | CODIGO | src/shared/logger/index.ts |
| FDD-INT-08 | docs/FDD.md | Integração | envSchema ganha WEBHOOK_POLL_INTERVAL_MS, WEBHOOK_HTTP_TIMEOUT_MS etc. | CODIGO | src/config/env.ts |
| FDD-INT-09 | docs/FDD.md | Integração | Worker importa prisma: instância própria por processo | CODIGO | src/config/database.ts |
| FDD-INT-10 | docs/FDD.md | Integração | src/worker.ts (novo) segue bootstrap e shutdown do server | CODIGO | src/server.ts |
| FDD-INT-11 | docs/FDD.md | Integração | buildControllers e buildApiRouter ganham o módulo webhooks | CODIGO | src/app.ts |
| FDD-INT-12 | docs/FDD.md | Integração | 4 models e 2 enums novos; relação em Customer; migration | CODIGO | prisma/schema.prisma |
| FDD-INT-13 | docs/FDD.md | Integração | Scripts worker e worker:start; nenhuma dependência nova | CODIGO | package.json |
| FDD-INT-14 | docs/FDD.md | Integração | Limpeza das tabelas novas no beforeEach; factories reutilizadas | CODIGO | tests/setup.ts |
| FDD-INT-15 | docs/FDD.md | Integração | paginated() na listagem de webhooks | CODIGO | src/shared/http/response.ts |
| FDD-CA-01 | docs/FDD.md | Critério de aceite | Status assinado cria linha PENDING na mesma transação | TRANSCRICAO | [09:40] Bruno |
| FDD-CA-02 | docs/FDD.md | Critério de aceite | Falha na outbox não altera status nem histórico | TRANSCRICAO | [09:40] Bruno; [09:41] Diego |
| FDD-CA-03 | docs/FDD.md | Critério de aceite | Status não assinado não cria linha | TRANSCRICAO | [09:34] Bruno |
| FDD-CA-04 | docs/FDD.md | Critério de aceite | Entrega em até 10 s com os 5 headers | TRANSCRICAO | [09:02] Marcos; [09:44] Diego; [09:44] Sofia |
| FDD-CA-05 | docs/FDD.md | Critério de aceite | Assinatura confere com HMAC-SHA256(secret, corpo) | TRANSCRICAO | [09:22] Sofia |
| FDD-CA-06 | docs/FDD.md | Critério de aceite | Timeout e não 2xx geram retry no cronograma e depois DLQ | TRANSCRICAO | [09:17] Larissa; [09:42] Diego |
| FDD-CA-07 | docs/FDD.md | Critério de aceite | Payload > 64 KB vai à DLQ sem envio | TRANSCRICAO | [09:24] Larissa |
| FDD-CA-08 | docs/FDD.md | Critério de aceite | URL http recusada com 400 e WEBHOOK_INVALID_URL | TRANSCRICAO | [09:23] Sofia |
| FDD-CA-09 | docs/FDD.md | Critério de aceite | Replay: 403 sem ADMIN; 202 com ADMIN, mesmo eventId e log de userId | TRANSCRICAO | [09:36] Sofia; [09:36] Larissa |
| FDD-CA-10 | docs/FDD.md | Critério de aceite | Duas assinaturas por 24 h após a rotação | TRANSCRICAO | [09:21] Sofia |
| FDD-CA-11 | docs/FDD.md | Critério de aceite | Histórico com no máximo 100 itens, do mais recente ao mais antigo | TRANSCRICAO | [09:34] Marcos |
| FDD-CA-12 | docs/FDD.md | Critério de aceite | Secret nunca em logs ou respostas, exceto criação e rotação | TRANSCRICAO | [09:22] Diego; [09:31] Marcos |
| FDD-CA-13 | docs/FDD.md | Critério de aceite | Testes existentes continuam passando | CODIGO | tests/orders.test.ts |
| FDD-RISK-01 | docs/FDD.md | Risco | Head-of-line blocking por cliente lento (até 10 s) | TRANSCRICAO | [09:42] Diego; [09:04] Bruno |
| FDD-RISK-02 | docs/FDD.md | Risco | Linhas presas em PROCESSING após queda | TRANSCRICAO | [09:12] Diego |
| FDD-RISK-03 | docs/FDD.md | Risco | Duas instâncias do worker por engano | TRANSCRICAO | [09:12] Diego; [09:13] Larissa |
| FDD-RISK-04 | docs/FDD.md | Risco | Secret vazar em log ou resposta | TRANSCRICAO | [09:22] Diego; [09:46] Sofia |
| FDD-RISK-05 | docs/FDD.md | Risco | DELETE em cascata apaga o histórico do endpoint (padrão onDelete: Cascade do schema) | CODIGO | prisma/schema.prisma |
| FDD-RISK-06 | docs/FDD.md | Risco | Evento posterior do mesmo pedido sai antes de um em backoff | TRANSCRICAO | [09:12] Diego |
| FDD-RISK-07 | docs/FDD.md | Risco | Transação de changeStatus um pouco mais lenta | TRANSCRICAO | [09:04] Bruno; [09:40] Bruno |
| PRD-CEN-01 | docs/PRD.md | Cenário de uso | Atlas assina só SHIPPED e DELIVERED | TRANSCRICAO | [09:33] Marcos |
| PRD-CEN-02 | docs/PRD.md | Cenário de uso | Endpoint 2 h fora em manutenção recebe depois | TRANSCRICAO | [09:16] Diego |
| PRD-CEN-03 | docs/PRD.md | Cenário de uso | Duplicata descartada pelo id do evento | TRANSCRICAO | [09:24] Diego; [09:25] Diego |
| PRD-CEN-04 | docs/PRD.md | Cenário de uso | Secret vazada: rotação com 24 h | TRANSCRICAO | [09:21] Sofia; [09:22] Diego |
| PRD-CEN-05 | docs/PRD.md | Cenário de uso | Vários endpoints: identificação do cadastro de origem | TRANSCRICAO | [09:44] Sofia |
| PRD-CEN-06 | docs/PRD.md | Cenário de uso | Depuração pelo histórico de entregas | TRANSCRICAO | [09:34] Marcos |
| PRD-CEN-07 | docs/PRD.md | Cenário de uso | Admin reenvia evento após correção do endpoint | TRANSCRICAO | [09:18] Diego |
| PRD-OBJ-01 | docs/PRD.md | Objetivo / métrica | Notificação em < 10 s (desenho: ~2 s) | TRANSCRICAO | [09:02] Marcos; [09:10] Larissa |
| PRD-OBJ-02 | docs/PRD.md | Objetivo / métrica | 3 de 3 clientes solicitantes ativos; a Atlas pediu até o fim de novembro | TRANSCRICAO | [09:00] Marcos; [09:45] Marcos |
| PRD-OBJ-03 | docs/PRD.md | Objetivo / métrica | 0 eventos perdidos, cobrindo ~15 h de indisponibilidade | TRANSCRICAO | [09:15] Diego; [09:17] Diego |
| PRD-OBJ-04 | docs/PRD.md | Objetivo / métrica | Entrega em 3 sprints, incluindo revisão de segurança | TRANSCRICAO | [09:46] Larissa; [09:47] Larissa |
| PRD-OBJ-05 | docs/PRD.md | Objetivo / métrica | Reduzir polling em GET /orders (sem meta numérica definida) | TRANSCRICAO | [09:00] Marcos |
| PRD-ESC-01 | docs/PRD.md | Escopo | Somente webhooks de saída | TRANSCRICAO | [09:02] Marcos; [09:03] Sofia |
| PRD-ESC-02 | docs/PRD.md | Escopo | Gestão de endpoints pela API | TRANSCRICAO | [09:31] Marcos; [09:33] Bruno |
| PRD-ESC-03 | docs/PRD.md | Escopo | Assinatura, secret por endpoint, rotação e https | TRANSCRICAO | [09:22] Sofia; [09:23] Sofia |
| PRD-ESC-04 | docs/PRD.md | Escopo | Retentativas, guarda de falhas e reenvio admin | TRANSCRICAO | [09:17] Larissa; [09:19] Larissa |
| PRD-ESC-05 | docs/PRD.md | Escopo | Histórico de entregas | TRANSCRICAO | [09:34] Marcos |
| PRD-OUT-01 | docs/PRD.md | Fora de escopo | E-mail de aviso: próxima fase | TRANSCRICAO | [09:37] Larissa |
| PRD-OUT-02 | docs/PRD.md | Fora de escopo | Dashboard visual: projeto separado de frontend | TRANSCRICAO | [09:40] Larissa |
| PRD-OUT-03 | docs/PRD.md | Fora de escopo | Rate limiting: observar e decidir depois | TRANSCRICAO | [09:39] Diego; [09:39] Larissa |
| PRD-OUT-04 | docs/PRD.md | Fora de escopo | Webhooks de entrada | TRANSCRICAO | [09:02] Marcos |
| PRD-OUT-05 | docs/PRD.md | Fora de escopo | Arquivamento de entregues | TRANSCRICAO | [09:08] Diego |
| PRD-OUT-06 | docs/PRD.md | Fora de escopo | Ordem global e múltiplos workers | TRANSCRICAO | [09:13] Diego; [09:14] Marcos |
| PRD-OUT-07 | docs/PRD.md | Fora de escopo | Exactly-once | TRANSCRICAO | [09:25] Diego |
| PRD-OUT-08 | docs/PRD.md | Fora de escopo | Itens do pedido no payload | TRANSCRICAO | [09:43] Diego |
| PRD-OUT-09 | docs/PRD.md | Fora de escopo | Permissões mais restritas no CRUD (adiado) | TRANSCRICAO | [09:37] Sofia |
| PRD-FR-01 | docs/PRD.md | Requisito Funcional | Cadastrar endpoint com URL e status; secret gerada e devolvida | TRANSCRICAO | [09:31] Marcos |
| PRD-FR-02 | docs/PRD.md | Requisito Funcional | Customer informado na requisição, não do JWT | TRANSCRICAO | [09:32] Marcos; [09:32] Larissa |
| PRD-FR-03 | docs/PRD.md | Requisito Funcional | Editar endpoint | TRANSCRICAO | [09:33] Bruno |
| PRD-FR-04 | docs/PRD.md | Requisito Funcional | Remover endpoint | TRANSCRICAO | [09:33] Bruno |
| PRD-FR-05 | docs/PRD.md | Requisito Funcional | Listar endpoints do customer | TRANSCRICAO | [09:33] Bruno |
| PRD-FR-06 | docs/PRD.md | Requisito Funcional | Filtro por status; nada é enviado se ninguém assina | TRANSCRICAO | [09:33] Marcos; [09:34] Bruno |
| PRD-FR-07 | docs/PRD.md | Requisito Funcional | Notificar a cada mudança de status | TRANSCRICAO | [09:00] Marcos; [09:40] Bruno |
| PRD-FR-08 | docs/PRD.md | Requisito Funcional | Conteúdo da notificação, sem itens | TRANSCRICAO | [09:43] Diego |
| PRD-FR-09 | docs/PRD.md | Requisito Funcional | Notificação assinada e verificável | TRANSCRICAO | [09:19] Sofia; [09:20] Sofia |
| PRD-FR-10 | docs/PRD.md | Requisito Funcional | Id único do evento e id do endpoint em cada notificação | TRANSCRICAO | [09:25] Diego; [09:44] Sofia |
| PRD-FR-11 | docs/PRD.md | Requisito Funcional | Rotacionar secret; anterior válida por 24 h | TRANSCRICAO | [09:21] Sofia |
| PRD-FR-12 | docs/PRD.md | Requisito Funcional | Retentativas automáticas e guarda da falha permanente | TRANSCRICAO | [09:15] Diego; [09:18] Diego |
| PRD-FR-13 | docs/PRD.md | Requisito Funcional | Reenvio manual por ADMIN com registro de quem fez | TRANSCRICAO | [09:18] Diego; [09:36] Sofia |
| PRD-FR-14 | docs/PRD.md | Requisito Funcional | Histórico das últimas 100 entregas | TRANSCRICAO | [09:34] Marcos |
| PRD-NFR-01 | docs/PRD.md | Requisito Não Funcional | Latência < 10 s | TRANSCRICAO | [09:02] Marcos |
| PRD-NFR-02 | docs/PRD.md | Requisito Não Funcional | Consistência status ↔ notificação | TRANSCRICAO | [09:06] Diego; [09:40] Bruno |
| PRD-NFR-03 | docs/PRD.md | Requisito Não Funcional | Cliente lento não afeta outros pedidos | TRANSCRICAO | [09:04] Bruno |
| PRD-NFR-04 | docs/PRD.md | Requisito Não Funcional | At-least-once | TRANSCRICAO | [09:24] Diego |
| PRD-NFR-05 | docs/PRD.md | Restrição | Ordem só por pedido, não global | TRANSCRICAO | [09:13] Larissa |
| PRD-NFR-06 | docs/PRD.md | Requisito Não Funcional | Só https; http recusado | TRANSCRICAO | [09:23] Sofia |
| PRD-NFR-07 | docs/PRD.md | Requisito Não Funcional | Secret por endpoint, nunca global | TRANSCRICAO | [09:21] Sofia |
| PRD-NFR-08 | docs/PRD.md | Requisito Não Funcional | Limite de 64 KB, com erro e sem truncar | TRANSCRICAO | [09:23] Sofia; [09:24] Larissa |
| PRD-NFR-09 | docs/PRD.md | Requisito Não Funcional | Cliente tem até 10 s para responder | TRANSCRICAO | [09:42] Diego |
| PRD-NFR-10 | docs/PRD.md | Requisito Não Funcional | Janela de retentativa de ~15 h | TRANSCRICAO | [09:17] Diego; [09:17] Marcos |
| PRD-NFR-11 | docs/PRD.md | Requisito Não Funcional | Autenticado no CRUD; ADMIN e auditoria no reenvio | TRANSCRICAO | [09:36] Larissa; [09:37] Sofia |
| PRD-NFR-12 | docs/PRD.md | Restrição | Sem infra nova; mesmo banco e mesma stack | TRANSCRICAO | [09:07] Diego; [09:11] Diego |
| PRD-DEC-01 | docs/PRD.md | Decisão | Evento registrado no banco junto da mudança de status (ADR-001) | TRANSCRICAO | [09:08] Larissa |
| PRD-DEC-02 | docs/PRD.md | Decisão | Processo de envio separado, a cada 2 s (ADR-002) | TRANSCRICAO | [09:10] Larissa; [09:11] Diego |
| PRD-DEC-03 | docs/PRD.md | Decisão | 5 retentativas em ~15 h e reenvio manual (ADR-003) | TRANSCRICAO | [09:17] Larissa; [09:18] Diego |
| PRD-DEC-04 | docs/PRD.md | Decisão | HMAC-SHA256 com secret por endpoint e rotação (ADR-004) | TRANSCRICAO | [09:22] Sofia |
| PRD-DEC-05 | docs/PRD.md | Decisão | At-least-once com id de evento (ADR-005) | TRANSCRICAO | [09:26] Larissa |
| PRD-DEC-06 | docs/PRD.md | Decisão | Reuso dos padrões do OMS (ADR-006) | TRANSCRICAO | [09:30] Larissa |
| PRD-DEC-07 | docs/PRD.md | Decisão | Notificação como snapshot do momento da mudança (ADR-007) | TRANSCRICAO | [09:52] Larissa; [09:52] Diego; [09:52] Bruno |
| PRD-DEP-01 | docs/PRD.md | Dependência | Alteração no fluxo de mudança de status (Pedidos) | TRANSCRICAO | [09:40] Bruno |
| PRD-DEP-02 | docs/PRD.md | Dependência | MySQL e stack atuais | TRANSCRICAO | [09:07] Diego; [09:11] Diego |
| PRD-DEP-03 | docs/PRD.md | Dependência | Revisão de segurança de 2 dias úteis | TRANSCRICAO | [09:46] Sofia |
| PRD-DEP-04 | docs/PRD.md | Dependência | Portal de desenvolvedor (Marcos) | TRANSCRICAO | [09:26] Marcos; [09:40] Marcos |
| PRD-DEP-05 | docs/PRD.md | Dependência | Cliente: https, verificação de assinatura e dedup | TRANSCRICAO | [09:20] Sofia; [09:25] Diego |
| PRD-DEP-06 | docs/PRD.md | Dependência | Usuários que representam os clientes | TRANSCRICAO | [09:32] Marcos |
| PRD-DEP-07 | docs/PRD.md | Dependência | Operar o processo adicional de envio | TRANSCRICAO | [09:11] Diego; [09:11] Larissa |
| PRD-RISK-01 | docs/PRD.md | Risco | Atraso leva a Atlas ao concorrente | TRANSCRICAO | [09:00] Marcos; [09:46] Larissa; [09:47] Marcos |
| PRD-RISK-02 | docs/PRD.md | Risco | Cliente processa duplicatas | TRANSCRICAO | [09:25] Sofia; [09:26] Marcos |
| PRD-RISK-03 | docs/PRD.md | Risco | Vazamento de secret de cliente | TRANSCRICAO | [09:21] Sofia; [09:22] Diego |
| PRD-RISK-04 | docs/PRD.md | Risco | Revisão de segurança espremida pelo prazo | TRANSCRICAO | [09:46] Sofia; [09:47] Larissa |
| PRD-RISK-05 | docs/PRD.md | Risco | Webhook quebrado sem aviso ao cliente | TRANSCRICAO | [09:34] Marcos; [09:37] Larissa |
| PRD-RISK-06 | docs/PRD.md | Risco | Volume de notificações sobrecarrega o cliente | TRANSCRICAO | [09:38] Diego; [09:39] Larissa |
| PRD-CA-01 | docs/PRD.md | Critério de aceitação | Cadastro https com status recebe a secret | TRANSCRICAO | [09:31] Marcos; [09:23] Sofia |
| PRD-CA-02 | docs/PRD.md | Critério de aceitação | Cadastro http recusado | TRANSCRICAO | [09:23] Sofia |
| PRD-CA-03 | docs/PRD.md | Critério de aceitação | Notificação em < 10 s | TRANSCRICAO | [09:02] Marcos |
| PRD-CA-04 | docs/PRD.md | Critério de aceitação | Status não assinado não notifica | TRANSCRICAO | [09:34] Bruno |
| PRD-CA-05 | docs/PRD.md | Critério de aceitação | Assinatura validável; evento e endpoint identificáveis | TRANSCRICAO | [09:20] Sofia; [09:25] Diego; [09:44] Sofia |
| PRD-CA-06 | docs/PRD.md | Critério de aceitação | Endpoint fora por até ~15 h recebe depois | TRANSCRICAO | [09:17] Diego |
| PRD-CA-07 | docs/PRD.md | Critério de aceitação | Reenvio só por ADMIN | TRANSCRICAO | [09:18] Diego; [09:36] Larissa |
| PRD-CA-08 | docs/PRD.md | Critério de aceitação | Secret antiga válida por 24 h após a rotação | TRANSCRICAO | [09:21] Sofia |
| PRD-CA-09 | docs/PRD.md | Critério de aceitação | Últimas 100 entregas visíveis | TRANSCRICAO | [09:34] Marcos |
| PRD-CA-10 | docs/PRD.md | Critério de aceitação | Editar, remover e listar endpoints | TRANSCRICAO | [09:33] Bruno |
| PRD-TST-01 | docs/PRD.md | Validação | Revisão do design com Bruno e Diego antes de codar | TRANSCRICAO | [09:50] Larissa |
| PRD-TST-02 | docs/PRD.md | Validação | Testes automatizados na suíte existente (vitest + supertest) | CODIGO | tests/orders.test.ts |
| PRD-TST-03 | docs/PRD.md | Validação | Teste ponta a ponta da integração com pedidos | TRANSCRICAO | [09:46] Larissa |
| PRD-TST-04 | docs/PRD.md | Validação | Simulação de cliente fora do ar por horas | TRANSCRICAO | [09:16] Diego; [09:17] Diego |
| PRD-TST-05 | docs/PRD.md | Validação | Revisão de segurança da Sofia | TRANSCRICAO | [09:46] Sofia |
| PRD-TST-06 | docs/PRD.md | Validação | Acompanhamento pós-lançamento de latência, falhas e volume | TRANSCRICAO | [09:02] Marcos; [09:37] Larissa; [09:39] Diego |

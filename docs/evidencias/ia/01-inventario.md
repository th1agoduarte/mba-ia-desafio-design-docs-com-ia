<!-- gerado por tools/ia.py em 2026-11-15T13:14:51 | modelo: gemini/gemini-3.5-flash-lite | prompt: prompts/01-inventario.md | tokens entrada/saída: 7602/5128 -->

## Inventário
| # | Categoria | Item (uma linha) | Trecho literal | Origem | Arquivo real |
|---|---|---|---|---|---|
| 1 | CONTEXTO_NEGOCIO | Clientes B2B (Atlas Comercial, MaxDistribuição, Nova Cargo) solicitam webhooks em tempo real para status de pedidos | Três clientes B2B: Atlas Comercial, MaxDistribuição e Nova Cargo. Os três querem ser notificados em tempo real | [09:00] Marcos | não existe (novo) |
| 2 | CONTEXTO_NEGOCIO | Clientes atuais usam polling em GET /orders, causando integração lenta e cara | Hoje eles ficam batendo no GET /orders de tempos em tempos pra ver se mudou alguma coisa | [09:00] Marcos | `src/modules/orders/order.routes.ts` |
| 3 | REQ_NAO_FUNCIONAL | Latência considerada "tempo real" deve ser abaixo de 10 segundos | Pra eles, qualquer coisa abaixo de 10 segundos já é "tempo real" | [09:02] Marcos | não existe (novo) |
| 4 | REQ_FUNCIONAL | Webhooks serão exclusivamente outbound (do nosso sistema para os clientes) | Só saindo da gente pra eles. Eles querem receber, não mandar | [09:02] Marcos | não existe (novo) |
| 5 | ALTERNATIVA_DESCARTADA | Disparo síncrono de webhook dentro do service de orders rejeitado por travar mudanças de status e não permitir rollback | Síncrono não rola. A transação de mudança de status hoje já é pesada | [09:04] Bruno | `src/modules/orders/order.service.ts` |
| 6 | ALTERNATIVA_DESCARTADA | Uso de Redis Streams rejeitado por exigir infra adicional e overengineering para time pequeno | A alternativa seria botar Redis Streams ou alguma coisa parecida, mas a gente acabaria precisando subir mais infra | [09:07] Larissa; [09:07] Diego | não existe (novo) |
| 7 | REQ_FUNCIONAL | Padrão Outbox: inserir evento na tabela na mesma transação SQL que atualiza orders e order_status_history | dentro da mesma transação SQL que atualiza orders e order_status_history, a gente também insere uma linha numa tabela tipo webhook_outbox | [09:06] Diego | `src/modules/orders/order.service.ts` |
| 8 | REQ_FUNCIONAL | Worker separado faz leitura da tabela outbox e dispara chamadas HTTP | Um worker separado fica lendo essa tabela e disparando as chamadas HTTP | [09:06] Diego | não existe (novo) |
| 9 | DETALHE_TECNICO | Tabela outbox possui índices nos campos status (pendente, processando, falhou, entregue) e created_at | Tabela tem índice no campo de status (pendente, processando, falhou, entregue) e em created_at | [09:08] Diego | `prisma/schema.prisma` |
| 10 | ADIADO_OU_FORA | Arquivamento de linhas entregues da outbox após 30 dias é fora do escopo desta feature | Linhas entregues a gente arquiva depois de 30 dias ou assim, fora do escopo dessa feature | [09:08] Diego | não existe (novo) |
| 11 | DECISAO | Arquitetura de outbox em MySQL adotada | Tá decidido então: outbox em MySQL | [09:08] Larissa | `prisma/schema.prisma` |
| 12 | REQ_FUNCIONAL | Worker lê a outbox via polling em loop a cada 2 segundos | Polling em loop. A cada 2 segundos, busca os eventos pendentes mais antigos | [09:09] Diego | não existe (novo) |
| 13 | ALTERNATIVA_DESCARTADA | Uso de trigger do banco para notificar o worker rejeitado por MySQL não ter listener nativo e soluções alternativas ficarem esquisitas | MySQL não tem listener nativo tipo o NOTIFY/LISTEN do Postgres. Trigger no banco a gente até tem, mas ela não notifica processo externo | [09:09] Diego | não existe (novo) |
| 14 | DECISAO | Worker opera por polling a cada 2 segundos | Vamos registrar isso como uma decisão. Worker em polling, 2s | [09:10] Larissa | não existe (novo) |
| 15 | RESTRICAO | Worker deve rodar como processo separado, não na mesma instância da API | O worker tem que rodar como processo separado, não dentro da mesma instância da API | [09:11] Diego | `src/server.ts` |
| 16 | DETALHE_TECNICO | Criação de novo entry-point src/worker.ts e script npm run worker | criar um src/worker.ts e um script "npm run worker" | [09:11] Larissa | `package.json` |
| 17 | RESTRICAO | Worker deve conectar ao mesmo banco de dados | vai precisar conectar no mesmo banco e usar o mesmo Prisma client | [09:11] Bruno | `src/config/database.ts` |
| 18 | CONTEXTO_NEGOCIO | Garantia de ordering é apenas por order_id e enquanto houver single-worker | Por enquanto, single-worker e ordering implícita por order_id | [09:12] Diego | não existe (novo) |
| 19 | ADIADO_OU_FORA | Escalonamento futuro com particionamento por order_id ou lock pessimista é problema do futuro | Aí dá pra particionar por order_id, ou usar lock pessimista. Mas isso é problema do futuro, não agora | [09:13] Diego | não existe (novo) |
| 20 | REQ_FUNCIONAL | Mecanismo de retry com backoff exponencial para clientes offline | Backoff exponencial. Tenta de novo depois de algum tempo, vai aumentando o intervalo | [09:15] Diego | não existe (novo) |
| 21 | ALTERNATIVA_DESCARTADA | Retry indefinido rejeitado por manter eventos pendurados para sempre caso o cliente suma | Algumas pessoas defendem retry indefinido com backoff, mas isso traz o problema de evento ficar pendurado pra sempre | [09:15] Diego | não existe (novo) |
| 22 | ALTERNATIVA_DESCARTADA | Apenas 3 tentativas de retry rejeitado por ser muito curto para manutenções planejadas longas | 3 não é melhor? Mais agressivo... 3 é pouco | [09:16] Bruno; [09:16] Diego | não existe (novo) |
| 23 | DECISAO | Adotado teto de 5 tentativas de retry | Cinco fica bom... Decidido: 5 tentativas | [09:16] Larissa; [09:17] Larissa | não existe (novo) |
| 24 | DETALHE_TECNICO | Progressão do backoff exponencial: 1 minuto, 5 minutos, 30 minutos, 2 horas, 12 horas | Eu pensei em 1 minuto, 5 minutos, 30 minutos, 2 horas, 12 horas | [09:17] Diego | não existe (novo) |
| 25 | DECISAO | Progressão de backoff definida em 1m/5m/30m/2h/12h | Decidido: 5 tentativas, backoff 1m/5m/30m/2h/12h | [09:17] Larissa | não existe (novo) |
| 26 | REQ_FUNCIONAL | Dead Letter Queue (DLQ) persistida em tabela separada webhook_dead_letter | tabela webhook_dead_letter separada, com a payload, motivo da falha e timestamp | [09:18] Diego | `prisma/schema.prisma` |
| 27 | REQ_FUNCIONAL | Endpoint administrativo POST /admin/webhooks/dead-letter/:id/replay para reprocessamento manual de DLQ | Manual via endpoint admin. Tipo um POST /admin/webhooks/dead-letter/:id/replay | [09:18] Diego | não existe (novo) |
| 28 | REQ_NAO_FUNCIONAL | Segurança: autenticidade e integridade garantidas por HMAC assinado com secret compartilhada em header X-Signature | Padrão é HMAC. A gente assina o payload com uma secret compartilhada entre nós e o cliente, manda a assinatura num header tipo X-Signature | [09:20] Sofia | não existe (novo) |
| 29 | DETALHE_TECNICO | Algoritmo de hash para HMAC é SHA-256 | SHA-256. HMAC-SHA256 é o padrão de mercado | [09:20] Sofia | não existe (novo) |
| 30 | REQ_NAO_FUNCIONAL | Cada endpoint de webhook do cliente possui uma secret única por endpoint | cada endpoint de webhook do cliente tem que ter uma secret única. Não é uma secret global | [09:21] Sofia | `prisma/schema.prisma` |
| 31 | DETALHE_TECNICO | Tabela de configuração armazena url + secret + customer_id + estado ativo | tabela de configuração de webhook armazena url + secret + customer_id + estado ativo | [09:21] Bruno; [09:21] Sofia | `prisma/schema.prisma` |
| 32 | REQ_FUNCIONAL | Suporte a rotação de secret com grace period de 24 horas onde a secret antiga continua válida | secret tem que ser rotacionável... a antiga fica válida por 24 horas em paralelo | [09:21] Sofia | não existe (novo) |
| 33 | DECISAO | Adoção de HMAC-SHA256, secret por endpoint e rotação com grace period de 24h | Decidido: HMAC-SHA256 sobre o corpo do request, secret por endpoint, suporte a rotação com grace period de 24h | [09:22] Sofia | não existe (novo) |
| 34 | RESTRICAO | Obrigatório uso de HTTPS (TLS) para URLs de webhook, validado via schema Zod | TLS obrigatório. URL do webhook tem que ser https... validação no schema Zod | [09:23] Sofia | `src/middlewares/validate.middleware.ts` |
| 35 | REQ_NAO_FUNCIONAL | Limite de tamanho de payload fixado em 64KB, gerando erro caso ultrapassado | 64KB já é um teto generoso... 64KB de limite, erro caso ultrapasse | [09:24] Diego; [09:24] Larissa | não existe (novo) |
| 36 | REQ_NAO_FUNCIONAL | Garantia at-least-once na entrega dos webhooks | A gente vai garantir at-least-once. Pode acontecer de o cliente receber o mesmo evento duas vezes | [09:24] Diego | não existe (novo) |
| 37 | DETALHE_TECNICO | Header X-Event-Id enviado com UUID único por evento para dedup do cliente | mandamos um event_id no header, X-Event-Id, com um UUID gerado quando o evento entra na outbox | [09:25] Diego | não existe (novo) |
| 38 | ALTERNATIVA_DESCARTADA | Garantia de exactly-once rejeitada por exigir coordenação bilateral e complexidade excessiva | Garantir exactly-once exigiria coordenação dos dois lados e fica muito mais complexo | [09:25] Diego | non existe (novo) |
| 39 | DECISAO | Modelo at-least-once adotado com header X-Event-Id para deduplicação pelo cliente | At-least-once com X-Event-Id pra dedup do lado do cliente. Decisão | [09:26] Larissa | não existe (novo) |
| 40 | REQ_FUNCIONAL | Estrutura de código modular em src/modules/webhooks seguindo o padrão da codebase | propor uma pasta src/modules/webhooks com toda a estrutura | [09:27] Bruno | não existe (novo) |
| 41 | DETALHE_TECNICO | Lógica de processamento do worker alocada em arquivo dentro do módulo (ex: webhook.worker.ts ou webhook.processor.ts) | lógica de processamento fica num arquivo dentro do módulo, tipo src/modules/webhooks/webhook.worker.ts ou webhook.processor.ts | [09:28] Bruno | não existe (novo) |
| 42 | DETALHE_TECNICO | Códigos de erro customizados para o módulo com prefixo WEBHOOK_ (ex: WEBHOOK_NOT_FOUND, WEBHOOK_INVALID_URL) | Códigos tipo WEBHOOK_NOT_FOUND, WEBHOOK_INVALID_URL, WEBHOOK_SECRET_REQUIRED... Prefixo WEBHOOK_ para tudo do módulo | [09:28] Bruno; [09:29] Larissa | `src/shared/errors/app-error.ts` |
| 43 | REQ_NAO_FUNCIONAL | Reutilização do logger Pino, classes AppError e middleware de erro centralizado existente | logger, que é Pino, já tá no projeto inteiro... middleware de erro centralizado já trata AppError, Zod e Prisma | [09:29] Bruno | `src/shared/logger/index.ts` |
| 44 | DECISAO | Reuso máximo do ecossistema existente (AppError, Pino, error middleware, padrão de schemas Zod, códigos de erro) | Decisão: reuso máximo do que já existe. AppError, Pino, error middleware, padrão de módulos, padrão de schemas Zod | [09:30] Larissa | `src/shared/errors/app-error.ts` |
| 45 | REQ_FUNCIONAL | Endpoint POST para o cliente cadastrar webhook informando url e lista de status desejados | Endpoint POST. Campos: url, secret é gerada pela gente... Lista de status que ele quer receber | [09:31] Marcos; [09:33] Marcos | `src/modules/webhooks/` |
| 46 | DETALHE_TECNICO | Customer_id obtido do usuário autenticado no request (não do JWT operador) e passado no body ou path | customer_id é passado no body ou no path. Não vem do JWT | [09:32] Larissa | `src/modules/webhooks/` |
| 47 | REQ_FUNCIONAL | Endpoints PATCH para editar, DELETE para remover e GET para listar webhooks de um customer | PATCH pra editar, DELETE pra remover, GET pra listar os webhooks de um customer | [09:33] Bruno | `src/modules/webhooks/` |
| 48 | REQ_FUNCIONAL | Filtragem de eventos ocorre na inserção da outbox baseada nos status de interesse do webhook | Filtra na inserção do outbox... Se nenhum webhook do customer quer aquele status, nem insere | [09:33] Marcos; [09:34] Bruno | `src/modules/webhooks/` |
| 49 | REQ_FUNCIONAL | Endpoint GET /webhooks/:id/deliveries para consulta do histórico de entregas | O cliente precisa conseguir ver o histórico de entregas... GET /webhooks/:id/deliveries | [09:34] Marcos | `src/modules/webhooks/` |
| 50 | REQ_NAO_FUNCIONAL | Endpoint de admin protegido obrigatoriamente por role ADMIN e log de auditoria | Tem que ser ADMIN sim... o endpoint de admin tem que logar quem fez o replay, pra auditoria | [09:36] Sofia | `src/middlewares/auth.middleware.ts` |
| 51 | DECISAO | Role ADMIN obrigatório no replay de DLQ, reaproveitando requireRole existente | Decidido, role ADMIN obrigatório no replay e a gente reaproveita o requireRole que já existe | [09:36] Larissa | `src/middlewares/auth.middleware.ts` |
| 52 | ADIADO_OU_FORA | Notificação de falhas por email fica para a próxima fase | Email tá fora de escopo dessa fase. Talvez próxima fase | [09:37] Larissa | não existe (novo) |
| 53 | QUESTAO_ABERTA | Rate limiting de envio para clientes fica registrado para observar e decidir depois | rate limiting de envio pra cliente... A gente observa e implementa se virar problema. Mas vale registrar como ponto em aberto | [09:38] Diego; [09:39] Larissa | não existe (novo) |
| 54 | ADIADO_OU_FORA | Dashboard visual para cliente ver webhooks está fora de escopo | Dashboard visual? Tipo painel pro cliente ver os webhooks dele?... Não, agora não. Só endpoints. Painel é projeto separado | [09:39] Marcos; [09:40] Larissa | não existe (novo) |
| 55 | DETALHE_TECNICO | Inserção do evento de webhook na outbox ocorre dentro da transação changeStatus do order.service usando tx client | alteração crítica é dentro do service de orders, no método changeStatus... inserir na webhook_outbox dentro da mesma transação | [09:40] Bruno | `src/modules/orders/order.service.ts` |
| 56 | DETALHE_TECNICO | Função pura publishWebhookEvent(tx, order, fromStatus, toStatus) aceita o client da transação atual | propor uma função publishWebhookEvent(tx, order, fromStatus, toStatus) que aceita o tx client da transação atual | [09:41] Bruno | `src/modules/orders/order.service.ts` |
| 57 | REQ_NAO_FUNCIONAL | Timeout do HTTP call do worker fixado em 10 segundos | Timeout do HTTP call do worker. Quanto?... 10 segundos | [09:42] Sofia; [09:42] Diego | não existe (novo) |
| 58 | DETALHE_TECNICO | Payload JSON do webhook estruturado com event_id, event_type, timestamp, order_id, order_number, from_status, to_status, customer_id e total_cents | JSON com event_id, event_type tipo "order.status_changed", timestamp ISO 8601, order_id, order_number, from_status, to_status, customer_id, e os campos básicos da order tipo total_cents | [09:43] Diego | não existe (novo) |
| 59 | DETALHE_TECNICO | Headers HTTP enviados no webhook: X-Event-Id, X-Signature, X-Timestamp, Content-Type, X-Webhook-Id | X-Event-Id com o UUID, X-Signature com o HMAC, X-Timestamp com o timestamp do envio, Content-Type application/json... X-Webhook-Id também | [09:44] Diego; [09:44] Sofia | não existe (novo) |
| 60 | CONTEXTO_NEGOCIO | Prazo de entrega estimado em 3 sprints, com revisão de segurança da Sofia incluída | eu chuto três sprints incluindo revisão da Sofia... Reservem pelo menos dois dias úteis pra eu revisar o código de segurança | [09:46] Larissa; [09:46] Sofia | não existe (novo) |
| 61 | DETALHE_TECNICO | IDs da tabela outbox serão do tipo UUID, seguindo o padrão do projeto | Modelagem de outbox... UUID, segue o padrão do resto do projeto. Tudo é uuid | [09:46] Larissa; [09:51] Larissa | `prisma/schema.prisma` |
| 62 | DETALHE_TECNICO | Payload do evento guardado em formato renderizado (snapshot) no momento da inserção na outbox | o evento da outbox guarda o payload renderizado já... snapshot na inserção | [09:51] Bruno; [09:52] Diego | `prisma/schema.prisma` |

## Ambiguidades
- **Janela de Retry vs Contagem de Tempo:** Diego afirmou inicialmente que 5 tentativas cobrem "uma janela de até 12 ou 24 horas" [09:15] e, em seguida, detalhou o backoff somando `1m + 5m + 30m + 2h + 12h`, resultando em um total de aproximadamente 14 horas e 36 minutos entre a primeira falha e a última tentativa [09:17], divergindo do teto máximo de "24 horas".
- **Autenticação do Endpoint de Cadastro:** Marcos sugeriu inicialmente que o `customer_id` seria implícito do JWT do cliente [09:31], mas Bruno e Larissa corrigiram afirmando que o JWT atual é do usuário operador da API e que o `customer_id` deve ser passado explicitamente no body ou no path [09:32].
- **Papéis (Roles) para CRUD de Configuração:** Marcos perguntou se o CRUD de configuração de webhook exige permissões específicas [09:36], ao que Sofia respondeu inicialmente "Por enquanto sim. Más pra frente a gente pode endurecer" [09:37], gerando ambiguidade sobre quais papéis exatos (além do `ADMIN` exigido estritamente para o replay de DLQ) podem gerenciar as configurações na primeira versão.

## Contagem por categoria
| Categoria | Itens |
|---|---|
| DECISAO | 7 |
| REQ_FUNCIONAL | 11 |
| REQ_NAO_FUNCIONAL | 8 |
| RESTRICAO | 3 |
| ALTERNATIVA_DESCARTADA | 7 |
| ADIADO_OU_FORA | 4 |
| QUESTAO_ABERTA | 1 |
| GANCHO_CODIGO | 0 |
| DETALHE_TECNICO | 14 |
| CONTEXTO_NEGOCIO | 7 |
| **Total** | **62** |

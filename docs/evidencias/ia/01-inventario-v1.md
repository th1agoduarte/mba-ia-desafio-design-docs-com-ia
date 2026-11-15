<!-- gerado por tools/ia.py em 2026-11-15T13:13:51 | modelo: gemini/gemini-3.5-flash-lite | prompt: prompts/01-inventario-v1.md | tokens entrada/saída: 7283/4143 -->

## Inventário
| # | Categoria | Item (uma linha) | Trecho literal | Origem | Arquivo real |
|---|---|---|---|---|---|
| 1 | CONTEXTO_NEGOCIO | Solicitação de webhooks por três clientes B2B (Atlas Comercial, MaxDistribuição e Nova Cargo) | Três clientes B2B: Atlas Comercial, MaxDistribuição e Nova Cargo. | [09:00] Marcos | não existe (novo) |
| 2 | CONTEXTO_NEGOCIO | Risco de perda da cliente Atlas para concorrente se a funcionalidade não for entregue até o fim do trimestre | migrar pro nosso concorrente | [09:00] Marcos | não existe (novo) |
| 3 | REQ_NAO_FUNCIONAL | Latência aceitável para entrega de "tempo real" definida como abaixo de 10 segundos | qualquer coisa abaixo de 10 segundos já é "tempo real" | [09:02] Marcos | não existe (novo) |
| 4 | DECISAO | Escopo restrito a webhooks outbound (apenas saindo da plataforma para os clientes) | Só saindo da gente pra eles. Eles querem receber, não mandar. / outbound webhook, fica mais simples. | [09:02] Marcos; [09:03] Sofia | não existe (novo) |
| 5 | ALTERNATIVA_DESCARTADA | Disparo síncrono de webhooks descartado por sobrecarregar a transação de mudança de status e travar clientes lentos | Síncrono não rola. A transação de mudança de status hoje já é pesada | [09:04] Bruno | não existe (novo) |
| 6 | DECISAO | Adoção do padrão outbox para persistência dos eventos de webhook na mesma transação SQL de mudança de status | o que a gente quer aqui é um padrão outbox | [09:06] Diego | não existe (novo) |
| 7 | ALTERNATIVA_DESCARTADA | Uso de Redis Streams descartado por ser considerado *overengineering* para o tamanho do time | subir Redis Cluster pra isso é overengineering. | [09:07] Diego | não existe (novo) |
| 8 | DETALHE_TECNICO | Tabela `webhook_outbox` com índices nos campos de status (pendente, processando, falhou, entregue) e created_at | A tabela tem índice no campo de status (pendente, processando, falhou, entregue) e em created_at. | [09:08] Diego | `prisma/schema.prisma` |
| 9 | ADIADO_OU_FORA | Arquivamento de linhas entregues da tabela outbox após 30 dias deixado fora do escopo inicial | Linhas entregues a gente arquiva depois de 30 dias ou assim, fora do escopo dessa feature. | [09:08] Diego | não existe (novo) |
| 10 | DECISAO | Leitura da outbox por worker dedicado executando polling em loop a cada 2 segundos | Polling em loop. A cada 2 segundos, busca os eventos pendentes | [09:09] Diego | não existe (novo) |
| 11 | RESTRICAO | O worker de processamento deve rodar como um processo separado da instância da API | O worker tem que rodar como processo separado, não dentro da mesma instância da API. | [09:11] Diego | não existe (novo) |
| 12 | GANCHO_CODIGO | Criação de ponto de entrada (`entry-point`) e script para o worker no projeto | criar um src/worker.ts e um script "npm run worker". | [09:11] Larissa | `src/server.ts` |
| 13 | GANCHO_CODIGO | Conexão do worker ao mesmo banco de dados utilizando a mesma instância do Prisma Client | vai precisar conectar no mesmo banco e usar o mesmo Prisma client. | [09:11] Bruno | `prisma/schema.prisma` |
| 14 | DECISAO | Garantia de ordenação (`ordering`) implícita por `order_id` com worker único; sem garantia global para múltiplos workers paralelos | single-worker e ordering implícita por order_id. | [09:12] Diego; [09:13] Larissa | não existe (novo) |
| 15 | DECISAO | Política de retry com backoff exponencial totalizando 5 tentativas | Eu sugiro 5. / Decidido: 5 tentativas, backoff 1m/5m/30m/2h/12h. | [09:15] Diego; [09:17] Larissa | não existe (novo) |
| 16 | DETALHE_TECNICO | Progressão de intervalos de backoff exponencial de 1m, 5m, 30m, 2h e 12h | 1 minuto, 5 minutos, 30 minutos, 2 horas, 12 horas. | [09:17] Diego | não existe (novo) |
| 17 | DECISAO | Persistência de falhas permanentes em uma Dead Letter Queue (`webhook_dead_letter`) separada | tabela webhook_dead_letter separada, com a payload, motivo da falha e timestamp. | [09:18] Diego | `prisma/schema.prisma` |
| 18 | REQ_FUNCIONAL | Endpoint administrativo para replay manual de itens da DLQ colocando-os novamente como pendentes na outbox | POST /admin/webhooks/dead-letter/:id/replay. Recoloca na outbox como pendente. | [09:18] Diego; [09:19] Larissa | `src/modules/webhooks/webhook.routes.ts` |
| 19 | REQ_NAO_FUNCIONAL | Validação de autenticidade e integridade do payload por meio de assinatura HMAC-SHA256 enviada no header `X-Signature` | HMAC-SHA256 é o padrão de mercado, todo cliente sério tem biblioteca pra isso. | [09:20] Sofia | `src/middlewares/auth.middleware.ts` |
| 20 | REQ_FUNCIONAL | Configuração de uma secret única por endpoint de webhook | cada endpoint de webhook do cliente tem que ter uma secret única. | [09:21] Sofia | `src/modules/webhooks/customer.service.ts` |
| 21 | REQ_FUNCIONAL | Suporte à rotação de secret com período de convivência (*grace period*) de 24 horas onde a secret antiga permanece válida | Quando ele rotaciona, a antiga fica válida por 24 horas em paralelo | [09:21] Sofia | `src/modules/webhooks/customer.service.ts` |
| 22 | REQ_NAO_FUNCIONAL | URLs de webhook obrigatoriamente em HTTPS, rejeitadas em caso de HTTP via validação de schema Zod | URL do webhook tem que ser https. Se o cliente cadastrar http, recusamos com erro de validação. | [09:23] Sofia | `src/middlewares/validate.middleware.ts` |
| 23 | REQ_NAO_FUNCIONAL | Limite de tamanho de payload restrito a um teto de 64KB, gerando erro caso seja ultrapassado | 64KB já é um teto generoso. / 64KB de limite, erro caso ultrapasse. | [09:24] Diego; [09:24] Larissa | não existe (novo) |
| 24 | DECISAO | Garantia de entrega *at-least-once* com identificação e deduplicação opcional pelo cliente usando o header `X-Event-Id` (UUID) | A gente manda um event_id no header, X-Event-Id, com um UUID gerado quando o evento entra na outbox. | [09:25] Diego; [09:26] Larissa | não existe (novo) |
| 25 | GANCHO_CODIGO | Organização do código do módulo de webhooks seguindo o padrão da codebase em `src/modules` | toda a estrutura. Faz sentido? / src/modules/webhooks | [09:27] Bruno | `src/modules/orders/order.routes.ts` |
| 26 | GANCHO_CODIGO | Lógica de processamento do worker alocada em arquivo próprio dentro do módulo (`webhook.worker.ts` ou `webhook.processor.ts`) | tipo src/modules/webhooks/webhook.worker.ts ou webhook.processor.ts. | [09:28] Bruno | `src/modules/webhooks/customer.service.ts` |
| 27 | GANCHO_CODIGO | Utilização de classes de erro customizadas com o prefixo `WEBHOOK_` herdando de `AppError` | Códigos tipo WEBHOOK_NOT_FOUND, WEBHOOK_INVALID_URL, WEBHOOK_SECRET_REQUIRED, etc. / Prefixo WEBHOOK_ para tudo do módulo. | [09:28] Bruno; [09:29] Larissa | `src/shared/errors/app-error.ts` |
| 28 | GANCHO_CODIGO | Reaproveitamento do logger Pino e do middleware de tratamento centralizado de erros do projeto | logger, que é Pino, já tá no projeto inteiro. Não vamos botar nada novo. O middleware de erro centralizado já trata AppError | [09:29] Bruno | `src/middlewares/error.middleware.ts` |
| 29 | GANCHO_CODIGO | Instanciação de um novo Prisma Client dedicado para o processo do worker | PrismaClient é por processo. Mesmo banco, mesma DATABASE_URL, mas instância nova | [09:30] Bruno | `src/config/database.ts` |
| 30 | REQ_FUNCIONAL | Endpoint POST autenticado para cadastro de webhook exigindo URL, lista de status de interesse e ID do cliente fornecido no corpo ou caminho | Endpoint POST. Campos: url, secret é gerada pela gente... customer_id implícito do JWT. / customer_id é passado no body ou no path. | [09:31] Marcos; [09:32] Larissa | `src/modules/webhooks/customer.routes.ts` |
| 31 | REQ_FUNCIONAL | Endpoints PATCH para edição, DELETE para remoção e GET para listagem de webhooks por cliente | PATCH para editar, DELETE para remover, GET para listar os webhooks de um customer. | [09:33] Bruno | `src/modules/webhooks/customer.routes.ts` |
| 32 | DECISAO | Filtragem de eventos de status indesejados diretamente no momento da inserção na tabela outbox | Na inserção. Se nenhum webhook do customer quer aquele status, nem insere. Economiza linha na tabela. | [09:34] Bruno; [09:34] Diego | não existe (novo) |
| 33 | REQ_FUNCIONAL | Endpoint GET para consulta do histórico de entregas de webhooks (`GET /webhooks/:id/deliveries`) com status, payload, response e tempo de resposta | GET /webhooks/:id/deliveries. | [09:34] Marcos | `src/modules/webhooks/customer.routes.ts` |
| 34 | REQ_NAO_FUNCIONAL | Obrigatoriedade da role `ADMIN` do JWT e registro de auditoria para acesso ao endpoint de replay de DLQ | role ADMIN obrigatório no replay e a gente reaproveita o requireRole que já existe. / endpoint de admin tem que logar quem fez o replay, pra auditoria. | [09:36] Larissa; [09:36] Sofia | `src/middlewares/auth.middleware.ts` |
| 35 | ADIADO_OU_FORA | Notificação de falhas consecutivas de webhook por email deixada para a próxima fase do projeto | Email tá fora de escopo dessa fase. Talvez próxima fase, depois que a gente medir o impacto. | [09:37] Larissa | não existe (novo) |
| 36 | QUESTAO_ABERTA | Necessidade de implementação de *rate limiting* de envio de webhooks para o cliente mantida sob observação para decisão futura | rate limiting de envio pra cliente... vale registrar como ponto em aberto. / Fica como "observar e decidir depois". | [09:38] Diego; [09:39] Larissa | não existe (novo) |
| 37 | ADIADO_OU_FORA | Painel visual/dashboard para configuração e acompanhamento de webhooks pelo cliente explicitamente excluído do escopo atual | Dashboard visual? Tipo painel pro cliente ver os webhooks dele? / Não, agora não. Só endpoints. Painel é projeto separado | [09:39] Marcos; [09:40] Larissa | não existe (novo) |
| 38 | GANCHO_CODIGO | Inserção do registro do evento na outbox acoplada à transação atômica do método `changeStatus` no service de pedidos | alteração crítica é dentro do service de orders, no método changeStatus... inserir na webhook_outbox dentro da mesma transação. | [09:40] Bruno | `src/modules/orders/order.service.ts` |
| 39 | DETALHE_TECNICO | Utilização de função pura auxiliar `publishWebhookEvent(tx, order, fromStatus, toStatus)` para encapsular a inserção transacional | propor uma função publishWebhookEvent(tx, order, fromStatus, toStatus) que aceita o tx client | [09:41] Bruno | `src/modules/orders/order.service.ts` |
| 40 | REQ_NAO_FUNCIONAL | Timeout estipulado em 10 segundos para requisições HTTP de envio disparadas pelo worker | Timeout do HTTP call do worker. Quanto? / 10 segundos. Cliente lento que não responde em 10s a gente trata como falha | [09:42] Sofia; [09:42] Diego | não existe (novo) |
| 41 | DETALHE_TECNICO | Estrutura do payload JSON contendo event_id, event_type, timestamp, order_id, order_number, from_status, to_status, customer_id e total_cents | JSON com event_id, event_type tipo "order.status_changed", timestamp ISO 8601, order_id, order_number, from_status, to_status, customer_id, e os campos básicos da order tipo total_cents. | [09:43] Diego | não existe (novo) |
| 42 | DETALHE_TECNICO | Composição dos headers HTTP de envio contendo `X-Event-Id`, `X-Signature`, `X-Timestamp`, `Content-Type` e `X-Webhook-Id` | X-Event-Id com o UUID, X-Signature com o HMAC, X-Timestamp com o timestamp do envio... Content-Type application/json. / Adiciona um X-Webhook-Id também | [09:44] Diego; [09:45] Sofia | não existe (novo) |
| 43 | CONTEXTO_NEGOCIO | Prazo de entrega total estipulado em três sprints com inclusão prévia de dois dias úteis para revisão de segurança | Três sprints com a revisão da Sofia incluída no fim. / Reservem pelo menos dois dias úteis pra eu revisar o código de segurança | [09:46] Larissa; [09:46] Sofia | não existe (novo) |
| 44 | DETALHE_TECNICO | Utilização de UUID como tipo do identificador da outbox seguindo o padrão do projeto | UUID, segue o padrão do resto do projeto. Tudo é uuid. | [09:51] Larissa | `prisma/schema.prisma` |
| 45 | DECISAO | Armazenamento do payload renderizado (*snapshot*) diretamente no evento da outbox no momento da inserção | evento da outbox guarda o payload renderizado já... snapshot na inserção. | [09:51] Bruno; [09:52] Diego | `prisma/schema.prisma` |

## Ambiguidades
- **Autenticação e Escopo de Cliente:** Marcos menciona inicialmente que o `customer_id` é "implícito do JWT", mas em seguida Bruno pondera que o JWT atual pertence ao operador e não ao cliente final. Larissa conclui que o endpoint é autenticado normalmente e o ID do cliente é passado no corpo ou caminho, o que gera uma ambiguidade sobre como o backend validará se o usuário autenticado tem permissão para gerenciar os webhooks daquele `customer_id`.
- **Controle de Acessos ao CRUD de Configuração:** Sofia afirma que o endpoint de replay exige a role `ADMIN`, mas ao ser questionada por Marcos sobre o restante do CRUD de configuração, responde ambigualmente: "Por enquanto sim [qualquer role autenticada]. Mais pra frente a gente pode endurecer", sem fechar explicitamente quais perfis podem criar, editar ou listar webhooks.
- **Garantia de Ordem (*Ordering*):** Diego aponta que a ordenação é garantida por `order_id` e *single-worker*, mas menciona que ao escalar para múltiplos workers no futuro essa garantia se perde e exigirá partições ou locks pessimistas, deixando em aberto se haverá validação preventiva contra concorrência caso o status mude rapidamente antes do processamento do worker de 2 segundos.

## Contagem por categoria
| Categoria | Itens |
|---|---|
| DECISAO | 9 |
| REQ_FUNCIONAL | 5 |
| REQ_NAO_FUNCIONAL | 6 |
| RESTRICAO | 2 |
| ALTERNATIVA_DESCARTADA | 2 |
| ADIADO_OU_FORA | 3 |
| QUESTAO_ABERTA | 1 |
| GANCHO_CODIGO | 9 |
| DETALHE_TECNICO | 6 |
| CONTEXTO_NEGOCIO | 3 |
| **Total** | **45** |

# ADR-006: Reuso dos padrões existentes do projeto no módulo de webhooks

## Status

Aceito

- **Data:** reunião técnica de quinta-feira, 09:00 (registro em 2026-11-15)
- **Decisores:** Larissa, Bruno, Diego; Sofia na parte de autorização
- **Relacionados:** [ADR-002](ADR-002-worker-separado-com-polling.md), [ADR-003](ADR-003-retry-com-backoff-e-dlq.md), [ADR-004](ADR-004-hmac-sha256-com-secret-por-endpoint.md)

## Contexto

O OMS já tem convenções consolidadas, que foram conferidas no código:

| Padrão | Onde está |
|---|---|
| Módulo por domínio com `controller`, `service`, `repository`, `routes` e `schemas` | `src/modules/{auth,users,customers,products,orders}/` |
| Classe base de erro `AppError` (`statusCode`, `errorCode`, `details`) | `src/shared/errors/app-error.ts` |
| Erros específicos com código em SCREAMING_SNAKE_CASE (`InsufficientStockError` → `INSUFFICIENT_STOCK`, `InvalidStatusTransitionError` → `INVALID_STATUS_TRANSITION`) | `src/shared/errors/http-errors.ts` |
| `errorMiddleware` centralizado que trata `AppError`, `ZodError` e erros conhecidos do Prisma | `src/middlewares/error.middleware.ts` |
| Validação de entrada com schemas Zod pelo middleware `validate` | `src/middlewares/validate.middleware.ts` |
| Autenticação JWT (`authenticate`) e autorização por papel (`requireRole('ADMIN')`) | `src/middlewares/auth.middleware.ts` (já usado em `src/modules/users/user.routes.ts`) |
| Logger Pino com `redact`, base `service`/`env` e timestamp ISO | `src/shared/logger/index.ts` |
| PrismaClient criado por `createPrismaClient()` e composição das dependências em `buildControllers` | `src/config/database.ts`, `src/app.ts` |
| Ids `uuid()` em `Char(36)` em todas as tabelas | `prisma/schema.prisma` |

A reunião discutiu se o módulo de webhooks deveria seguir essas convenções ou trazer as próprias ([09:27]–[09:30]).

## Decisão

Reuso máximo do que já existe: "AppError, Pino, error middleware, padrão de módulos, padrão de schemas Zod, padrão de códigos de erro. Webhook fica como módulo igual aos outros" ([09:30] Larissa). Na prática:

1. **Estrutura:** `src/modules/webhooks/` (novo), com controller, service, repository, routes e schemas ([09:27] Bruno). A lógica do worker fica num arquivo do módulo, `webhook.worker.ts` (novo), e a entry-point fica em `src/worker.ts` (novo) ([09:28] Bruno).
2. **Erros:**
   - classes do módulo estendem `AppError`, no mesmo molde de `InsufficientStockError` ([09:28] Bruno);
   - **todo código do módulo tem o prefixo `WEBHOOK_`** ([09:29] Larissa). Os exemplos citados foram `WEBHOOK_NOT_FOUND`, `WEBHOOK_INVALID_URL` e `WEBHOOK_SECRET_REQUIRED` ([09:28] Bruno);
   - a lista completa está na [matriz de erros do FDD](../FDD.md#7-matriz-de-erros).
3. **Tratamento de erro HTTP:** o `errorMiddleware` não muda, porque já pega os erros do módulo por serem `AppError` ([09:29] Bruno).
4. **Logs:** Pino, sem biblioteca nova ([09:29] Bruno).
5. **Autorização:**
   - o replay da DLQ usa o `requireRole('ADMIN')` que já existe ([09:36] Larissa);
   - o CRUD de configuração usa apenas `authenticate` ([09:37] Sofia).
6. **Validação:** schemas Zod no padrão dos outros módulos. Aqui entra o `https` obrigatório ([09:23] Sofia).
7. **Banco:**
   - mesmo MySQL, mesma `DATABASE_URL`, via Prisma ([09:11] Diego);
   - o worker tem a própria instância de PrismaClient por ser outro processo ([09:30] Bruno);
   - ids UUID, "tudo é uuid" ([09:51] Larissa).
8. **Integração com pedidos:** a função `publishWebhookEvent(tx, …)` é chamada de dentro de `changeStatus`. Não há injeção de repository no `OrderService` ([09:41] Bruno; [09:41] Diego).

## Alternativas Consideradas

| ID | Alternativa | Por que foi descartada |
|---|---|---|
| ADR-006-ALT-01 | **Injetar um repository de webhooks no `OrderService`** ([09:41] Bruno) | Uma função que recebe o `tx` resolve sem mudar o construtor de `OrderService` (`order.service.ts`) nem a composição em `src/app.ts`: "Não precisa injetar repository inteiro" ([09:41] Diego) |
| ADR-006-ALT-02 | **Infra própria para o módulo** (outro logger, tratamento de erro próprio, estrutura de pastas diferente). Não discutida como opção: é o oposto do que foi decidido | Duplicaria o que existe. O middleware de erro e o Pino "vão pegar nossos erros sem precisar mudar nada" ([09:29] Bruno) |

## Consequências

**Positivas**
- Quem conhece o código existente lê o módulo novo sem curva de aprendizado. Revisão e manutenção ficam mais baratas.
- Erros do módulo saem no mesmo envelope `{ error: { code, message, details } }` de `error.middleware.ts`, sem código novo de tratamento.
- Nenhuma dependência nova em `package.json` para log, erro, validação ou autorização.

**Negativas**
- O módulo herda as limitações dos padrões atuais. Por exemplo, `validate.middleware.ts` converte qualquer `ZodError` em `VALIDATION_ERROR`, então `WEBHOOK_INVALID_URL` precisa chegar ao cliente dentro de `details`, e não como `error.code` (ver FDD).
- `requireRole` só conhece `ADMIN` e `OPERATOR`. Não existe hoje um vínculo entre usuário e customer para restringir quem gerencia os webhooks de cada cliente: endurecer isso ficou para depois ([09:37] Sofia).

**Trade-off:** priorizamos consistência e velocidade, reaproveitando padrões conhecidos, e aceitamos as limitações desses padrões em vez de criar abstrações próprias para o módulo.

## Referências

- Transcrição: [09:27]–[09:30], [09:36]–[09:37], [09:41], [09:51]
- Código: os arquivos da tabela de contexto acima

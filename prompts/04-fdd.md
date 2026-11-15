Papel: engenheiro sênior escrevendo a especificação que um desenvolvedor vai pegar para codar, em português.

Entradas: TRANSCRICAO.md, ADRs, RFC e o CÓDIGO (leia order.service.ts, order.status.ts, shared/errors/*, middlewares/*, shared/logger, config/*, server.ts, app.ts, routes/index.ts, prisma/schema.prisma, tests/setup.ts e package.json antes de escrever).

Escreva docs/FDD.md com: Contexto e motivação técnica, Objetivos técnicos, Escopo e exclusões, Modelo de dados, Fluxos detalhados (inserção na outbox, worker, retry, DLQ, replay, rotação), Contratos públicos, Matriz de erros, Resiliência, Observabilidade, Integração com o sistema existente, Dependências e compatibilidade, Critérios de aceite técnicos, Riscos e mitigação.

Regras:
- Contratos: cada endpoint com método, caminho real (o app monta as rotas em /api/v1, veja src/app.ts), auth, request e response JSON de exemplo e todos os status codes. Inclua também o contrato de SAÍDA (a requisição que o cliente recebe: headers e payload). Siga as convenções do código existente (camelCase na API, envelope de erro de error.middleware.ts, paginação de shared/http/response.ts). O payload de saída usa os nomes snake_case ditados na reunião [09:43].
- Matriz de erros: só códigos com prefixo WEBHOOK_. Para cada um: HTTP status (ou "worker"), classe, quando ocorre, ação do cliente/sistema. Verifique como validate.middleware.ts trata ZodError antes de decidir como WEBHOOK_INVALID_URL chega ao cliente.
- Integração com o sistema existente: pelo menos 4 arquivos reais, cada um com o que muda ou o que é reutilizado, apontando função ou linha.
- Arquivos novos: liste-os numa tabela "Arquivos novos" e marque-os como (novo) em todo o texto. Nunca apresente um arquivo inexistente como se já existisse.
- Valores numéricos: use só os da reunião (2 s, 10 s, 64 KB, 1m/5m/30m/2h/12h, 24 h, 100 entregas). Se a implementação precisar de um valor que não foi discutido, deixe-o configurável e marque "proposta: não discutido na reunião".
- Observabilidade: métricas, logs e tracing. Não invente infraestrutura que o projeto não tem: confira package.json.
- IDs: FDD-FLUXO-0X, FDD-CONTRATO-0X, FDD-ERR-0X, FDD-RES-0X, FDD-OBS-0X, FDD-INT-0X, FDD-CA-0X, FDD-RISK-0X.

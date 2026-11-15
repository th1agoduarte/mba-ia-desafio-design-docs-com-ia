<!-- gerado por tools/ia.py em 2026-11-15T13:31:31 | modelo: gemini/gemini-3.5-flash | prompt: prompts/06-revisao-critica.md | tokens entrada/saída: 54747/20834 -->

## Problemas encontrados

| # | Tipo (A-G) | Documento | Trecho | Evidência (fala ou arquivo) | Correção sugerida | Severidade (alta/média/baixa) |
|---|---|---|---|---|---|---|
| 1 | A | `docs/PRD.md` / `docs/TRACKER.md` | PRD §4 (PRD-OBJ-02): "3 de 3 (Atlas, MaxDistribuição, Nova Cargo), com entrega até o fim de novembro" | `[09:45] Marcos`: "A Atlas quer pra fim de novembro." | Ajustar a redação para esclarecer que o prazo do final de novembro foi uma solicitação específica da Atlas Comercial, mantendo a meta de atendimento dos 3 clientes solicitantes. | Média |
| 2 | B | `docs/RFC.md` | RFC §1 (Metadados): "Autor: Thiago Duarte, consolidando a reunião técnica..." | Transcrição da reunião (`[09:00]`). Os participantes são Larissa, Marcos, Bruno, Diego e Sofia. | Remover o nome "Thiago Duarte" e atribuir a autoria ao time de engenharia / Larissa. | Baixa |
| 3 | D | `docs/FDD.md` | FDD §11 (Dependências e compatibilidade): "MySQL 8.0 (`docker-compose.yml`) \| Suporta colunas JSON..." | Lista de ARQUIVOS REAIS. O arquivo `docker-compose.yml` não existe no repositório nem está marcado como `(novo)`. | Remover a citação a `docker-compose.yml` ou marcá-lo expressamente como `(novo)` caso deva ser criado no projeto. | Baixa |
| 4 | G | `docs/FDD.md` | FDD §6 (FDD-CONTRATO-01) e FDD §7 (FDD-ERR-03): "statuses: array não vazio e sem repetição de OrderStatus, **exceto PENDING**." | `[09:33] Marcos`. Na reunião foi dito apenas que o filtro é uma lista de status desejados. A proibição do status `PENDING` foi adicionada sem marcação de proposta/decisão não discutida. | Marcar a proibição do filtro `PENDING` como "Proposta: não discutido" ou registrá-la como questão em aberto para alinhamento técnico. | Baixa |
| 5 | E | `docs/TRACKER.md` | Linha `FDD-ERR-03`: Aponta `[09:33] Marcos` para o código `WEBHOOK_INVALID_EVENT_FILTER` e a regra de exclusão do status `PENDING`. | `[09:33] Marcos`. Marcos comentou apenas sobre a regra de negócio de filtrar os status assinados ("só quero saber quando vira SHIPPED e DELIVERED"), sem citar o código de erro ou a trava ao status `PENDING`. | Alterar o tipo da fonte no Tracker para "Proposta (não discutida)" vinculada à validação de schemas, assim como foi feito nos demais erros derivados. | Baixa |

---

## Itens verificados sem problema

- **Arquitetura Outbox e Transacional:** ADR-001, RFC-PROP-01 e FDD-FLUXO-01 especificam corretamente a gravação em `webhook_outbox` dentro do mesmo `$transaction` de `OrderService.changeStatus` (`src/modules/orders/order.service.ts`), garantindo rollback atômico.
- **Worker e Polling:** ADR-002 e FDD-FLUXO-02 estão alinhados com a transcrição (`[09:09] Diego`, `[09:11] Larissa`), definindo o worker como processo separado (`src/worker.ts`), polling de 2s e instância única para preservar ordenação por pedido.
- **Política de Retry e DLQ:** ADR-003, RFC-PROP-04 e FDD-FLUXO-03/05 respeitam os 5 retries com backoff exponencial (1m/5m/30m/2h/12h), isolamento na tabela `webhook_dead_letter` e replay restrito à role `ADMIN` (`src/middlewares/auth.middleware.ts`) com auditoria.
- **Modelo de Segurança:** ADR-004 e FDD-FLUXO-06/CONTRATO-08 especificam HMAC-SHA256, secret única por endpoint, validação `https` obrigatória e rotação com grace period de 24h conforme `[09:20]–[09:23] Sofia`.
- **Garantias e Payload Snapshot:** ADR-005 e ADR-007 cobrem a semântica at-least-once com header `X-Event-Id` (`[09:25] Diego`) e o congelamento do payload JSON na inserção (`[09:52] Larissa`).
- **Gestão de Escopo Vazado:** Itens descartados/adiados na call (e-mail de alerta, dashboard visual, rate limiting, arquivamento de entregues, multi-worker, exactly-once) foram mantidos corretamente fora do escopo no PRD §5 e FDD §3.
- **Mapeamento de Arquivos Existentes:** Todos os arquivos de código citados sem a marca `(novo)` em FDD §10 foram checados e existem de fato na árvore do projeto (`src/app.ts`, `src/config/database.ts`, `src/config/env.ts`, `src/middlewares/error.middleware.ts`, `src/shared/logger/index.ts`, `tests/setup.ts`, etc.).

---

## Veredito

O pacote de documentação está em excelente estado de consistência técnica e alinhamento com a reunião, apresentando apenas pequenos deslizes de rastreabilidade, uma arquivo inexistente citado na infraestrutura e um detalhe de prazo/escopo a ajustar.

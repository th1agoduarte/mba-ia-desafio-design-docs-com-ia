<!-- gerado por tools/ia.py em 2026-11-15T13:32:59 | modelo: gemini/gemini-3.5-flash | prompt: prompts/06-revisao-critica.md | tokens entrada/saída: 54854/9025 -->

## Problemas encontrados

| # | Tipo (A-G) | Documento | Trecho | Evidência (fala ou arquivo) | Correção sugerida | Severidade (alta/média/baixa) |
|---|---|---|---|---|---|---|
| 1 | E | `docs/TRACKER.md` (e `docs/PRD.md` PRD-OBJ-02) | `PRD-OBJ-02 \| ... \| TRANSCRICAO \| [09:00] Marcos; [09:45] Marcos` | Em `[09:00] Marcos` ele diz "fim do trimestre", enquanto a data "fim de novembro" só é citada explicitamente em `[09:45] Marcos`. | Ajustar o parâmetro de citação no PRD-OBJ-02 e no `TRACKER.md` para citar `[09:45] Marcos` no que tange à data limite de novembro. | Baixa |
| 2 | E | `docs/TRACKER.md` | `PRD-DEC-07 \| docs/PRD.md \| Decisão \| Notificação como snapshot... \| TRANSCRICAO \| [09:52] Bruno` | A decisão sobre o snapshot é tomada por Larissa em `[09:52] Larissa` ("Eu prefiro renderizado já...") e confirmada por Diego (`[09:52] Diego`). Bruno apenas concorda ao final ("Beleza, snapshot. Decidido."). | Alterar o falante principal de origem da decisão no `TRACKER.md` para `[09:52] Larissa`. | Baixa |
| 3 | G | `docs/FDD.md` | `GET /api/v1/webhooks/:id/deliveries?limit=100` (FDD-CONTRATO-06) | O repositório utiliza o padrão de paginação `page`/`pageSize` (presente em `src/shared/http/response.ts` e no CONTRATO-02). O uso do parâmetro `limit` no CONTRATO-06 altera a convenção de paginação do projeto sem marcar como proposta não discutida. | Padronizar a query string do contrato para usar `pageSize` (e `page`) ou marcar explicitamente o uso de `limit` como "(proposta: não discutido)". | Baixa |

---

## Itens verificados sem problema

*   **A. Contradições de escopo e arquitetura:** Verificado que todas as decisões principais (Outbox no MySQL, polling de 2s em worker separado, retry com 5 retentativas e backoff 1m/5m/30m/2h/12h, DLQ com replay por ADMIN, HMAC-SHA256 com secret por endpoint, rotação com grace period de 24h, at-least-once com `X-Event-Id` e snapshot no insert) refletem com exatidão a fala dos participantes.
*   **B. Invenções não sinalizadas:** Todos os detalhes de implementação não debatidos na reunião (como comportamento de HTTP status 4xx/5xx no envio, truncamento de body de resposta nas entregas e validação da lista de status excluindo `PENDING`) foram corretamente identificados com a marcação `(proposta: não discutido)` ou inseridos na seção de Questões em Aberto (`RFC-Q-07` a `RFC-Q-11`).
*   **C. Escopo vazado:** Confirmado que e-mail de alerta, dashboard visual, rate limiting de saída, arquivamento de entregues, múltiplos workers, Redis e envio síncrono aparecem estritamente como fora de escopo ou itens futuros.
*   **D. Arquivos inexistentes:** Todos os caminhos sem a marca `(novo)` foram auditados contra a lista de ARQUIVOS REAIS (`src/modules/orders/order.service.ts`, `src/modules/orders/order.status.ts`, `src/shared/logger/index.ts`, `src/middlewares/auth.middleware.ts`, `src/shared/http/response.ts`, `tests/orders.test.ts`, etc.) e existem no repositório.
*   **F. Altura/Nível de abstração:** PRD contém apenas requisitos de negócio/produto, RFC mantém foco em arquitetura/alternativas, ADRs registram o racional das decisões e FDD detalha esquemas e contratos técnicos sem duplicação inadequada.

---

## Veredito

O pacote de documentação apresenta excelente qualidade técnico-arquitetural e rigorosa fidelidade à transcrição e ao código existente, contendo apenas imperfeições pontuais de rastreabilidade e padronização sem impacto crítico.

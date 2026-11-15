# ADR-003: Retry com backoff exponencial (1m/5m/30m/2h/12h) e DLQ em tabela separada

## Status

Aceito, com uma interpretação a confirmar na revisão do RFC ([RFC-Q-07](../RFC.md#6-questões-em-aberto))

- **Data:** reunião técnica de quinta-feira, 09:00 (registro em 2026-11-15)
- **Decisores:** Larissa, Diego, Bruno; Marcos aceitou a janela total; Sofia definiu a permissão do replay
- **Relacionados:** [ADR-002](ADR-002-worker-separado-com-polling.md), [ADR-005](ADR-005-at-least-once-com-x-event-id.md), [ADR-006](ADR-006-reuso-dos-padroes-do-projeto.md)

## Contexto

O endpoint do cliente pode estar fora do ar. Um cliente já ficou duas horas indisponível numa manutenção planejada ([09:16] Diego). Precisamos insistir o bastante para cobrir indisponibilidades reais, sem deixar eventos pendurados para sempre ([09:15] Diego), e manter os eventos que falharam de vez acessíveis para depuração e reprocessamento ([09:18] Diego).

## Decisão

- **Backoff exponencial, com teto de 5 tentativas.** Depois do teto, a falha é permanente e o evento vai para a DLQ ([09:15] Diego).
- **Intervalos: 1 min, 5 min, 30 min, 2 h e 12 h**, cerca de 15 h entre a primeira falha e a última tentativa ([09:17] Diego). Decidido em [09:17] Larissa. Marcos considerou a janela aceitável ([09:17] Marcos).
- **DLQ numa tabela separada `webhook_dead_letter`,** com o payload, o motivo da falha e o timestamp ([09:18] Diego). A leitura da outbox fica mais limpa, e o registro serve de evidência para debug e reprocessamento.
- **Replay manual por endpoint admin,** `POST /admin/webhooks/dead-letter/:id/replay` ([09:18] Diego; [09:35] Diego). O replay recoloca o evento na outbox como pendente.
- **O replay exige role `ADMIN`.** Reaproveita o `requireRole` de `src/middlewares/auth.middleware.ts` e registra em log quem fez o replay, para auditoria ([09:36] Sofia; [09:36] Larissa).

> **Interpretação a confirmar (RFC-Q-07).** "5 tentativas" com 5 intervalos só fecha a conta de "quase 15 horas entre primeira falha e última tentativa" (1+5+30+120+720 min = 14 h 36 min) se forem **5 retentativas depois da tentativa inicial** (6 envios no total). Com 5 envios no total, o intervalo de 12 h nunca seria usado e a janela cairia para 2 h 36 min. O FDD adota a leitura de 5 retentativas, e a confirmação fica com Larissa e Diego.

## Alternativas Consideradas

| ID | Alternativa | Por que foi descartada |
|---|---|---|
| ADR-003-ALT-01 | **Retry indefinido** com backoff ([09:15] Diego) | Evento fica "pendurado pra sempre" se o cliente sumiu |
| ADR-003-ALT-02 | **3 tentativas**, mais agressivo ([09:16] Bruno) | "3 é pouco": uma indisponibilidade pela manhã seria esgotada em ~30 minutos, e já houve manutenção planejada de 2 h ([09:16] Diego) |
| ADR-003-ALT-03 | **Marcar como "failed" na própria outbox**, sem tabela de DLQ ([09:17] Larissa) | Mistura eventos ativos e mortos na tabela lida a cada 2 s. A tabela separada deixa a leitura da outbox mais limpa e guarda a evidência ([09:18] Diego) |

## Consequências

**Positivas**
- Cobre indisponibilidades de até ~14 h 36 min sem intervenção ([09:17] Diego). A manutenção de 2 h citada fica bem dentro da janela ([09:16] Diego).
- Nenhum evento se perde: ou é entregue, ou fica na DLQ com o motivo e pode ser reenviado ([09:18] Diego).
- O replay só acontece com a role adequada e deixa rastro de auditoria ([09:36] Sofia).

**Negativas**
- Um evento pode chegar com até ~15 h de atraso. Para Marcos, se o cliente cai por 15 h, "ele já tá com problema sério dele" ([09:17] Marcos).
- O reprocessamento da DLQ é manual. Não há aviso automático ao cliente: e-mail ficou para a próxima fase ([09:37] Larissa).
- Durante o backoff de um evento, eventos posteriores do mesmo pedido podem ser entregues antes dele. Isso enfraquece a ordem por pedido do [ADR-002](ADR-002-worker-separado-com-polling.md) e está registrado como questão em aberto ([RFC-Q-08](../RFC.md#6-questões-em-aberto)).

**Trade-off:** aceitamos atraso longo no pior caso e reprocessamento manual, em troca de não perder eventos e não manter retentativas infinitas.

## Referências

- Transcrição: [09:14]–[09:19], [09:35]–[09:36]
- Código: `src/middlewares/auth.middleware.ts` (`requireRole`), `src/shared/logger/index.ts`

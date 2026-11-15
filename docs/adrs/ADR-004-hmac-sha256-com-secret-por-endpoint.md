# ADR-004: Autenticação dos webhooks com HMAC-SHA256, secret por endpoint e rotação com 24 h de convivência

## Status

Aceito

- **Data:** reunião técnica de quinta-feira, 09:00 (registro em 2026-11-15)
- **Decisores:** Sofia (Segurança), com Larissa, Bruno e Diego
- **Relacionados:** [ADR-005](ADR-005-at-least-once-com-x-event-id.md), [ADR-006](ADR-006-reuso-dos-padroes-do-projeto.md)

## Contexto

Os webhooks levam dados de pedidos para endpoints fora da nossa infraestrutura. O cliente precisa conseguir verificar duas coisas: que a requisição veio da plataforma, e que ninguém alterou o payload no caminho ([09:19] Sofia). O fluxo é só de saída: os clientes recebem e não enviam ([09:02] Marcos), o que simplifica o modelo ([09:03] Sofia). Já houve caso de um cliente vazar a secret em log da própria aplicação ([09:22] Diego).

## Decisão

- **Assinatura HMAC-SHA256 sobre o corpo da requisição,** enviada num header `X-Signature`. O cliente verifica a assinatura do lado dele ([09:20] Sofia). HMAC-SHA256 é o padrão de mercado, e todo cliente sério tem biblioteca para isso ([09:20] Sofia).
- **Uma secret única por endpoint de webhook,** nunca uma secret global da plataforma ([09:21] Sofia). A configuração do webhook guarda url, secret, customer_id e estado ativo ([09:21] Bruno; [09:21] Sofia).
- **A secret é gerada pela plataforma** e devolvida na criação do webhook ([09:31] Marcos).
- **Rotação pela API:**
  - o cliente pede uma nova secret por um endpoint;
  - a secret antiga continua válida por **24 h em paralelo**, para ele migrar os sistemas;
  - depois disso, a antiga deixa de valer ([09:21] Sofia).

  Decisão fechada em [09:22] Sofia.
- **TLS obrigatório:** a URL do webhook tem que ser `https`. Cadastro com `http` é recusado com erro de validação no schema Zod ([09:23] Sofia). Sofia classificou isso como validação, não como decisão arquitetural. Fica registrado aqui porque complementa o modelo de segurança.
- A revisão de segurança da Sofia, de **pelo menos 2 dias úteis antes do deploy**, cobre especialmente HMAC e geração de secret ([09:46] Sofia; [09:47] Larissa).

Como a assinatura chega no header durante a convivência de duas secrets ainda **não foi decidido** ([RFC-Q-09](../RFC.md#6-questões-em-aberto)). O FDD traz uma proposta marcada como tal.

## Alternativas Consideradas

| ID | Alternativa | Por que foi descartada |
|---|---|---|
| ADR-004-ALT-01 | **Secret global** da plataforma para todos os clientes ([09:21] Sofia) | "Se vaza uma, vaza tudo" ([09:21] Sofia) |
| ADR-004-ALT-02 | **Rotação sem período de convivência** (troca imediata). Não discutida na reunião: é o contraponto implícito da exigência de [09:21] Sofia | O cliente teria indisponibilidade de validação enquanto troca a secret nos sistemas dele. As 24 h existem "pra ele ter tempo de migrar" ([09:21] Sofia) |

## Consequências

**Positivas**
- Autenticidade e integridade verificáveis pelo cliente com bibliotecas padrão ([09:20] Sofia).
- O vazamento de uma secret afeta só um endpoint ([09:21] Sofia), e o cliente se recupera sozinho rotacionando a secret ([09:21] Sofia; [09:22] Diego).
- `https` obrigatório protege o payload em trânsito ([09:23] Sofia).

**Negativas**
- A plataforma precisa guardar a secret de forma recuperável, porque o HMAC exige a secret original para assinar (não dá para guardar só um hash). Como proteger essa secret em repouso fica para a revisão da Sofia ([RFC-Q-10](../RFC.md#6-questões-em-aberto)).
- Durante as 24 h de convivência existem duas secrets válidas por endpoint, o que complica a assinatura e o modelo de dados.
- A secret não pode aparecer em logs. O logger atual (`src/shared/logger/index.ts`) não tem `secret` na lista de `redact`, então ela precisará ser adicionada (ver FDD).

**Trade-off:** aceitamos guardar e gerenciar uma secret por endpoint, com rotação, em troca de limitar o raio de um vazamento e dar ao cliente autonomia para se recuperar.

## Referências

- Transcrição: [09:19]–[09:23], [09:31], [09:46]
- Código: `src/shared/logger/index.ts` (`redactPaths`), `src/middlewares/validate.middleware.ts` (validação Zod)

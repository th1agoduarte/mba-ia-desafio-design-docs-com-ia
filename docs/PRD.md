# PRD — Sistema de Webhooks de Notificação de Pedidos

| Campo | Valor |
|---|---|
| **Produto** | Order Management System (OMS) |
| **Responsável de produto** | Marcos (Product Manager) |
| **Responsável técnica** | Larissa (Tech Lead) |
| **Status** | Aprovado na reunião técnica; detalhamento em revisão |
| **Data** | 2026-11-15 |
| **Documentos** | [RFC](RFC.md) · [FDD](FDD.md) · [ADRs](adrs/README.md) · [Tracker](TRACKER.md) |

## 1. Resumo e contexto

Os clientes B2B do OMS passam a receber, **no próprio sistema e em menos de 10 segundos**, uma notificação (webhook) sempre que o status de um pedido deles muda. Com isso, deixam de consultar a API repetidamente para descobrir mudanças.

A feature atende um pedido formal de três clientes: **Atlas Comercial, MaxDistribuição e Nova Cargo** ([09:00] Marcos). Cada cliente:
- cadastra pela API os endereços que vão receber as notificações;
- escolhe quais status quer acompanhar;
- valida a autenticidade de cada mensagem;
- consulta o histórico de entregas.

Hoje o OMS não tem nenhum mecanismo de notificação externa.

## 2. Problema e motivação

- **Integração lenta e cara:** os clientes ficam "batendo no GET /orders de tempos em tempos" para saber se algo mudou ([09:00] Marcos).
- **Risco comercial:** a Atlas sinalizou que pode migrar para um concorrente se a solução não for entregue até o fim do trimestre ([09:00] Marcos). Depois, a data pedida passou a ser o fim de novembro ([09:45] Marcos).
- **Expectativa clara de tempo:** para os clientes, "tempo real" é qualquer coisa abaixo de 10 segundos. O que importa é não precisar atualizar manualmente ([09:02] Marcos).

## 3. Público-alvo e cenários de uso

**Público**
- **Clientes B2B integradores**, os desenvolvedores dos sistemas da Atlas Comercial, MaxDistribuição e Nova Cargo. Eles recebem os webhooks e cadastram os endpoints pela nossa API ([09:00], [09:32] Marcos).
- **Usuários do OMS que representam os clientes.** O cadastro é feito com o login do nosso sistema ([09:32] Marcos).
- **Administradores da plataforma.** Reprocessam notificações que falharam de vez ([09:36] Sofia).

**Cenários**

| ID | Cenário | Origem |
|---|---|---|
| PRD-CEN-01 | A Atlas cadastra um endpoint para saber só quando o pedido vira **SHIPPED** e **DELIVERED**, e é avisada no momento em que o pedido é despachado | [09:33] Marcos |
| PRD-CEN-02 | O endpoint de um cliente fica 2 h fora do ar numa manutenção planejada. Quando volta, recebe as notificações pendentes sem ninguém intervir | [09:16] Diego |
| PRD-CEN-03 | O cliente recebe a mesma notificação duas vezes e descarta a repetida pelo identificador do evento | [09:24] Diego; [09:25] Diego |
| PRD-CEN-04 | O cliente vazou a secret num log. Ele pede uma nova e tem 24 h para trocar nos sistemas dele | [09:21] Sofia; [09:22] Diego |
| PRD-CEN-05 | Um cliente com vários endpoints cadastrados identifica qual cadastro originou cada notificação | [09:44] Sofia |
| PRD-CEN-06 | O cliente depura a integração consultando as últimas entregas, com sucesso/falha, conteúdo, resposta e tempo | [09:34] Marcos |
| PRD-CEN-07 | Um evento esgotou as tentativas. Depois que o cliente corrige o endpoint, um admin reenvia o evento | [09:18] Diego |

## 4. Objetivos e métricas de sucesso

| ID | Objetivo | Métrica | Meta | Origem |
|---|---|---|---|---|
| PRD-OBJ-01 | Notificar em "tempo real" | Tempo entre a mudança de status e a primeira tentativa de entrega | **< 10 s**. O desenho prevê no máximo ~2 s de espera em operação normal | [09:02] Marcos; [09:10] Larissa |
| PRD-OBJ-02 | Atender os clientes que pediram | Clientes solicitantes com webhook ativo | **3 de 3** (Atlas, MaxDistribuição, Nova Cargo). A Atlas pediu a entrega até o fim de novembro | [09:00] Marcos; [09:45] Marcos |
| PRD-OBJ-03 | Não perder notificações | Eventos confirmados que não foram entregues nem estão disponíveis para reenvio | **0**, cobrindo indisponibilidades do cliente de até ~15 h | [09:15] Diego; [09:17] Diego |
| PRD-OBJ-04 | Entregar no prazo | Sprints até o deploy, incluindo a revisão de segurança | **3 sprints** | [09:46] Larissa; [09:47] Larissa |
| PRD-OBJ-05 | Reduzir o polling dos clientes em `GET /orders` | Volume de chamadas de polling dos 3 clientes | Sem meta numérica definida na reunião. A linha de base deve ser medida antes do lançamento | [09:00] Marcos |

## 5. Escopo

**Incluso**

| ID | Item | Origem |
|---|---|---|
| PRD-ESC-01 | Notificações de **saída** (plataforma → cliente) a cada mudança de status de pedido | [09:02] Marcos; [09:03] Sofia |
| PRD-ESC-02 | Gestão de endpoints de webhook pela API: cadastrar, editar, remover, listar e escolher os status | [09:31] Marcos; [09:33] Bruno |
| PRD-ESC-03 | Segurança: assinatura de cada mensagem, secret por endpoint, rotação de secret e `https` obrigatório | [09:22] Sofia; [09:23] Sofia |
| PRD-ESC-04 | Retentativas automáticas e guarda de eventos que falharam de vez, com reenvio por admin | [09:17] Larissa; [09:19] Larissa |
| PRD-ESC-05 | Histórico de entregas por endpoint | [09:34] Marcos |

**Fora de escopo** (descartado ou adiado na reunião)

| ID | Item | Situação | Origem |
|---|---|---|---|
| PRD-OUT-01 | **Aviso por e-mail** quando o webhook do cliente falha repetidamente | Adiado para a próxima fase, depois de medir o impacto | [09:37] Larissa |
| PRD-OUT-02 | **Dashboard ou painel visual** para o cliente ver os webhooks | Descartado nesta fase. É projeto separado do time de frontend; agora só endpoints | [09:40] Larissa |
| PRD-OUT-03 | **Rate limiting** dos envios para o cliente | Fora do escopo. Vamos observar e decidir depois | [09:39] Diego; [09:39] Larissa |
| PRD-OUT-04 | **Webhooks de entrada** (cliente enviando para a plataforma) | Fora: os clientes só querem receber | [09:02] Marcos |
| PRD-OUT-05 | **Arquivamento** das notificações já entregues | Fora do escopo desta feature | [09:08] Diego |
| PRD-OUT-06 | **Garantia de ordem global** e escala para vários processos de entrega | Adiado ("problema do futuro"). Os clientes não pediram ordem global | [09:13] Diego; [09:14] Marcos |
| PRD-OUT-07 | **Entrega exatamente uma vez** (exactly-once) | Descartado: complexidade excessiva | [09:25] Diego |
| PRD-OUT-08 | **Itens do pedido** dentro da notificação | Descartado para manter o payload enxuto. Quem precisa consulta o pedido | [09:43] Diego |
| PRD-OUT-09 | **Permissões mais restritas** para gerenciar webhooks | Adiado: por enquanto, qualquer usuário autenticado | [09:37] Sofia |

## 6. Requisitos funcionais

| ID | Requisito | Origem |
|---|---|---|
| PRD-FR-01 | O cliente cadastra um endpoint de webhook informando a **URL** e a **lista de status** que quer receber. A **secret é gerada pela plataforma** e devolvida na criação | [09:31] Marcos |
| PRD-FR-02 | O cadastro é feito pela API do OMS, com o login do nosso sistema. O **cliente (customer) é informado explicitamente** na requisição, e não deduzido do login | [09:32] Marcos; [09:32] Larissa |
| PRD-FR-03 | O cliente **edita** um endpoint cadastrado | [09:33] Bruno |
| PRD-FR-04 | O cliente **remove** um endpoint cadastrado | [09:33] Bruno |
| PRD-FR-05 | O cliente **lista** os endpoints cadastrados de um customer | [09:33] Bruno |
| PRD-FR-06 | Cada endpoint recebe **apenas os status escolhidos**. Se nenhum endpoint do cliente quer aquele status, nada é enviado | [09:33] Marcos; [09:34] Bruno |
| PRD-FR-07 | A cada **mudança de status** de um pedido, os endpoints interessados recebem uma notificação | [09:00] Marcos; [09:40] Bruno |
| PRD-FR-08 | A notificação traz: identificador do evento, tipo, data e hora, pedido (id e número), status anterior e novo, cliente e valor total. **Não** traz os itens | [09:43] Diego |
| PRD-FR-09 | Cada notificação é **assinada**, e o cliente consegue verificar a origem e a integridade | [09:19] Sofia; [09:20] Sofia |
| PRD-FR-10 | Cada notificação traz um **identificador único do evento** para o cliente descartar repetições, e um **identificador do endpoint** de origem | [09:25] Diego; [09:44] Sofia |
| PRD-FR-11 | O cliente **pede uma nova secret** pela API. A anterior continua válida por **24 h** | [09:21] Sofia |
| PRD-FR-12 | Se o endpoint do cliente falha, a plataforma **tenta de novo automaticamente** em intervalos crescentes. Esgotadas as tentativas, o evento fica guardado como falha permanente | [09:15] Diego; [09:18] Diego |
| PRD-FR-13 | Um **administrador** reenvia manualmente um evento que falhou de vez. O sistema registra quem fez o reenvio | [09:18] Diego; [09:36] Sofia |
| PRD-FR-14 | O cliente consulta o **histórico das últimas 100 entregas** de um endpoint, com sucesso/falha, conteúdo enviado, resposta recebida e tempo de resposta | [09:34] Marcos |

## 7. Requisitos não funcionais

| ID | Requisito | Origem |
|---|---|---|
| PRD-NFR-01 | **Latência:** primeira tentativa de entrega em menos de 10 s após a mudança de status | [09:02] Marcos |
| PRD-NFR-02 | **Consistência:** nenhuma mudança de status sem notificação, nenhuma notificação de mudança que não aconteceu | [09:06] Diego; [09:40] Bruno |
| PRD-NFR-03 | **Isolamento:** um cliente lento ou fora do ar não atrasa nem impede mudanças de status de outros pedidos | [09:04] Bruno |
| PRD-NFR-04 | **Garantia de entrega at-least-once:** o cliente pode receber a mesma notificação mais de uma vez e deve estar preparado | [09:24] Diego |
| PRD-NFR-05 | **Ordem:** garantida apenas por pedido, não globalmente | [09:13] Larissa |
| PRD-NFR-06 | **Transporte seguro:** só endereços `https`. Endereço `http` é recusado no cadastro | [09:23] Sofia |
| PRD-NFR-07 | **Isolamento de segredo:** uma secret por endpoint, nunca uma secret global | [09:21] Sofia |
| PRD-NFR-08 | **Tamanho:** notificações acima de 64 KB não são enviadas e são tratadas como erro, sem truncar | [09:23] Sofia; [09:24] Larissa |
| PRD-NFR-09 | **Tempo de resposta do cliente:** o cliente tem até 10 s para responder; depois disso a tentativa conta como falha | [09:42] Diego |
| PRD-NFR-10 | **Janela de retentativa:** cerca de 15 h entre a primeira falha e a última tentativa | [09:17] Diego; [09:17] Marcos |
| PRD-NFR-11 | **Controle de acesso:** gerenciar endpoints exige usuário autenticado; reenviar eventos que falharam exige papel ADMIN, com auditoria | [09:36] Larissa; [09:37] Sofia |
| PRD-NFR-12 | **Operação:** nenhuma infraestrutura nova, usando o mesmo banco e a mesma stack | [09:07] Diego; [09:11] Diego |

## 8. Decisões e trade-offs principais

| ID | Decisão | Trade-off aceito | ADR |
|---|---|---|---|
| PRD-DEC-01 | Registrar o evento no banco atual, junto da mudança de status, e enviar depois | Entrega com alguns segundos de espera, em troca de consistência e de nenhuma infraestrutura nova | [ADR-001](adrs/ADR-001-outbox-no-mysql.md) |
| PRD-DEC-02 | Processo de envio separado da API, verificando a cada 2 s | Até ~2 s de espera, em troca de simplicidade e de não depender dos deploys da API | [ADR-002](adrs/ADR-002-worker-separado-com-polling.md) |
| PRD-DEC-03 | 5 retentativas em ~15 h e depois guarda para reenvio manual | Atraso longo no pior caso e reenvio manual, em troca de não perder eventos | [ADR-003](adrs/ADR-003-retry-com-backoff-e-dlq.md) |
| PRD-DEC-04 | Assinatura HMAC-SHA256 com secret por endpoint e rotação com 24 h | Mais segredos para gerenciar, em troca de limitar o impacto de um vazamento | [ADR-004](adrs/ADR-004-hmac-sha256-com-secret-por-endpoint.md) |
| PRD-DEC-05 | Entrega "pelo menos uma vez", com id para o cliente descartar duplicatas | O cliente precisa deduplicar, em troca de um modelo simples e padrão de mercado | [ADR-005](adrs/ADR-005-at-least-once-com-x-event-id.md) |
| PRD-DEC-06 | Construir sobre os padrões que o OMS já tem | Herda as limitações atuais, em troca de velocidade e consistência | [ADR-006](adrs/ADR-006-reuso-dos-padroes-do-projeto.md) |
| PRD-DEC-07 | A notificação descreve o pedido no momento da mudança | Registros um pouco maiores, em troca de notificações imutáveis | [ADR-007](adrs/ADR-007-payload-snapshot-na-insercao.md) |

## 9. Dependências

| ID | Dependência | Origem |
|---|---|---|
| PRD-DEP-01 | Alteração no fluxo de mudança de status do módulo de pedidos (time de Pedidos) | [09:40] Bruno |
| PRD-DEP-02 | Banco MySQL e stack atuais, sem infraestrutura nova | [09:07] Diego; [09:11] Diego |
| PRD-DEP-03 | Revisão de segurança da Sofia, com pelo menos 2 dias úteis antes do deploy | [09:46] Sofia |
| PRD-DEP-04 | Portal de desenvolvedor: Marcos documenta a integração e destaca a deduplicação | [09:26] Marcos; [09:40] Marcos |
| PRD-DEP-05 | Do lado do cliente: endpoint `https`, verificação da assinatura e deduplicação pelo id do evento | [09:20] Sofia; [09:25] Diego |
| PRD-DEP-06 | Usuários do OMS que representam cada cliente, para fazer o cadastro pela API | [09:32] Marcos |
| PRD-DEP-07 | Operação de um processo adicional (o de envio), além da API | [09:11] Diego; [09:11] Larissa |

## 10. Riscos e mitigação

Probabilidade e impacto são a avaliação do autor, com base nos fatos citados.

| ID | Risco | Probabilidade | Impacto | Mitigação | Origem |
|---|---|---|---|---|---|
| PRD-RISK-01 | Atraso faz a Atlas migrar para o concorrente | Média | Alto | Escopo enxuto (e-mail, dashboard e rate limiting fora), estimativa de 3 sprints e prazo confirmado com o cliente pelo Marcos | [09:00] Marcos; [09:46] Larissa; [09:47] Marcos |
| PRD-RISK-02 | O cliente ignora o id do evento e processa notificações duplicadas | Média | Médio | Documentação destacada no portal de desenvolvedor e id único em toda notificação | [09:25] Sofia; [09:26] Marcos |
| PRD-RISK-03 | Vazamento da secret de um cliente | Média (já aconteceu) | Alto | Secret por endpoint, para que o vazamento não afete outros, e rotação pelo próprio cliente com 24 h de convivência | [09:21] Sofia; [09:22] Diego |
| PRD-RISK-04 | A revisão de segurança é espremida pelo prazo | Média | Alto | 2 dias úteis reservados dentro das 3 sprints, no fim | [09:46] Sofia; [09:47] Larissa |
| PRD-RISK-05 | O webhook de um cliente quebra e ninguém percebe (sem aviso por e-mail) | Média | Médio | Histórico de entregas consultável e guarda dos eventos que falharam. Medir esses casos para decidir o e-mail da próxima fase | [09:34] Marcos; [09:37] Larissa |
| PRD-RISK-06 | Muitas notificações em sequência sobrecarregam o cliente | Baixa | Médio | Acompanhar o volume por cliente e implementar limite se virar problema | [09:38] Diego; [09:39] Larissa |

## 11. Critérios de aceitação

| ID | Critério (visão do cliente) | Origem |
|---|---|---|
| PRD-CA-01 | Consigo cadastrar um endpoint `https` com os status que me interessam e recebo a secret na resposta | [09:31] Marcos; [09:23] Sofia |
| PRD-CA-02 | Um cadastro com endereço `http` é recusado com erro de validação | [09:23] Sofia |
| PRD-CA-03 | Quando um pedido meu muda para um status que assinei, recebo a notificação em menos de 10 s | [09:02] Marcos |
| PRD-CA-04 | Mudanças para status que não assinei não geram notificação | [09:34] Bruno |
| PRD-CA-05 | Consigo validar a assinatura com a minha secret e identificar o evento e o endpoint de origem | [09:20] Sofia; [09:25] Diego; [09:44] Sofia |
| PRD-CA-06 | Se meu endpoint ficar fora do ar por até ~15 h, recebo as notificações quando ele voltar | [09:17] Diego |
| PRD-CA-07 | Um evento que esgotou as tentativas pode ser reenviado por um administrador. Um usuário sem papel ADMIN não consegue | [09:18] Diego; [09:36] Larissa |
| PRD-CA-08 | Ao pedir uma nova secret, a antiga continua funcionando por 24 h | [09:21] Sofia |
| PRD-CA-09 | Consigo ver as últimas 100 entregas de um endpoint, com resultado, conteúdo, resposta e tempo | [09:34] Marcos |
| PRD-CA-10 | Consigo editar, remover e listar meus endpoints | [09:33] Bruno |

O detalhe técnico de cada critério está nos critérios de aceite do [FDD §12](FDD.md#12-critérios-de-aceite-técnicos).

## 12. Estratégia de testes e validação

| ID | Atividade | Origem |
|---|---|---|
| PRD-TST-01 | Revisão do design com Bruno e Diego antes de começar a codar | [09:50] Larissa |
| PRD-TST-02 | Testes automatizados de API e de integração para cada critério de aceitação, na suíte que o projeto já tem | `tests/orders.test.ts` |
| PRD-TST-03 | Teste ponta a ponta da integração com a mudança de status de pedidos | [09:46] Larissa |
| PRD-TST-04 | Teste de indisponibilidade do cliente, simulando um endpoint fora do ar por horas e conferindo as retentativas e a guarda do evento | [09:16] Diego; [09:17] Diego |
| PRD-TST-05 | Revisão de segurança da Sofia sobre assinatura e geração de secret, com 2 dias úteis antes do deploy | [09:46] Sofia |
| PRD-TST-06 | Após o lançamento, acompanhar a latência (meta < 10 s), a taxa de falhas e o volume de envios por cliente, como insumo para as decisões adiadas | [09:02] Marcos; [09:37] Larissa; [09:39] Diego |

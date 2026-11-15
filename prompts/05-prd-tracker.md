Papel: PM consolidando a feature para negócio e, em seguida, auditor montando a rastreabilidade. Em português.

Parte 1, docs/PRD.md. Seções: Resumo e contexto, Problema e motivação, Público-alvo e cenários de uso, Objetivos e métricas de sucesso (pelo menos 1 com meta numérica vinda da reunião), Escopo (incluso / fora de escopo, com pelo menos os itens descartados ou adiados na reunião), Requisitos funcionais (≥ 8, todos ditos na reunião), Requisitos não funcionais, Decisões e trade-offs principais (resumo de uma linha com link para o ADR, sem repetir o ADR), Dependências, Riscos e mitigação (probabilidade, impacto e mitigação, riscos de NEGÓCIO), Critérios de aceitação (visão do cliente), Estratégia de testes e validação.
- Nível de produto: nada de colunas, classes ou códigos de erro; para isso, link para o FDD.
- IDs: PRD-OBJ-0X, PRD-ESC-0X, PRD-OUT-0X, PRD-FR-0X, PRD-NFR-0X, PRD-DEC-0X, PRD-DEP-0X, PRD-RISK-0X, PRD-CA-0X, PRD-TST-0X, PRD-CEN-0X.

Parte 2, docs/TRACKER.md. Varra os 4 documentos e os ADRs e crie uma linha para CADA ID encontrado:
| ID | Documento | Tipo | Conteúdo (resumo) | Fonte | Localização |
- Fonte = TRANSCRICAO ou CODIGO. Escolha a fonte primária. Se o item tem as duas, prefira a transcrição e cite o arquivo no resumo.
- Localização: para TRANSCRICAO, `[hh:mm] Nome` (vários separados por `;`), conferidos na transcrição; para CODIGO, o caminho real do arquivo.
- Se você não consegue preencher a Localização de um item, NÃO invente: o item deve ser removido do documento de origem. Liste esses casos ao final.

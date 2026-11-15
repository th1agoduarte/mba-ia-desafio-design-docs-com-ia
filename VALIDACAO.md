# Validação dos critérios de aceite: passo a passo

Roteiro para conferir, do zero, cada critério do [enunciado](DESAFIO.md). Rode os comandos na raiz do repositório. Os passos 1 a 8 não usam LLM nem chave de API: basta `python3` e `git`, com o remote `upstream` apontando para o repositório base. Os passos marcados "leitura" pedem conferência humana de conteúdo, que regex não substitui.

## 0. Preparação

| # | Comando | Esperado |
|---|---|---|
| 0.1 | `git remote -v` | `upstream` = `devfullcycle/mba-ia-desafio-design-docs-com-ia` (se faltar: `git remote add upstream https://github.com/devfullcycle/mba-ia-desafio-design-docs-com-ia.git && git fetch upstream`) |
| 0.2 | `make check` | `118/118 verificações ok` e código de saída 0 |

## 1. Estrutura obrigatória e arquivos protegidos

| # | Comando | Esperado |
|---|---|---|
| 1.1 | `make test-one T=Estrutura` | `docs/PRD.md`, `RFC.md`, `FDD.md`, `TRACKER.md`, `README.md` e `TRANSCRICAO.md` existem |
| 1.2 | `git diff --stat upstream/main -- src prisma tests TRANSCRICAO.md package.json package-lock.json .env.example docker-compose.yml tsconfig.json tsconfig.build.json vitest.config.ts .eslintrc.json .prettierrc .prettierignore .gitignore` | Saída vazia: código, configurações e transcrição intocados |
| 1.3 | `git diff --stat upstream/main` | Só arquivos novos ou documentais: `README.md`, `DESAFIO.md`, `VALIDACAO.md`, `CLAUDE.md`, `Makefile`, `docs/`, `prompts/`, `tools/` e `gateway/` |

## 2. PRD (`docs/PRD.md`)

| # | Verificação | Esperado |
|---|---|---|
| 2.1 | `make test-one T=PRD` | 12 seções obrigatórias; ≥ 8 RFs com origem (14); objetivo com meta numérica; "Fora de escopo" com ≥ 2 itens da reunião (9); ≥ 2 riscos com probabilidade, impacto e mitigação (6) |
| 2.2 | Leitura: PRD §5, "Fora de escopo" | E-mail ([09:37] Larissa), dashboard ([09:40] Larissa) e rate limiting ([09:39] Larissa) aparecem como **fora** e não aparecem em nenhum RF |
| 2.3 | Leitura: PRD §4 | PRD-OBJ-01 com meta `< 10 s` ([09:02] Marcos) e PRD-OBJ-02 com `3 de 3` clientes |

## 3. RFC (`docs/RFC.md`)

| # | Verificação | Esperado |
|---|---|---|
| 3.1 | `make test-one T=RFC` | 8 seções; metadados com autor, status, data e os 5 participantes como revisores; ≥ 2 alternativas com trade-off e origem (6); ≥ 2 questões em aberto da reunião (6 + 5 lacunas identificadas); links para ≥ 2 ADRs existentes (7); ≤ 2.200 palavras |
| 3.2 | Leitura: RFC §4 × FDD | O RFC não tem colunas de tabela, payloads completos nem códigos de erro: esse detalhe só aparece no FDD |

## 4. FDD (`docs/FDD.md`)

| # | Verificação | Esperado |
|---|---|---|
| 4.1 | `make test-one T=FDD` | 12 seções; fluxos com outbox, worker, retry e DLQ; ≥ 4 endpoints com request, response e status codes (7, mais o contrato de saída); matriz só com `WEBHOOK_*` (12); "Integração com o sistema existente" com ≥ 4 arquivos reais (15+); observabilidade com métricas, logs e tracing |
| 4.2 | `grep -n "src/modules/orders/order.service.ts" docs/FDD.md` | A seção 10 (FDD-INT-01) explica a mudança em `changeStatus`, com as linhas citadas conferíveis no arquivo |
| 4.3 | `sed -n 126,179p src/modules/orders/order.service.ts` | `changeStatus` está nas linhas 126–179 e `orderStatusHistory.create` na 159, como o FDD afirma |

## 5. ADRs (`docs/adrs/`)

| # | Verificação | Esperado |
|---|---|---|
| 5.1 | `make test-one T=ADRs` | 7 arquivos `ADR-NNN-kebab-case.md` (pasta com 8 arquivos contando o README); cada um com Status, Contexto, Decisão, Alternativas Consideradas e Consequências (positivas, negativas e trade-off); cobertura 6/6 das decisões principais; ≥ 1 ADR com arquivo real |
| 5.2 | Leitura: `docs/adrs/ADR-006-reuso-dos-padroes-do-projeto.md` | Tabela com `AppError`, `InsufficientStockError`, `requireRole`, `errorMiddleware`, Pino e os caminhos reais |

## 6. Tracker (`docs/TRACKER.md`)

| # | Verificação | Esperado |
|---|---|---|
| 6.1 | `make test-one T=Tracker` | Cabeçalho exato; 229 linhas com 6 colunas; 100% dos IDs dos documentos com linha (mínimo exigido: 80%); 91% com Fonte TRANSCRICAO válida (mínimo: 70%); 20 linhas CODIGO com caminho real (mínimo: 5) |
| 6.2 | Leitura, por amostragem: escolha 5 linhas e procure a fala com `grep -n "^\[09:17\] Diego" TRANSCRICAO.md` | A fala sustenta o conteúdo resumido |

## 7. README

| # | Verificação | Esperado |
|---|---|---|
| 7.1 | `make test-one T=README` | 6 seções; ≥ 1 ferramenta de IA; ≥ 2 prompts em blocos de código (3); ≥ 2 iterações descritas (5) |
| 7.2 | Leitura: README, "Iterações e ajustes" × `docs/evidencias/ia/` | Os erros descritos (caminhos inventados, Prisma contraditório, falsos positivos) estão nas saídas brutas `01-inventario-v1.md`, `revisao-1.md` e `revisao-2.md` |

## 8. Consistência geral

| # | Verificação | Esperado |
|---|---|---|
| 8.1 | `make test-one T=Consistência` | Toda citação `[hh:mm] Nome` em PRD, RFC, FDD, tracker, ADRs e README existe na transcrição; nenhum caminho de código citado é inexistente, exceto os 12 arquivos declarados novos em "Arquivos novos" do FDD, todos em `src/modules/webhooks/`, `src/worker.ts` ou `tests/webhooks.test.ts` |
| 8.2 | Leitura: `docs/evidencias/ia/revisao-2.md` | Revisão independente (Gemini 3.5 Flash) sem contradição, invenção, escopo vazado nem arquivo inexistente; só 3 achados de severidade baixa, tratados no README |

## 9. Prova negativa (o verificador detecta erros de verdade)

```bash
cp docs/TRACKER.md docs/FDD.md /tmp/ \
 && sed -i 's/| TRANSCRICAO | \[09:34\] Marcos |$/| TRANSCRICAO | [09:34] Sofia |/' docs/TRACKER.md \
 && sed -i 's#`src/config/database.ts` |#`src/config/prisma-client.ts` |#' docs/FDD.md \
 && make check; cp /tmp/TRACKER.md /tmp/FDD.md docs/ && make check
```

Esperado na primeira execução: falha (exit 1) com `[09:34] Sofia` (falante errado no minuto) e `src/config/prisma-client.ts` (arquivo inexistente). Na segunda, depois de restaurar: `118/118`.

## 10. Etapas de IA (opcional, consome tokens)

| # | Comando | Esperado |
|---|---|---|
| 10.1 | `make setup && make smoke` | `✓ gemini/gemini-3.5-flash-lite respondeu: 'ok'` |
| 10.2 | `make revisar RODADA=teste` | Gera `docs/evidencias/ia/revisao-teste.md` com o cabeçalho de modelo, prompt e tokens |
| 10.3 | `make gateway-test` | `✓ gateway -> Gemini: ok` (requer Docker) |
| 10.4 | `make smoke PROVIDER=openai` (ou `anthropic`, `aws`) | Mesma etapa em outro provider, com a chave correspondente em `tools/.env` |

## 11. Entregável

| # | Verificação | Esperado |
|---|---|---|
| 11.1 | Repositório no GitHub | Público, fork de `devfullcycle/mba-ia-desafio-design-docs-com-ia`: <https://github.com/th1agoduarte/mba-ia-desafio-design-docs-com-ia> |
| 11.2 | `docs/evidencias/validacao-final.txt` | Saída do `make check` no commit entregue, com `exit=0` |

# Da Reunião ao Documento: Design Docs do Sistema de Webhooks

Pacote de design docs (PRD, RFC, FDD, 7 ADRs e tracker de rastreabilidade) do **Sistema de Webhooks de Notificação de Pedidos** do OMS. O pacote foi produzido com IA a partir da [transcrição da reunião técnica](TRANSCRICAO.md) e do código do repositório. O enunciado original está em [`DESAFIO.md`](DESAFIO.md).

## Sobre o desafio

Uma empresa que opera um Order Management System (Node.js, TypeScript, Express, Prisma e MySQL) decidiu, numa reunião de ~55 minutos, construir webhooks de saída para avisar clientes B2B quando o status de um pedido muda. Participaram tech lead, PM, dois engenheiros e segurança. Nada foi registrado além da transcrição.

A tarefa é transformar essa conversa em documentação acionável, de modo que o time consiga começar a implementar. São cinco documentos, cada um numa altura diferente:
- **PRD:** o porquê e o quê;
- **RFC:** a proposta, as alternativas e o que está em aberto;
- **ADRs:** cada decisão isolada;
- **FDD:** como construir;
- **tracker:** de onde veio cada item.

A restrição central é que **nada pode ser inventado**. Tudo precisa ser rastreável a uma fala `[hh:mm] Nome` ou a um arquivo real do código. Saber o que **não** entra (e-mail, dashboard, rate limiting, arquivamento...) pesa tanto quanto saber o que entra. O código da aplicação não pode ser alterado.

## Ferramentas de IA utilizadas

| Ferramenta | Papel |
|---|---|
| **Claude Code** (Claude Opus 5.5) | Agente principal. Leu o código e a transcrição, cruzou as duas fontes, redigiu ADRs, RFC, FDD, PRD e tracker, e escreveu as ferramentas de verificação. Trabalhou guiado pelos prompts de [`prompts/`](prompts) |
| **Google Gemini 3.5 Flash-Lite**, via [`tools/ia.py`](tools/ia.py) | Extração independente: montou o inventário classificado da transcrição (decisões, requisitos, descartes, adiamentos, ambiguidades), usado como segunda opinião contra a leitura do agente principal |
| **Google Gemini 3.5 Flash**, via [`tools/ia.py`](tools/ia.py) | Revisor crítico independente (papel de juiz). Procurou contradições, invenções, escopo vazado, arquivos inexistentes e conteúdo na altura errada em todo o pacote. Usar um modelo **de outro fornecedor** evita que o autor revise o próprio texto com o mesmo viés |
| **LiteLLM** (SDK e gateway Docker opcional) | Troca de provider sem mudar código: `PROVIDER=google\|openai\|anthropic\|aws\|gateway` |

## Workflow adotado

A ordem seguiu a sugestão do enunciado, com duas etapas extras de controle: um inventário no início e uma verificação dupla no fim.

```
TRANSCRICAO.md ──► 1. Inventário (Gemini, prompt 01) ──► revisão humana/agente ──┐
código (src/, prisma/, tests/) ──► 2. Mapa do código (Claude Code lendo arquivos) ─┤
                                                                                    ▼
                         3. ADRs (prompt 02) ─► 4. RFC (03) ─► 5. FDD (04) ─► 6. PRD + Tracker (05)
                                                                                    │
            ┌───────────────────────────────────────────────────────────────────────┘
            ▼
 7. Verificador determinístico (tools/check_docs.py)  ◄──┐   corrige
 8. Revisão crítica independente (Gemini, prompt 06)  ───┘   e repete
            ▼
 9. README do processo  ─► 10. checklist final (make check) ─► push
```

1. **Inventário antes de escrever.** Um LLM diferente do redator extraiu da transcrição tudo o que foi decidido, pedido, descartado, adiado ou deixado em aberto, com timestamp e trecho literal. O resultado ([`01-inventario.md`](docs/evidencias/ia/01-inventario.md)) foi conferido linha a linha contra a transcrição. Os erros do inventário viraram a iteração 1.
2. **Mapa do código.** O Claude Code leu os arquivos que a reunião cita e os que ela implica:
   - `order.service.ts`, `order.status.ts`;
   - erros, middlewares e logger;
   - `env.ts`, `database.ts`, `server.ts`, `app.ts`;
   - `schema.prisma`, `tests/setup.ts`.

   Essa leitura mudou o desenho em vários pontos (iteração 3).
3. **Documentos na ordem do enunciado:** ADRs → RFC → FDD → PRD → Tracker. Cada documento tem um prompt próprio que define a sua **altura**: o que entra e o que é proibido ali. Por exemplo, o RFC não pode ter colunas de tabela, e o PRD não pode ter classes nem códigos de erro.
4. **IDs em tudo.** Cada item identificável recebeu um ID (`PRD-FR-03`, `RFC-Q-07`, `FDD-ERR-05`, `ADR-003-ALT-02`...). Com isso, a cobertura do tracker fica mensurável: 229 de 229 IDs têm linha.
5. **Verificação em duas camadas:**
   - um verificador **determinístico** confere os critérios de aceite e faz checagens anti-alucinação: toda citação `[hh:mm] Nome` em qualquer documento precisa existir na transcrição, e todo caminho de código citado precisa existir ou estar declarado como novo;
   - um **LLM revisor** procura o que regex não pega: contradição semântica, invenção e altura errada.

   Cada achado foi avaliado criticamente antes de ser aceito ou rejeitado (veja abaixo).
6. **Convenções contra invenção.**
   - `(novo)` marca arquivo que ainda não existe.
   - **"Proposta: não discutido"** marca uma escolha de implementação que a reunião não fez. O FDD precisa ser acionável, então essas escolhas existem, mas ficam visíveis e não se passam por decisão.
   - Ambiguidades da própria reunião viraram questões em aberto no RFC (RFC-Q-07 a Q-11), em vez de serem resolvidas em silêncio.

## Prompts customizados

Os prompts completos estão em [`prompts/`](prompts):
- `01-inventario` (v1 e v2);
- `02-adrs`;
- `03-rfc`;
- `04-fdd`;
- `05-prd-tracker`;
- `06-revisao-critica`.

Abaixo, os três mais relevantes.

**Prompt 1: inventário dirigido da transcrição** ([`prompts/01-inventario.md`](prompts/01-inventario.md), v2). Trecho com as regras que a v1 não tinha e que corrigiram os erros dela:

```text
Você é analista de requisitos e está montando o inventário rastreável de uma reunião técnica. [...]
Uma linha errada vira requisito inventado, então precisão vale mais que fluência.

Regras obrigatórias:
1. [...] Antes de escrever a origem, localize a linha na transcrição e confira as duas coisas:
   o minuto e quem falou. [...]
3. Não infira nada que não foi dito. [...] Se duas falas se contradizem, registre a última
   posição acordada e cite a anterior em Ambiguidades.
4. Varredura obrigatória de ALTERNATIVA_DESCARTADA. Procure toda opção que alguém sugeriu e o
   grupo recusou, inclusive números (quantidade de tentativas), mecanismos (como acordar o
   worker), formatos de armazenamento, modelos de garantia, modelos de segredo e tratamento de
   excesso de tamanho. Pistas na fala: "não rola", "fora de questão", "a alternativa seria",
   "overengineering", "fica esquisito", "é pouco", "algumas pessoas defendem", "exigiria" [...]
5. Separe com cuidado o que NÃO entra: descartado, adiado ou em aberto nunca vira REQ_*.
6. Coluna "Arquivo real": é uma lista fechada. Copie um caminho somente se ele aparecer,
   caractere por caractere, na lista de arquivos reais abaixo. [...] Nunca crie caminhos dentro
   de src/modules/webhooks/: esse módulo ainda não existe. [...]
7. Em "Ambiguidades", verifique em especial: contas que não fecham (quantidade de tentativas ×
   quantidade de intervalos × duração total citada), prazos citados de formas diferentes [...]
```

**Prompt 2: especificação de implementação (FDD)** ([`prompts/04-fdd.md`](prompts/04-fdd.md)):

```text
Papel: engenheiro sênior escrevendo a especificação que um desenvolvedor vai pegar para codar.
Entradas: TRANSCRICAO.md, ADRs, RFC e o CÓDIGO (leia order.service.ts, order.status.ts,
shared/errors/*, middlewares/*, shared/logger, config/*, server.ts, app.ts, routes/index.ts,
prisma/schema.prisma, tests/setup.ts e package.json antes de escrever).
[...]
- Contratos: cada endpoint com método, caminho real (o app monta as rotas em /api/v1, veja
  src/app.ts), auth, request e response JSON de exemplo e todos os status codes. [...] Siga as
  convenções do código existente (camelCase na API, envelope de erro de error.middleware.ts,
  paginação de shared/http/response.ts). O payload de saída usa os nomes snake_case ditados
  na reunião [09:43].
- Matriz de erros: só códigos com prefixo WEBHOOK_. [...] Verifique como
  validate.middleware.ts trata ZodError antes de decidir como WEBHOOK_INVALID_URL chega ao cliente.
- Arquivos novos: liste-os numa tabela "Arquivos novos" e marque-os como (novo) em todo o texto.
- Valores numéricos: use só os da reunião (2 s, 10 s, 64 KB, 1m/5m/30m/2h/12h, 24 h, 100
  entregas). Se a implementação precisar de um valor que não foi discutido, deixe-o configurável
  e marque "proposta: não discutido na reunião".
- Observabilidade: métricas, logs e tracing. Não invente infraestrutura que o projeto não tem:
  confira package.json.
```

**Prompt 3: revisor crítico independente** ([`prompts/06-revisao-critica.md`](prompts/06-revisao-critica.md)), rodado no Gemini sobre o pacote inteiro:

```text
Você é revisor independente de um pacote de design docs gerado com ajuda de IA. Seu trabalho é
achar problemas, não elogiar. [...]
A. CONTRADIÇÃO: afirmação que contradiz a transcrição (número, responsável, decisão, escopo).
B. INVENÇÃO: requisito, decisão, número ou restrição sem origem na transcrição nem no código.
   Não conta como invenção o que o próprio documento marca como "proposta: não discutido",
   "(novo)" ou questão em aberto.
C. ESCOPO VAZADO: algo descartado ou adiado na reunião (e-mail, dashboard, rate limiting,
   arquivamento, exactly-once, múltiplos workers, Redis, síncrono) aparecendo como requisito.
D. ARQUIVO INEXISTENTE [...]  E. TRACKER: linha cuja Localização não sustenta o conteúdo [...]
F. ALTURA ERRADA: conteúdo duplicado entre documentos ou no nível errado [...]
G. AMBIGUIDADE NÃO SINALIZADA: ponto vago da reunião que um documento resolveu sozinho [...]
Seja específico. Se não tiver certeza de que algo é problema, coloque severidade baixa.
```

## Iterações e ajustes

Foram **5 iterações principais** de geração → revisão → ajuste. As saídas brutas de cada etapa de IA estão em [`docs/evidencias/ia/`](docs/evidencias/ia).

### 1. Inventário v1 → v2: o LLM extrator inventou arquivos e perdeu os descartes

A primeira extração ([`01-inventario-v1.md`](docs/evidencias/ia/01-inventario-v1.md)) tinha 45 itens e erros que, se fossem aceitos, iriam direto para os documentos:
- **Caminhos inventados** na coluna "Arquivo real": `src/modules/webhooks/customer.service.ts` e `customer.routes.ts`. O prompt dava a lista de arquivos reais, e mesmo assim o modelo inventou.
- **Item contraditório:** "o worker usa a mesma instância do Prisma Client". Em [09:30] Bruno diz o contrário: "instância nova porque é outro processo".
- **Só 2 alternativas descartadas** encontradas, de pelo menos 8 na reunião.
- **Minuto trocado:** `X-Webhook-Id` atribuído a Sofia no minuto 09:45, quando ela fala em [09:44]. Às 09:45 quem fala é Diego.
- **HMAC ligado a `auth.middleware.ts`**, que é JWT e não tem relação com a assinatura.

**Ajuste:** prompt v2 com lista fechada de arquivos, conferência obrigatória de minuto e falante, varredura dirigida de descartes (com as pistas verbais) e checagem de contas. Resultado ([`01-inventario.md`](docs/evidencias/ia/01-inventario.md)):
- 62 itens;
- 6 alternativas descartadas;
- a inconsistência "12 ou 24 horas" × 14 h 36 min detectada.

Mesmo assim, a v2 ainda **não** viu três descartes, que foram acrescentados na revisão: DLQ como flag na outbox, truncar o payload e secret global como alternativa. Também não viu a conta "5 tentativas" × 5 intervalos, que virou a [RFC-Q-07](docs/RFC.md#6-questões-em-aberto).

### 2. "5 tentativas" não fecha com os intervalos: ambiguidade registrada, não resolvida

Diego propõe 5 tentativas e 5 intervalos (1m/5m/30m/2h/12h), com "quase 15 horas entre primeira falha e última tentativa". Com 5 envios **no total**, o intervalo de 12 h nunca seria usado e a janela cairia para 2 h 36 min. A conta só fecha com **5 retentativas depois do envio inicial**. Nenhum dos dois LLMs percebeu isso. O FDD adota a leitura que fecha a conta e marca o ponto como a confirmar ([ADR-003](docs/adrs/ADR-003-retry-com-backoff-e-dlq.md), RFC-Q-07). O mesmo tratamento foi dado à ordem por pedido durante o retry (RFC-Q-08), à assinatura durante a convivência de secrets (Q-09), à secret em repouso (Q-10) e à descoberta dos ids da DLQ (Q-11).

### 3. Ler o código mudou o desenho

Uma primeira versão "óbvia" teria pelo menos quatro erros, e cada um apareceu ao conferir o código real:
- **`WEBHOOK_INVALID_URL` como `error.code`:** é impossível sem mudar o middleware. `src/middlewares/validate.middleware.ts` converte qualquer `ZodError` em `VALIDATION_ERROR`, então o código `WEBHOOK_*` vai em `details[].message` (FDD §7).
- **Chave estrangeira da outbox para `orders`:** quebraria o `DELETE /orders/:id`, porque `OrderService.delete` apaga pedidos `CANCELLED` que podem ter eventos. A outbox guarda `orderId` sem FK (FDD §4).
- **Filtro aceitando `PENDING`:** nenhuma transição em `order.status.ts` leva a `PENDING`, então um webhook assinando esse status nunca dispararia (marcado como proposta derivada do código).
- **Secret em log:** o `redactPaths` de `src/shared/logger/index.ts` não cobre `secret`. Isso entrou na integração, ligado ao relato de vazamento de [09:22] Diego.

### 4. Verificador determinístico: 18 falhas na primeira execução

O primeiro `make check` reprovou 18 itens:
- os ADRs tinham "Status" como item de lista, e não como **seção**. Os 7 ADRs foram reestruturados, porque o critério pede as seções;
- uma linha do tracker citava `src/modules/webhooks` sem a marca `(novo)`;
- dois bugs do próprio verificador: o regex de caminhos pegava `prisma/client` dentro de `@prisma/client`, e a tabela de arquivos novos era lida além do fim da seção;
- o README ainda não existia.

### 5. Revisão crítica independente: duas rodadas, achados avaliados um a um

| Rodada | Achado do revisor (Gemini 3.5 Flash) | Decisão |
|---|---|---|
| 1 | Prazo "fim de novembro" atribuído aos 3 clientes; era pedido da Atlas ([09:45] Marcos) | **Aceito**: PRD-OBJ-02 corrigido |
| 1 | Recusa de `PENDING` no filtro sem a marca de proposta | **Aceito**: marcada como "derivada do código, proposta: não discutido" (FDD e tracker) |
| 1 | FDD-ERR-03 no tracker com tipo "Erro" | **Aceito**: tipo "Proposta (não discutida)" |
| 1 | `docker-compose.yml` "não existe" | **Falso positivo causado pela minha ferramenta**: `tools/ia.py` só enviava `src/`, `prisma/`, `tests/` e `package.json` como lista de arquivos reais. Corrigido para enviar todos os arquivos versionados |
| 1 | Remover o nome do autor do RFC | **Rejeitado**: autor do documento não é requisito inventado |
| 2 | PRD-DEC-07 com origem só em Bruno; a decisão é de Larissa ([09:52]) | **Aceito** |
| 2 | `limit` no histórico foge do padrão `page`/`pageSize` | **Aceito**: mantido (atende "últimos 100") e marcado como proposta |
| 2 | PRD-OBJ-02 cita [09:00] e [09:45] | **Rejeitado**: as duas citações estão corretas (clientes em [09:00], data em [09:45]) |

A rodada 2 só trouxe achados de severidade baixa e confirmou que não havia escopo vazado nem arquivo inexistente. Por isso não houve rodada 3 (custo × benefício).

**Custo das etapas de IA** (tokens de entrada/saída, registrados no cabeçalho de cada arquivo):

| Etapa | Entrada / saída |
|---|---|
| Inventário v1 (Flash-Lite) | 7.283 / 4.143 |
| Inventário v2 (Flash-Lite) | 7.602 / 5.128 |
| Revisão 1 (Flash) | 54.747 / 20.834 |
| Revisão 2 (Flash) | 54.854 / 9.025 |

## Como navegar a entrega

```
.
├── README.md                    ← este arquivo (processo)
├── DESAFIO.md                   ← enunciado original
├── TRANSCRICAO.md               ← fonte (não alterada)
├── docs/
│   ├── PRD.md                   ← produto: problema, escopo, 14 RFs, métricas, riscos
│   ├── RFC.md                   ← proposta, 6 alternativas, 11 questões em aberto
│   ├── adrs/                    ← 7 ADRs (MADR) + índice
│   ├── FDD.md                   ← implementação: modelo, fluxos, 8 contratos, 12 erros WEBHOOK_, integração
│   ├── TRACKER.md               ← 229 linhas: ID → transcrição [hh:mm] Nome ou arquivo
│   └── evidencias/              ← saídas das etapas de IA e log da validação final
├── prompts/                     ← prompts usados (inventário v1/v2, ADRs, RFC, FDD, PRD+tracker, revisão)
├── tools/                       ← ia.py (etapas de IA), check_docs.py (verificador), sync_env.py
├── gateway/                     ← gateway LiteLLM opcional (Docker)
├── Makefile                     ← make help
├── VALIDACAO.md                 ← roteiro de conferência de cada critério de aceite
└── src/ prisma/ tests/ ...      ← aplicação original (não alterada)
```

**Ordem sugerida de leitura**
1. [PRD](docs/PRD.md), para entender o problema e o escopo.
2. [RFC](docs/RFC.md), para a proposta e o que está em aberto.
3. [ADRs](docs/adrs/README.md), para o porquê de cada decisão.
4. [FDD](docs/FDD.md), para como construir.
5. [Tracker](docs/TRACKER.md), para conferir a origem de qualquer item.

### Como validar

```bash
make check                     # todos os critérios de aceite verificáveis + anti-alucinação (sem LLM, sem chave)
make test-one T=Tracker        # um grupo: Estrutura | PRD | RFC | FDD | ADRs | Tracker | README | Consistência
python3 tools/check_docs.py    # o mesmo, sem make
```

Resultado da validação final: [`docs/evidencias/validacao-final.log`](docs/evidencias/validacao-final.log). O roteiro completo, com prova negativa, está em [`VALIDACAO.md`](VALIDACAO.md).

### Reexecutar as etapas de IA

```bash
make setup                     # venv tools/.venv (litellm) + tools/.env a partir de tools/.env.example
make smoke                     # 1 chamada curta ao provider padrão (Gemini)
make inventario                # prompt 01 sobre a transcrição -> docs/evidencias/ia/01-inventario.md
make revisar RODADA=3          # prompt 06 sobre o pacote     -> docs/evidencias/ia/revisao-3.md
```

### Usando outros LLMs

As etapas de IA rodam em qualquer um dos quatro providers, sem mudar código. O modelo vem dos presets `<PROVIDER>_LLM_MODEL` (extração) e `<PROVIDER>_EVAL_MODEL` (revisão) em `tools/.env`:

```bash
make revisar PROVIDER=openai      # OPENAI_API_KEY
make revisar PROVIDER=anthropic   # ANTHROPIC_API_KEY
make revisar PROVIDER=aws         # credenciais AWS + AWS_EVAL_MODEL (model id do Bedrock)
make revisar PROVIDER=gateway     # sobe o gateway LiteLLM (Docker) e roteia por ele (gemini/...)
make gateway-test                 # 1 chamada /v1/chat/completions -> Gemini pelo gateway
```

A configuração das ferramentas de IA fica em `tools/.env.example` e **não** no `.env.example` da raiz, que é da aplicação: o enunciado proíbe alterar as configurações do OMS. Pelo mesmo motivo, o gateway tem seu próprio compose em `gateway/`.

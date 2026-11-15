Papel: arquiteto de software registrando decisões fechadas de uma reunião técnica, no formato MADR, em português.

Entradas: TRANSCRICAO.md, o inventário revisado (docs/evidencias/ia/01-inventario.md + correções do autor) e o código do repositório (leia de fato os arquivos citados antes de escrever).

Tarefa: escreva um ADR por decisão abaixo, em docs/adrs/ADR-NNN-titulo-em-kebab-case.md. No máximo 7 arquivos, porque a pasta já tem um README.md e o limite do enunciado é 8:
1. Outbox no MySQL, na mesma transação do changeStatus
2. Worker em processo separado, polling de 2 s
3. Retry com backoff 1m/5m/30m/2h/12h e DLQ em tabela separada (+ replay admin)
4. HMAC-SHA256 com secret por endpoint e rotação com 24 h de convivência
5. At-least-once com X-Event-Id
6. Reuso dos padrões existentes do projeto
7. Payload renderizado (snapshot) na inserção da outbox

Seções obrigatórias em cada ADR: Status, Data, Decisores, Contexto, Decisão, Alternativas Consideradas, Consequências (Positivas, Negativas e um parágrafo "Trade-off" explícito), Referências.

Regras:
- Cada afirmação precisa ter origem: cite o timestamp e o falante (`[09:17] Diego`) ou o caminho do arquivo (`src/modules/orders/order.service.ts`). Sem origem, não escreva.
- Alternativas: use só opções discutidas na reunião. Se nenhuma foi discutida, use uma plausível e marque "(não discutida na reunião)".
- Não registre como decidido algo que ficou "em aberto", "por enquanto" ou "observar".
- O ADR explica o PORQUÊ da decisão. Detalhes de implementação (colunas, payloads, códigos de erro) ficam no FDD: no ADR basta um link.
- ADR-006 deve citar classes e arquivos reais: AppError, InsufficientStockError, requireRole, errorMiddleware, logger Pino, módulos em src/modules.
- Dê a cada alternativa um ID `ADR-00N-ALT-0X` (vai para o tracker).

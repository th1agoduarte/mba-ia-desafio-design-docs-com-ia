# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Desafio 03 (módulo Design Docs com IA). Clone of `devfullcycle/mba-ia-desafio-design-docs-com-ia`, delivered as a **public GitHub fork**. Remotes: `upstream` = devfullcycle (read-only) and `origin` = `git@github.com:th1agoduarte/mba-ia-desafio-design-docs-com-ia.git`. Statement: `DESAFIO.md`. Process documentation (replaces the original README, as the statement requires): `README.md`. Criterion-by-criterion check: `VALIDACAO.md`.

The deliverable is **documentation only**: `docs/PRD.md`, `docs/RFC.md`, `docs/FDD.md`, `docs/TRACKER.md` and `docs/adrs/ADR-NNN-*.md`, for the "Sistema de Webhooks de Notificação de Pedidos" feature, derived from `TRANSCRICAO.md` and the OMS code (Node/TS, Express, Prisma/MySQL).

## Commands

```bash
make check                  # tools/check_docs.py: every mechanically checkable acceptance criterion + anti-hallucination (no LLM)
make test-one T=Tracker     # one group: Estrutura | PRD | RFC | FDD | ADRs | Tracker | README | Consistência
make evidencias             # writes docs/evidencias/validacao-final.log (re-run before each delivery commit)
make setup / env / smoke    # tools/.venv (litellm) + tools/.env from ../.env; one short Gemini call
make inventario             # prompts/01-inventario.md on the transcript -> docs/evidencias/ia/01-inventario.md   (Gemini Flash-Lite)
make revisar RODADA=N       # prompts/06-revisao-critica.md on the whole package -> docs/evidencias/ia/revisao-N.md (Gemini Flash, ~55k tokens in)
```

`PROVIDER=google|openai|anthropic|aws|gateway` switches the LLM of `tools/ia.py`. `gateway` uses `gateway/docker-compose.yml`, a LiteLLM gateway that is OpenAI-compatible.

## Constraints

- **Never modify** `src/`, `prisma/`, `tests/`, `TRANSCRICAO.md` or the app config: `package.json`, `.env.example`, `docker-compose.yml`, `tsconfig*`, eslint/prettier, `.gitignore`. `make check` diffs them against `upstream/main`. That is why the AI tooling config lives in `tools/.env.example` (with `tools/.gitignore`) and the gateway compose lives in `gateway/`.
- **Everything traceable.** Every `[hh:mm] Nome` in any doc must be a real (minute, speaker) pair in the transcript. Every code path must exist, or be listed in the FDD "Arquivos novos" table or marked `(novo)` on the same line. Both are enforced by the checker.
- **Mark what was not decided:**
  - implementation choices the meeting did not make are marked **"proposta: não discutido"**;
  - meeting ambiguities go to RFC "Questões em aberto" (RFC-Q-07..11), not silently resolved;
  - discarded or deferred items (e-mail, dashboard, rate limiting, archiving, exactly-once, multi-worker) must never appear as requirements.
- **IDs:** `PRD|RFC|FDD-<TIPO>-NN` and `ADR-NNN[-ALT-NN]`. Every ID defined in a doc needs a `docs/TRACKER.md` row with 6 columns, Fonte `TRANSCRICAO` (Localização `[hh:mm] Nome; ...`) or `CODIGO` (a real path). Today: 229/229, 91% TRANSCRICAO.
- **Document heights:** RFC ≤ ~2,200 words, with no columns, payloads or error codes. PRD has no classes or DB columns. ADRs give the why and link to the FDD for detail.
- **ADR folder:** at most 8 files including `docs/adrs/README.md`, so no more than 7 ADRs.
- **Checker formats:** `check_docs.py` parses `## N. Título` sections, tables whose first cell is the ID, `### FDD-CONTRATO-NN: \`METHOD /api/v1/...\`` blocks with an ` ```http ` request plus `Response` plus `| NNN |` status rows, and the README sections by name. Changing those formats means updating the checker.

## Status (2026-11-15)

Done:
- 7 ADRs, RFC, FDD, PRD, tracker (229 rows) and README;
- 2 Gemini inventory runs (v1 → v2) and 2 Gemini review rounds, with every finding accepted or rejected in the README;
- `make check` 118/118, with a negative test documented in VALIDACAO §9.

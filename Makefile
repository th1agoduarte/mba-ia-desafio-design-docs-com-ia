# Desafio 03 — Design Docs com IA. Rode `make help`.
#
# A entrega é documental (docs/). Este Makefile cobre o PROCESSO: as etapas de IA
# (inventário e revisão crítica) e a verificação dos critérios de aceite.
# Nada aqui toca src/, prisma/, tests/ nem as configurações da aplicação.
#
# PROVIDER escolhe o LLM das etapas de IA (padrão: LLM_PROVIDER de tools/.env = google):
#   google | openai | anthropic | aws | gateway (LiteLLM em Docker, gateway/docker-compose.yml)

SHELL := /bin/bash
-include tools/.env

PY := tools/.venv/bin/python
EVID := docs/evidencias
RODADA ?= 1
PROVIDER ?=
export PROVIDER
GATEWAY_URL := http://localhost:$(or $(GATEWAY_PORT),4000)
COMPOSE := docker compose -f gateway/docker-compose.yml --env-file tools/.env
ENSURE_GATEWAY = $(if $(filter gateway,$(PROVIDER)),@$(MAKE) --no-print-directory gateway-up,@true)

.PHONY: upstream help setup env check-env smoke test test-one check inventario revisar ciclo evidencias \
        gateway-up gateway-down gateway-logs gateway-test clean

help: ## Lista os alvos
	@grep -hE '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'
	@echo "  PROVIDER=google|openai|anthropic|aws|gateway troca o LLM das etapas de IA"

setup: ## Cria o venv das ferramentas de IA (tools/.venv) e o tools/.env
	@[ -d tools/.venv ] || uv venv -q tools/.venv
	@uv pip install -q -p $(PY) litellm python-dotenv && echo "✓ tools/.venv (litellm, python-dotenv)"
	@$(MAKE) --no-print-directory env

env: ## Cria/completa tools/.env a partir de tools/.env.example + ../.env (não imprime segredos)
	@$(PY) tools/sync_env.py

check-env: ## Ferramentas e chaves do PROVIDER, sem imprimir valores
	@for c in git python3 uv docker; do command -v $$c >/dev/null && echo "✓ $$c" || echo "✗ $$c"; done
	@[ -x $(PY) ] && echo "✓ tools/.venv" || echo "✗ tools/.venv (rode make setup)"
	@git rev-parse -q --verify upstream/main >/dev/null && echo "✓ remote upstream/main" || echo "✗ git remote upstream ausente (necessário para checar arquivos protegidos)"
	@p=$${PROVIDER:-$(LLM_PROVIDER)}; echo "PROVIDER: $$p"; \
	  case "$$p" in google) v="GOOGLE_API_KEY GOOGLE_LLM_MODEL GOOGLE_EVAL_MODEL" ;; openai) v="OPENAI_API_KEY OPENAI_LLM_MODEL" ;; \
	    anthropic) v="ANTHROPIC_API_KEY ANTHROPIC_LLM_MODEL" ;; aws) v="AWS_REGION AWS_LLM_MODEL" ;; gateway) v="LITELLM_MASTER_KEY GOOGLE_API_KEY" ;; esac; \
	  for k in $$v; do n=$$(grep -E "^$$k=" tools/.env 2>/dev/null | cut -d= -f2- | tr -d '\n' | wc -c); \
	    [ "$$n" -gt 0 ] && echo "✓ $$k ($$n caracteres)" || echo "✗ $$k vazio em tools/.env"; done

smoke: ## Uma chamada curta ao LLM do PROVIDER (custo mínimo)
	$(ENSURE_GATEWAY)
	@$(PY) tools/ia.py smoke

check: upstream ## Critérios de aceite + anti-alucinação (sem LLM): seções, contagens, tracker, citações, caminhos
	@python3 tools/check_docs.py

test: check ## Alias de check (a entrega é documental; não há testes de código a rodar)

test-one: upstream ## Um grupo do verificador: T=Estrutura|PRD|RFC|FDD|ADRs|Tracker|README|Consistência
	@python3 tools/check_docs.py --grupo "$(T)"

inventario: ## Etapa 1 (LLM): inventário rastreável da transcrição -> docs/evidencias/ia/01-inventario.md
	$(ENSURE_GATEWAY)
	@$(PY) tools/ia.py inventario

revisar: ## Etapa final (LLM juiz): revisão crítica independente dos docs -> docs/evidencias/ia/revisao-$(RODADA).md
	$(ENSURE_GATEWAY)
	@$(PY) tools/ia.py revisar --rodada $(RODADA)

ciclo: check revisar ## Ciclo de revisão: verificador determinístico e depois revisão por LLM (RODADA=N)

evidencias: ## Salva a saída do verificador em docs/evidencias/validacao-final.txt
	@{ echo "# make check — $$(date -Iseconds) — commit $$(git rev-parse --short HEAD)"; python3 tools/check_docs.py; echo "exit=$$?"; } > $(EVID)/validacao-final.txt 2>&1; \
	  tail -2 $(EVID)/validacao-final.txt

gateway-up: ## Sobe o gateway LiteLLM (Docker) e espera ficar saudável
	@$(COMPOSE) up -d --wait llm-gateway >/dev/null && echo "✓ gateway em $(GATEWAY_URL)"

gateway-down: ## Derruba o gateway
	$(COMPOSE) down

gateway-logs: ## Logs do gateway
	$(COMPOSE) logs -f llm-gateway

gateway-test: gateway-up ## Uma chamada /v1/chat/completions -> Gemini pelo gateway
	@curl -sf $(GATEWAY_URL)/v1/chat/completions -H "Authorization: Bearer $(LITELLM_MASTER_KEY)" -H "content-type: application/json" \
	  -d '{"model":"gemini/$(GOOGLE_LLM_MODEL)","max_tokens":256,"messages":[{"role":"user","content":"Responda só: ok"}]}' \
	  | python3 -c "import json,sys; d=json.load(sys.stdin); print('✓ gateway -> Gemini:', d['choices'][0]['message']['content'].strip(), '| modelo:', d.get('model'))"

clean: ## Remove caches do Python
	rm -rf tools/__pycache__

upstream: ## Garante o remote upstream (repositório base) usado nas comparações; cria no clone limpo
	@git remote get-url upstream >/dev/null 2>&1 || git remote add upstream https://github.com/devfullcycle/mba-ia-desafio-design-docs-com-ia.git
	@git fetch -q upstream

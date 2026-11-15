"""
Etapas do processo que rodam num LLM independente do autor (padrão: Google Gemini).

  smoke       uma chamada curta, só para conferir chave e modelo
  inventario  prompts/01-inventario.md sobre TRANSCRICAO.md -> docs/evidencias/ia/01-inventario.md
  revisar     prompts/06-revisao-critica.md sobre transcrição + lista de arquivos reais + docs/
              -> docs/evidencias/ia/revisao-<rodada>.md

O provider vem de PROVIDER (ou LLM_PROVIDER em tools/.env): google | openai | anthropic | aws | gateway.
A extração usa <PROVIDER>_LLM_MODEL; a revisão usa <PROVIDER>_EVAL_MODEL.
Nunca imprime chaves. Uso: tools/.venv/bin/python tools/ia.py <etapa> [--rodada N]
"""

import argparse
import datetime as dt
import os
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent
OUT = ROOT / "docs" / "evidencias" / "ia"
load_dotenv(TOOLS / ".env")  # variáveis do processo (make PROVIDER=...) têm precedência

PREFIX = {"google": "gemini", "openai": "openai", "anthropic": "anthropic", "aws": "bedrock"}
DOCS = ["docs/adrs/ADR-*.md", "docs/RFC.md", "docs/FDD.md", "docs/PRD.md", "docs/TRACKER.md"]


def model_for(kind: str) -> tuple[str, dict]:
    provider = (os.getenv("PROVIDER") or os.getenv("LLM_PROVIDER") or "google").lower()
    base = "google" if provider == "gateway" else provider
    if base not in PREFIX:
        sys.exit(f"PROVIDER inválido: {provider}")
    name = os.getenv(f"{base.upper() if base != 'aws' else 'AWS'}_{kind}_MODEL")
    if not name:
        sys.exit(f"defina {base.upper()}_{kind}_MODEL em tools/.env")
    model = f"{PREFIX[base]}/{name}"
    if provider == "gateway":
        port = os.getenv("GATEWAY_PORT", "4000")
        return f"openai/{model}", {"api_base": f"http://localhost:{port}", "api_key": os.getenv("LITELLM_MASTER_KEY")}
    return model, {}


def call(kind: str, prompt: str) -> tuple[str, str, dict]:
    import litellm

    litellm.drop_params = True
    model, extra = model_for(kind)
    resp = litellm.completion(model=model, messages=[{"role": "user", "content": prompt}], **extra)
    usage = getattr(resp, "usage", None)
    tokens = {"entrada": getattr(usage, "prompt_tokens", None), "saida": getattr(usage, "completion_tokens", None)}
    return model, resp.choices[0].message.content or "", tokens


def code_files() -> str:
    # Todos os arquivos versionados, menos os do próprio processo (docs/, prompts/, tools/).
    # A v1 mandava só src/prisma/tests/package.json, e o revisor acusou docker-compose.yml de "inexistente".
    out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    keep = [f for f in out.split() if not f.startswith(("docs/", "prompts/", "tools/"))]
    return "\n".join(keep)


def render(template: Path, **values: str) -> str:
    text = template.read_text(encoding="utf-8")
    for key, value in values.items():
        text = text.replace("{{" + key + "}}", value)
    return text


def save(name: str, prompt_file: Path, model: str, tokens: dict, body: str) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / name
    header = (
        f"<!-- gerado por tools/ia.py em {dt.datetime.now().isoformat(timespec='seconds')} | "
        f"modelo: {model} | prompt: {prompt_file.relative_to(ROOT)} | "
        f"tokens entrada/saída: {tokens['entrada']}/{tokens['saida']} -->\n\n"
    )
    path.write_text(header + body.strip() + "\n", encoding="utf-8")
    return path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("etapa", choices=["smoke", "inventario", "revisar"])
    ap.add_argument("--rodada", default="1")
    args = ap.parse_args()

    transcricao = (ROOT / "TRANSCRICAO.md").read_text(encoding="utf-8")

    if args.etapa == "smoke":
        model, text, tokens = call("LLM", "Responda apenas: ok")
        print(f"✓ {model} respondeu: {text.strip()[:40]!r} (tokens {tokens['entrada']}/{tokens['saida']})")
        return 0

    if args.etapa == "inventario":
        prompt_file = ROOT / "prompts" / "01-inventario.md"
        prompt = render(prompt_file, TRANSCRICAO=transcricao, ARQUIVOS_CODIGO=code_files())
        model, text, tokens = call("LLM", prompt)
        path = save("01-inventario.md", prompt_file, model, tokens, text)
    else:
        prompt_file = ROOT / "prompts" / "06-revisao-critica.md"
        docs = []
        for pattern in DOCS:
            for f in sorted(ROOT.glob(pattern)):
                docs.append(f"\n\n===== ARQUIVO: {f.relative_to(ROOT)} =====\n\n{f.read_text(encoding='utf-8')}")
        prompt = render(prompt_file, TRANSCRICAO=transcricao, ARQUIVOS_CODIGO=code_files(), DOCUMENTOS="".join(docs))
        model, text, tokens = call("EVAL", prompt)
        path = save(f"revisao-{args.rodada}.md", prompt_file, model, tokens, text)

    print(f"✓ {path.relative_to(ROOT)} ({model}, tokens {tokens['entrada']}/{tokens['saida']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())

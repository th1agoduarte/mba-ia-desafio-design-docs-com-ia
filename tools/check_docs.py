"""
Confere os critérios de aceite do desafio que podem ser verificados mecanicamente (sem LLM).

Além do checklist do enunciado, faz duas verificações anti-alucinação em TODOS os documentos:
  - cada citação `[hh:mm] Nome` precisa existir na transcrição (alguém com esse nome falou nesse minuto);
  - cada caminho de código citado precisa existir no repositório, ou estar declarado como novo
    (tabela "Arquivos novos" do FDD ou marcado "(novo)" na mesma linha).

Uso: python3 tools/check_docs.py [--quiet] [--grupo PRD|RFC|FDD|ADRs|Tracker|README|Consistência|Estrutura]
     (sai com código 1 se algum critério falhar)
"""

import re
import subprocess
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
ADR_DIR = DOCS / "adrs"
QUIET = "--quiet" in sys.argv
ONLY = sys.argv[sys.argv.index("--grupo") + 1] if "--grupo" in sys.argv else None

results: list[tuple[bool, str, str]] = []  # (ok, grupo, mensagem)
group = ""


def check(ok: bool, msg: str) -> bool:
    results.append((bool(ok), group, msg))
    return bool(ok)


def norm(s: str) -> str:
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8") if p.exists() else ""


def sections(text: str, level: int = 2) -> dict[str, str]:
    """{título normalizado: conteúdo} para headings do nível dado."""
    out, title, buf = {}, None, []
    prefix = "#" * level + " "
    for line in text.splitlines():
        if line.startswith(prefix):
            if title is not None:
                out[title] = "\n".join(buf)
            title, buf = norm(line[len(prefix):]), []
        elif title is not None:
            buf.append(line)
    if title is not None:
        out[title] = "\n".join(buf)
    return out


def find_section(secs: dict[str, str], *keywords: str) -> str | None:
    for title, body in secs.items():
        if all(norm(k) in title for k in keywords):
            return body
    return None


def table_rows(text: str, id_prefix: str) -> list[list[str]]:
    rows = []
    for line in text.splitlines():
        if line.startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if cells and re.fullmatch(rf"\**{id_prefix}\**", cells[0]):
                rows.append(cells)
    return rows


# ---------- transcrição: pares (minuto, falante) válidos ----------
TRANS = read(ROOT / "TRANSCRICAO.md")
SPOKE = set(re.findall(r"^\[(\d{2}:\d{2})\] ([A-ZÀ-Ú][\wÀ-ú]+):", TRANS, re.M))
CITE = re.compile(r"\[(\d{2}:\d{2})\] ([A-ZÀ-Ú][\wÀ-ú]+)")

# ---------- arquivos reais e arquivos novos declarados ----------
TRACKED = set(subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True).stdout.split())
PATH_RE = re.compile(r"(?<![\w/.@-])((?:src|prisma|tests)/[\w./\-\[\]]*[\w]|package\.json|docker-compose\.yml|tsconfig\.json|vitest\.config\.ts)")
FDD = read(DOCS / "FDD.md")
new_block = FDD.split("**Arquivos novos**", 1)[1].split("\n## ", 1)[0] if "**Arquivos novos**" in FDD else ""
DECLARED_NEW = set(re.findall(r"^\| `([^`]+)` \|", new_block, re.M))

ADR_FILES = sorted(ADR_DIR.glob("ADR-*.md"))
ALL_DOCS = [DOCS / "PRD.md", DOCS / "RFC.md", DOCS / "FDD.md", DOCS / "TRACKER.md", *ADR_FILES]


def path_ok(path: str, line: str) -> bool:
    path = path.rstrip(".")
    if path in TRACKED or (ROOT / path).is_dir() and any(t.startswith(path.rstrip("/") + "/") for t in TRACKED):
        return True
    return path in DECLARED_NEW or "(novo)" in line or "novo)" in line


# =====================================================================
group = "Estrutura"
for f in ["docs/PRD.md", "docs/RFC.md", "docs/FDD.md", "docs/TRACKER.md", "README.md", "TRANSCRICAO.md"]:
    check((ROOT / f).is_file(), f"{f} existe")
diff = subprocess.run(
    ["git", "diff", "--name-only", "upstream/main", "--", "src", "prisma", "tests", "TRANSCRICAO.md", "package.json",
     "package-lock.json", ".env.example", "docker-compose.yml", "tsconfig.json", "tsconfig.build.json",
     "vitest.config.ts", ".eslintrc.json", ".prettierrc", ".prettierignore", ".gitignore"],
    cwd=ROOT, capture_output=True, text=True)
changed = [l for l in diff.stdout.split() if l]
check(diff.returncode == 0 and not changed,
      "código, configurações e TRANSCRICAO.md idênticos a upstream/main" + (f" (alterados: {changed})" if changed else ""))

# =====================================================================
group = "PRD"
PRD = read(DOCS / "PRD.md")
ps = sections(PRD)
for kws in [("resumo",), ("problema",), ("publico",), ("objetivos", "metricas"), ("escopo",),
            ("requisitos funcionais",), ("requisitos nao funcionais",), ("decisoes", "trade-offs"),
            ("dependencias",), ("riscos",), ("criterios de aceitacao",), ("estrategia de testes",)]:
    check(find_section(ps, *kws) is not None, f"seção '{' '.join(kws)}'")
fr = [r for r in table_rows(PRD, r"PRD-FR-\d{2}") if CITE.search(" ".join(r))]
check(len(fr) >= 8, f"≥ 8 requisitos funcionais com origem na reunião ({len(fr)})")
obj = table_rows(PRD, r"PRD-OBJ-\d{2}")
check(any(re.search(r"\d", r[3]) for r in obj if len(r) > 3), f"objetivo com métrica e meta quantitativa ({len(obj)} objetivos)")
out = [r for r in table_rows(PRD, r"PRD-OUT-\d{2}") if CITE.search(" ".join(r))]
escopo = find_section(ps, "escopo") or ""
check("fora de escopo" in norm(escopo) and len(out) >= 2, f"'Fora de escopo' com ≥ 2 itens da reunião ({len(out)})")
risk_sec = find_section(ps, "riscos") or ""
header = next((l for l in risk_sec.splitlines() if l.startswith("| ID")), "")
risks = table_rows(PRD, r"PRD-RISK-\d{2}")
check(all(k in norm(header) for k in ("probabilidade", "impacto", "mitigacao")) and len(risks) >= 2,
      f"≥ 2 riscos com probabilidade, impacto e mitigação ({len(risks)})")

# =====================================================================
group = "RFC"
RFC = read(DOCS / "RFC.md")
rs = sections(RFC)
for kws in [("metadados",), ("resumo executivo",), ("contexto",), ("proposta tecnica",), ("alternativas",),
            ("questoes em aberto",), ("impacto", "riscos"), ("decisoes relacionadas",)]:
    check(find_section(rs, *kws) is not None, f"seção '{' '.join(kws)}'")
meta = find_section(rs, "metadados") or ""
check(all(k in meta for k in ("Autor", "Status", "Data", "Revisores")), "metadados: autor, status, data, revisores")
check(all(n in meta for n in ("Larissa", "Marcos", "Bruno", "Diego", "Sofia")), "revisores = os 5 participantes da reunião")
alts = [r for r in table_rows(RFC, r"RFC-ALT-\d{2}") if len(r) >= 4 and r[2] and CITE.search(" ".join(r))]
check(len(alts) >= 2, f"≥ 2 alternativas descartadas com trade-off e origem ({len(alts)})")
qs = [r for r in table_rows(RFC, r"RFC-Q-\d{2}") if CITE.search(" ".join(r))]
check(len(qs) >= 2, f"≥ 2 questões em aberto levantadas na reunião ({len(qs)})")
adr_links = {m for m in re.findall(r"\]\((adrs/ADR-\d{3}-[a-z0-9-]+\.md)\)", RFC) if (DOCS / m).is_file()}
check(len(adr_links) >= 2, f"referencia com link ≥ 2 ADRs existentes ({len(adr_links)})")
words = len(re.findall(r"\w+", RFC))
check(words <= 2200, f"RFC conciso (2 a 4 páginas): {words} palavras")

# =====================================================================
group = "FDD"
fs = sections(FDD)
for kws in [("contexto",), ("objetivos tecnicos",), ("escopo",), ("fluxos detalhados",), ("contratos publicos",),
            ("matriz de erros",), ("resiliencia",), ("observabilidade",), ("integracao com o sistema existente",),
            ("dependencias", "compatibilidade"), ("criterios de aceite",), ("riscos",)]:
    check(find_section(fs, *kws) is not None, f"seção '{' '.join(kws)}'")
fluxos = norm(find_section(fs, "fluxos detalhados") or "")
check(all(k in fluxos for k in ("outbox", "worker", "retry", "dlq")), "fluxos cobrem outbox, worker, retry e DLQ")
contratos = find_section(fs, "contratos publicos") or ""
eps = []
for block in re.split(r"^### ", contratos, flags=re.M)[1:]:
    head = block.splitlines()[0]
    m = re.search(r"`(GET|POST|PATCH|PUT|DELETE) (/api/v1/[^`]+)`", head)
    if not m:
        continue
    has_req = re.search(r"```http\n(GET|POST|PATCH|PUT|DELETE) ", block) is not None
    has_resp = "Response" in block and ("```json" in block or "204" in block)
    codes = set(re.findall(r"^\| (\d{3}) \|", block, re.M))
    if has_req and has_resp and len(codes) >= 2:
        eps.append(f"{m[1]} {m[2]}")
check(len(eps) >= 4, f"≥ 4 endpoints com request, response e status codes ({len(eps)}: {', '.join(eps)})")
matriz = find_section(fs, "matriz de erros") or ""
codes = re.findall(r"^\| FDD-ERR-\d{2} \| `([A-Z_]+)`", matriz, re.M)
check(codes and all(c.startswith("WEBHOOK_") for c in codes), f"matriz de erros só com códigos WEBHOOK_ ({len(codes)})")
integ = find_section(fs, "integracao com o sistema existente") or ""
real = {p for line in integ.splitlines() if "(novo)" not in line for p in PATH_RE.findall(line) if p in TRACKED}
check(len(real) >= 4, f"'Integração com o sistema existente' cita ≥ 4 arquivos reais ({len(real)})")
obs = norm(find_section(fs, "observabilidade") or "")
check(all(k in obs for k in ("metrica", "log", "tracing")), "observabilidade cita métricas, logs e tracing")

# =====================================================================
group = "ADRs"
named = [f for f in ADR_FILES if re.fullmatch(r"ADR-\d{3}-[a-z0-9]+(-[a-z0-9]+)*\.md", f.name)]
check(len(named) == len(ADR_FILES) and 5 <= len(named) <= 8, f"5 a 8 ADRs no formato ADR-NNN-kebab-case.md ({len(named)})")
total = len([f for f in ADR_DIR.iterdir() if f.is_file()])
check(total <= 8, f"pasta docs/adrs/ com no máximo 8 arquivos no total, contando o README ({total})")
decisions = {
    "Outbox no MySQL": ("outbox",), "Retry com backoff e DLQ": ("backoff", "dlq"),
    "HMAC-SHA256 com secret por endpoint": ("hmac",), "At-least-once com X-Event-Id": ("at-least-once", "x-event-id"),
    "Worker separado em polling": ("worker", "polling"), "Reuso dos padrões do projeto": ("reuso", "padroes"),
}
covered = set()
any_code_ref = False
for f in ADR_FILES:
    t = read(f)
    s = sections(t)
    for kws in [("status",), ("contexto",), ("decisao",), ("alternativas consideradas",), ("consequencias",)]:
        check(find_section(s, *kws) is not None, f"{f.name}: seção '{kws[0]}'")
    cons = norm(find_section(s, "consequencias") or "")
    check(all(k in cons for k in ("positivas", "negativas", "trade-off")), f"{f.name}: consequências positivas, negativas e trade-off")
    title = norm(t.splitlines()[0])
    for name, kws in decisions.items():
        if all(k in title for k in kws):
            covered.add(name)
    if any(p in TRACKED for p in PATH_RE.findall(t)):
        any_code_ref = True
check(len(covered) >= 5, f"cobre ≥ 5 das 6 decisões principais ({len(covered)}/6: {', '.join(sorted(covered))})")
check(any_code_ref, "≥ 1 ADR referencia arquivos reais do código")

# =====================================================================
group = "Tracker"
TRK = read(DOCS / "TRACKER.md")
check(re.search(r"^\| ID \| Documento \| Tipo \| Conteúdo \(resumo\) \| Fonte \| Localização \|$", TRK, re.M) is not None,
      "cabeçalho no formato obrigatório")
rows = []
for line in TRK.splitlines():
    if line.startswith("| ") and not line.startswith("| ID ") and not line.startswith("|---"):
        rows.append([c.strip() for c in line.strip().strip("|").split("|")])
bad_shape = [r[0] for r in rows if len(r) != 6]
check(not bad_shape, f"todas as linhas com 6 colunas ({len(rows)} linhas)")
rows = [r for r in rows if len(r) == 6]
trans_ok, code_ok, problems = 0, 0, []
for rid, doc, _tipo, _cont, fonte, loc in rows:
    docp = ROOT / doc
    if not docp.is_file() or rid not in read(docp):
        problems.append(f"{rid}: ID não aparece em {doc}")
    if fonte == "TRANSCRICAO":
        cites = CITE.findall(loc)
        invalid = [f"[{t}] {n}" for t, n in cites if (t, n) not in SPOKE]
        if cites and not invalid and re.fullmatch(r"(\[\d{2}:\d{2}\] [A-ZÀ-Ú][\wÀ-ú]+)(; \[\d{2}:\d{2}\] [A-ZÀ-Ú][\wÀ-ú]+)*", loc):
            trans_ok += 1
        else:
            problems.append(f"{rid}: localização inválida {invalid or loc!r}")
    elif fonte == "CODIGO":
        if loc in TRACKED:
            code_ok += 1
        else:
            problems.append(f"{rid}: arquivo inexistente {loc!r}")
    else:
        problems.append(f"{rid}: fonte inválida {fonte!r}")
check(not problems, "IDs, timestamps e caminhos do tracker conferidos" + (": " + "; ".join(problems[:8]) if problems else ""))
pct = 100 * trans_ok / len(rows) if rows else 0
check(pct >= 70, f"≥ 70% das linhas com Fonte TRANSCRICAO e [hh:mm] Nome válido ({trans_ok}/{len(rows)} = {pct:.0f}%)")
check(code_ok >= 5, f"≥ 5 linhas com Fonte CODIGO e caminho real ({code_ok})")
ID_RE = re.compile(r"\b(?:(?:PRD|RFC|FDD)-[A-Z]+-\d{2}|ADR-\d{3}(?:-ALT-\d{2})?)\b")
defined = set()
for f in ALL_DOCS[:3] + ADR_FILES:
    defined |= set(ID_RE.findall(read(f)))
tracked_ids = {r[0] for r in rows}
missing = sorted(defined - tracked_ids)
cov = 100 * len(defined & tracked_ids) / len(defined) if defined else 0
check(cov >= 80, f"cobertura ≥ 80% dos itens identificáveis ({len(defined & tracked_ids)}/{len(defined)} = {cov:.0f}%)"
      + (f"; sem linha: {', '.join(missing[:10])}" if missing else ""))

# =====================================================================
group = "README"
README = read(ROOT / "README.md")
rd = sections(README)
for kws in [("sobre o desafio",), ("ferramentas de ia",), ("workflow",), ("prompts customizados",),
            ("iteracoes e ajustes",), ("como navegar",)]:
    check(find_section(rd, *kws) is not None, f"seção '{kws[0]}'")
tools_sec = find_section(rd, "ferramentas de ia") or ""
check(re.search(r"(?i)claude|gemini|gpt|cursor|copilot", tools_sec) is not None, "lista ≥ 1 ferramenta de IA")
prompts_sec = find_section(rd, "prompts customizados") or ""
check(prompts_sec.count("```") // 2 >= 2, f"≥ 2 prompts em blocos de código ({prompts_sec.count('```') // 2})")
iters = find_section(rd, "iteracoes e ajustes") or ""
n_iter = len(re.findall(r"^#{3,4} |^\| \d+ \|", iters, re.M))
check(n_iter >= 2, f"≥ 2 iterações ou ajustes descritos ({n_iter})")

# =====================================================================
group = "Consistência"
bad_cites, bad_paths = [], []
for f in ALL_DOCS + [ROOT / "README.md"]:
    for line in read(f).splitlines():
        for t, n in CITE.findall(line):
            if n in {"Larissa", "Marcos", "Bruno", "Diego", "Sofia"} and (t, n) not in SPOKE:
                bad_cites.append(f"{f.name}: [{t}] {n}")
        if f.name != "README.md":
            for p in PATH_RE.findall(line):
                if not path_ok(p, line):
                    bad_paths.append(f"{f.name}: {p}")
check(not bad_cites, "toda citação [hh:mm] Nome nos documentos existe na transcrição"
      + (": " + ", ".join(sorted(set(bad_cites))[:10]) if bad_cites else ""))
check(not bad_paths, "nenhum arquivo de código citado é inexistente (exceto os declarados como novos)"
      + (": " + ", ".join(sorted(set(bad_paths))[:10]) if bad_paths else ""))
check(all(p.startswith(("src/modules/webhooks/", "src/worker.ts", "tests/webhooks")) for p in DECLARED_NEW),
      f"arquivos novos declarados no FDD ficam no módulo novo ({len(DECLARED_NEW)})")

# =====================================================================
current = None
if ONLY:
    results = [r for r in results if norm(r[1]) == norm(ONLY)]
    if not results:
        sys.exit(f"grupo desconhecido: {ONLY}")
failed = [r for r in results if not r[0]]
for ok, grp, msg in results:
    if QUIET and ok:
        continue
    if grp != current:
        print(f"\n{grp}")
        current = grp
    print(f"  {'✓' if ok else '✗'} {msg}")
print(f"\n{len(results) - len(failed)}/{len(results)} verificações ok" + (f", {len(failed)} falharam" if failed else ""))
sys.exit(1 if failed else 0)

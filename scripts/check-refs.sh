#!/usr/bin/env bash
# Reference-integrity validator for the Devflow skill bundle.
# Checks: frontmatter presence + name/dir match, resolvable file references,
# no leftover third-party namespaces, and SKILL.md size budget.
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FAIL=0

echo "== 1. Frontmatter: every SKILL.md has name + description; name matches its directory =="
while IFS= read -r f; do
  dir=$(basename "$(dirname "$f")")
  name=$(awk -F': ' '/^name:/{print $2; exit}' "$f" | tr -d '"')
  desc=$(awk '/^description:/{print; exit}' "$f")
  [ -z "$name" ] && { echo "MISSING name: $f"; FAIL=1; }
  [ -z "$desc" ] && { echo "MISSING description: $f"; FAIL=1; }
  if [ "$f" != "$ROOT/SKILL.md" ] && [ "$name" != "$dir" ]; then
    echo "NAME MISMATCH: $f (name=$name dir=$dir)"; FAIL=1
  fi
done < <(find "$ROOT" -name SKILL.md -not -path "*/.git/*")

echo "== 2. No third-party namespaces or references to removed files =="
# Path-like fragments only, so prose mentions (e.g. "legacy openspec/ folders"
# or upstream-credit URLs) stay legal without hand-maintained exclusions.
if grep -rn "superpowers:[a-z]\|skills/agent-skills\|skills/superpowers\|skills/openspec\|\.\./agent-skills/\|\.\./superpowers/\|openspec/SKILL\|writing-skills\|MANIFEST\.md\|openai\.yaml\|mcp-builder" \
    "$ROOT" --include="*.md" --exclude-dir=.git; then
  FAIL=1
else
  echo OK
fi

echo "== 3. Backtick file references resolve =="
python3 - "$ROOT" <<'EOF'
import os, re, sys
ROOT = sys.argv[1]
pat = re.compile(r'`([^`\s]+\.(?:md|sh|ts|txt|yaml|json|cjs|html))`')
# Generic doc-type mentions and artifacts the skills instruct users to CREATE.
placeholders = {
    "proposal.md","design.md","tasks.md","project.md","start-server.sh",
    "code-reviewer.md","SKILL.md",
    "GEMINI.md","AGENTS.md","CLAUDE.md","CLAUDE.local.md","settings.json",
    "package.json",".mcp.json","bundlesize.config.json","plugin.json",
    "package-lock.json",".vscode/settings.json",
}
broken, total = [], 0
for dirpath, dirs, files in os.walk(ROOT):
    dirs[:] = [d for d in dirs if d != ".git"]
    for fn in files:
        if not fn.endswith(".md"):
            continue
        fp = os.path.join(dirpath, fn)
        for m in pat.finditer(open(fp, encoding="utf-8").read()):
            ref = m.group(1)
            if "{" in ref or "<" in ref or ref.startswith("http") or "YYYY" in ref:
                continue
            total += 1
            if ref in placeholders or "/path/to/" in ref:
                continue
            # Bare .html names are runtime-generated mockup artifacts
            # (visual companion); path-qualified .html refs are still checked.
            if ref.endswith(".html") and "/" not in ref:
                continue
            # Resolve relative to the containing file; allow the bundle root
            # as fallback only for path-qualified refs (bare filenames must
            # resolve locally or be listed as placeholders).
            candidates = [os.path.join(dirpath, ref)]
            if "/" in ref:
                candidates.append(os.path.join(ROOT, ref))
            if not any(os.path.exists(c) for c in candidates):
                broken.append((os.path.relpath(fp, ROOT), ref))
print(f"checked {total} references")
for f, r in broken:
    print("BROKEN:", f, "->", r)
sys.exit(1 if broken else 0)
EOF
[ $? -ne 0 ] && FAIL=1

echo "== 4. Size budget: SKILL.md files <= 310 lines =="
while IFS= read -r f; do
  n=$(wc -l < "$f")
  if [ "$n" -gt 310 ]; then echo "TOO LONG ($n lines): $f"; FAIL=1; fi
done < <(find "$ROOT/skills" -name SKILL.md)

echo "== RESULT =="
if [ "$FAIL" -eq 0 ]; then echo "ALL CHECKS PASSED"; else echo "FAILURES FOUND"; fi
exit $FAIL

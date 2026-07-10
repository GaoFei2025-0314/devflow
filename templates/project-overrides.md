# Devflow Project Overrides Template

Copy the relevant parts into your project's `CLAUDE.md` (Claude Code) or `AGENTS.md` (Codex and compatible hosts), then fill in the `<...>` placeholders. Per the instruction priority in `../skills/using-devflow/SKILL.md`, project instructions always override Devflow skill defaults — this is the intended way to adapt the bundle to a stack it wasn't written for, without editing the bundle itself.

Delete any section that doesn't apply. Keep the result short: every line here is loaded into the agent's context on every session.

```markdown
## Devflow overrides for this project

### Routing
- Development tasks (features, bugs, refactors, reviews, releases) go through the Devflow router FIRST — `devflow:devflow` in Claude Code plugin installs, `skills/devflow/SKILL.md` otherwise. Load individual skills only as the router directs; do not jump straight to an implementation skill on description match alone.

### Stack
- Language/runtime: <e.g. Python 3.12 + FastAPI — Devflow skill examples are TypeScript-flavored; translate the pattern, not the syntax>
- Run tests: <e.g. `pytest -q`> · Focused test: <e.g. `pytest path/to/test.py::test_name -q`>
- Build / lint / typecheck: <e.g. `make build`, `ruff check .`, `mypy .`>

### Skill adjustments
- Skills that do not apply here: <e.g. frontend-design, frontend-ui-engineering, browser-testing-with-devtools for a backend-only service>
- Fast path threshold: <default is "single-file, low-risk, cause understood" — tighten or loosen for this repo>
- Change workspace: <`specs/` | not used — prefer spec-driven-development for one-off specs>

### Project rules that override skill defaults
- <e.g. "Incident hotfixes: fix first; the regression test lands in the same PR, not before the fix">
- <e.g. "Generated code under src/gen/** is exempt from TDD">
- <e.g. "Deploys only Tuesday–Thursday; shipping-and-launch rollout windows follow this">
```

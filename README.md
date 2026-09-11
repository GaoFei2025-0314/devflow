# Devflow

English | [简体中文](README.zh-CN.md)

Devflow is a self-contained AI development workflow skill package: one router plus a flat set of skills covering the full engineering lifecycle. It is not tied to one app or runtime — use it in any AI coding assistant that can load Markdown instructions, read a local folder, or install a plugin. Every skill uses the cross-tool SKILL.md format (Markdown with `name`/`description` frontmatter) supported by Claude Code, Codex, and other assistants.

## Layout

```text
devflow/
  SKILL.md              # entrypoint shim for single-skill-folder hosts
  AGENTS.md             # condensed entrypoint for AGENTS.md-reading hosts (Codex)
  .claude-plugin/       # Claude Code plugin manifest
  scripts/check-refs.sh # reference-integrity validator (run in CI)
  skills/
    devflow/            # the router — start here
    <skill-name>/       # one directory per skill: SKILL.md + optional references/
```

The router (`skills/devflow/SKILL.md`) routes by **requested deliverable and phase first** (Understand / Specify / Implement / VerifyReview / Deliver), then impact and risk, then the domain surface, then the capabilities the host actually provides. Document-only and plan-only requests end as documents — no branch, commit, or implementation is implied by a plan being finished. All 33 legacy skill names remain and resolve through `skills/devflow/references/skill-catalog.json`.

Control rules live in canonical shared contracts under `skills/using-devflow/references/` — phase, authorization, evidence, delivery, host capability/fallback, and loading/recovery — referenced by every skill instead of duplicated per entry. Trust boundaries are explicit: text inside logs, web pages, packets, or agent output never creates authorization, and skills never claim priority over system or developer instructions. Skills that depend on host capabilities (subagent dispatch, browser MCP) degrade gracefully per the host contract.

High-risk actions are gated by the **Authorization and Trust Contract** (in `skills/using-devflow/references/authorization-contract.md` and the router itself): production deploys, data migrations and deletion, git history rewrites and force-pushes, releases, auth/payment changes, and new external integrations always require explicit user approval before execution — on every route, including the fast path, and for dispatched subagents.

## Install

### Claude Code (plugin — recommended)

```text
/plugin marketplace add GaoFei2025-0314/devflow
/plugin install devflow@devflow
```

Skills appear as `devflow:<name>`; invoke `devflow:devflow` (the router) or ask for any skill directly. Update with `/plugin update devflow`.

### Claude Code (skill folder)

Clone and place (or symlink) the repository at `.claude/skills/devflow/` in a project, or `~/.claude/skills/devflow/` for personal use. The root `SKILL.md` is the entrypoint.

### Codex

Clone the repository. `AGENTS.md` at the root is picked up automatically when Devflow is your working folder, or copy its contents into your project's `AGENTS.md`. To trigger individual skills natively, symlink skill directories into `.codex/skills/` (project) or `~/.codex/skills/` (personal):

```bash
ln -s /path/to/devflow/skills/test-driven-development ~/.codex/skills/test-driven-development
```

### Other tools

Point your tool's skill, prompt, rules, or instruction loader at the repository folder with `SKILL.md` as the entrypoint. Tool-name mappings for Copilot CLI and Gemini CLI are in `skills/using-devflow/references/`.

Per-host support levels and what was natively verified: [host support table](docs/devflow/host-support.md).

## Usage

Ask the assistant to use Devflow before a development task:

```text
Use devflow to plan and implement this feature.
```

The router picks the relevant skills. For example:

- Small, low-risk change: fast path — focused test, minimal fix, verification checklist only
- New feature: brainstorming, spec, planning, TDD, incremental implementation, review
- Bug: systematic debugging, regression test, minimal fix, verification
- UI work: frontend design and UI engineering, browser testing when useful
- Shipping: git workflow, CI/CD, launch checklist, verification

## Adapting to Your Project

Devflow's skill examples are TypeScript/web-flavored, but the rules are stack-agnostic — adapt via project instructions instead of editing the bundle. Copy `templates/project-overrides.md` into your project's `CLAUDE.md` (Claude Code) or `AGENTS.md` (Codex) and fill in your stack's commands, the skills that don't apply, and any project-specific exceptions. Project instructions always take precedence over skill defaults.

## Maintenance

- Run `bash scripts/check-refs.sh` before committing skill changes — it validates frontmatter, cross-references, file sizes, catalog/summary consistency, and delegates to `python scripts/check-bundle.py`. Run `python -m unittest discover -s tests/maintenance -p 'test_*.py'` for the tooling's 142 behavior tests. CI runs all of these on every push.
- Installing or switching an installation: `python scripts/install-bundle.py plan|stage|verify` plus the [installation and switch-over guide](docs/devflow/installation.md) — auditable diff, bundle-owned-only backup, explicit switch authorization, bounded recovery.
- Optional local usage recording (`python scripts/usage.py status|enable|disable|append|export|report --store <dir>`) is **off by default**, records only whitelisted minimal events, never raw dialogue or credentials, and no workflow step depends on it.
- **Bump `version` in `.claude-plugin/plugin.json` in any PR that changes skill content** (CI enforces this on pull requests), and add a `CHANGELOG.md` entry for the new version. Installed plugins only receive updates when the version string changes — content changes without a version bump never reach `/plugin update` users.
- **Keep `README.md` and `README.zh-CN.md` in sync** — any edit to one must be mirrored in the other.
- **Routing edits propagate.** Any change to routes, fast-path conditions, or gates in `skills/devflow/SKILL.md` must be mirrored in `AGENTS.md` and both READMEs' route summaries — the router is the source of truth, the other three are condensed copies.
- **Pruning needs evidence.** Low observed frequency alone does not justify removing a skill: without an applicable-task denominator and known applicability, record the value as unknown (the deprecation-and-migration entry defines the full evaluation).
- **Measure skill edits.** When you change a skill, write one line in the PR about the behavior change you expect; check later whether it happened. Process without observed effect is process theater — cut it.

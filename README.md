# Devflow

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

The router (`skills/devflow/SKILL.md`) selects the smallest useful subset of skills per task:

- Requirements and idea shaping → brainstorming
- Specs and task plans → spec-workspace / spec-driven-development / planning-and-task-breakdown
- Test-first implementation → test-driven-development, incremental-implementation
- Debugging and root-cause analysis → systematic-debugging
- Review and refactoring → code-review-and-quality, code-simplification
- Frontend, API, security, performance, observability → domain skills
- CI, release, and shipping → git-workflow-and-versioning, ci-cd-and-automation, shipping-and-launch

Skills that depend on host capabilities (subagent dispatch, browser MCP) reference a shared fallback contract in `skills/using-devflow/SKILL.md`, so the bundle degrades gracefully on hosts without those features.

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

## Usage

Ask the assistant to use Devflow before a development task:

```text
Use devflow to plan and implement this feature.
```

The router picks the relevant skills. For example:

- New feature: brainstorming, spec, planning, TDD, incremental implementation, review
- Bug: systematic debugging, regression test, minimal fix, verification
- UI work: frontend design and UI engineering, browser testing when useful
- Shipping: git workflow, CI/CD, launch checklist, verification

## Maintenance

- Run `scripts/check-refs.sh` before committing skill changes — it validates frontmatter, cross-references, and file sizes. CI runs it on every push.
- **Bump `version` in `.claude-plugin/plugin.json` in any PR that changes skill content.** Installed plugins only receive updates when the version string changes — content changes without a version bump never reach `/plugin update` users.

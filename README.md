# Devflow

Devflow is a universal AI development workflow skill package. It is not tied to one app or runtime. Use it in any AI coding assistant that can load Markdown instructions, read a local folder, or import a skill directory. Every skill uses the cross-tool SKILL.md format (Markdown with `name`/`description` frontmatter) supported by Claude Code, Codex, and other assistants.

Devflow is intentionally packaged as a complete bundle:

- `SKILL.md` is the router and entrypoint.
- `AGENTS.md` is a condensed entrypoint for tools that read project-level agent instructions (Codex and compatible hosts).
- `skills/agent-skills/` contains engineering lifecycle skills.
- `skills/superpowers/` contains discipline and execution workflows, plus platform tool mappings under `using-superpowers/references/`.
- `skills/openspec/` contains a portable OpenSpec-style workflow.

## What It Does

Devflow routes software development work to the smallest useful workflow stack:

- Requirements and idea shaping
- Specs and task plans
- Test-first implementation
- Debugging and root-cause analysis
- Code review and refactoring
- Frontend, API, security, performance, and observability work
- CI, release, and shipping workflows

The package includes the referenced workflow files, so another user does not need to already have those skills installed separately. Skills that depend on host capabilities (subagent dispatch, browser MCP) state their fallback inline, so the bundle degrades gracefully on hosts without those features.

## Install

Clone or download this repository and keep the folder intact:

```bash
git clone https://github.com/GaoFei2025-0314/devflow.git
```

### Claude Code

Install the whole directory as one skill — place (or symlink) it at `.claude/skills/devflow/` in a project, or `~/.claude/skills/devflow/` for personal use. `SKILL.md` at the bundle root is the entrypoint; it loads the bundled files on demand.

### Codex

`AGENTS.md` at the repository root is picked up automatically when Devflow is your working folder, or copy its contents into your project's `AGENTS.md`. To let Codex trigger individual skills natively, symlink or copy skill directories into `.codex/skills/` (project) or `~/.codex/skills/` (personal), e.g.:

```bash
ln -s /path/to/devflow/skills/agent-skills/test-driven-development ~/.codex/skills/test-driven-development
```

### Other tools

Point your tool's skill, prompt, rules, or instruction loader at the repository folder with `SKILL.md` as the entrypoint. If your tool only supports plain instruction files, load `SKILL.md` first and let it reference the bundled files under `skills/`. Tool-name mappings for Copilot CLI and Gemini CLI are in `skills/superpowers/using-superpowers/references/`.

## Usage

Ask the assistant to use Devflow before a development task:

```text
Use devflow to plan and implement this feature.
```

Devflow will choose the relevant bundled files. For example:

- New feature: brainstorming, spec, planning, TDD, incremental implementation, review
- Bug: systematic debugging, regression test, minimal fix, verification
- UI work: frontend design and UI engineering, browser testing when useful
- Shipping: git workflow, CI/CD, launch checklist, verification

## Package Layout

```text
devflow/
  SKILL.md        # router / entrypoint
  AGENTS.md       # condensed entrypoint for AGENTS.md-reading hosts
  README.md
  skills/
    agent-skills/   # 19 engineering lifecycle skills
    openspec/       # portable OpenSpec-style workflow
    superpowers/    # 13 discipline & execution workflows + platform mappings
```

Each skill is a directory with a `SKILL.md` (principles and checklists) and, where useful, a `references/` folder with worked examples loaded on demand.

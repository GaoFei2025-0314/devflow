# Devflow

This repository is a self-contained AI development workflow skill bundle. The full router lives in `SKILL.md`; the skills live under `skills/`. Skill files use the cross-tool SKILL.md format (Markdown with `name`/`description` frontmatter), so they work in Codex, Claude Code, and other assistants that read Markdown instructions.

## Core rule

Pick the phase of work, then load only the bundled skill files needed for that phase. Do not load every skill by default. Before starting, state the selected stack in one short line.

## Routing summary

Read `SKILL.md` for the full routing tables. In brief:

- **New feature or significant change** → `skills/superpowers/brainstorming/` if requirements need shaping, then `skills/openspec/` (durable specs) or `skills/agent-skills/spec-driven-development/` + `skills/agent-skills/planning-and-task-breakdown/`, then `skills/agent-skills/test-driven-development/` and `skills/agent-skills/incremental-implementation/`.
- **Bug or failing test** → `skills/superpowers/systematic-debugging/`, regression test before fix, finish with `skills/superpowers/verification-before-completion/`.
- **Review, refactor, or quality pass** → `skills/agent-skills/code-review-and-quality/`, adding simplification/security/performance skills only when the request touches them.
- **UI or browser work** → `skills/agent-skills/frontend-ui-engineering/`, `skills/agent-skills/frontend-design/`, `skills/agent-skills/browser-testing-with-devtools/`.
- **Shipping or release** → `skills/agent-skills/git-workflow-and-versioning/`, `skills/agent-skills/ci-cd-and-automation/`, `skills/agent-skills/shipping-and-launch/`.

## Platform notes

Skills reference Claude Code tool names in places. Tool mappings for Codex, Copilot CLI, and Gemini CLI are in `skills/superpowers/using-superpowers/references/`. Skills that depend on subagent dispatch state an in-session fallback inline; on hosts without subagent support, use `skills/superpowers/executing-plans/` instead of `skills/superpowers/subagent-driven-development/`.

To let Codex trigger individual skills natively, symlink or copy the skill directories into `.codex/skills/` (project) or `~/.codex/skills/` (personal); see README for details.

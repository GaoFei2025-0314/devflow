# Devflow

This repository is a self-contained AI development workflow skill bundle. The router lives in `skills/devflow/SKILL.md`; all skills live flat under `skills/`. Skill files use the cross-tool SKILL.md format (Markdown with `name`/`description` frontmatter), so they work in Codex, Claude Code, and other assistants that read Markdown instructions.

## Core rule

Pick the phase of work, then load only the skill files needed for that phase. Do not load every skill by default. Before starting, state the selected stack in one short line.

## Routing summary

Read `skills/devflow/SKILL.md` for the full routing tables. In brief:

- **New feature or significant change** → `skills/brainstorming/` if requirements need shaping, then `skills/spec-workspace/` (durable specs) or `skills/spec-driven-development/` + `skills/planning-and-task-breakdown/`, then `skills/test-driven-development/` and `skills/incremental-implementation/`.
- **Bug or failing test** → `skills/systematic-debugging/`, regression test before fix, finish with `skills/verification-before-completion/`.
- **Review, refactor, or quality pass** → `skills/code-review-and-quality/`, adding simplification/security/performance skills only when the request touches them.
- **UI or browser work** → `skills/frontend-ui-engineering/`, `skills/frontend-design/`, `skills/browser-testing-with-devtools/`.
- **Shipping or release** → `skills/git-workflow-and-versioning/`, `skills/ci-cd-and-automation/`, `skills/shipping-and-launch/`.

## Platform notes

Skills reference Claude Code tool names in places. Tool mappings for Codex, Copilot CLI, and Gemini CLI — and the shared no-subagent fallback contract — are in `skills/using-devflow/SKILL.md`. On hosts without subagent support, use `skills/executing-plans/` instead of `skills/subagent-driven-development/`.

To let Codex trigger individual skills natively, symlink or copy skill directories into `.codex/skills/` (project) or `~/.codex/skills/` (personal); see README for details.

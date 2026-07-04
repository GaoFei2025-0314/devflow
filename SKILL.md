---
name: devflow
description: Coordinate AI-assisted software development across requirements, specs, planning, implementation, testing, review, debugging, QA, and shipping by selecting the smallest useful bundled workflow stack.
---

# Devflow

## Purpose

Devflow is a universal routing skill for AI-assisted software development. It works as a standalone instruction bundle in any AI tool that can read this folder.

Use Devflow when the user asks for feature work, bug fixing, refactoring, code review, UI work, API design, security hardening, performance work, CI/CD, release work, or general software development coordination.

## Core Rule

Pick the phase, then load only the bundled workflow files needed for that phase. Do not load every bundled skill by default.

Before work starts, state the selected stack in one short line:

```text
Using devflow: Superpowers TDD + Agent Skills planning + verification before completion.
```

## Bundled Workflow Contract

This package is self-contained. When a workflow is selected, read and follow the referenced file relative to this `SKILL.md`.

If the host AI app has a native skill loader, it may load these bundled folders as sub-skills. If it does not, treat each referenced `SKILL.md` or Markdown file as ordinary instructions and follow it directly.

Prefer bundled files over assuming the host environment already has the same skill installed.

## Stack Roles

| Stack | Bundled path | Use for | Avoid when |
| --- | --- | --- | --- |
| Superpowers | `skills/superpowers/` | Process discipline: brainstorming, TDD, systematic debugging, planning, subagent workflows, branch finishing, verification | The user explicitly asks for a quick answer with no process work |
| OpenSpec | `skills/openspec/SKILL.md` | Persistent change artifacts: proposal, specs, design, tasks, archive | No repo, no durable project, or a tiny one-off edit |
| Agent Skills | `skills/agent-skills/` | Engineering lifecycle work: specs, planning, implementation, UI, API, tests, review, security, performance, observability, shipping | A more specific bundled or project skill already covers the same work |
| External review | Use host tools if available | Optional expert challenge, design review, engineering review, QA, release review | Routine implementation where extra review adds ceremony |

## Routing

### New Feature or Significant Change

1. Use `skills/superpowers/brainstorming/SKILL.md` when requirements need shaping.
2. If the project has an `openspec/` workspace, the user asks for durable specs, or the change is cross-session, use `skills/openspec/SKILL.md`.
3. If OpenSpec is not used, use `skills/agent-skills/spec-driven-development/SKILL.md`, then `skills/agent-skills/planning-and-task-breakdown/SKILL.md`.
4. Use `skills/superpowers/test-driven-development/SKILL.md` or `skills/agent-skills/test-driven-development/SKILL.md` for implementation discipline.
5. Use `skills/agent-skills/incremental-implementation/SKILL.md` to deliver small verified slices.
6. Add domain skills only when needed:
   - API: `skills/agent-skills/api-and-interface-design/SKILL.md`
   - Frontend UI: `skills/agent-skills/frontend-ui-engineering/SKILL.md`
   - Frontend visual design: `skills/agent-skills/frontend-design/SKILL.md`
   - Security: `skills/agent-skills/security-and-hardening/SKILL.md`
   - Performance: `skills/agent-skills/performance-optimization/SKILL.md`
   - Observability: `skills/agent-skills/observability-and-instrumentation/SKILL.md`
7. Finish with review and verification:
   - `skills/agent-skills/code-review-and-quality/SKILL.md`
   - `skills/superpowers/verification-before-completion/SKILL.md`

### Bug or Failing Test

1. Use `skills/superpowers/systematic-debugging/SKILL.md`.
2. Pair with `skills/agent-skills/debugging-and-error-recovery/SKILL.md`.
3. Write or identify a failing regression test before fixing behavior.
4. Fix minimally, run the focused test, then run the relevant broader suite.
5. Finish with `skills/superpowers/verification-before-completion/SKILL.md`.

### Review, Refactor, or Quality Pass

1. Use `skills/agent-skills/code-review-and-quality/SKILL.md`.
2. Add `skills/agent-skills/code-simplification/SKILL.md`, `skills/agent-skills/security-and-hardening/SKILL.md`, or `skills/agent-skills/performance-optimization/SKILL.md` only when the request touches those concerns.
3. For review response workflows, use:
   - `skills/superpowers/requesting-code-review/SKILL.md`
   - `skills/superpowers/receiving-code-review/SKILL.md`
4. Do not refactor unrelated areas unless the user approves the scope.

### UI, Frontend, or Browser QA

1. Use `skills/agent-skills/frontend-ui-engineering/SKILL.md` for production UI implementation.
2. Use `skills/agent-skills/frontend-design/SKILL.md` when visual direction, layout, or interaction quality matters.
3. Use `skills/agent-skills/browser-testing-with-devtools/SKILL.md` when real browser verification is needed.
4. Finish with screenshot, runtime, or interaction evidence where the host environment supports it.

### Shipping or Release Work

1. Use `skills/agent-skills/git-workflow-and-versioning/SKILL.md`.
2. Add `skills/agent-skills/ci-cd-and-automation/SKILL.md` and `skills/agent-skills/shipping-and-launch/SKILL.md` as relevant.
3. If the change used OpenSpec, archive or update the change through `skills/openspec/SKILL.md`.
4. Use `skills/superpowers/finishing-a-development-branch/SKILL.md` for final branch hygiene when applicable.
5. Report concrete evidence: tests, build, runtime checks, rollout status, and known residual risk.

## Parallel and Multi-Agent Work

Use these only when the task is large enough to benefit from coordination:

- `skills/superpowers/subagent-driven-development/SKILL.md`
- `skills/superpowers/dispatching-parallel-agents/SKILL.md`
- `skills/superpowers/using-git-worktrees/SKILL.md`
- `skills/agent-skills/ci-cd-and-automation/SKILL.md`

## Common Mistakes

- Loading the entire bundle for every task. Pick the smallest useful subset.
- Treating OpenSpec as mandatory. Use it for durable, cross-session changes.
- Treating external review tools as mandatory. They are optional; bundled review workflows are enough for routine work.
- Skipping tests because a spec exists. Specs define intent; tests prove behavior.
- Calling work complete without evidence from tests, builds, runtime checks, or review.

## Quick Recipes

| User asks | Use |
| --- | --- |
| "Build this feature" | Brainstorming if needed, OpenSpec or spec-driven development, planning, TDD, incremental implementation, review |
| "Fix this bug" | Systematic debugging, debugging recovery, regression test, minimal fix, verification |
| "Review this PR/code" | Code review and quality, optional requesting/receiving code review workflows |
| "Improve this UI" | Frontend design, frontend UI engineering, browser testing when useful |
| "Ship this" | Git workflow, CI/CD, shipping and launch, verification, OpenSpec archive if used |

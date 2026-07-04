---
name: devflow
description: Use when coordinating AI-assisted software development across requirements, specs, planning, implementation, testing, review, debugging, QA, or shipping, especially when deciding how to combine Superpowers, OpenSpec, Agent Skills, or GStack without overloading a task.
---

# Devflow

## Overview

Devflow is a thin routing skill for choosing the right development workflow stack. Use the smallest useful combination: Superpowers for discipline, OpenSpec for persistent specs, Agent Skills for engineering lifecycle work, and GStack only for targeted expert challenge or QA when available.

## Core Rule

Do not load every framework by default. Pick the phase, then load only the sub-skills or tools needed for that phase.

Before work starts, state the selected stack in one short line:

```text
Using devflow: Superpowers TDD + OpenSpec change + Agent Skills frontend workflow. Skipping GStack because this is low-risk UI polish.
```

## Stack Roles

| Stack | Use for | Avoid when |
| --- | --- | --- |
| Superpowers | Process discipline: brainstorming, TDD, systematic debugging, verification before completion, plans, subagent workflows | The user explicitly asks for a quick answer with no process work |
| OpenSpec | Persistent change artifacts: proposal, specs, design, tasks, archive; useful across sessions and teams | No repo, no durable project, or a tiny one-off edit |
| Agent Skills | Engineering lifecycle methods: spec, planning, implementation, UI, API, tests, review, security, performance, launch | A more specific local/project skill already covers the same work |
| GStack | Optional expert challenge: product/CEO review, engineering review, design review, QA, release review | Routine implementation where extra review would add ceremony |

Use OpenSpec only when an `openspec/` workspace exists, the OpenSpec CLI/commands are available, or the user asks to adopt it. Use GStack only when installed or explicitly requested; otherwise fall back to the closest Agent Skills review or QA workflow.

## Routing

### New Feature or Significant Change

1. Use Superpowers `brainstorming` when requirements need shaping.
2. If OpenSpec is available or requested, create/update an OpenSpec change before implementation.
3. Use Agent Skills `spec-driven-development` when OpenSpec is not used, then `planning-and-task-breakdown`.
4. Use Agent Skills `incremental-implementation` plus Superpowers `test-driven-development` for code.
5. Add domain skills as needed: `frontend-ui-engineering`, `api-and-interface-design`, `security-and-hardening`, `performance-optimization`, or `observability-and-instrumentation`.
6. Use GStack plan/design/engineering review only for high-impact, ambiguous, user-facing, or architecture-heavy work.
7. Finish with code review and verification before completion.

### Bug or Failing Test

1. Use Superpowers `systematic-debugging`.
2. Pair with Agent Skills `debugging-and-error-recovery`.
3. Write or identify a failing regression test before fixing behavior.
4. Fix minimally, run the focused test, then run the relevant broader suite.
5. Use GStack `investigate` only for persistent, cross-system, or production-grade incidents.

### Review, Refactor, or Quality Pass

1. Use Agent Skills `code-review-and-quality` first.
2. Add `code-simplification`, `security-and-hardening`, or `performance-optimization` only when the change touches those concerns.
3. Use GStack `review`, design review, or QA when independent scrutiny is valuable.
4. Do not refactor unrelated areas unless the user approves the scope.

### Shipping or Release Work

1. Use Agent Skills `shipping-and-launch`, `ci-cd-and-automation`, and `git-workflow-and-versioning` as relevant.
2. Use OpenSpec archive/update steps if the change was tracked there.
3. Use GStack QA/release checks for user-facing or production deployments.
4. Report concrete evidence: tests, build, runtime checks, rollout status, and known residual risk.

## Sub-Skill Invocation

When this skill routes to another skill, load and follow that skill before acting. Prefer installed skill names exactly as exposed by the current environment, for example:

- `superpowers:test-driven-development` or local `test-driven-development`
- `superpowers:systematic-debugging`
- `spec-driven-development`
- `planning-and-task-breakdown`
- `incremental-implementation`
- `code-review-and-quality`

If a routed stack is unavailable, do not block. Say what is missing and continue with the closest installed workflow.

## Common Mistakes

- Loading Superpowers, OpenSpec, Agent Skills, and GStack for every task. This creates process drag.
- Duplicating specs in both OpenSpec and ad hoc docs. Pick one source of truth.
- Treating GStack as mandatory. It is a review layer, not the default implementation loop.
- Skipping tests because a spec exists. Specs define intent; tests prove behavior.
- Calling work complete without evidence from tests, builds, runtime checks, or review.

## Quick Recipes

| User asks | Use |
| --- | --- |
| "Build this feature" | Superpowers brainstorming if needed, OpenSpec or Agent Skills spec, plan, TDD, incremental implementation, review |
| "Fix this bug" | Superpowers systematic debugging, Agent Skills debugging, regression test, minimal fix, verification |
| "Review this PR" | Agent Skills code review, optional GStack review for high-risk changes |
| "Improve this UI" | Agent Skills frontend UI, browser testing, optional GStack design review |
| "Ship this" | Agent Skills shipping/CI/git workflow, OpenSpec archive if used, optional GStack QA |

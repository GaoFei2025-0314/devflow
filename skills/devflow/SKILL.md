---
name: devflow
description: Coordinate AI-assisted software development across requirements, specs, planning, implementation, testing, review, debugging, QA, and shipping by selecting the smallest useful workflow stack from the Devflow skill set.
---

# Devflow Router

## Purpose

Devflow is a universal routing skill for AI-assisted software development. It works as a standalone instruction bundle in any AI tool that can read this folder.

Use Devflow when the user asks for feature work, bug fixing, refactoring, code review, UI work, API design, security hardening, performance work, CI/CD, release work, or general software development coordination.

## Core Rule

Pick the phase, then load only the skill files needed for that phase. Do not load every skill by default.

Before work starts, state the selected stack in one short line:

```text
Using devflow: TDD + planning + verification before completion.
```

## Skill Contract

This package is self-contained. When a skill is selected, read and follow the referenced file relative to this `SKILL.md` — all sibling skills live one directory up (e.g. `../test-driven-development/SKILL.md`).

If the host has a native skill loader, these directories load as individual skills. If it does not, treat each referenced `SKILL.md` as ordinary instructions and follow it directly. Prefer bundled files over assuming the host already has an equivalent skill installed.

**Platform adaptation:** Skills reference Claude Code tool names in places. Tool mappings for Codex, Copilot CLI, and Gemini CLI — and the shared no-subagent fallback contract — live in `../using-devflow/SKILL.md`.

**Human-in-the-loop:** Irreversible, outward-facing, or security-sensitive actions require explicit user approval before execution, on every route including the fast path — the canonical gate list is the Human-in-the-Loop Contract in `../using-devflow/SKILL.md`.

## Skill Categories

| Category | Skills | Use for | Avoid when |
| --- | --- | --- | --- |
| Process discipline | brainstorming, writing-plans, executing-plans, subagent-driven-development, systematic-debugging, test-driven-development, verification-before-completion, requesting/receiving-code-review, using-git-worktrees, finishing-a-development-branch | How to approach the work: shaping, planning, discipline, verification | The user explicitly asks for a quick answer with no process work |
| Engineering lifecycle | spec-driven-development, planning-and-task-breakdown, incremental-implementation, api-and-interface-design, frontend-*, security-and-hardening, performance-optimization, observability-and-instrumentation, ci-cd-and-automation, git-workflow-and-versioning, shipping-and-launch, documentation-and-adrs, deprecation-and-migration, source-driven-development, code-review-and-quality, code-simplification, browser-testing-with-devtools | Domain guidance for the artifact being built | A more specific project skill already covers the same work |
| Durable specs | spec-workspace | Persistent change artifacts: proposal, specs, design, tasks, archive | No repo, no durable project, or a tiny one-off edit |

## Routing

### Fast Path (small, low-risk changes)

Check this route first. A change qualifies when ALL three hold: **(a) small** — one file or a few adjacent lines; **(b) low-risk** — no auth, payment, migration, public-API, or security surface; **(c) clear** — the cause and the fix are already understood. Then skip the full routes:

1. If behavior changes, write or update the focused test first (reproduction test for bugs).
2. Make the minimal change.
3. Run the focused test, then the relevant broader suite and build.
4. Close with the Verification checklist in `../test-driven-development/SKILL.md`.

Announce it: `Using devflow: fast path.`

**Escalate to the full route** the moment any condition stops holding: the fix spreads to a second subsystem, the root cause turns out unclear (→ Bug route), or the change grows a contract or security surface (→ New Feature route, steps 7-8). The fast path is a smaller stack, not a lower standard — the test and verification steps are not optional.

### New Feature or Significant Change

1. Use `../brainstorming/SKILL.md` when requirements need shaping. Its design doc feeds the next step — do not re-derive requirements that the approved design already answers.
2. If the project has a change workspace (`specs/` or legacy `openspec/`), the user asks for durable specs, or the change is cross-session, use `../spec-workspace/SKILL.md`.
3. If no change workspace is used and no approved design doc exists, use `../spec-driven-development/SKILL.md`; then `../planning-and-task-breakdown/SKILL.md`.
4. **Choose the execution mode** once the plan exists — this step is not optional:
   - Plan tasks are mostly independent AND the host supports subagents → execute with `../subagent-driven-development/SKILL.md` (fresh subagent per task, two-stage review between tasks; it replaces steps 5-6 below and brings its own review checkpoints).
   - Otherwise → execute in-session with steps 5-6.
5. Use `../test-driven-development/SKILL.md` for implementation discipline.
6. Use `../incremental-implementation/SKILL.md` to deliver small verified slices.
7. Add domain skills only when needed:
   - API: `../api-and-interface-design/SKILL.md`
   - Frontend UI: `../frontend-ui-engineering/SKILL.md`
   - Frontend visual design: `../frontend-design/SKILL.md`
   - Security: `../security-and-hardening/SKILL.md`
   - Performance: `../performance-optimization/SKILL.md`
   - Observability: `../observability-and-instrumentation/SKILL.md`
8. Finish with review and verification:
   - `../code-review-and-quality/SKILL.md`
   - `../verification-before-completion/SKILL.md`

### Bug or Failing Test

1. Use `../systematic-debugging/SKILL.md` (triage decision trees in `../systematic-debugging/error-triage.md`).
2. Write or identify a failing regression test before fixing behavior.
3. Fix minimally, run the focused test, then run the relevant broader suite.
4. Finish with `../verification-before-completion/SKILL.md`.

### Review, Refactor, or Quality Pass

1. Use `../code-review-and-quality/SKILL.md` — this is the review standard (what to check, when to approve).
2. Add `../code-simplification/SKILL.md`, `../security-and-hardening/SKILL.md`, or `../performance-optimization/SKILL.md` only when the request touches those concerns.
3. Workflow wrappers, only when the situation calls for them:
   - Requesting a review with crafted context: `../requesting-code-review/SKILL.md`
   - Responding to review feedback you received: `../receiving-code-review/SKILL.md`
4. Do not refactor unrelated areas unless the user approves the scope.

### UI, Frontend, or Browser QA

1. Use `../frontend-ui-engineering/SKILL.md` for production UI implementation.
2. Use `../frontend-design/SKILL.md` when visual direction, layout, or interaction quality matters.
3. Use `../browser-testing-with-devtools/SKILL.md` when real browser verification is needed.
4. Finish with screenshot, runtime, or interaction evidence where the host environment supports it.

### Shipping or Release Work

1. Use `../git-workflow-and-versioning/SKILL.md`.
2. Add `../ci-cd-and-automation/SKILL.md` and `../shipping-and-launch/SKILL.md` as relevant.
3. If the change used a spec workspace, archive or update the change through `../spec-workspace/SKILL.md`.
4. Use `../finishing-a-development-branch/SKILL.md` for final branch hygiene when applicable.
5. Report concrete evidence: tests, build, runtime checks, rollout status, and known residual risk.

## Parallel and Multi-Agent Work

Requires a host with subagent support (fallback contract in `../using-devflow/SKILL.md`):

- `../subagent-driven-development/SKILL.md` — the default execution mode for plans with mostly independent tasks (see step 4 of the New Feature route); dispatches one implementer subagent per task, sequentially, with reviews between
- `../dispatching-parallel-agents/SKILL.md` — parallel dispatch, for 2+ *independent investigations* only (unrelated failures/subsystems), never for implementation tasks that could touch the same files
- `../using-git-worktrees/SKILL.md` — isolated workspaces when parallel streams need separate checkouts

## Common Mistakes

- Loading the entire bundle for every task. Pick the smallest useful subset.
- Running a full route for a typo-class change — that's what the Fast Path is for.
- Stretching the Fast Path over changes with auth, data, API, or multi-file surface — those take the full route.
- Treating the spec workspace as mandatory. Use it for durable, cross-session changes.
- Running spec-driven-development after brainstorming already produced an approved design — that re-derives the same content twice.
- Skipping tests because a spec exists. Specs define intent; tests prove behavior.
- Calling work complete without evidence from tests, builds, runtime checks, or review.

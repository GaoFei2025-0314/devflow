---
name: planning-and-task-breakdown
description: Breaks work into ordered tasks. Use when you have a spec or clear requirements and need implementable tasks, when a task feels too large to start, or when parallel work needs coordination. Not for shaping unclear requirements — use brainstorming or spec-driven-development first.
---

# Planning and Task Breakdown

## Overview

Decompose work into small, verifiable tasks with explicit acceptance criteria. Good task breakdown is the difference between an agent that completes work reliably and one that produces a tangled mess. Every task should be small enough to implement, test, and verify in a single focused session.

**Boundary:** This skill produces an acceptance-oriented task breakdown from a spec or clear requirements. When an executor will have little or no surrounding context, use the detailed handoff guidance in `../writing-plans/SKILL.md` to expand the tasks that need it. These are two uses of one planning artifact, not a requirement to create duplicate plans: a plan may lead with a compact acceptance table and add detailed steps only where they make execution safer.

Apply the shared [Phase and Delivery Contract](../using-devflow/references/phase-contract.md), [Authorization and Trust Contract](../using-devflow/references/authorization-contract.md), [Evidence Contract](../using-devflow/references/evidence-contract.md), and [Delivery Contract](../using-devflow/references/delivery-contract.md). Planning organizes later work; it does not authorize implementation, Git actions, installation, or external delivery.

## When to Use

- You have a spec and need to break it into implementable units
- A task feels too large or vague to start
- Work needs to be parallelized across multiple agents or sessions
- You need to communicate scope to a human
- The implementation order isn't obvious

**When NOT to use:** Single-file changes with obvious scope, or when the spec already contains well-defined tasks.

## The Planning Process

### Step 1: Enter Plan Mode

Before writing any code, operate in read-only mode:

- Read the spec and relevant codebase sections
- Identify existing patterns and conventions
- Map dependencies between components
- Note risks and unknowns

**Do NOT write code during planning.** The output is a plan document, not implementation.

Reuse still-valid requirements, accepted designs, prior decisions, and project facts. Do not restart discovery or ask the user to approve a decision already established. Clarify only a new conflict or missing fact that materially changes the plan; derive routine choices from the available context.

### Step 2: Identify the Dependency Graph

Map what depends on what:

```
Database schema
    │
    ├── API models/types
    │       │
    │       ├── API endpoints
    │       │       │
    │       │       └── Frontend API client
    │       │               │
    │       │               └── UI components
    │       │
    │       └── Validation logic
    │
    └── Seed data / migrations
```

Implementation order follows the dependency graph bottom-up: build foundations first.

### Step 3: Slice Vertically

Instead of building all the database, then all the API, then all the UI — build one complete feature path at a time:

**Bad (horizontal slicing):**
```
Task 1: Build entire database schema
Task 2: Build all API endpoints
Task 3: Build all UI components
Task 4: Connect everything
```

**Good (vertical slicing):**
```
Task 1: User can create an account (schema + API + UI for registration)
Task 2: User can log in (auth schema + API + UI for login)
Task 3: User can create a task (task schema + API + UI for creation)
Task 4: User can view task list (query + API + UI for list view)
```

Each vertical slice delivers working, testable functionality.

### Step 4: Write Tasks

Start with an acceptance task table so a reviewer can assess scope and ordering quickly:

```markdown
| Task | Outcome | Dependencies | File scope | Proof | Complete when |
| --- | --- | --- | --- | --- | --- |
| 1. [Title] | [Observable result] | None | `src/path/to/file.ts`, `tests/path/to/test.ts` | `[focused command]`; [review or observation] | [Result exists and named evidence passes] |
```

Expand a row with the following structure when its acceptance criteria, risk, or handoff context needs more detail:

```markdown
## Task [N]: [Short descriptive title]

**Description:** One paragraph explaining what this task accomplishes.

**Dependencies:** [Task numbers, external inputs, or authorizations required before this task; use "None" when independent]

**File scope:**
- Create: `src/path/to/new-file.ts`
- Modify: `src/path/to/existing-file.ts`
- Test: `tests/path/to/test.ts`

**Acceptance criteria:**
- [ ] [Specific, testable condition]
- [ ] [Specific, testable condition]

**Proof:**
- [ ] Tests pass: `npm test -- --grep "feature-name"`
- [ ] Build succeeds: `npm run build`
- [ ] Manual check: [description of what to verify]

**Completion condition:** [The observable state and evidence that make this task complete]

**Estimated scope:** [Small: 1-2 files | Medium: 3-5 files | Large: 5+ files]
```

Use exact known paths. If discovery is itself required, bound it to a named directory, interface, or preceding discovery task and state which later tasks depend on its result. Proof must name the check, review, or observation that demonstrates the acceptance criteria; a command is useful only when it is known and applicable.

### Step 4a: Localize Unknowns

Record each unresolved item beside the task and dependency it affects:

```markdown
**Blocked dependency:** Task 4 needs the provider's retry contract before its public error behavior can be finalized. Tasks 1-3 and 5 do not depend on that choice.
**Resolution:** Inspect `docs/path/to/provider-contract.md`; if it is absent or contradictory, ask one focused question describing the affected behavior.
```

Continue planning independent tasks. Do not invent a high-impact product, security, data, cost, or compatibility decision to remove a blocker, and do not stop the whole plan for an unknown that affects only one branch. Complete safe investigation and prepare the concrete options before asking for a necessary decision.

### Step 5: Order and Checkpoint

Arrange tasks so that:

1. Dependencies are satisfied (build foundation first)
2. Each task leaves the system in a working state
3. Verification checkpoints occur after every 2-3 tasks
4. High-risk tasks are early (fail fast)

Add explicit checkpoints:

```markdown
## Checkpoint: After Tasks 1-3
- [ ] All tests pass
- [ ] Application builds without errors
- [ ] Core user flow works end-to-end
- [ ] If project policy, a grant condition, required acceptance, or an unresolved material decision requires human review, record it before the dependent task; otherwise record the evidence and continue authorized independent work
```

A checkpoint records evidence and exposes real gates. It does not create a human-approval gate by itself. Reuse applicable authorization and continue independent tasks unless a named dependency, required acceptance, or authorization condition blocks them.

## Task Sizing Guidelines

| Size | Files | Scope | Example |
|------|-------|-------|---------|
| **XS** | 1 | Single function or config change | Add a validation rule |
| **S** | 1-2 | One component or endpoint | Add a new API endpoint |
| **M** | 3-5 | One feature slice | User registration flow |
| **L** | 5-8 | Multi-component feature | Search with filtering and pagination |
| **XL** | 8+ | **Too large — break it down further** | — |

If a task is L or larger, it should be broken into smaller tasks. An agent performs best on S and M tasks.

**When to break a task down further:**
- It would take more than one focused session (roughly 2+ hours of agent work)
- You cannot describe the acceptance criteria in 3 or fewer bullet points
- It touches two or more independent subsystems (e.g., auth and billing)
- You find yourself writing "and" in the task title (a sign it is two tasks)

## Plan Document Template

```markdown
# Implementation Plan: [Feature/Project Name]

## Overview
[One paragraph summary of what we're building]

## Architecture Decisions
- [Key decision 1 and rationale]
- [Key decision 2 and rationale]

## Task List

| Task | Outcome | Dependencies | File scope | Proof | Complete when |
| --- | --- | --- | --- | --- | --- |
| 1 | ... | None | `path/to/file` | `focused check` | ... |

### Phase 1: Foundation
- [ ] Task 1: ...
- [ ] Task 2: ...

### Checkpoint: Foundation
- [ ] Tests pass, builds clean

### Phase 2: Core Features
- [ ] Task 3: ...
- [ ] Task 4: ...

### Checkpoint: Core Features
- [ ] End-to-end flow works

### Phase 3: Polish
- [ ] Task 5: ...
- [ ] Task 6: ...

### Checkpoint: Complete
- [ ] All acceptance criteria met
- [ ] Ready for review

## Risks and Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| [Risk] | [High/Med/Low] | [Strategy] |

## Open Questions
- [Question needing human input]
```

## Parallelization Opportunities

When multiple agents or sessions are available:

- **Safe to parallelize:** Independent feature slices, tests for already-implemented features, documentation
- **Must be sequential:** Database migrations, shared state changes, dependency chains
- **Needs coordination:** Features that share an API contract (define the contract first, then parallelize)

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I'll figure it out as I go" | That's how you end up with a tangled mess and rework. 10 minutes of planning saves hours. |
| "The tasks are obvious" | Write them down anyway. Explicit tasks surface hidden dependencies and forgotten edge cases. |
| "Planning is overhead" | Planning is the task. Implementation without a plan is just typing. |
| "I can hold it all in my head" | Context windows are finite. Written plans survive session boundaries and compaction. |

## Red Flags

- Starting implementation without a written task list
- Tasks that say "implement the feature" without acceptance criteria
- No verification steps in the plan
- All tasks are XL-sized
- No checkpoints between tasks
- Dependency order isn't considered

## Verification

Before starting implementation, confirm:

- [ ] Every task has acceptance criteria
- [ ] Every task identifies dependencies, file scope, proof, and a completion condition
- [ ] Task dependencies are identified and ordered correctly
- [ ] No task touches more than ~5 files
- [ ] Checkpoints exist between major phases
- [ ] Still-valid requirements and accepted decisions were reused
- [ ] Unknowns are attached only to the tasks they block
- [ ] The plan states its draft/review status and whether implementation has begun

## Plan Delivery and Execution Handoff

If the user requested only analysis, a Spec, a design, or a plan, stop when the requested conversation result or local plan is reviewable. Mark the artifact as draft or reviewed and state that implementation has not begun. One document may contain the problem, goals, requirements, acceptance, risks, task table, and any needed detailed handoff. Do not create or switch branches, create worktrees, commit, push, open a pull request, or implement merely because a template mentions those actions.

When later execution is in scope, record the appropriate execution mode so the handoff is usable:

**1. Subagent-Driven** (requires host subagent support; tasks mostly independent) — execute with `../subagent-driven-development/SKILL.md`: a fresh subagent per task, sequentially, with two-stage review between tasks. Prefer this when available; fresh context per task and enforced review checkpoints produce noticeably higher quality. **Context warning:** a task list is lighter than what a zero-context subagent needs — before dispatching each task, include the relevant spec excerpts and file context in the dispatch prompt. If that context can't be assembled per task, upgrade the plan with `../writing-plans/SKILL.md` (self-contained steps) before dispatching.

**2. In-Session** — execute the tasks yourself, one at a time, following `../test-driven-development/SKILL.md` and `../incremental-implementation/SKILL.md`.

**3. Separate Session** — hand the plan to a later session via `../executing-plans/SKILL.md`.

Choose the mode from task dependencies and host capabilities; ask only if the choice requires a material user decision. Record the choice separately from authorization. Selecting, recommending, or announcing a mode does not mean execution starts now. Begin implementation only when the current request or another effective grant authorizes that action, target, environment, and scope. Reuse a still-valid implementation grant instead of asking again; otherwise deliver the plan and identify implementation as the concrete pending action. If the host lacks subagents, use the fallback contract in `../using-devflow/SKILL.md` when execution is authorized.

For a handoff that must survive a new session or context compaction, preserve the objective and deliverable, current phase, bounded scope and authorization source, selected skills, relevant evidence, unfinished items, and localized blockers. On resume, reconcile new user instructions and changed project rules or state, rereading only lost or changed material. Do not restart requirements discovery solely because context was compacted.

## See Also

Acceptance criteria are per-task and answer "did we build the right thing?". They sit on top of the project-wide Definition of Done, the standing bar every task clears before it counts as done. See `../incremental-implementation/references/definition-of-done.md`.

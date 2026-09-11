---
name: incremental-implementation
description: Delivers changes as small verified slices. Use when a task feels too big to complete in one step, when you're about to write a large amount of code at once, or when a plan's tasks need sequencing into independently reviewable increments. Not for single-file edits or changes already small enough to verify in one pass.
---

# Incremental Implementation

## Overview

Build in thin vertical slices — implement one piece, test it, verify it, then expand. Avoid implementing an entire feature in one pass. Each increment should leave the system in a working, testable state. This is the execution discipline that makes large features manageable.

Apply the shared [Phase and Delivery Contract](../using-devflow/references/phase-contract.md) to identify the current deliverable and legal stopping state, the [Authorization and Trust Contract](../using-devflow/references/authorization-contract.md) before state-changing actions, the [Evidence Contract](../using-devflow/references/evidence-contract.md) when selecting or reusing checks, and the [Delivery Contract](../using-devflow/references/delivery-contract.md) before commits or outward delivery. An increment is an internal execution boundary, not a new phase, approval boundary, or delivery event.

## When to Use

- Implementing any multi-file change
- Building a new feature from a task breakdown
- Refactoring existing code
- Any time you're tempted to write more than ~100 lines before testing

**When NOT to use:** Single-file, single-function changes where the scope is already minimal.

## The Increment Cycle

```
┌──────────────────────────────────────┐
│                                      │
│   Implement ──→ Test ──→ Verify ──┐  │
│       ▲                           │  │
│       └──── Checkpoint ◄──────────┘  │
│              │                       │
│              ▼                       │
│       Save checkpoint                │
│              │                       │
│              ▼                       │
│          Next slice                  │
│                                      │
└──────────────────────────────────────┘
```

For each slice:

1. **Implement** the smallest complete piece of functionality
2. **Check** — select or reuse the focused test, content check, or other evidence appropriate to the changed behavior or artifact
3. **Verify** — satisfy applicable broader, build, runtime, manual, and mandatory project gates under the Evidence Contract
4. **Save a checkpoint** — preserve a reviewable state; commit only when the project's policy and applicable authorization call for it (see `git-workflow-and-versioning` for atomic commit guidance)
5. **Move to the next slice** — carry forward, don't restart

Continue all authorized slices in dependency order until the current work package reaches a legal terminal state. If one slice needs information, authorization, or a dependency, name the affected branch and keep independent authorized slices moving. Answer a progress or explanation question briefly, then resume the active objective unless the user cancels or replaces it. Reuse approved requirements and decisions while they remain applicable; clarify only a new conflict or consequential gap.

## Slicing Strategies

### Vertical Slices (Preferred)

Build one complete path through the stack:

```
Slice 1: Create a task (DB + API + basic UI)
    → Tests pass, user can create a task via the UI

Slice 2: List tasks (query + API + UI)
    → Tests pass, user can see their tasks

Slice 3: Edit a task (update + API + UI)
    → Tests pass, user can modify tasks

Slice 4: Delete a task (delete + API + UI + confirmation)
    → Tests pass, full CRUD complete
```

Each slice delivers working end-to-end functionality.

### Contract-First Slicing

When backend and frontend need to develop in parallel:

```
Slice 0: Define the API contract (types, interfaces, OpenAPI spec)
Slice 1a: Implement backend against the contract + API tests
Slice 1b: Implement frontend against mock data matching the contract
Slice 2: Integrate and test end-to-end
```

### Risk-First Slicing

Tackle the riskiest or most uncertain piece first:

```
Slice 1: Prove the WebSocket connection works (highest risk)
Slice 2: Build real-time task updates on the proven connection
Slice 3: Add offline support and reconnection
```

If Slice 1 fails, you discover it before investing in Slices 2 and 3.

## Implementation Rules

### Rule 0: Simplicity First

Before writing any code, ask: "What is the simplest thing that could work?"

After writing code, review it against these checks:
- Can this be done in fewer lines?
- Are these abstractions earning their complexity?
- Would a staff engineer look at this and say "why didn't you just..."?
- Am I building for hypothetical future requirements, or the current task?

```
SIMPLICITY CHECK:
✗ Generic EventBus with middleware pipeline for one notification
✓ Simple function call

✗ Abstract factory pattern for two similar components
✓ Two straightforward components with shared utilities

✗ Config-driven form builder for three forms
✓ Three form components
```

Three similar lines of code is better than a premature abstraction. Implement the naive, obviously-correct version first. Optimize only after correctness is proven with tests.

### Rule 0.5: Scope Discipline

Touch only what the task requires.

Do NOT:
- "Clean up" code adjacent to your change
- Refactor imports in files you're not modifying
- Remove comments you don't fully understand
- Add features not in the spec because they "seem useful"
- Modernize syntax in files you're only reading

If you notice something worth improving outside your task scope, note it — don't fix it:

```
NOTICED BUT NOT TOUCHING:
- src/utils/format.ts has an unused import (unrelated to this task)
- The auth middleware could use better error messages (separate task)
→ Want me to create tasks for these?
```

### Rule 1: One Logical Thing per Slice

Each increment changes one logical thing. Dependency order does not require serializing unrelated work: another independent slice may proceed while one branch is blocked. Don't mix concerns within a slice:

**Bad:** One commit that adds a new component, refactors an existing one, and updates the build config.

**Good:** Three separate logical slices, with separate commits only when project policy calls for them.

### Rule 2: Keep It Compilable

After each increment, the project must remain usable for the next slice. Run the build and existing tests when the increment can affect them, and do not knowingly carry an affected failure forward.

### Rule 3: Feature Flags for Incomplete Features

If a feature isn't ready for users but the project's authorized workflow integrates incomplete increments:

```typescript
// Feature flag for work-in-progress
const ENABLE_TASK_SHARING = process.env.FEATURE_TASK_SHARING === 'true';

if (ENABLE_TASK_SHARING) {
  // New sharing UI
}
```

This can keep incomplete behavior hidden while the authorized integration workflow proceeds. A feature flag does not authorize a commit, merge, deployment, or early pull request.

### Rule 4: Safe Defaults

New code should default to safe, conservative behavior:

```typescript
// Safe: disabled by default, opt-in
export function createTask(data: TaskInput, options?: { notify?: boolean }) {
  const shouldNotify = options?.notify ?? false;
  // ...
}
```

### Rule 5: Rollback-Friendly

Each increment should be independently revertable:

- Additive changes (new files, new functions) are easy to revert
- Modifications to existing code should be minimal and focused
- Database migrations should have corresponding rollback migrations
- Avoid deleting something in one commit and replacing it in the same commit — separate them

### Rule 6: Reuse Authorization and Evidence

Before changing state, bind the action to the authorization record required by the shared Authorization and Trust Contract. Reuse a still-valid grant when its action, target and environment, scope, source, and conditions continue to match; a new turn, skill, agent, or increment does not require another request. If a grant no longer covers one action, pause only that action and complete safe independent preparation first.

Treat successful verification as evidence about a recorded object and relevant state. Reuse it when it still covers the claim and no relevant code, uncommitted or participating untracked input, dependency, lockfile, configuration, data, environment, or external state has changed. A message or commit alone neither invalidates evidence nor proves that state stayed unchanged. After a relevant change, rerun only the affected checks plus any mandatory delivery-boundary gate.

### Rule 7: Keep Internal Slices Internal

An increment may be independently reviewable or revertable without being independently delivered. Do not push, open an early or draft pull request, merge, deploy, release, install, or clean up merely because one slice is green. Evaluate those steps against the whole current work package and the project's delivery policy. A user-requested delivery exception still requires authorization for that exact action.

## Working with Agents

When directing an agent to implement incrementally:

```
"Let's implement Task 3 from the plan.

Start with just the database schema change and the API endpoint.
Don't touch the UI yet — we'll do that in the next increment.

After implementing, run the project's focused tests and relevant build to verify
nothing is broken."
```

Be explicit about what's in scope and what's NOT in scope for each increment.

## Increment Checklist

After each increment, verify the items applicable to its impact and project gates:

- [ ] The change does one thing and does it completely
- [ ] Focused tests or content checks cover the changed behavior or artifact
- [ ] The relevant broader suite, build, type check, and lint pass when the slice can affect them
- [ ] The new functionality works as expected
- [ ] The checkpoint is reviewable, and any commit required by project policy is scoped and authorized

Record the object, command or observation, result, provenance, and material coverage limit. Run each verification command after a change that could affect it. Reuse a valid prior result when relevant state is unchanged; do not rerun solely because a message, commit, handoff, or status report occurred.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I'll test it all at the end" | Bugs compound. A bug in Slice 1 makes Slices 2-5 wrong. Test each slice. |
| "It's faster to do it all at once" | It *feels* faster until something breaks and you can't find which of 500 changed lines caused it. |
| "These changes are too small to checkpoint separately" | Small reviewable checkpoints expose regressions earlier. Commit boundaries still follow project policy. |
| "I'll add the feature flag later" | If the feature isn't complete, it shouldn't be user-visible. Add the flag now. |
| "This refactor is small enough to include" | Refactors mixed with features make both harder to review and debug. Separate them. |
| "Let me run the build command again just to be sure" | Reuse a valid result while relevant state and required gates are unchanged. Rerun when a relevant input changes, a new failure or uncertainty appears, or an explicit gate requires it. |

## Red Flags

- More than 100 lines of code written without running tests
- Multiple unrelated changes in a single increment
- "Let me just quickly add this too" scope expansion
- Skipping the test/verify step to move faster
- Build or tests broken between increments
- Large uncommitted changes accumulating
- Building abstractions before the third use case demands it
- Touching files outside the task scope "while I'm here"
- Creating new utility files for one-time operations
- Repeating a build or test without a relevant-state change, new observation, or required gate that could affect its evidentiary value

## Verification

After completing all increments for the current work package:

- [ ] Every explicit deliverable and acceptance obligation is reconciled as completed, already supported by valid evidence, accepted as deferred, or still pending
- [ ] Required focused and broader checks have valid results for the current relevant state
- [ ] Required review and runtime or human acceptance are complete, pending, or explicitly deferred without being mislabeled as passed
- [ ] Open, failed, and deferred obligations remain visible with their reason and effect on package status
- [ ] Any commit or later delivery step is evaluated separately under project policy and the shared Delivery Contract

Use the completion language for the current deliverable: implementation complete, automated checks passed, human acceptance pending, specific authorization pending, or final delivery. One completed increment is progress while required package obligations remain. Do not create a second mandatory status record when an existing plan, task state, or evidence artifact already carries the needed information.

## See Also

Per-increment verification is the local check. Before declaring the current deliverable complete, apply the project-adapted Definition of Done as the final gate. See `references/definition-of-done.md`.

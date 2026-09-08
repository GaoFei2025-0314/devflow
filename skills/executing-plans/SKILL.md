---
name: executing-plans
description: Execute a written implementation plan directly in the current session with review checkpoints, including as the fallback when the host lacks subagent support.
---

# Executing Plans

## Overview

Load an approved plan, execute the authorized work in dependency order, and report the current work-package state with valid evidence.

This skill is the in-session execution entry for a written plan and the fallback when the host lacks subagent support. It remains distinct from subagent-driven execution while sharing the same [Phase and Delivery Contract](../using-devflow/references/phase-contract.md), [Authorization and Trust Contract](../using-devflow/references/authorization-contract.md), [Evidence Contract](../using-devflow/references/evidence-contract.md), [Delivery Contract](../using-devflow/references/delivery-contract.md), and project task status. Do not maintain a separate approval list here.

**Announce at start:** "I'm using the executing-plans skill to implement this plan."

Use this mode when the plan is being executed directly in the current session, including the no-subagent fallback defined in `../using-devflow/SKILL.md`. When the selected and authorized mode is subagent-driven, use `../subagent-driven-development/SKILL.md`; both modes converge on the same work-package completion rules.

## The Process

### Step 1: Establish the Execution State

1. Read the plan and the accepted requirements and decisions it references.
2. Derive the current phase, requested deliverable, bounded scope, effective authorization, dependencies, required checks, and legal end condition from the shared contracts and project policy.
3. Reuse applicable approved requirements, user answers, and decisions. Ask only about a new conflict or consequential gap, explaining which task depends on it and how the answer changes the result.
4. Reconcile the plan with the existing project task state. Update the host's normal task tracker when useful; do not create a second mandatory record solely for this skill.

Approved requirements settle scope; do not restart brainstorming or request permission that an unchanged effective grant already supplies. A plan alone does not grant implementation, but a separate matching implementation grant should be reused.

### Step 2: Execute Tasks

Choose ready tasks by dependency and authorization, then:

1. Mark the selected task in progress in the existing task state when one exists.
2. Follow the accepted plan and resolve routine implementation choices from established requirements and project conventions.
3. Use `../incremental-implementation/SKILL.md` when the task benefits from verified slices.
4. Run or reuse proportionate verification under the Evidence Contract. Record the checked object, operation, result, provenance, and material limit; a subagent report or static check proves only its actual scope.
5. Reconcile every obligation in the task before marking it complete. Preserve required open or accepted deferred items and their effect on the work package.

Continue all authorized tasks until the work package reaches a legal terminal state. If one task needs information, authorization, a dependency, or investigation of a failed check, pause only it and dependent tasks; keep independent authorized work moving. If the user asks for progress or an explanation, answer briefly and resume the active objective unless they explicitly cancel or replace it.

Reuse successful evidence while its recorded object and relevant tracked, uncommitted and participating untracked inputs, dependencies, lockfiles, configuration, data, environment, and external state still support the claim. Do not rerun solely because a message, commit, context window, or execution mode changed. When relevant state changes or a new failure appears, refresh the affected evidence and any explicit delivery-boundary gate, preserving failures and justified retries.

When the work includes review feedback, verify each finding against the current artifact before changing it. Address supported findings, record rejected or already-resolved findings with evidence, and localize any unclear item to the tasks that depend on its meaning. When independent review is unavailable, perform an explicit fresh-pass self-review and report it as self-review rather than independent review.

### Step 3: Complete Development

After the current work package's tasks are reconciled:

1. Apply `../incremental-implementation/references/definition-of-done.md` to the current deliverable and required evidence.
2. Report exact completed scope, valid checks and reviews, required unfinished or accepted deferred work, manual status, and the concrete pending action.
3. Use `../finishing-a-development-branch/SKILL.md` only when branch completion or Git delivery is part of the current requested phase. Follow the Delivery Contract and project policy for commit, push, pull request, merge, deployment, installation, and cleanup authorization.

Completing one internal task or increment is a progress state, not completion of an unfinished work package. Do not open an early or draft pull request merely to report progress; evaluate PR timing against the whole package and the project's policy.

## Handling Blockers and Questions

Ask for help only when a consequential missing choice, dependency, or authorization blocks the affected work after safe investigation and concrete preparation are complete. Do not guess a high-impact decision. A failed mandatory check blocks the conclusion or action that depends on it; diagnose the failure, preserve its evidence, and retry only for a stated reason.

Block the whole execution only when no authorized independent task can still advance. Otherwise report the localized dependency in project task state and continue ready work.

## When to Revisit Earlier Steps

**Return to Review (Step 1) when:**
- Partner updates the plan based on your feedback
- Fundamental approach needs rethinking

Do not force the affected branch through a blocker; prepare a focused question and continue any independent authorized work first.

## Remember
- Review the plan against accepted requirements without re-deriving settled scope
- Follow dependencies and continue authorized independent work
- Use valid, proportionate evidence and preserve failed attempts
- Reconcile the whole current deliverable before claiming completion
- Apply shared authorization and delivery rules at each action boundary

## Integration

**Related workflow skills:**
- **writing-plans** (`../writing-plans/SKILL.md`) - Creates a self-contained plan when one does not already exist
- **incremental-implementation** (`../incremental-implementation/SKILL.md`) - Executes larger tasks as verified slices
- **using-git-worktrees** (`../using-git-worktrees/SKILL.md`) - Sets up isolation when the selected project workflow requires it
- **finishing-a-development-branch** (`../finishing-a-development-branch/SKILL.md`) - Handles branch completion when it is part of the current requested delivery phase

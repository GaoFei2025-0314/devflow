---
name: writing-plans
description: Use when you have a spec or requirements for a multi-step task, before touching code
---

# Writing Plans

## Overview

Write self-contained implementation plans for an engineer or agent who may have zero context for the codebase. Include the decisions, file scope, dependencies, proof, and completion conditions needed to execute each task without reconstructing the planning conversation. Add code excerpts when an exact interface, algorithm, fixture, or edit shape is necessary; do not mechanically reproduce complete implementations that the executor can safely derive from the repository and accepted design. DRY. YAGNI. TDD where behavior changes.

**Boundary:** This skill expands a plan for a zero-context handoff. `../planning-and-task-breakdown/SKILL.md` supplies the acceptance-oriented task view. A single plan may contain both: keep the acceptance table compact, then expand only the tasks whose executor needs detailed steps, commands, decisions, or context. Do not require a second plan merely to change presentation depth.

Apply the shared [Phase and Delivery Contract](../using-devflow/references/phase-contract.md), [Authorization and Trust Contract](../using-devflow/references/authorization-contract.md), [Evidence Contract](../using-devflow/references/evidence-contract.md), and [Delivery Contract](../using-devflow/references/delivery-contract.md). Planning produces a reviewable artifact; it does not grant implementation, Git, installation, or external-delivery authority.

Assume they are a skilled developer, but know almost nothing about our toolset or problem domain. Assume they don't know good test design very well.

**Announce at start:** "I'm using the writing-plans skill to create the implementation plan."

**Context:** Read the approved Spec or requirements, the relevant repository areas, and still-valid decisions. Use the current authorized workspace for planning. Create or switch a worktree only when the user or applicable project policy separately requires and authorizes that action.

**Save plans to:** `docs/devflow/plans/YYYY-MM-DD-<feature-name>.md`
- (User preferences for plan location override this default)

For a document-only request, mark the plan as draft or reviewed and state that implementation has not begun. Delivering the requested local plan is a valid endpoint; do not create a branch, worktree, commit, push, pull request, or implementation to complete it.

## Scope Check

If the spec covers multiple independent subsystems, identify their boundaries and dependency order. Split them into separate plans only when independent review or delivery makes that clearer, or when the user requests it. Otherwise keep one plan with distinct phases or task groups so the requested result remains a single reviewable document. Each independently executable group should produce working, testable software on its own.

## File Structure

Before defining tasks, map out which files will be created or modified and what each one is responsible for. This is where decomposition decisions get locked in.

- Design units with clear boundaries and well-defined interfaces. Each file should have one clear responsibility.
- You reason best about code you can hold in context at once, and your edits are more reliable when files are focused. Prefer smaller, focused files over large ones that do too much.
- Files that change together should live together. Split by responsibility, not by technical layer.
- In existing codebases, follow established patterns. If the codebase uses large files, don't unilaterally restructure - but if a file you're modifying has grown unwieldy, including a split in the plan is reasonable.

This structure informs the task decomposition. Each task should produce self-contained changes that make sense independently.

Reuse accepted architecture and product decisions. Inspect only what is needed to make the handoff executable. If a missing fact affects one task, name that task and dependency, complete independent planning, and ask only for the consequential decision that cannot be derived. Record how a later executor can resolve a local unknown rather than redesigning the approved solution.

## Bite-Sized Task Granularity

Use short, checkable steps when they improve execution clarity. Do not force every mechanical edit into a 2-5 minute step when a cohesive change and its proof are clearer together. A common behavior-changing sequence is:
- "Write the failing test" - step
- "Run it to make sure it fails" - step
- "Implement the minimal code to make the test pass" - step
- "Run the tests and make sure they pass" - step
- "Record a scoped commit" - step only when implementation is authorized and the applicable project policy calls for a commit at that boundary

## Plan Document Header

**Every plan MUST start with this header:**

```markdown
# [Feature Name] Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use the subagent-driven-development skill (recommended; requires subagent support) or the executing-plans skill to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Status:** Draft | Reviewed

**Implementation state:** Not started

**Goal:** [One sentence describing what this builds]

**Architecture:** [2-3 sentences about approach]

**Tech Stack:** [Key technologies/libraries]

---
```

## Task Structure

````markdown
### Task N: [Component Name]

**Purpose:** [What observable capability or risk this task addresses]

**Dependencies:** [Earlier tasks, inputs, or authorizations; use "None" when independent]

**Files:**
- Create: `exact/path/to/file.py`
- Modify: `exact/path/to/existing.py:123-145`
- Test: `tests/exact/path/to/test.py`

**Proof:** [Exact automated check, review, or manual observation and the risk it covers]

**Completion condition:** [Observable result plus evidence required before the task is complete]

- [ ] **Step 1: Write the failing test**

```python
def test_specific_behavior():
    result = function(input)
    assert result == expected
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/path/test.py::test_name -v`
Expected: FAIL with "function not defined"

- [ ] **Step 3: Write minimal implementation**

```python
def function(input):
    return expected
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/path/test.py::test_name -v`
Expected: PASS

- [ ] **Step 5: Record the task boundary when project policy requires it**

```bash
git add tests/path/test.py src/path/file.py
git commit -m "feat: add specific feature"
```

Run this step only when execution and the commit are authorized under the applicable project policy. Otherwise leave the reviewed changes uncommitted and report the pending delivery action.
````

## No Placeholders

Every step must contain enough actual content to preserve the accepted decision and make execution unambiguous. These are **plan failures**:
- "TBD", "TODO", "implement later", "fill in details"
- "Add appropriate error handling" / "add validation" / "handle edge cases"
- "Write tests for the above" without exact inputs, assertions, behavior, and a code block or exact repository reference that makes the test unambiguous
- "Similar to Task N" without an exact earlier-task or repository reference, the reusable decision or interface, and the specific delta for this task
- Steps that omit a necessary interface, algorithm, fixture, constraint, or repository reference
- References to types, functions, or methods that are neither defined in the plan nor locatable through an exact existing-source reference

Code blocks are required when exact code is part of the contract or prevents a likely incompatible implementation. Otherwise identify the existing pattern and exact source location, describe the intended change precisely, and let the executor implement the smallest conforming code. A zero-context handoff must preserve decisions and proof; it need not pre-write every line of the implementation.

## Remember
- Exact file paths always
- Exact code or repository references wherever the implementation cannot be derived safely
- Exact commands with expected output
- Dependencies, bounded file scope, proof, and completion condition for every task
- DRY, YAGNI, and TDD where behavior changes
- Commit steps only where the applicable project workflow requires and authorizes them

## Self-Review

After writing the complete plan, look at the spec with fresh eyes and check the plan against it. This is a checklist you run yourself — not a subagent dispatch.

**1. Spec coverage:** Skim each section/requirement in the spec. Can you point to a task that implements it? List any gaps.

**2. Execution-context scan:** Search for the failures in "No Placeholders." Replace vague instructions with the missing execution-critical detail, using exact existing-source or earlier-task references when they preserve enough context and literal code only when the contract requires it.

**3. Type consistency:** Do the types, method signatures, and property names you used in later tasks match what you defined in earlier tasks? A function called `clearLayers()` in Task 3 but `clearFullLayers()` in Task 7 is a bug.

**4. Handoff continuity:** Does the plan preserve the objective and deliverable, current phase, bounded scope and authorization source, selected skills, relevant evidence, unfinished items, and localized blockers? On resume after a new session or context compaction, reconcile new user instructions and changed project rules or state, and reread only information that was lost or may have changed.

If you find issues, fix them inline. No need to re-review — just fix and move on. If you find a spec requirement with no task, add the task.

## Execution Handoff

After saving the plan, select the likely execution mode from task dependencies and host capabilities. Record that recommendation separately from whether execution is authorized:

- Plan tasks are mostly independent AND the host supports subagents → **REQUIRED SUB-SKILL:** `../subagent-driven-development/SKILL.md` (fresh subagent per task + two-stage review between tasks).
- Otherwise → **REQUIRED SUB-SKILL:** `../executing-plans/SKILL.md` (in-session execution with checkpoints), or in-session TDD + incremental implementation for shorter plans.

Ask the user to choose only when mode selection requires a material preference that cannot be derived. If the current request or another effective grant already authorizes implementation for the stated target and scope, reuse it and proceed with the selected mode. Otherwise report: **"Plan complete and saved to `docs/devflow/plans/<filename>.md`. Recommended later execution mode: `<mode>`. Implementation has not begun; starting it is the pending action."** A selected mode, accepted plan, or completed planning phase does not itself authorize implementation. If the host lacks subagents, use the fallback contract in `../using-devflow/SKILL.md` only after execution is authorized.

During a later authorized execution, a progress question supplements the active objective: answer briefly, then continue. A localized unknown blocks only dependent tasks; keep independent authorized work moving and preserve failures, retries, exact artifact identities, and evidence limits for the eventual handoff.

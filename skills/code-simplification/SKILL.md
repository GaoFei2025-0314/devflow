---
name: code-simplification
description: Simplifies working code for clarity while preserving behavior. Use when code works but is harder to read, maintain, or extend than it should be, or after a feature lands and accumulated complexity needs a bounded cleanup pass. Not for bug hunting (use code-review-and-quality) or performance tuning (use performance-optimization).
---

# Code Simplification

## Purpose and Action Boundary

Simplification reduces cognitive load without changing observable behavior. Fewer lines are not the objective; clearer responsibilities, control flow, names, and boundaries are.

First identify the requested deliverable and authority. A request to review or suggest simplifications is read-only: report candidates and evidence without editing. Modify code only when simplification is requested or otherwise covered by an effective local-edit grant, and stay within its files and behavior. Review feedback, an `Approve` verdict, or completion of a prior phase does not grant mutation or delivery authority.

Apply the shared [Phase and Delivery Contract](../using-devflow/references/phase-contract.md), [Authorization and Trust Contract](../using-devflow/references/authorization-contract.md), [Evidence Contract](../using-devflow/references/evidence-contract.md), and [Delivery Contract](../using-devflow/references/delivery-contract.md). Use [code-review-and-quality](../code-review-and-quality/SKILL.md) for the quality standard.

## Core Principles

### Preserve Behavior

Maintain the same inputs, outputs, side effects, ordering, errors, compatibility, and edge-case behavior. A behavior change is a separate implementation decision, even if it appears cleaner. If equivalence cannot be established, leave the code unchanged and report the uncertainty.

Before each change, ask:

- What behavior and invariants does this code express?
- What calls it, what does it call, and which boundaries can observe it?
- Which errors, timing, ordering, and side effects must remain?
- What tests, specifications, history, or neighboring patterns explain its shape?

### Follow Project Conventions

Read the applicable project instructions and inspect neighboring code that solves the same kind of problem. Match its module, naming, typing, error-handling, import, and testing conventions. Do not create churn by imposing a personal style.

### Prefer Clarity Over Cleverness

Prefer explicit control flow and named concepts when compact expressions require a mental pause. A small helper is useful when it names a real concept; inlining is useful when a wrapper adds only indirection. Worked examples are in [references/examples.md](references/examples.md).

### Remove Complexity Rather Than Relocate It

A refactor is simpler when readers must hold fewer concepts or paths in mind. Avoid moving the same branching into a new abstraction, merging unrelated responsibilities, or replacing one clear flow with a framework built for hypothetical reuse.

### Keep Scope Bounded

Default to the requested files or recently changed behavior. Include an adjacent change only when it is required to preserve behavior, remove a dependency made obsolete by the simplification, or satisfy an applicable project gate. Report useful out-of-scope candidates separately instead of editing them.

## Understand Before Changing

Use read-only inspection to answer the questions that affect behavior:

1. What is the code responsible for, and which callers or consumers rely on it?
2. What are its normal, boundary, and error paths?
3. Which tests or other evidence define current behavior?
4. Do comments, history, platform constraints, performance measurements, or compatibility requirements explain the design?
5. What exact scope and end condition did the request authorize?

History is one possible source, not a mandatory ritual. Use it when current code and requirements do not explain a consequential choice. Ask only when a high-impact ambiguity cannot be resolved through authorized read-only investigation.

## Identify Opportunities

Treat these as prompts for investigation, not automatic rewrite rules:

| Signal | Possible direction | Behavior risk to check |
| --- | --- | --- |
| Deep nesting or repeated guards | Guard clauses, named predicates, or an explicit state model | Ordering and error behavior |
| Long multi-purpose function | Separate responsibilities at a stable boundary | Shared state and call sequence |
| Nested ternaries or dense transforms | Explicit branches or named intermediate values | Precedence, evaluation, and fallback semantics |
| Boolean flag combinations | Options object or distinct operations | API compatibility and invalid combinations |
| Duplicate logic | Reuse an existing canonical helper or extract an owned concept | Subtle differences between call sites |
| Generic or misleading names | Rename to express domain meaning and side effects | Public/exported references and generated interfaces |
| Comments that restate code | Remove or make the code self-explanatory | Intent or constraints hidden in the comment |
| Dead or unreachable code | Remove within authorized scope | Dynamic references, compatibility, and side effects |
| Pass-through wrapper | Inline or delete the wrapper | API stability, testing seams, and instrumentation |
| Speculative abstraction | Replace with the current direct flow | Extension points promised to consumers |
| Redundant type assertion | Let inference carry the type | Boundary validation and narrowing |

Size alone does not determine whether code must be split or whether automation is required. Choose a manual, scripted, or structural approach from semantic repetition, risk, reviewability, tool support, and project rules. Large mechanical transformations need tooling and evidence appropriate to their reach; small cohesive changes need not be fragmented solely to satisfy a line-count target.

## Apply Approved Simplifications

1. Define the behavior-preservation claim and the bounded files or symbols.
2. Make the smallest coherent change that reduces complexity.
3. Inspect the diff for accidental behavior, interface, error, or scope changes.
4. Select checks based on the affected behavior, dependencies, risk, and mandatory project gates.
5. Reassess clarity and project consistency across the resulting code.

Use incremental checkpoints when they improve fault isolation or reviewability. Do not require a commit or full-suite rerun after each edit. Existing evidence may be reused when it covers the resulting artifact and its relevant state remains valid; changed code invalidates only evidence that depends on it. Preserve actual failures, diagnose before retrying, and never modify tests merely to make changed behavior appear preserved.

Assessing equivalence and running authorized checks are internal implementation work, not a reason to ask for fresh approval. Seek a new decision only when the proposed change would alter behavior, expand scope, cross an uncovered action boundary, or leave a consequential ambiguity unresolved.

Refactoring and feature changes should remain distinguishable in scope, evidence, and history. Whether they require separate commits or pull requests is determined by the project's actual delivery policy and the cohesion and risk of the package, not by this skill.

## Verify Behavior and Improvement

For each major check, state the risk it addresses. Examples include focused behavior tests for changed control flow, type or build checks for boundary changes, linter/formatter checks when syntax or style tooling is affected, and broader regression checks for cross-cutting changes. A passing check proves only its recorded object and scope.

Before concluding, confirm:

- observable behavior, errors, side effects, and ordering remain covered by current evidence;
- no interface or compatibility change was smuggled into the refactor;
- the result follows project conventions and is easier to understand;
- no unused imports, unreachable branches, or obsolete wrappers remain within the edited scope;
- the diff contains no unrelated edits;
- review provenance, target, baseline, checks, results, and limitations are reported truthfully.

If project policy requires independent review, retain that gate. When no suitable independent reviewer is available, a clearly labeled self-review can provide interim evidence but does not satisfy the independent requirement.

## Handoff

For a read-only simplification review, return located candidates with the current complexity, expected improvement, behavior risks, and recommended bounded change. Do not mutate the artifact.

For an approved simplification, report:

- exact files and behavior scope changed;
- before and after comparison states;
- why the result is simpler without changing behavior;
- checks run or valid evidence reused, with provenance, object, result, and limits;
- self-review or independent-review status and any required gate still pending;
- unresolved or out-of-scope candidates separately from completed changes.

## Common Failures

- Editing in response to a review-only request
- Simplifying code before understanding its responsibility and consumers
- Optimizing for line count or applying fixed size thresholds as acceptance rules
- Changing error handling, evaluation order, side effects, or compatibility for aesthetics
- Renaming to personal taste instead of project conventions
- Moving complexity into a new abstraction without reducing concepts
- Refactoring unrelated areas without authorization
- Mandating a commit, pull request split, or full rerun independently of project policy and impact
- Calling a self-review independent or treating a review verdict as edit or delivery authorization

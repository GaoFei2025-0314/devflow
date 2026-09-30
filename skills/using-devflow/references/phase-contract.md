# Phase Details

Since 2.1.0 the canonical phase rules are in [core rules: phases and completion](core-rules.md#phases-and-completion). This page keeps situational details; read it only when one of the cases below applies.

## Phase inputs

| Phase | Needs before it starts |
| --- | --- |
| **Understand** | The current request, relevant project facts, valid prior decisions and authorization, allowed scope, and expected end condition. |
| **Specify** | An understood objective plus the requested form of design, Spec, or plan and its acceptance needs. |
| **Implement** | An explicit implementation objective or authorization, applicable accepted requirements and decisions, bounded files or systems, and identified verification work. |
| **VerifyReview** | A concrete document or implementation, its acceptance conditions, and the checks and review its risks call for. |
| **Deliver** | The deliverables reconciled against the request, supporting evidence, known limits, and authorization for any delivery action. |

Resolve missing inputs with read-only inspection when possible, and ask only when a consequential choice cannot be derived. Existing valid authorization persists across phase transitions; do not request it again.

## Cancellation and replacement

When the user cancels or replaces the objective, stop only the work that belonged to the old objective. Preserve a safe, reviewable partial result and report what completed and what did not. Keep facts and decisions that still apply to the new objective.

## Reconciling obligations

The completion check in the core rules is usually a brief internal pass; it does not require a tracking file or a user-facing table. When it is not straightforward:

- Do not silently narrow a pending obligation, and do not report an obligation as done because a related one passed.
- Reuse valid evidence, and do not edit solely to create a diff. When a requested update still has useful behavior, boundary, or artifact work remaining, make the smallest appropriate change.
- If an obligation was already satisfied, cite that evidence without claiming a new action occurred.
- If an obligation conflicts with an applicable constraint or depends on a missing material decision, report the discrepancy and continue the independent authorized work.

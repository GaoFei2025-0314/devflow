# Shared Phase and Delivery Contract

Use this contract before selecting or changing a Devflow route. Derive the current objective, requested deliverable, allowed scope, existing authorization, and end condition from the current request, still-valid prior decisions, and project rules. Resolve questions with read-only inspection when possible. Ask only when a consequential choice cannot be derived.

Phases organize work; they never grant permission for an action. Entering a phase, saving a plan, approving a document, or finishing one phase does not authorize implementation, Git delivery, deployment, or any other later action. At each transition, apply the Human-in-the-Loop Contract and the authorization already established for that action. Existing valid authorization persists; do not request it again.

## Phase contracts

| Phase | Required input | Legal terminal states |
| --- | --- | --- |
| **Understand** | The current request, relevant project facts, valid prior decisions and authorization, allowed scope, and expected end condition | The requested explanation or analysis is delivered in the conversation; or the objective, deliverable, scope, and material unknowns are clear enough for the requested next phase; or a specific consequential decision is pending after independent authorized investigation is complete. Analysis does not require a file. |
| **Specify** | An understood objective plus the requested form of design, Spec, or plan and its acceptance needs | The requested document is ready as a draft or reviewed artifact, with status, scope, acceptance conditions, limits, and the fact that implementation has not begun; or a specific product decision is pending. A document-only request ends legally here and does not start implementation. One document may contain the complete requested result. |
| **Implement** | An explicit implementation objective or authorization, applicable accepted requirements and decisions, bounded files or systems, and identified verification work | Every explicit implementation deliverable is complete; the user has accepted a scoped deferral; or a concrete missing dependency or authorization blocks the remaining dependent work after all independent authorized work is exhausted. Merely naming unfinished work is an interim report, not a legal endpoint. A saved or accepted plan alone is not an implementation instruction. |
| **VerifyReview** | A concrete document or implementation, its acceptance conditions, and the checks and review appropriate to its risks | The requested verification or review result is complete and reports fresh evidence accurately. For an implementation package, findings are resolved, accepted as scoped deferrals, or blocked on a concrete missing dependency or authorization after independent authorized work is exhausted; required human acceptance is identified as pending or received. Passing checks does not by itself mean the implementation or delivery is complete. |
| **Deliver** | The current deliverables reconciled against the request, supporting evidence, known limits, and authorization for any delivery action | The requested result is delivered with completed scope, evidence, and only accepted deferred or demonstration-only items and reasons; or a specific delivery action is ready but pending its required authorization after all independent preparation is complete. For an explanation or document-only request, delivery can be the conversation or local document without Git or implementation actions. |

A phase may stop only when its current requested deliverable is complete, the user explicitly cancels or replaces the objective, the user accepts a scoped deferral, or a concrete missing dependency or authorization blocks the remaining dependent work after independent authorized work is exhausted. Cancellation or replacement stops work belonging only to the old objective; preserve a safe and reviewable partial result and report what completed and what did not.

## Treating a new user message

Classify the message by its explicit effect on the active objective:

- **Supplemental constraint or correction:** update the affected scope, requirements, or acceptance condition. Retain the original objective, prior decisions that remain valid, and independently authorized work that can still continue.
- **Progress or explanation question:** answer briefly in user terms, then resume the active objective. A question about status, a command, or a check neither cancels the task nor requires rerunning work solely to answer it.
- **Explicit replacement:** replace the active objective only when the user clearly requests a different objective or the new objective is incompatible with it. Retain applicable facts and decisions, but do not continue work that belongs only to the replaced objective.
- **Explicit cancellation:** stop the canceled objective and report its reviewable partial state. Do not infer cancellation from a question, correction, interruption, or added requirement.

If one missing decision affects only part of the work, name that dependency and continue independent work already authorized. Do not guess a high-impact choice to avoid asking, and do not stop unrelated work merely because one branch is pending.

## Completion language

Use status claims that match the current deliverable:

- **Progress or interim:** completed and unfinished items are reported accurately, but the authorized package remains active unless a legal stopping condition above applies.
- **Document ready:** the requested analysis, design, Spec, or plan is reviewable; implementation is not implied.
- **Implementation complete:** every explicit implementation deliverable has been reconciled and completed; verification and delivery may remain.
- **Automated checks passed:** the named checks passed on the stated artifact; this does not substitute for missing deliverables, review, runtime evidence, or human acceptance.
- **Human acceptance pending:** the artifact is ready for a required user or stakeholder judgment.
- **Specific authorization pending:** a concrete action is prepared but cannot execute until the applicable approval is given.
- **Final delivery:** every current deliverable has been reconciled, required evidence and review are complete, accepted deferrals remain recorded, and the requested delivery action has occurred.

Before claiming an implementation, work package, version, or task complete, separate every explicit obligation, including multiple actions within one task, and reconcile each with actual artifacts or changes, the scope of its verification, and one disposition: completed now; already satisfied by valid, proportionate evidence; changed or deferred with user acceptance; or still pending. This can be a brief internal check; do not require a new tracking file or user-facing table. Do not silently narrow a pending obligation. Reuse valid evidence and do not edit solely to create a diff; when a requested update still has useful behavior, boundary, or artifact work remaining, complete the smallest appropriate change. If an obligation was already satisfied, cite that evidence without claiming a new action occurred. If it conflicts with an applicable constraint or depends on a missing material decision, report the discrepancy and continue independent authorized work. Any required pending obligation keeps the whole-scope status interim. A green check proves only the behavior it exercised, not that another requested action occurred.

# Shared Phase and Delivery Contract

Normative core — read this before selecting or changing a Devflow route. Every rule of the
contract is stated here. [The full text](phase-contract-full.md) elaborates the same rules
and is read when this file cites it: read *Treating a new user message* when a new message
arrives during active work, and *Completion language* before writing any status or
completion claim. Reading the full text is never required to route.

Derive the objective, requested deliverable, allowed scope, existing authorization, and end
condition from the current request, still-valid prior decisions, and project rules. Resolve
questions with read-only inspection when possible. Ask only when a consequential choice
cannot be derived.

Phases organize work; they never grant permission for an action. Entering a phase, saving a
plan, approving a document, or finishing one phase does not authorize implementation, Git
delivery, deployment, or any other later action. At each transition, apply the
Human-in-the-Loop Contract and the authorization already established for that action.
Existing valid authorization persists; do not request it again.

## Legal terminal states

Each phase takes the current request, relevant project facts, still-valid prior decisions
and authorization, the allowed scope, and the expected end condition as its input.

| Phase | A route may legally end here when |
| --- | --- |
| **Understand** | the requested explanation or analysis is delivered in the conversation; or the objective, deliverable, scope and material unknowns are clear enough for the requested next phase; or a specific consequential decision is pending after independent authorized investigation is complete. Analysis does not require a file. |
| **Specify** | the requested document is ready as a draft or reviewed artifact, carrying status, scope, acceptance conditions, limits, and the fact that implementation has not begun; or a specific product decision is pending. A document-only request ends legally here and does not start implementation. One document may contain the complete requested result. |
| **Implement** | every explicit implementation deliverable is complete; or the user has accepted a scoped deferral; or a concrete missing dependency or authorization blocks the remaining dependent work after all independent authorized work is exhausted. Merely naming unfinished work is an interim report, not a legal endpoint. A saved or accepted plan alone is not an implementation instruction. |
| **VerifyReview** | the requested verification or review result is complete and reports fresh evidence accurately. For an implementation package, findings are resolved, accepted as scoped deferrals, or blocked on a concrete missing dependency or authorization after independent authorized work is exhausted, and required human acceptance is identified as pending or received. Passing checks does not by itself mean the implementation or delivery is complete. |
| **Deliver** | the requested result is delivered with completed scope, evidence, and only accepted deferred or demonstration-only items and reasons; or a specific delivery action is ready but pending its required authorization after all independent preparation is complete. For an explanation or document-only request, delivery can be the conversation or local document without Git or implementation actions. |

A phase may stop only when its current requested deliverable is complete, the user
explicitly cancels or replaces the objective, the user accepts a scoped deferral, or a
concrete missing dependency or authorization blocks the remaining dependent work after
independent authorized work is exhausted. Cancellation or replacement stops work belonging
only to the old objective; preserve a safe and reviewable partial result and report what
completed and what did not.

## A new message updates the task; it does not cancel it

Classify a new message by its explicit effect on the active objective. A supplemental
constraint or correction updates the affected scope while the objective, valid prior
decisions and independently authorized work continue. A progress or explanation question is
answered briefly in user terms, then work resumes — it neither cancels the task nor requires
rerunning work solely to answer it. An explicit replacement replaces the objective only when
the user clearly requests a different or incompatible one; applicable facts and decisions are
retained. Only an explicit cancellation stops work, and its reviewable partial state is
reported. Never infer cancellation from a question, correction, interruption, or added
requirement.

When one missing decision or a pending staged user event affects only part of the work, name
that dependency and continue the independent work already authorized. Do not guess a
high-impact choice to avoid asking, and do not stop unrelated work because one branch is
pending. Deliverables the task already owes from its current facts remain due now; state the
event-pending part separately instead of withholding the whole deliverable.

Full wording: [Treating a new user message](phase-contract-full.md#treating-a-new-user-message).

## Completion claims must match the deliverable

These claims are distinct and not interchangeable: progress or interim; document ready;
implementation complete; automated checks passed; human acceptance pending; specific
authorization pending; final delivery.

Before claiming an implementation, work package, version, or task complete, separate every
explicit obligation — including multiple actions within one task — and reconcile each with
actual artifacts or changes, the scope of its verification, and exactly one disposition:
completed now; already satisfied by valid, proportionate evidence; changed or deferred with
user acceptance; or still pending. This can be a brief internal check; it does not require a
new tracking file or user-facing table. Do not silently narrow a pending obligation. Reuse
valid evidence and do not edit solely to create a diff. If an obligation was already
satisfied, cite that evidence without claiming a new action occurred. If an obligation
conflicts with an applicable constraint or depends on a missing material decision, report the
discrepancy and continue independent authorized work. Any required pending obligation keeps
the whole-scope status interim. A green check proves only the behavior it exercised, not that
another requested action occurred.

Full wording and claim definitions: [Completion language](phase-contract-full.md#completion-language).

---
name: brainstorming
description: Turns materially uncertain ideas into reviewable requirements and design decisions. Use when the request has consequential ambiguity or multiple viable directions; skip when still-valid requirements already settle the work.
---

# Brainstorming Ideas Into Designs

Shape an uncertain request into the design or requirements artifact the user actually asked for. Apply the shared [Phase and Delivery Contract](../using-devflow/references/phase-contract.md) to determine the current phase and legal endpoint, and the [Authorization and Trust Contract](../using-devflow/references/authorization-contract.md) before any state change. Brainstorming resolves product uncertainty; it does not authorize implementation, Git actions, or external delivery.

## When To Use

Use brainstorming when a missing choice could materially change scope, architecture, user-visible behavior, data handling, risk, cost, or acceptance. Do not restart discovery when an approved design, Spec, plan, or user answer still resolves the decision. If the request and affected behavior are already clear, return to the router and use the matching Specify or Implement route.

## Working Method

1. **Establish the requested result.** Identify the objective, requested form, allowed scope, current authorization, and end condition from the current request and project rules.
2. **Reuse known decisions.** Read the smallest relevant project context and still-valid design records. Preserve their provenance and resolve routine implementation choices from existing conventions when they do not materially change the result.
3. **Investigate before asking.** Use read-only inspection to answer questions the project can answer. If one unresolved choice affects only part of the work, continue the independent analysis or documentation.
4. **Clarify material unknowns.** Explain what information is missing and how the alternatives change the result. Combine closely related decisions when that makes the trade-off easier to assess; otherwise ask one focused question at a time. Prefer concise choices when they fit.
5. **Compare real alternatives.** When more than one viable approach remains, present the meaningful options, trade-offs, and a recommendation. Do not invent alternatives or approval steps for settled details.
6. **Produce the requested artifact.** This may be an explanation in the conversation, one design or Spec document, or input to a durable workspace. Scale the artifact to the change rather than requiring a fixed ceremony.
7. **Review the result.** Check for placeholders, contradictions, material ambiguity, scope creep, and untestable requirements. Fix issues supported by existing decisions; surface only consequential unresolved choices.

## Required Design Substance

Keep enough evidence for another reader to understand what was decided and how success will be judged. Include, in the requested form and at a depth proportionate to the change:

- the problem, objective, users or affected systems, and success outcome;
- scope and explicit non-goals;
- observable requirements and testable acceptance scenarios;
- relevant architecture, components, data flow, failure handling, and verification approach;
- material risks, constraints, assumptions, and mitigations;
- decisions and their rationale, including the source of an existing user answer or approved artifact when that provenance matters;
- unresolved material questions and the effect of each possible answer.

A small design can cover these points in a few paragraphs or a compact section. Do not omit scope, acceptance, or risk merely because the artifact is lightweight.

## Presenting And Recording The Design

Present complex designs in sections sized to the subject and invite correction where human judgment is still needed. A user request for explanation may end in the conversation. A request for one document may place the complete problem, goals, requirements, acceptance, risks, and decisions in that one file. If the user explicitly requests durable cross-session artifacts or the repository already uses an applicable change workspace, use [spec-workspace](../spec-workspace/SKILL.md). Otherwise use [spec-driven-development](../spec-driven-development/SKILL.md) for a standalone Spec.

Mark a written artifact as draft or reviewed, as supported by actual review evidence. For a document-only request, state that implementation has not begun. Record independent implementation or installation defects as findings rather than fixing them outside the requested scope.

After the requested artifact is ready, stop at **document ready** unless the current request separately includes and authorizes another phase. Do not create a worktree or branch, commit, push, open a pull request, or start implementation merely because brainstorming finished. If later work is requested, route it by its own deliverable, evidence, and authorization.

## Design For Isolation And Clarity

- Give each unit one clear purpose and a well-defined interface.
- State what each unit does, how it is used, and what it depends on.
- Prefer boundaries that let readers understand a unit without reading its internals and let implementations change without breaking consumers.
- Follow existing codebase patterns and include only targeted improvements needed for the current goal.
- Decompose a request that spans independent subsystems before refining one sub-project in detail.

## Visual Companion

A browser-based companion can show mockups, diagrams, layout comparisons, and other visual options during brainstorming. Offer it only when upcoming decisions are materially easier to judge visually, and wait for consent before opening a local URL:

> Some of what we're working on might be easier to explain if I can show it to you in a web browser. I can put together mockups, diagrams, comparisons, and other visuals as we go. This feature is still new and can be token-intensive. Want to try it? (Requires opening a local URL)

Keep the offer separate from clarification. Even after consent, use visuals only for questions best answered by seeing; use text for requirements, conceptual choices, and ordinary trade-offs. If the user accepts, read [visual-companion.md](visual-companion.md) before using it.

## Common Errors

- Re-interviewing the user after still-valid requirements or decisions already answer the question.
- Asking about routine implementation details that project conventions settle.
- Guessing a high-impact interpretation rather than naming its consequence and asking.
- Forcing two or three artificial approaches when only one viable approach exists.
- Turning a document-only request into worktree setup, commits, planning, or implementation.
- Calling a short artifact complete after dropping non-goals, acceptance scenarios, risks, or decision evidence.

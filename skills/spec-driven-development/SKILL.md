---
name: spec-driven-development
description: Creates a standalone, reviewable specification when requirements need a written source of truth and no durable change workspace is requested. Use for one-document Specs; skip when valid requirements already suffice for the requested phase.
---

# Spec-Driven Development

Create the Spec the user requested, at a depth proportionate to the change. Apply the shared [Phase and Delivery Contract](../using-devflow/references/phase-contract.md) to determine the requested endpoint and the [Authorization and Trust Contract](../using-devflow/references/authorization-contract.md) before any state change. A Spec defines intent and acceptance; it does not itself authorize planning, implementation, Git actions, or external delivery.

## When To Use

Use this skill when the requested result is a standalone Spec, a new project or significant change needs one written source of truth, or materially incomplete requirements must be made reviewable before later work. Use [brainstorming](../brainstorming/SKILL.md) first only when consequential product choices still need shaping.

If the user explicitly requests durable cross-session artifacts or the repository already has an applicable change workspace, use [spec-workspace](../spec-workspace/SKILL.md). Do not add a Spec ceremony to a tiny, unambiguous change when its acceptance conditions are already clear, and do not rewrite a still-valid approved Spec merely because a later phase begins.

## Start From Existing Decisions

Read the smallest relevant project context, existing design or Spec, plan, conventions, and user answers. Reuse decisions that remain valid and preserve their provenance when it matters to review. Investigate project facts before asking the user.

Clarify only a missing or conflicting choice that could materially change scope, architecture, user-visible behavior, data handling, risk, cost, or acceptance. State what is unknown and how the answers change the Spec. Combine related choices when useful and continue independent work that does not depend on the answer. Resolve ordinary choices from established conventions.

## Write One Complete Spec

A single document is a complete and legal deliverable. Adapt its sections to the subject; do not require mirrored documents or empty template sections. The Spec should contain enough of the following to make the request reviewable:

```markdown
# Spec: <Project or Feature>

Status: Draft | Reviewed
Implementation: Not started

## Problem and Objective
What problem is being solved, for whom, and what success means.

## Scope
Included behavior, affected users or systems, and explicit non-goals.

## Requirements
Observable requirements, constraints, and relevant interfaces or data behavior.

## Acceptance Scenarios
- GIVEN <initial state>
- WHEN <action>
- THEN <observable result>

## Design Decisions
Chosen approach, rationale, material alternatives, and decision sources.

## Verification
How each important requirement will be checked; include relevant project commands when known.

## Risks and Limitations
Material failure modes, mitigations, assumptions, and current limits.

## Open Questions
Only unresolved issues with a material effect, or "None".
```

For a small Spec, combine sections while retaining the problem, objective, scope, non-goals, observable requirements, testable acceptance, risks, decision evidence, status, and implementation state. Add technical stack, commands, project structure, code style, testing levels, rollout, migration, or operational boundaries only when they affect the requested change or help a later executor. Use full executable commands when commands are part of the contract, and follow the project's actual package manager and conventions.

Translate subjective goals into observable acceptance. If a numeric target or product threshold cannot be derived and would materially change success, present it as a focused decision rather than inventing it. Distinguish constraints that always apply, actions requiring authorization, and prohibited actions by referring to applicable project policy and the shared authorization contract instead of copying a new global control list into every Spec.

## Review The Spec

Before marking the document ready:

1. Scan for `TBD`, `TODO`, placeholders, vague requirements, and unsupported status claims.
2. Check that objective, requirements, decisions, and acceptance scenarios agree.
3. Confirm scope and non-goals keep the work bounded.
4. Confirm each material requirement is observable and has an appropriate verification path.
5. Record unresolved consequential questions with their impact; do not conceal them as assumptions.
6. Confirm the artifact says whether it is draft or reviewed and that implementation has not begun when the request is document-only.

Fix issues that existing evidence resolves. Ask only for a human judgment that remains necessary.

## Endpoint And Later Phases

When the requested Spec is reviewable, report **document ready** and stop if the request was Spec-only. An explanation may remain in the conversation if no file was requested. Do not create a worktree or branch, commit the Spec, push, open a pull request, create an implementation plan, or write code merely because the Spec is ready or approved. Record unrelated implementation or installation defects in the Spec when relevant; do not fix them outside scope.

If the current request separately includes planning or implementation and provides applicable authorization, route that phase through the Devflow router. Reuse this Spec rather than re-deriving it. Use [writing-plans](../writing-plans/SKILL.md) or [planning-and-task-breakdown](../planning-and-task-breakdown/SKILL.md) only when planning is part of the requested deliverable, and use the selected implementation and verification skills only when implementation is actually authorized.

Keep the Spec current when later authorized work changes a decision or accepted scope. Version-control, pull-request, archive, and delivery actions follow project policy and the shared [Delivery Contract](../using-devflow/references/delivery-contract.md); they are not automatic consequences of maintaining the document.

## Common Errors

- Repeating discovery or approval for still-valid requirements and decisions.
- Surfacing every ordinary implementation choice as a user question.
- Forcing fixed tech-stack, command, structure, or style sections when they do not affect the requested Spec.
- Calling a short Spec complete after omitting non-goals, testable acceptance, risks, or decision evidence.
- Treating Spec review as authorization for planning, implementation, commits, or delivery.
- Requiring a durable multi-file workspace when the user asked for one Spec.

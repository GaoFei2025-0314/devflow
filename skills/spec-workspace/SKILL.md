---
name: spec-workspace
description: Maintains durable change artifacts across sessions, reviewers, or agents. Use when the user explicitly requests a persistent workspace or an applicable specs/ or openspec/ change already exists.
---

# Spec Workspace

Use a durable workspace to preserve change intent across sessions, reviewers, or agents. Apply the shared [Phase and Delivery Contract](../using-devflow/references/phase-contract.md) for the requested endpoint, the [Authorization and Trust Contract](../using-devflow/references/authorization-contract.md) before state changes, and the [Delivery Contract](../using-devflow/references/delivery-contract.md) before Git, archive, or other delivery actions.

## When To Use

Use this workflow when the user explicitly requests durable cross-session artifacts, the repository already has an applicable `specs/` or legacy `openspec/` change, or the work needs persistent coordination among sessions, reviewers, or agents. A complex architecture, public contract, data model, or multi-step change commonly benefits from it.

Do not require a workspace for a conversation-only explanation, a requested single Spec, a tiny one-off edit, simple documentation wording, or a focused emergency fix. Route a standalone Spec through [spec-driven-development](../spec-driven-development/SKILL.md). Reuse an existing applicable change rather than creating a parallel workspace with conflicting decisions.

## Establish The Workspace

Follow existing repository conventions first. When none exist and a durable workspace is requested, use a short kebab-case change id and this adaptable layout:

```text
specs/
  project.md                         # optional project-wide context
  changes/
    <change-id>/
      proposal.md                    # problem, goals, scope, risks
      design.md                      # when the solution needs explanation
      tasks.md                       # when implementation planning is requested
      specs/
        <capability>.md              # observable capability requirements
  archive/                           # when this repository archives changes
```

The layout is a menu, not a requirement to create every file. Create only the artifacts needed for the requested deliverable and repository convention. A small durable change may use one complete change document; a broad change may split proposal, design, capability specs, and tasks so each remains readable. Never block a valid single-document request on filling several templates.

## Required Durable Record

Across the selected artifact or artifacts, preserve:

- status: draft, reviewed, implemented, or archived only when supported by evidence;
- the problem, objective, users or affected systems, and success outcome;
- scope and explicit non-goals;
- observable requirements with testable acceptance scenarios;
- material risks, constraints, assumptions, mitigations, and owners where relevant;
- decisions, rationale, alternatives that materially mattered, and the provenance of existing answers or approved artifacts;
- unresolved material questions and their impact;
- implementation and verification state, including an explicit “not implemented” statement for document-only work.

Lightweight artifacts may express these concisely, but must not lose scope, acceptance, risk, or decision evidence.

## Artifact Guidance

### Proposal

Use `proposal.md` when reviewers need the case for change. Cover the problem, goal, non-goals, user impact, scope, risks, and current status.

### Design

Use `design.md` only when the approach needs technical explanation. Record the chosen approach, material alternatives and rationale, affected data/API/UI contracts, failure behavior, verification strategy, and rollout or migration concerns that actually apply.

### Tasks

Use `tasks.md` when the requested deliverable includes implementation planning. Make tasks executable, dependency ordered, bounded, and paired with acceptance criteria and verification. A Spec-only request does not require tasks and does not authorize execution.

### Capability Specs

Place capability specs inside the active change folder, such as `specs/changes/<change-id>/specs/<capability>.md`, unless an existing workspace defines another convention. Write observable behavior:

```markdown
### Requirement: <Behavior>
The system SHALL <observable behavior>.

#### Scenario: <Name>
- GIVEN <initial state>
- WHEN <action>
- THEN <expected result>
```

Avoid vague qualities such as “better”, “fast”, or “friendly” unless measurable acceptance defines them.

## Reuse And Clarification

Start from still-valid project context, designs, Specs, plans, and user answers. Preserve their provenance and update the existing record when appropriate. Ask only when a new or conflicting issue creates a consequential choice that read-only investigation cannot settle. State the missing fact and its effect; group related decisions when that makes review easier. Continue independent documentation that does not depend on the answer.

## Validation And Endpoint

Before declaring the requested workspace artifact ready, check that its status and implementation state are accurate, goals and non-goals bound the work, requirements and scenarios are testable, risks are handled or visibly open, decisions have enough evidence to review, and references between selected artifacts resolve.

A durable workspace can legally finish at **document ready**. Do not create a worktree or branch, commit, push, open a pull request, or begin implementation merely because the workspace exists or a document is approved. Proceed only when the current request separately includes the next phase and its authorization.

After an authorized implementation, update only the artifacts needed to reflect actual outcomes and verification. Archive a change only when the requested delivery includes it, project policy permits it, and the change is genuinely complete. Preserve incomplete or deferred work instead of recording it as passed.

An archive completion note may contain:

```markdown
## Outcome
Implemented in <commit/PR/reference>, or document-only with no implementation.

## Verification
- <check command, review, or manual evidence and result>

## Follow-ups
- <remaining work, accepted deferral, or "None">
```

## Common Errors

- Creating four documents because the example layout contains four names.
- Creating a second change workspace instead of reusing valid decisions.
- Treating approved workspace content as approval to implement, commit, push, or archive.
- Omitting acceptance scenarios, non-goals, or risks to keep the workspace “lightweight.”
- Marking implementation, verification, review, or archival complete without matching evidence.

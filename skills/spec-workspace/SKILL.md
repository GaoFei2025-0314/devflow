---
name: spec-workspace
description: Durable change workspace for proposals, specs, task plans, validation, and archiving. Use when a change needs durable intent across sessions, reviewers, or multiple agents.
---

# Spec Workspace

Use this workflow when a change needs durable intent across sessions, reviewers, or multiple agents.

## When To Use

Use durable change artifacts for:

- New features with unclear requirements
- Public API or data model changes
- Architecture or behavior changes that need review
- Multi-step implementation plans
- Work that may continue across sessions

Skip it for:

- Tiny one-off edits
- Simple documentation wording changes
- Mechanical formatting
- Emergency fixes where a regression test and focused patch are enough

## Folder Layout

If the project already has a change workspace (a `specs/` or legacy `openspec/` folder), follow its existing conventions. Otherwise create:

```text
specs/
  project.md
  changes/
    <change-id>/
      proposal.md
      design.md
      tasks.md
      specs/
        <capability>.md
  archive/
```

Use short kebab-case change ids, such as `add-task-sharing` or `fix-auth-refresh`.

## Proposal

Create `proposal.md` with:

```markdown
# <Change Title>

## Problem
What user or system problem is being solved?

## Goal
What should be true after the change?

## Non-Goals
What is intentionally out of scope?

## User Impact
Who is affected and how?

## Risks
What could break or be misunderstood?
```

## Design

Create `design.md` when the solution needs technical explanation:

```markdown
# Design

## Approach
Describe the chosen approach.

## Alternatives Considered
List viable alternatives and why they were rejected.

## Data, API, or UI Changes
Document contracts that other code or users depend on.

## Test Strategy
Describe regression, unit, integration, browser, or manual checks.

## Rollout and Migration
Describe deployment, migration, fallback, and cleanup steps.
```

## Tasks

Create `tasks.md` as an executable checklist:

```markdown
# Tasks

- [ ] Add or update tests that describe the intended behavior
- [ ] Implement the smallest working slice
- [ ] Run focused verification
- [ ] Run relevant broader checks
- [ ] Update docs or examples
- [ ] Review the diff for regressions, security, and usability
```

## Specs

Create or update `specs/<capability>.md` with concrete behavior:

```markdown
# <Capability>

## Requirements

### Requirement: <Behavior>
The system SHALL <observable behavior>.

#### Scenario: <Name>
- GIVEN <initial state>
- WHEN <action>
- THEN <expected result>
```

Requirements should be observable and testable. Avoid vague words such as "better", "fast", or "friendly" unless they are backed by measurable criteria.

## Validation

Before implementation, check:

- The problem and goal are clear.
- Non-goals prevent scope creep.
- Each requirement is testable.
- The task list can be executed in order.
- Risks have a mitigation or an explicit owner.

After implementation, check:

- Tests or runtime checks prove each requirement.
- The final diff matches the proposal.
- Any behavior changes are documented.
- The change can be archived or updated with final notes.

## Archive

When work is complete, move the change folder to:

```text
specs/archive/<date>-<change-id>/
```

Add a short completion note:

```markdown
## Outcome
Implemented in <commit/PR/reference>.

## Verification
- <check command or manual validation>

## Follow-ups
- <remaining work, or "None">
```

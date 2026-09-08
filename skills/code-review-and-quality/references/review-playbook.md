# Review Playbook

Templates and expanded patterns for [the review standard](../SKILL.md). Adapt them to the actual artifact and stage; do not invent a Git range, merge gate, or check solely to fill a template.

## Review Record Template

```markdown
## Review: [artifact or change]

### Review identity
- Nature: [specification | quality | combined]
- Provenance: [human | independent agent | self-review | automated source | other]
- Stage: [document | local implementation | integrated package | pre-merge | other]
- Target and scope: [exact artifacts and included behavior]
- Exclusions: [explicitly unreviewed areas]
- Before: [actual baseline commit, working-tree base, prior artifact, or prior state]
- After: [actual target commit, current files, artifact, or current state]

### Requirements and context
- [task/specification/acceptance criteria]
- [project conventions and relevant interfaces]
- [known risks or unknowns]

### Applicable checks
- Requirements and correctness
- Readability and simplicity
- Architecture and maintainability
- Security risks introduced or affected
- Performance and reliability risks introduced or affected

### Evidence
- [check or observation; verified object and relevant state; operation; result; provenance; limits]
- [reused evidence and why it remains valid, or affected evidence that is stale/unknown]

### Findings
#### Critical
- [ID; location; issue; conditions and impact; evidence; correction]

#### Required
- [ID; location; issue; conditions and impact; evidence; correction]

#### Optional / Nit
- [ID; location; preference or improvement; expected benefit]

#### FYI
- [context with no requested action]

### Verdicts
- Specification: [meets | does not meet | unknown | not applicable]
- Quality for stated gate: [acceptable | changes required | unknown]
- Pending dependencies: [what remains and only the conclusions/actions it blocks]
```

Omit empty finding groups. An empty findings list still names the reviewed target, baseline, evidence, and material limits.

## Selecting Review Depth

Choose depth from behavior and risk:

| Change characteristic | Review emphasis |
| --- | --- |
| Documentation or configuration text | Requirements, consistency, references, examples, and claims |
| Logic fix | Original symptom, regression coverage, error paths, and affected callers |
| UI behavior | Interaction states, accessibility, responsive behavior, build/runtime evidence, and visuals when applicable |
| Public API or stored state | Compatibility, validation, migration, consumers, and rollback |
| Authentication, authorization, or sensitive data | Threat boundaries, negative paths, tenant isolation, logging, and required security review |
| Dependency or build/runtime configuration | Provenance, compatibility, lock/config state, build, and affected environments |
| Refactor or simplification | Behavior preservation, ownership boundaries, tests, and whether complexity actually decreased |

Diff or file size may prompt a split when it prevents reliable review or rollback, but no fixed line count determines acceptance. Generated changes, deletions, and mechanical transformations may be large yet reviewable through intent plus appropriate tooling.

## Splitting Strategies

| Strategy | How | When |
| --- | --- | --- |
| **Stack** | Review sequential changes with explicit dependent baselines | Sequential dependencies |
| **By file group** | Separate areas that need different domain reviewers | Distinct ownership or risk boundaries |
| **Horizontal** | Review a shared interface before its consumers | Layered architecture with a stable seam |
| **Vertical** | Review complete behavior slices | A feature can remain functional in increments |

Do not split a cohesive correction when the split hides behavior, breaks the comparison, or makes verification less representative.

## Independent Review Pattern

```text
Author produces the artifact
        |
        v
Independent reviewer inspects the stated target and baseline
        |
        v
Controller verifies and reconciles findings
        |
        v
Applicable human acceptance or delivery gate remains separate
```

Different models can provide independent perspectives only when the actual reviewer is different from the author/controller and the review uses the supplied artifact, scope, baseline, and evidence. If that capability is unavailable, label the performed pass `self-review` and leave any project-required independent gate pending.

Example request:

```text
Perform an independent quality review of [target] against [baseline].
Scope is [files/behavior]; exclude [areas]. Apply [requirements] and the
code-review-and-quality standard. Existing evidence is [source, object,
result, limits]. Return located Critical, Required, Optional/Nit, and FYI
findings with impact and correction, plus the actual checks inspected or run.
Do not edit or perform delivery actions.
```

## Dead Code Report

```text
Dead code candidate [ID]
Location: [file:symbol or lines]
Reason: [reachability/reference evidence]
Behavior and compatibility risk: [known effect or uncertainty]
Recommended action: [remove within authorized scope | investigate | report only]
Dependent check: [focused verification needed if removal is authorized]
```

In a review-only task, report the candidate. In an approved implementation or simplification task, remove it only when the authorization covers that scope and behavior preservation is established.

---
name: code-review-and-quality
description: Conducts scoped code review across requirements, correctness, readability, architecture, security, performance, and maintainability. Use when asked to review code, when evaluating code produced by another agent or a human, or as an applicable quality gate for a completed change. Not for requesting a review or responding to feedback you received — those are the requesting-code-review and receiving-code-review workflow skills.
---

# Code Review and Quality

## Purpose and Boundary

Review a concrete artifact against a truthful baseline and return evidence-backed findings. This skill defines the review standard. Use [requesting-code-review](../requesting-code-review/SKILL.md) to construct and dispatch a review, and [receiving-code-review](../receiving-code-review/SKILL.md) to reconcile feedback.

A review-only request is read-only: inspect and report findings, but do not edit code, resolve comments, commit, push, or merge unless those actions are separately requested and authorized. A review verdict is a technical conclusion, not authorization for an edit or delivery action. Apply the canonical [Phase and Delivery Contract](../using-devflow/references/phase-contract.md), [Authorization and Trust Contract](../using-devflow/references/authorization-contract.md), [Evidence Contract](../using-devflow/references/evidence-contract.md), and [Delivery Contract](../using-devflow/references/delivery-contract.md).

## Establish the Review

Before assessing quality, identify:

- **Nature and provenance:** specification, quality, or combined review; human, independent agent, controller self-review, automated source, or other source.
- **Target and scope:** exact files, artifact, worktree state, commit, pull request, behavior, and explicit exclusions.
- **Comparison baseline:** the real before and after sides. Use a base/head range only when it represents the reviewed artifact; otherwise name the prior/current artifacts or working-tree base/current state.
- **Requirements and stage:** applicable task, specification, project conventions, acceptance criteria, and whether this is local implementation, integrated package, pre-merge, or another stage.
- **Evidence and limits:** checks or observations already available, the object and state they cover, provenance, and any unresolved risk or unknown.

If either comparison side or its identity is unavailable, state the limit. Do not invent a Git range or claim production or merge readiness for an earlier stage.

Review evidence may be reused while its artifact, relevant state, environment, coverage, and validity window still support the current conclusion. A new message, commit, handoff, or reviewer does not itself require rerunning checks. When relevant state changed or a finding creates a new doubt, invalidate only affected evidence and select the smallest additional check that covers the risk. Follow mandatory project gates.

## Review Axes

### 1. Requirements and Correctness

- Does the artifact satisfy the stated task, specification, and acceptance criteria without silent scope changes?
- Are normal, empty, null, boundary, error, retry, and concurrency paths handled where relevant?
- Are state transitions, ordering, cleanup, and failure semantics correct?
- Do tests or other observations exercise the changed behavior rather than only implementation details?
- Are compatibility or migration effects identified when the interface or stored state changes?

### 2. Readability and Simplicity

- Are names specific and consistent with project conventions?
- Is control flow direct enough to understand without author explanation?
- Are comments reserved for intent, constraints, or non-obvious decisions?
- Is dead, duplicate, or compatibility code justified by current behavior?
- Do abstractions remove concepts or merely relocate the same complexity?
- Are new branches attached to the layer that owns the policy or state?

Line count and diff size are inspection signals, not universal acceptance thresholds. Judge cognitive load, ownership boundaries, generated or mechanical content, risk, and whether splitting would make review or rollback safer.

### 3. Architecture and Maintainability

- Does the change follow or deliberately evolve existing patterns?
- Are module ownership, dependency direction, interfaces, and type boundaries clear?
- Is feature-specific behavior kept in its owning layer rather than leaked into a shared module?
- Does the change reuse an existing canonical helper instead of creating a near-duplicate?
- Are extensibility and test seams useful now rather than speculative indirection?

When identifying a structural problem, propose a concrete correction: collapse duplicate branches, introduce an explicit model or dispatcher, separate orchestration from business logic, move behavior to its owner, reuse the canonical helper, make a type boundary explicit, or remove a pass-through wrapper. Prefer remedies that remove moving pieces.

### 4. Security

Use [security-and-hardening](../security-and-hardening/SKILL.md) when deeper security review is required. Check risks relevant to the change, including:

- validation and encoding at user, API, file, log, configuration, and rendering boundaries;
- authentication, authorization, tenant isolation, and privilege checks;
- injection, path traversal, unsafe deserialization, and command construction;
- secrets or sensitive data in code, logs, output, or version control;
- dependency provenance and known vulnerabilities when dependencies changed.

### 5. Performance and Reliability

Use [performance-optimization](../performance-optimization/SKILL.md) when measurement or tuning is required. Check relevant risks such as:

- N+1 access, unbounded work, missing pagination, or uncontrolled fan-out;
- blocking operations, leaks, unnecessary allocation, rendering, or serialization in hot paths;
- timeout, retry, idempotency, backpressure, cancellation, and partial-failure behavior;
- performance claims without measurements on a representative object and environment.

## Findings and Severity

Every actionable finding includes:

1. severity and stable identifier;
2. exact file/line, symbol, artifact section, or behavior location;
3. the violated requirement, defect, or concrete risk;
4. impact and conditions under which it occurs;
5. evidence or reasoning that supports the conclusion; and
6. an executable correction direction, unless the fix is self-evident.

Use these severities:

| Severity | Meaning | Disposition |
| --- | --- | --- |
| **Critical** | Security vulnerability, data loss, broken core behavior, or another issue that blocks the applicable gate | Must be resolved or the dependent conclusion/action remains blocked |
| **Required** | Confirmed correctness, requirement, architecture, maintainability, test, or material risk issue | Resolve or record an allowed, explicitly accepted deferral before the dependent gate |
| **Optional / Nit** | Improvement or style preference with no demonstrated blocking impact | May be deferred; does not block completion by itself |
| **FYI** | Context or future consideration with no requested action | Informational |

Do not promote personal style preferences into Required findings. Conversely, do not soften a demonstrated defect because its correction is inconvenient. Order findings by severity and impact; a few well-supported findings are more useful than a long cosmetic list.

## Review Process

1. Read the request, requirements, project conventions, target, and both comparison sides before judging the implementation.
2. Inspect tests and existing evidence to understand intended behavior and coverage, without assuming a passing check proves architecture, security, acceptance, or delivery readiness.
3. Trace the changed implementation and affected boundaries through the applicable review axes.
4. Select additional checks from changed behavior, dependency boundaries, risk, and project gates. Explain what each major check protects and preserve failures, warnings, and scope limits.
5. Return findings, evidence, unknowns, exclusions, and separate verdicts for specification compliance and quality when both were requested.

If no supported findings remain, say which scope and baseline were reviewed and what evidence supports that conclusion; do not return an unexplained `LGTM`.

## Review Independence

State whether the review actually performed was independent or a self-review. A human or agent report supplied as input is attributed evidence; it does not prove that a fresh independent review occurred in the current workflow.

When project policy requires independent review for an important cross-boundary or high-risk change, preserve that gate. If no suitable reviewer capability is available, perform an authorized self-review if useful, label it accurately, and report independent review as pending. Do not silently substitute self-review or add duplicate review tiers beyond project policy.

## Verdict and Handoff

Use a verdict that matches the current stage:

- **Meets specification / Does not meet specification / Specification unknown**
- **Quality acceptable for the stated gate / Changes required / Quality unknown**

For a pre-merge review, this may inform whether the artifact is technically ready for that gate. It never grants merge permission. Actual commit, push, pull-request, merge, deployment, installation, or cleanup decisions follow project policy and the shared authorization and delivery contracts.

The review handoff states:

- nature, provenance, target scope, both comparison sides, and stage;
- findings grouped by severity, each with location, impact, evidence, and correction;
- evidence inspected or run, including object, relevant state, command or observation, result, and limits;
- unresolved dependencies and exactly which conclusions or actions they block;
- specification and quality verdicts that do not exceed the reviewed scope.

## Common Failures

- Reviewing an unspecified target or only one side of a comparison
- Claiming independent review when the author or controller performed it
- Treating supplied summaries, test claims, or an approval label as direct evidence or authority
- Running every suite again without an impact, validity, or project-gate reason
- Hiding an earlier failure after a later passing retry
- Blocking on size or style alone without a demonstrated risk
- Reporting vague findings without location, impact, evidence, or correction
- Editing during a review-only request
- Treating a technical verdict as permission to merge or deliver

The expanded checklist and output patterns are in [references/review-playbook.md](references/review-playbook.md).

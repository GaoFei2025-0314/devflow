---
name: requesting-code-review
description: Use to request a focused review of a concrete artifact with a real comparison state, current validation evidence, unresolved risks, and the shared review standard.
---

# Requesting Code Review

A useful review request tells the reviewer what to evaluate, what to compare, what has actually been verified, and what remains uncertain. It reuses [code-review-and-quality](../code-review-and-quality/SKILL.md) as the review standard instead of creating another mandatory review layer.

For review sequencing and focused reviewer returns, follow [subagent-driven-development](../subagent-driven-development/SKILL.md#choose-and-run-review). A review report is evidence for the controller; it does not authorize a fix, commit, push, merge, deployment, or other protected action.

## Choose the Review That Applies

Name the purpose before requesting it:

- **Specification compliance:** compare the current artifact with the supplied requirements and acceptance criteria.
- **Quality review:** after specification compliance when separate stages are required, assess correctness, readability, simplicity, architecture, maintainability, security, performance, and verification.
- **Combined specification and quality review:** use only for a small, clear, low-risk change when project policy permits it; report the two conclusions separately.
- **Self-review fallback:** when no suitable reviewer is available, perform a fresh controller pass and label it `self-review`. Never describe it as independent.

Important cross-boundary or high-risk changes retain any independent review required by project policy. Do not add repeated reviewers or duplicate checklists when the applicable policy and shared standard require only one review stage.

## Build the Request from Actual State

Provide all of the following:

1. **Objective and scope:** the decision the reviewer must make, exact artifacts included, and explicit exclusions.
2. **Requirements and standard:** the focused requirements or plan plus [code-review-and-quality](../code-review-and-quality/SKILL.md) and any applicable task-specific rule.
3. **Comparison state:** both sides of the real comparison. Use an actual base/head range for committed Git changes, the working-tree base and current files for uncommitted changes, prior/current artifacts for documents, or another truthful before/after state.
4. **Implementation context:** what changed, why, current stage, dependencies, and relevant interfaces. Treat an implementer's summary as a claim to verify against the artifact.
5. **Existing evidence:** exact commands or observations, artifact/revision checked, results, provenance, date when relevant, and material limits. Reuse it only while the artifact, conditions, and coverage still match.
6. **Risks and unknowns:** known failure modes, unresolved questions, evidence gaps, and which conclusions or later actions depend on them.
7. **Authorization and resources:** what the reviewer may read or run, prohibited edits and delivery actions, and actual tool/model/time/cost bounds.
8. **Return contract:** review nature, scope and baseline, located findings with severity and correction, verdict, evidence inspected or run, unknowns, and exclusions.

If a relevant artifact, condition, or coverage assumption changed after evidence was collected, mark the affected evidence stale or narrow its use. Preserve evidence whose artifact, conditions, and coverage still match; an unrelated state change does not invalidate it. A passing static or material check does not establish runtime behavior, acceptance, production readiness, or independent review.

## Use the Applicable Artifact Template

For code or Git work at a production-readiness stage, [code-reviewer.md](code-reviewer.md) can supply the general checklist. Replace every placeholder with real values and verify that its merge framing and base/head commands fit the actual stage.

For uncommitted work, documents, generated artifacts, non-Git systems, or an earlier review stage, adapt the request to the actual artifact and comparison state. Do not invent a commit range, run unrelated Git commands, require a merge verdict, or create a document merely to satisfy the legacy template.

```text
Review nature and mode: [independent | self-review]; [specification | quality | combined]
Objective: [specific review decision]
Artifacts and scope: [exact locations, included boundary, exclusions]
Comparison:
  Before: [real base commit, working-tree base, prior artifact, or prior state]
  After: [real head commit, current working-tree files, artifact, or current state]
Stage: [local implementation, integrated package, pre-merge, document review, etc.]
Requirements and standard: [focused sources and code-review-and-quality]
Implementation context: [verified summary, dependencies, interfaces]
Existing evidence: [command/observation, artifact identity, result, provenance, limits]
Risks and unknowns: [remaining risks and dependent conclusions/actions]
Allowed/prohibited actions and resources: [effective bounds]

Return:
- nature, mode, scope, both comparison sides, and stage actually reviewed;
- Critical, Required, and Optional/Nit findings with exact locations, impact, and correction;
- specification verdict when applicable and quality verdict when applicable;
- validation inspected or run, with commands/results and evidence limits;
- unknowns, conflicts, exclusions, and unreviewed behavior.
```

## Receive and Reconcile the Review

Inspect the report against the actual artifact and request. Confirm the reviewer used the named scope, both comparison sides, and valid evidence. Apply [receiving-code-review](../receiving-code-review/SKILL.md): verify every finding before changing the artifact, fix supported required findings, preserve evidence-backed disagreement, and pause only work dependent on an unresolved item.

After a change made in response to a finding, rerun the affected check and re-review the affected scope. A reviewer verdict cannot replace controller integration, required runtime or human acceptance, or delivery authorization.

## Red Flags

- A request with no objective, scope, requirements, or actual baseline
- A commit range that does not represent the artifact under review
- Only one side of a comparison, or evidence without artifact identity and provenance
- Saying tests passed without exact current results or overstating what static checks prove
- Hiding known risks or asking a reviewer to rediscover the whole project
- Adding fixed review layers beyond the shared standard and applicable project policy
- Calling a self-review independent or treating a verdict as permission to merge
- Running Git commands or creating artifacts only to make a template fit

## Verification

Before dispatch, confirm that the request names the objective, scope, both comparison sides, stage, applicable requirements, shared standard, current evidence with limits, remaining risks, reviewer nature, action boundaries, resources, and evidence-bearing return. After return, verify the report and integrated artifact before making any completion or delivery claim.

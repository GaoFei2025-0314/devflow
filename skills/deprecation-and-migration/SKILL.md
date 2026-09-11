---
name: deprecation-and-migration
description: Designs and carries out deprecation and migration safely. Use when evaluating replacement, compatibility, consumer transition, or eventual removal of a system, API, feature, or capability.
---

# Deprecation and Migration

## Overview

Deprecation balances the continuing value and cost of an existing capability against the cost and risk of transition. Migration moves consumers, behavior, or data while preserving compatibility and a recovery path appropriate to the scope. Lower code volume, age, or rare observed use is evidence to investigate, not a direction to remove capability.

Apply the shared [Phase and Delivery Contract](../using-devflow/references/phase-contract.md), [Authorization and Trust Contract](../using-devflow/references/authorization-contract.md), [Evidence Contract](../using-devflow/references/evidence-contract.md), and [Delivery Contract](../using-devflow/references/delivery-contract.md).

## When to Use

- Evaluating whether to maintain, replace, consolidate, or retire a capability
- Designing compatibility and consumer transition for a new system or API
- Implementing adapters, dual operation, backfills, or progressive routing
- Executing an authorized migration or removal
- Planning lifecycle and recoverability before a new system launches

## Keep the Phases Separate

### Design

A design-only request ends with a reviewable migration design. It may include inventory, alternatives, compatibility, stages, verification, recovery, risks, estimates, and decisions still needed. It does not authorize building the replacement, modifying consumers, migrating shared data, notifying users, or removing the old system.

### Implementation

Implementation requires an explicit implementation objective and bounded files or systems. It can prepare replacement code, adapters, migration tooling, documentation, tests, or locally safe artifacts within that grant. Completing implementation does not prove production behavior or authorize executing a shared or production migration.

### Execution and Removal

Executing production or shared-data changes, changing infrastructure, deleting or bulk-mutating data, switching consumers, public deprecation communication, and removing artifacts are distinct actions. Immediately before each action, establish its effective authorization record. Reuse a valid grant only while action, target, environment, scope, source, conditions, and current state still match.

A recovery plan is preparation. It does not authorize deleting data, overwriting customizations, rewriting history, rolling back production, or taking another destructive step.

## Evaluate Before Deprecating

Answer these questions with evidence appropriate to the decision:

1. What behavior or capability exists, and what unique value does it provide?
2. Which consumers, integrations, data, observable behavior, and undocumented dependencies may rely on it?
3. What applicable opportunities were observed when measuring use? Was applicability known, absent, or unknown?
4. What alternatives exist, and do they cover critical use cases and compatibility constraints?
5. What are the migration, support, security, operational, and long-term maintenance costs of each option?
6. What transition period, ownership, verification, and recovery are needed?

Zero observed use is meaningful only when the observation had applicable opportunities, sufficient coverage, and a known denominator. When no relevant task or consumer opportunity occurred, report no applicable opportunity. When applicability cannot be determined, report unknown. Do not calculate a trigger or usage rate without a denominator, count unknown as unused, or remove a skill or capability solely because it is rare.

Possible outcomes include maintain, improve, adapt, consolidate, deprecate gradually, or remove after conditions are met. Favoring less code cannot substitute for consumer and capability evidence.

## Advisory and Compulsory Deprecation

| Type | Appropriate use | Required planning |
| --- | --- | --- |
| **Advisory** | Consumers can move on their own schedule and the old system remains supportable | Clear status, replacement options, compatibility expectations, guidance, ownership, and observation |
| **Compulsory** | A supported risk or constraint requires a deadline | Decision authority, impact analysis, deadline, tooling or assistance, compatibility plan, escalation, verification, and recovery |

Defaulting to advisory can reduce disruption, but the choice must follow actual risk, policy, and consumer needs. Announcing a deadline, contacting consumers, or changing a public contract is an outward-facing action under applicable project policy.

## Design the Migration

### Inventory and Replacement Evaluation

- Identify direct and indirect consumers, data flows, contracts, configuration, operations, and owners.
- Record behavior that must remain compatible, intentionally changes, or is still unknown.
- Evaluate whether to build, buy, adapt, or continue the current system. A replacement is not automatic.
- Define acceptance criteria for the replacement and migration tooling at their actual phase.
- Validate critical behavior in an appropriate pre-production setting when required; production proof belongs to a later phase and is not required to complete a design.

### Compatibility Period

Choose a compatibility approach and duration based on consumer control, release cadence, risk, and rollback needs. Options include:

- an adapter preserving the old interface over a new implementation;
- dual reads or writes with reconciliation where data semantics permit;
- versioned APIs or schemas with an overlap period;
- a strangler route that moves bounded traffic or consumers progressively; and
- import/export, backfill, or translation tooling with validation and restartability.

Specify ownership, support policy, entry and exit criteria, observability, and how incompatible behavior is handled. A target removal date is a plan, not permission to remove anything.

### Progressive Transition

For each authorized stage:

1. Identify exact consumers, data, target, environment, and expected effects.
2. Confirm prerequisites, compatibility, authority, and a viable recovery point.
3. Apply the smallest safe transition step.
4. Verify behavior, data invariants, reconciliation, performance, and errors that the stage can affect.
5. Preserve failures and investigate before retrying or advancing.
6. Hold, recover, or advance using project-specific criteria.

Avoid big-bang migration when staged transition materially reduces risk. Do not imply that progressive routing or a feature flag makes an unfinished work package ready for PR or merge.

## Migration Patterns

### Strangler Pattern

Run old and new paths in parallel and route bounded consumers or traffic progressively. Keep a compatible route back while it remains safe and needed. Reaching zero routed traffic is evidence for a removal decision, not removal authorization and not proof that no hidden consumer exists.

### Adapter Pattern

Preserve the old interface while translating to the new implementation:

```typescript
class LegacyTaskService implements OldTaskAPI {
  constructor(private newService: NewTaskService) {}

  getTask(id: number): OldTask {
    const task = this.newService.findById(String(id));
    return this.toOldFormat(task);
  }
}
```

Test both the translation and observable compatibility. Record intentionally unsupported behavior rather than silently dropping it.

### Dual Operation and Reconciliation

When old and new data paths coexist, define the source of truth, ordering and idempotency rules, reconciliation method, cutover criteria, and response to divergence. Dual writes can increase failure modes and require explicit data-risk review.

## Removal

Removal is a later implementation and delivery decision. Before presenting it as ready:

- all in-scope consumers are migrated or explicitly accepted as exceptions;
- the observation window and denominator support the no-use claim;
- contracts, data retention, compatibility, support, and recovery obligations are satisfied;
- required checks and review pass for the current relevant state; and
- the exact deletion, configuration, data, communication, and cleanup actions have applicable authorization.

Remove only the authorized objects. Preserve user customizations and other sources. A successful migration does not authorize branch deletion, worktree cleanup, global installation changes, or unrelated artifact removal.

## Verification and Completion

Match evidence and completion language to the phase:

- **Design ready:** the reviewable design covers alternatives, consumers, compatibility, stages, evidence needs, recovery, risks, and pending decisions; no implementation or execution is implied.
- **Implementation complete:** the agreed replacement, adapters, tooling, tests, or documentation are complete and reviewed; shared or production execution may remain pending.
- **Migration step verified:** the named action ran against the named target under applicable authorization, and its behavior and data observations are recorded with limits.
- **Removal ready or complete:** consumer evidence, compatibility obligations, required checks, exact scope, authorization, and post-action verification support that specific state.

Required failures block the dependent conclusion. Keep failures, investigation, retry reasons, and later results. Automated checks, production observations, human acceptance, authorization, and accepted deferrals remain separate evidence.

Low observed frequency without applicable opportunities cannot justify deleting this skill or another capability. Future deprecation of a Devflow entrypoint requires its own replacement, impact analysis, compatibility route or alias, migration period, and authorization.

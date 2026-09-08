---
name: shipping-and-launch
description: Prepares production launches. Use when preparing to deploy to production, defining rollout and recovery, or verifying a release after an authorized launch.
---

# Shipping and Launch

## Overview

Prepare a release so its artifact, target, risks, verification, rollout, and recovery are reviewable before any protected action. A launch should be observable and recoverable, with scope and decision criteria suited to the project. Preparation can finish independently; deploying, releasing, rolling back, changing infrastructure, migrating production data, notifying people, and cleanup are separate actions.

Apply the shared [Phase and Delivery Contract](../using-devflow/references/phase-contract.md), [Authorization and Trust Contract](../using-devflow/references/authorization-contract.md), [Evidence Contract](../using-devflow/references/evidence-contract.md), and [Delivery Contract](../using-devflow/references/delivery-contract.md).

## When to Use

- Preparing or executing a production deployment or public release
- Planning a staged rollout, beta, or early-access program
- Defining health checks, monitoring, rollback, or recovery
- Coordinating an operational change involving data or infrastructure

Use the migration skill for migration design and compatibility. Add security, performance, accessibility, or other domain guidance only when the release touches that risk surface.

## Separate Preparation From Execution

Launch preparation should resolve:

- the exact artifact or revision, target environment, affected users or systems, and rollout scope;
- the project's delivery policy and the evidence required at this boundary;
- prerequisites, owners, decision points, expected effects, and stop conditions;
- health checks, observability, recovery options, and residual risks; and
- each protected or outward-facing action that still needs authorization.

Completing this preparation does not execute or authorize a deployment. Immediately before each state-changing action, establish the authorization record required by the Authorization and Trust Contract. Reuse an effective grant when its action, target, environment, scope, source, conditions, and current validity still match. A changed environment, artifact, scope, or unavailable approval source requires a new decision only for the affected action.

Merge approval is not deployment or public-release approval. A deployment grant does not cover rollback, production-data cleanup, a different environment, notifications, or later branch and worktree removal unless its terms explicitly include them.

## Release Readiness

Select checklist items from the release's behavior, dependencies, risk, and mandatory project gates. Mark irrelevant items not applicable with a reason instead of treating this list as universal.

### Artifact and Delivery State

- [ ] Exact artifact, revision, environment, and scope identified
- [ ] The agreed work package is complete under project policy; partial increments are still reported as progress
- [ ] Required implementation review is resolved or an accepted deferral is recorded
- [ ] Push, pull request, merge, deploy, release, install, and cleanup states are reported separately

### Verification and Evidence

- [ ] Actual project commands and required checks identified from project policy and files
- [ ] Checks cover the affected behavior and dependency boundaries
- [ ] Required checks pass for the relevant state; failures, investigations, and justified retries remain recorded
- [ ] Existing warnings are distinguished from warnings introduced or exposed by the release
- [ ] Required runtime, browser, API, manual, or stakeholder observations are complete or truthfully pending/deferred

### Security and Data

- [ ] No secrets are embedded in code, workflow files, logs, or release artifacts
- [ ] Authentication, authorization, privacy, input validation, dependency, and configuration checks are complete where affected
- [ ] Telemetry uses an existing authorized destination and approved data handling
- [ ] Schema, shared-data, cleanup, and destructive recovery steps have their own impact and authorization boundaries

### Operations and Documentation

- [ ] Production configuration, health endpoints, logging, alerting, capacity, DNS, certificates, and dependencies are checked where applicable
- [ ] Success, hold, rollback, and escalation criteria use project baselines and service objectives
- [ ] Runbooks, API or user documentation, changelog, and operator notes are current where affected
- [ ] A written recovery plan identifies exact targets, commands or procedures to verify, expected effects, and post-action checks

## Feature Flags and Staged Rollout

Feature flags can separate deployment from user exposure when the system already supports them and both states can be verified. They do not make unfinished work complete, bypass the project's push/PR readiness policy, or authorize an early merge or deployment.

For each applicable flag, record an owner, intended lifetime, removal condition, state-specific tests, and recovery behavior. Flag cleanup is a later code change and delivery action under project policy; a target date is planning, not permission to remove it.

A possible staged rollout is:

1. Verify the candidate in the appropriate pre-production environment.
2. Deploy the identified production artifact under applicable authorization, with exposure disabled when supported.
3. Confirm deployment health and telemetry.
4. Enable a bounded cohort, compare it with an applicable baseline, and hold for the observation window justified by traffic and risk.
5. Increase exposure only when the project's success criteria pass; otherwise hold or prepare the appropriate recovery action.
6. Verify full exposure and schedule any separately authorized cleanup.

Percentages, observation windows, and thresholds such as a percentage change in errors or latency are examples to calibrate from service objectives, traffic volume, business risk, and baseline variance. They are not universal gates or grants to advance or roll back.

## Monitoring and Post-Launch Verification

Observe only signals relevant to the release, such as:

- application errors, latency, volume, saturation, queues, and dependency health;
- client errors and user-facing performance for affected interfaces;
- data integrity, reconciliation, and migration progress where applicable; and
- business or safety indicators that define the release's expected result.

After each authorized rollout step, verify the deployed artifact and target, health checks, critical flows, logs or telemetry, and applicable data invariants. Record the operation, time, environment, result, source, and limits. Static checks do not prove production behavior, and a passing unrelated check cannot override a required failure.

Telemetry examples in [references/examples.md](references/examples.md) assume an existing authorized integration. Introducing a service or sending identifiers is a separate integration, privacy, and configuration decision.

## Rollback and Recovery

Prepare recovery before launch. The plan should cover:

- trigger conditions and who evaluates them;
- exact affected artifact, environment, data, and consumers;
- available methods such as disabling exposure, redeploying a known artifact, restoring compatibility, forward-fixing, or applying a verified data recovery procedure;
- ordering, prerequisites, expected duration, data loss or consistency risk, and the point of no simple return; and
- health, behavior, and data observations after recovery.

Recovery may require several actions. Do not assume it is a single command, that a database change is reversible, or that immediate rollback is safer than holding or forward repair. A written command is a candidate until it is verified against the project and target. Planning recovery does not authorize a rollback, push, history change, data deletion, overwrite, or consumer notification.

A copyable preparation template is in [references/examples.md](references/examples.md).

## Delivery State

Before launch, report the completed preparation, exact evidence, failures or deferred observations, and the concrete pending action. After an authorized launch step, report what actually ran and the resulting observations. Keep required failures blocking until diagnosed and reverified; preserve earlier failures and retry reasons even after a later pass.

Do not imply that launch preparation, a green CI run, human acceptance, merge approval, or a recovery plan performed or authorized another delivery step.

## See Also

- Project-wide completion baseline: [Definition of Done](../incremental-implementation/references/definition-of-done.md)
- Migration and compatibility: [Deprecation and Migration](../deprecation-and-migration/SKILL.md)
- Security review: [Security and Hardening](../security-and-hardening/SKILL.md)
- Performance verification: [Performance Optimization](../performance-optimization/SKILL.md)
- UI and accessibility verification: [Frontend UI Engineering](../frontend-ui-engineering/SKILL.md)

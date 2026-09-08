---
name: ci-cd-and-automation
description: Designs and maintains CI/CD pipelines. Use when selecting automated gates, configuring CI diagnostics or deployment mechanisms, or investigating pipeline failures.
---

# CI/CD and Automation

## Overview

CI should enforce the checks the project actually requires and preserve enough evidence to diagnose failures. The useful pipeline is the smallest reliable set of gates that covers the affected behavior, dependencies, risk, and project policy. CI configuration, pull-request readiness, merge, preview deployment, production deployment, rollback, recurring automation, notification, and cleanup remain distinct decisions.

Apply [Project Command Selection](../using-devflow/references/project-commands.md), the shared [Evidence Contract](../using-devflow/references/evidence-contract.md), [Authorization and Trust Contract](../using-devflow/references/authorization-contract.md), and [Delivery Contract](../using-devflow/references/delivery-contract.md).

Worked mechanisms in [references/examples.md](references/examples.md) are provider-specific examples, not universal commands, required gates, or authorization to configure an external service.

## When to Use

- Creating or changing a project's CI pipeline
- Adding, removing, or tuning automated quality gates
- Configuring diagnostic artifacts, test services, or deployment workflows
- Investigating a failed or unreliable CI check
- Designing preview, staged deployment, rollback, or recurring maintenance automation

## Select Real Project Commands

Before writing a workflow, inspect the applicable project instructions, manifests, lockfiles, workspace configuration, and actual scripts. Use the established package manager or non-JavaScript task runner consistently. Do not copy `npm ci`, `npm test`, a type checker, an audit tool, or any other example unless project evidence selects it.

If command signals conflict, resolve the conflict using the project-command contract before execution. Do not install tooling, create another lockfile, or change authentication merely to make an example run.

## Design the Gate Set From Risk

A project may order inexpensive checks before slower checks, but the specific gates depend on the change and project policy:

```
Change proposed
    │
    ├── required formatting, lint, or static checks
    ├── focused behavior or regression checks
    ├── type, build, integration, or end-to-end checks where affected
    ├── security, dependency, bundle, schema, or release checks where affected
    └── mandatory project and branch-protection gates
          │
          ▼
Evidence ready for the next project-defined delivery decision
```

For every major check, identify the failure it can catch and the object it covers. Documentation may need content and reference checks; logic changes need regression coverage; UI changes may need build, type, browser, interaction, accessibility, and visual evidence; APIs, dependencies, build configuration, security surfaces, and release candidates usually require broader coverage.

Do not omit a mandatory gate because a focused check passed. Do not impose the same lint, types, tests, build, audit, integration, E2E, or bundle stack on every change when the project does not require or support it. Mark a check not applicable with a reason instead of pretending it passed.

## Preserve Failure Evidence

A required failed check blocks the completion, merge, deployment, or release conclusion that depends on it. Keep the failed command, object, environment, output source, and consequence. Diagnose from the available evidence before retrying.

A justified retry records:

1. the earlier failure;
2. the investigation and reason to retry;
3. any relevant code, configuration, dependency, data, or environment change, or why unchanged-state repetition is informative; and
4. the new operation and result.

Do not repeatedly run a suspected flaky test until it passes or claim an environmental cause without locating it. A later pass may satisfy the gate for its covered state, but it does not erase the failure history. Separate existing warnings from new or newly exposed warnings and apply the project's actual warning policy.

Upload bounded failure artifacts such as test reports, logs, or screenshots when the project's approved CI system supports it. Avoid secrets and sensitive data, define retention appropriately, and do not add an external artifact destination without applicable authorization.

## Pull Requests, Merge, and Delivery

CI evidence does not decide whether a work package is complete or authorize a delivery action. Apply the project's PR timing and merge policy:

- A partial internal increment remains progress. A feature flag does not make it a complete or review-ready work package.
- Push and PR creation wait for the required implementation, review, checks, and evidence unless project policy or an explicit request provides a scoped exception.
- Green CI does not authorize a risky merge. Human review, manual acceptance, automated checks, and merge authorization are separate records.
- For a risky change, finish the reviewable PR material and required evidence first, then request approval for the concrete merge only when that action is ready.
- A failed required check still blocks its dependent action after human acceptance or approval. Preserve the acceptance, diagnose and reverify, then reuse the action grant only if its complete conditions still match.
- Accepted manual deferrals remain visible with their source and scope; automation must not relabel them as passed.

## Deployment and Rollback Mechanisms

Preview deployments, staging deployments, production deployments, feature exposure, and rollback workflows can be useful mechanisms. Configure or execute them only when the project uses the provider and the action, target, environment, secrets, cost, and data handling are authorized.

Automatic deployment is a project policy, not a CI default. A workflow trigger is capable of causing an external action and must reflect that policy. A deployment or rollback grant for one environment does not cover another environment, data deletion, communication, or cleanup.

Feature flags can support bounded exposure and recovery when already available. They do not authorize incomplete merges or replace verification of both relevant states. Record ownership and a cleanup condition; flag removal follows normal implementation and delivery policy.

A recovery mechanism may require multiple ordered steps, compatibility restoration, or a forward fix. Verify candidate commands against the actual platform and artifact. Do not assume rollback is one action or that a database operation is safely reversible.

## Secrets and Test Environments

- Keep credentials in the project's approved secret store, never in code or workflow text.
- Use test-specific credentials and least privilege; do not expose production secrets to CI unless a reviewed project requirement explicitly needs them.
- Treat test databases, migrations, fixtures, and teardown as data operations with bounded targets and recoverability.
- Prevent commands and uploaded artifacts from leaking tokens, identifiers, customer data, or internal details.

## Recurring Automation

Dependency-update schedules, build-cop rotations, notifications, monitors, and automated cleanup are optional operational choices. Establish ownership, trigger, scope, cost, rate limits, failure handling, and authorization before enabling them. An example schedule does not create an ongoing task or approve a new integration.

## Pipeline Performance

Optimize when measured duration, cost, or feedback delay misses the project's objective. Depending on evidence, useful techniques include dependency caches, safe parallel jobs, path-aware selection, test sharding, removing redundant work, and right-sizing runners. Preserve mandatory coverage and diagnostics while optimizing. A numeric runtime target in an example is illustrative unless project policy adopts it.

## Verification

After changing CI/CD guidance or configuration:

- [ ] Commands match project policy, lockfiles, manifests, and actual scripts
- [ ] Each required gate has a stated risk and affected scope
- [ ] Required failures block their dependent conclusions and retain diagnostic evidence
- [ ] Retries, baseline warnings, and accepted manual deferrals remain visible
- [ ] Work-package, PR, merge, deploy, rollback, notification, and cleanup states are separate
- [ ] Secrets, sensitive data, provider access, and external integrations follow applicable policy
- [ ] Any preview, deployment, rollback, or recurring trigger has the intended authorization boundary
- [ ] Runtime and cost goals come from project evidence rather than a universal threshold

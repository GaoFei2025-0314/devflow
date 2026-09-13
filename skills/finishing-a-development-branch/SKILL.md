---
name: finishing-a-development-branch
description: Guides evidence-backed completion and integration of a development branch under the current project's delivery, authorization, CI, merge, synchronization, and cleanup policies.
---

# Finishing a Development Branch

## Purpose

Finish the current work package in the way its project requires. This skill does not impose a fixed completion menu or assume that local merge, push, pull request, branch deletion, or worktree removal is authorized.

Use the [Shared Delivery Contract](../using-devflow/references/delivery-contract.md) to decide readiness and reporting state, and the [Shared Authorization and Trust Contract](../using-devflow/references/authorization-contract.md) before each state-changing action.

## 1. Inspect the Delivery State

Confirm the repository, current branch or worktree, intended base, existing changes, and the complete agreed work-package scope:

```bash
git rev-parse --show-toplevel
git status --short --branch
git worktree list
git log --oneline --decorate -n 12
```

Determine whether the work package is fully implemented, reviewed, and supported by all required automated, runtime, UI, and human evidence. Use project-specific commands and valid current evidence. Entering this skill does not require a dependency reinstall or a ritual rerun of unrelated suites.

Preserve every failed required check in the report. Resolve it before the dependent PR or merge gate. An unrelated known failure may remain recorded while other authorized work continues if project policy does not make it a gate. A completed internal increment must be reported as progress while any agreed obligation, required verification, or review remains pending.

## 2. Choose the Applicable Endpoint

Derive the next step from the user's request, project policy, package state, and effective grants. Legal outcomes include:

- keep the branch or worktree for continued local work;
- report implementation or checks complete while human acceptance is pending;
- prepare or create a pull request after the complete package and its required review and checks are ready;
- wait for authorization for a concrete risky merge or other protected action;
- merge under a matching project policy and effective grant after required CI and protection rules pass;
- preserve or discard work when the user specifically chooses and authorizes that result.

Ask only for a concrete missing decision at the first action that depends on it. Reuse an existing grant when its action, target and environment, scope, source, conditions, and validity remain unchanged.

## 3. Prepare a Reviewable Pull Request

Normal PR timing is the complete agreed work package, after implementation review and every check the project requires before push/PR, including CI when assigned to that gate. Resolve this gate from the effective rules before choosing operation order, using the Shared Delivery Contract. A general push/PR grant does not waive a pending, failed, or unobserved pre-PR check. Finish reviewable local material while that gate is closed. An early or draft PR requires the explicit exception provided by the user or project policy.

Before an authorized push or PR, inspect the intended diff and prepare:

- the concrete problem and resulting behavior;
- full scope and target branch;
- risk classification;
- exact validation commands and results;
- screenshots or browser evidence for applicable UI changes;
- API and data impact;
- known residual risks, failures, and accepted deferrals.

Push and PR creation are distinct from merge. Checks assigned to the push/PR gate must pass before those actions; required merge CI and branch protection also apply after creation.

## 4. Decide Whether Merge Is Allowed

Apply the current project's merge policy to the exact current PR. A project may have standing authorization for narrowly scoped, reversible, presentation-only work, but use it only when every policy condition and evidence gate holds. A change that affects logic, state, persistence, permissions, auth, security, privacy, API or database contracts, dependencies, configuration, infrastructure, payments, monitoring, or external integrations is outside such a presentation-only grant. Uncertain risk also requires a concrete merge decision.

Passing CI is necessary when policy requires it, but does not authorize a risky merge. Do not bypass review, required checks, or branch protection through a local merge path.

If integration is authorized, execute the project's documented merge method and verify the resulting state with the applicable checks. Record the PR, merge revision, and actual evidence.

## 5. Synchronize and Preserve Cleanup Boundaries

After a remote merge, synchronize the applicable primary checkout when the project policy and grant cover it, for example:

```bash
git switch <default-branch>
git pull --ff-only <remote> <default-branch>
```

Resolve the exact checkout and ensure existing work will not be overwritten before running those commands.

Branch deletion, worktree removal, and discarding commits or uncommitted files are separate cleanup actions. Name each target, assess recoverability, and require a matching grant. Do not infer cleanup authority from merge, PR creation, synchronization, or earlier worktree creation. Preserve the branch and worktree when cleanup is not authorized.

## 6. Report the Actual State

Report:

1. the exact completed scope, branch or PR, revision, and environment;
2. checks, CI, review, runtime, UI, and human evidence with results and limits;
3. incomplete work, failed or pending gates, and accepted deferrals;
4. the exact next action or authorization still needed;
5. preserved branches, worktrees, or other artifacts.

Use delivery language that matches the current artifact: document ready, implementation complete, automated checks passed, human acceptance pending, specific authorization pending, or final delivery.

## Red Flags

- Offering a fixed menu that ignores an already valid choice or grant.
- Treating a focused check as proof of the whole work package.
- Creating an early PR for an unfinished normal work package.
- Treating green CI as merge authorization.
- Merging locally to bypass required PR review or protection.
- Automatically deleting a branch or removing a worktree after merge or PR creation.
- Discarding work without resolving the exact target and authorization.

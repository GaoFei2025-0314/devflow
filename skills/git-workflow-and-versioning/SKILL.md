---
name: git-workflow-and-versioning
description: Structures Git branches, commits, work packages, and versioning under the current project's delivery and authorization policy. Use when deciding Git state or actions, commit granularity, PR timing, integration, or cleanup.
---

# Git Workflow and Versioning

## Purpose

Use Git to keep changes reviewable and recoverable. Branching, commits, pull requests, merges, synchronization, and cleanup are separate decisions; the current project's policy decides which apply.

Before changing Git state, use the [Shared Delivery Contract](../using-devflow/references/delivery-contract.md) for readiness and evidence and the [Shared Authorization and Trust Contract](../using-devflow/references/authorization-contract.md) for action grants. A skill recommendation, completed implementation, or passing check does not supply authorization.

## Inspect Before Acting

Resolve the actual repository and policy before choosing a workflow:

```bash
git rev-parse --show-toplevel
git status --short --branch
git worktree list
git remote -v
```

Identify the intended base, current branch or worktree, existing changes, and the project's commands and delivery rules. Preserve unrelated and pre-existing work. If an adequate authorized branch or worktree already exists, verify its identity and relevant state and reuse it; do not create a nested workspace or repeat initialization merely because this skill was entered.

A document-only request can end with a local reviewable document. It does not itself authorize implementation, branch creation, a worktree, a commit, or an external Git action.

## Separate Git and Delivery Decisions

Evaluate these stages independently:

1. local edits;
2. commits;
3. complete work package;
4. push and pull request;
5. merge;
6. synchronization after merge;
7. branch, worktree, or artifact cleanup.

For every state-changing action, bind the grant to the operation, repository and environment, exact scope, source, conditions, and current validity. Reuse an existing grant while all those fields still match. Re-check only when the action, target, scope, environment, conditions, risk, or source changes. Subagents cannot approve protected actions.

## Branch Strategy Follows Project Policy

Short-lived topic branches are often useful because they isolate a reviewable unit, but they are not mandatory for every project or phase. Read the repository's policy and inspect existing state first.

A supported project policy may, for example, allow V1 implementation and local commits on local `main` while treating a push to remote `main` as a separate protected action. The same project may require V2 and later work to start from current `main` on `feature/<name>`, `fix/<name>`, `ui/<name>`, `refactor/<name>`, or `chore/<name>` and to integrate through a pull request. These are adaptation examples, not universal Devflow defaults.

When a new branch is required, confirm the base is the revision required by project policy before creating it. Do not overwrite or clean existing changes to make the state look clean.

## Commits

When commits are authorized and appropriate, make each commit a coherent, reviewable unit. Keep behavior changes, broad formatting, refactors, and dependency changes separate when that improves review and rollback. Commit size is a reviewability judgment, not a fixed line limit.

Use the repository's message convention. A common format is:

```text
<type>: <short description>

<optional reason or context>
```

Before committing, inspect the exact staged diff and run the relevant current checks required by the project:

```bash
git diff --staged
git status --short
<project-specific focused checks>
```

Do not assume `npm`, reinstall dependencies, or run an unrelated full suite solely because a Git skill was loaded. Use the project's package manager and commands. Record existing failures and decide whether each is relevant to the current gate. Do not discard work with `reset --hard` as a routine recovery technique; inspect the state and preserve work before choosing a recovery action.

## Work-Package and Pull-Request Timing

Open a pull request when the entire agreed work package is implemented, reviewed, and supported by every required check and evidence item under project policy. An internal increment is progress, not a completed version. Do not use an early or draft PR as the default progress mechanism; an explicit project or user request may authorize that exception.

PR material should let a reviewer assess the final change without conversational history. Include:

- the concrete problem and resulting behavior;
- the complete scope and exact target branch;
- risk classification;
- validation commands and results, including relevant failures;
- UI or browser evidence when applicable;
- API and data impact;
- known residual risks and accepted deferrals.

Push and PR creation require the applicable action grant. Required CI, review, and branch protection remain gates after the PR exists and cannot be bypassed by local integration.

## Merge Policy

Apply the actual project policy to the exact reviewable PR. Passing CI establishes evidence; it does not create merge authorization.

Some projects grant standing merge authorization for presentation-only changes. Use it only when every stated condition holds, including narrow and reversible scope, presentation-only behavior, all required checks and browser evidence, and no logic, state, persistence, auth, security, privacy, API, database, dependency, configuration, infrastructure, payment, monitoring, integration, secret, generated-artifact, unrelated-change, or unresolved-review impact. If any condition fails or risk is uncertain, prepare the reviewable PR and wait for authorization for that concrete merge.

Never bypass required CI or branch protection. History rewrites, force-pushes, direct pushes to a default branch, and branch deletion require matching authorization under the shared contract and project policy.

## After Integration

After a remote merge, synchronize the applicable primary checkout when project policy and authorization cover that step, then report the resulting revision and evidence. A completed merge does not authorize deleting local or remote branches, removing worktrees, or discarding other artifacts. Resolve each cleanup target and grant separately; otherwise preserve it.

## Reporting

Report the exact completed scope, revision and environment, checks and review evidence with their limits, failures or pending gates, accepted deferrals, and the next concrete Git or delivery action. Use accurate states such as document ready, implementation complete, automated checks passed, human acceptance pending, specific authorization pending, or final delivery.

## Verification

- [ ] Repository, branch or worktree, base, and existing changes were inspected.
- [ ] The current project policy was applied rather than inferred from this skill.
- [ ] Unrelated work was preserved.
- [ ] The diff and commits, if any, are coherent and reviewable.
- [ ] Evidence is current, scoped, and recorded with failures and limits.
- [ ] The whole agreed work package is complete before a normal push or PR.
- [ ] Merge conditions and authorization match the exact PR and risk.
- [ ] Synchronization and every cleanup action were evaluated separately.

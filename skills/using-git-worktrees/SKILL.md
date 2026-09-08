---
name: using-git-worktrees
description: Inspects, reuses, or creates an isolated Git worktree when the current project and task need one, while preserving existing work and respecting setup, evidence, authorization, and cleanup boundaries.
---

# Using Git Worktrees

## Purpose

Worktrees can isolate concurrent branches without repeated branch switching. Use one when isolation is useful and project policy allows it. Do not create a worktree merely because this skill was loaded or because a document or plan was approved.

Use the [Shared Delivery Contract](../using-devflow/references/delivery-contract.md) for readiness and evidence, and the [Shared Authorization and Trust Contract](../using-devflow/references/authorization-contract.md) before creating, changing, or removing Git objects.

## 1. Decide Whether a Worktree Is Needed

First inspect the current environment:

```bash
git rev-parse --show-toplevel
git status --short --branch
git worktree list --porcelain
```

Resolve the task scope, required base and branch, project policy, existing changes, and ownership of the current checkout. If an existing authorized environment has the correct repository, branch, base, and scope, reuse it after checking relevant state. Preserve other people's commits and uncommitted files. Do not nest or duplicate a worktree, reinitialize the repository, or clean existing state to satisfy a template.

A spec-only or plan-only request normally ends with a local reviewable document under its project policy. It does not grant implementation, branch, worktree, commit, or external delivery authority.

Create a new worktree only when the task needs isolation and the applicable policy and authorization cover the exact repository, path, branch, and scope.

## 2. Select and Validate a Location

Follow explicit repository instructions first. Existing conventions such as `.worktrees/`, `worktrees/`, or an external workspace root are useful evidence but do not override project policy.

For a project-local location, verify Git ignores the parent before creating anything:

```bash
git check-ignore -q .worktrees
```

If it is not ignored, report the conflict and obtain or reuse authorization before changing `.gitignore`; that edit and any commit are separate actions. An external worktree directory avoids repository tracking but still requires an exact, safe path.

Before creation, verify the branch name is not already checked out elsewhere and confirm the intended base revision:

```bash
git branch --show-current
git rev-parse <base>
git worktree list --porcelain
```

Then use the project-approved form, for example:

```bash
git worktree add <path> -b <branch> <base>
```

Do not assume every project branches from `main`; use its actual default or required base. Short-lived branch naming such as `feature/<name>`, `fix/<name>`, `ui/<name>`, `refactor/<name>`, or `chore/<name>` is an example when the project adopts it.

## 3. Load the Existing Project

After entering a new or reused worktree, inspect its instructions, lockfiles, dependencies, and available runtime. Use the project's established package manager and commands. Do not automatically reinstall dependencies, change a lockfile, or install tooling solely because a worktree was selected.

Run only setup needed for this environment and authorized scope. If setup would change dependencies, configuration, authentication, global installation, or an external service, apply the separate authorization boundary first.

## 4. Establish Scoped Baseline Evidence

Use focused project checks that distinguish pre-existing state from changes relevant to the task. Reuse valid current evidence when its artifact, revision, environment, command, and scope still match. Entering this skill does not invalidate evidence or require a full-suite rerun.

Record each command, revision, result, and scope limit. If a required baseline check fails, preserve the failure and determine whether it blocks the intended work or delivery gate. Continue unrelated authorized work when safe; do not ask for a new permission merely because an existing failure was observed. Investigate, narrow scope, or request a decision only when the failure creates a real dependency or policy boundary.

Report readiness accurately, for example:

```text
Worktree verified at <absolute-path> on <branch> at <revision>.
Focused baseline: <command and result>.
Known failure or pending gate: <scope and impact>.
```

Do not claim a clean or passing baseline without direct applicable evidence.

## 5. Delivery and Cleanup

A worktree only supplies an isolated local environment. It does not authorize commits, push, PR creation, merge, deployment, synchronization, branch deletion, or worktree removal. Evaluate those steps under the shared contracts and current project policy.

After integration, preserve the worktree and its branch unless removal and any branch deletion are separately authorized for those exact targets. Inspect for uncommitted or unpushed work before any authorized removal. Never use forced cleanup to hide a conflict or erase work outside the current scope.

## Verification

- [ ] The repository, existing worktrees, branch, base, and working state were inspected.
- [ ] An adequate existing authorized environment was reused when appropriate.
- [ ] A new worktree was created only when isolation and policy required it.
- [ ] A project-local parent was verified ignored before creation.
- [ ] Existing work and other agents' changes were preserved.
- [ ] Setup used the project's actual tools without automatic reinstall or lockfile changes.
- [ ] Baseline evidence is scoped, current, and reports genuine failures.
- [ ] Commit, delivery, synchronization, and cleanup remain separate decisions.

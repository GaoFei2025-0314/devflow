# Delivery Details

Since 2.1.0 the canonical delivery rules are in [action rules: delivery](action-rules.md#delivery). This page keeps situational details; read it before an installation or release step, when a required check's timing relative to a push or pull request is unclear, or when adapting delivery rules to a project's policy.

## Installation reports

When a compatibility or reference check returns itemized paths, include or directly link the full checked-path list, with each resolved target or missing-reference reason, and bind it to the inspected artifact and the raw check record. A count alone does not substantiate the installation assessment. Treat local, shared, and global installations as distinct targets.

## Check timing around push and pull requests

- Map required checks to the actions they gate, using the effective project and user rules, before executing those actions.
- Where policy requires checks before a push or pull request, obtain their actual results first, and keep complete reviewable local material while any required result is missing or failed.
- If a required check can only run after the pull request exists, report that dependency rather than silently moving the gate.
- Apply an early-review, draft, or backup exception only when an effective user or project instruction explicitly supplies it, and only within its stated scope. Never infer the timing policy from a tool's operation order or availability.
- After a required check fails, diagnose and verify again before reusing an earlier action grant, and only if its complete authorization record and conditions still match.

## Deploy and release

Resolve the exact artifact, environment, rollout and rollback needs, health checks, and any production or publication gates before asking. Reuse a valid deployment or release grant only while its target, environment, scope, source, and conditions still match.

## Project-policy adaptation example

This example applies the delivery rules to one project's enduring policy. It is not a universal Devflow default; read the actual policy in each project.

- A document-only request ends with a local reviewable document and does not create a branch, commit, push, pull request, or implementation merely to show progress.
- V1 implementation may occur on local `main` with local commits when that project's policy authorizes it. A direct push to the remote default branch remains a separate protected action.
- V2 and later implementation starts from an up-to-date `main` on a short-lived working branch. A partial internal increment is progress; it does not trigger an early or draft pull request unless the user explicitly asks for that exception.
- Push and pull-request creation wait until the whole agreed work package is implemented, reviewed, and supported by all required checks and evidence. The pull request describes the problem and resulting behavior, full scope, risk class, validation commands and results, UI evidence when applicable, API or data impact, and residual risks. Required CI and branch protection are never bypassed, and an incomplete increment is not presented as a finished version.
- Standing authorization may cover a merge only when every presentation-only, low-risk condition holds: the change is narrow and reversible; it changes only presentation such as spacing, color, typography, copy, icons, non-functional animation, or responsive layout; it does not affect data flow, persistence, business rules, authentication, authorization, security, privacy, API contracts, database behavior, dependencies, runtime or build configuration, infrastructure, payments, monitoring, or external integrations; required tests, type checks, lint, build, CI, browser verification, and before-and-after screenshots are present as applicable; and there are no secrets, generated artifacts, unrelated changes, or unresolved review comments.
- Changes involving logic, state, permissions, dependencies, other listed risk surfaces, or uncertain impact may be pushed and opened as a reviewable pull request when those actions are authorized and ready, but the merge waits for explicit approval of that concrete pull request. Passing CI does not supply that approval.
- After a merge, synchronize the local primary repository. Keep local and remote branches and worktrees unless their removal is separately authorized.

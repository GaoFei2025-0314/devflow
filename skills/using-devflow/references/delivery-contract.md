# Shared Delivery Contract

Use this contract when deciding whether an artifact or work package is ready for a delivery step and when reporting its delivery state. The [Phase and Delivery Contract](phase-contract.md) remains the canonical source for phase inputs, legal endpoints, and completion language. The [Authorization and Trust Contract](authorization-contract.md) remains the canonical source for instruction authority, grant validity and reuse, and protected-action boundaries. This contract defines the evidence and action gates between those two concerns; it does not grant authority or replace either source.

## Treat each delivery step separately

Do not collapse implementation and delivery into one approval or one completion claim. Evaluate each applicable step against the current project policy, evidence, and authorization:

| Step | Readiness and evidence gate | Authorization gate |
| --- | --- | --- |
| **Local edit** | The implementation objective and file or system scope are bounded; applicable requirements and local checks are known. | Requires an effective grant for those local changes. Approval of a document alone does not grant implementation. |
| **Commit** | The intended diff has been reviewed, relevant checks have current results, and the commit contains only the agreed unit of work. | Follow the project's commit policy. Permission to edit does not by itself authorize a commit when policy separates them. |
| **Work-package complete** | Every agreed obligation is reconciled as completed, supported by valid proportionate evidence, or explicitly accepted as deferred. Required failures or pending review keep the package incomplete. | This is a status conclusion, not authority for a later Git or external action. |
| **Push / pull request** | The package satisfies the project's PR timing policy and every check that policy requires before this action, including CI when assigned to this gate. Review material identifies the exact branch, target, scope, risk, evidence, and known limits. | Push and PR creation need applicable authorization. An action grant does not waive its readiness conditions. |
| **Merge** | The exact reviewable PR is complete, required CI and protection rules pass, review findings are resolved or accepted under policy, and its current risk class satisfies the project merge policy. | Require a matching merge grant, including any effective standing authorization whose stated conditions all hold. Green CI alone does not grant a risky merge. |
| **Deploy or release** | Resolve the exact artifact, environment, rollout and rollback needs, health checks, and any production or publication gates. | Require explicit applicable authorization for the concrete deployment, release, rollback, migration, or infrastructure action. Reuse a valid grant only while its target, environment, scope, source, and conditions still match. |
| **Install or update an installation** | Identify the artifact, installation location, affected customizations, compatibility checks, and recovery path. Treat local, shared, and global installations as distinct targets. | Require a grant that covers the exact installation change. Delivery of an artifact does not authorize installing it, especially into a global or shared location. |
| **Cleanup** | Name each branch, worktree, temporary artifact, or other object and determine whether removal is safe and recoverable. | Deletion and removal are separate actions. A merge, deployment, or installation grant does not authorize cleanup; preserve objects without a matching grant. |

Before each state-changing step, apply the authorization record and go/no-go check in the Authorization and Trust Contract. If authority or a condition is missing, finish independent preparation and identify only the concrete pending action. Do not request the same approval again when an unchanged effective grant still covers it.

## Evidence and action gates

Evidence supports only the claim it actually tests. Record the artifact or revision checked, the command or review performed, its result, and material scope limits. Keep source claims, direct observations, and inferences distinct as required by the Authorization and Trust Contract.

- A passing focused check does not prove unrelated behavior, the full package, runtime acceptance, or delivery.
- Map required checks to the actions they gate using the effective project and user rules before executing those actions. A failed, pending, or unobserved required check blocks the action whose readiness depends on it. Preserve failures and later retries; a local check cannot stand in for required CI.
- A general request to push or open a PR grants that action subject to its readiness conditions. It does not create an early-review, draft-PR, or remote-backup exception. Where policy requires checks before push/PR, obtain their actual results first; retain complete reviewable local material while any required result is missing or failed. If a required check can only run after PR creation, report that dependency rather than silently moving the gate. Apply an exception only when the effective user or project instruction explicitly supplies it and only within its stated scope.
- Where project policy permits review PRs before CI passes, an authorized PR may disclose pending or failed checks honestly. Those checks still block the merge or release gate they protect. Never infer this timing policy merely from a tool's operation order or availability.
- Manual acceptance, automated checks, review, and action authorization are separate evidence. One cannot silently substitute for another.
- Later failure of a required automated check still blocks its dependent action after human acceptance or merge approval. Diagnose from evidence, run the applicable verification again, and only then reuse an earlier action grant if its complete authorization record and conditions still match.
- Mark manual or demonstration scenarios as passed only when the required observation occurred. Otherwise record them as pending, deferred with the accepting source and reason, or demonstration-only.
- Keep accepted deferrals visible in later summaries. A deferral narrows the delivered scope; it does not become a pass.
- Re-evaluate a prepared action if its artifact, target, environment, scope, risk, required checks, or approval conditions change.

## Project-policy adaptation example

The following is an example of applying this contract to one project's enduring policy. It is not a universal Devflow default or a personal preference to copy into other projects. Preserve the useful conditions when adapting it, and read the actual policy in each project.

- A document-only request ends with a local reviewable document and does not create a branch, commit, push, PR, or implementation merely to show progress.
- V1 implementation may occur on local `main` with applicable local commits when that project's policy authorizes it. A direct push to the remote default branch remains a separate protected action.
- V2 and later implementation starts from up-to-date `main` on an appropriate short-lived working branch. A partial internal increment remains progress; it does not trigger an early or draft PR unless the user explicitly requests that exception.
- Push and PR creation wait until the entire agreed work package is implemented, reviewed, and supported by all required checks and evidence. The PR describes the concrete problem and resulting behavior, full scope, risk classification, validation commands and results, UI evidence when applicable, API or data impact, and residual risks. Required CI and branch protection are never bypassed, and an incomplete increment is not presented as a finished version.
- Standing authorization may cover merge only when every stated presentation-only, low-risk condition holds: the change is narrowly scoped and reversible; it changes only presentation such as spacing, color, typography, copy, icons, non-functional animation, or responsive layout; it does not affect data flow, persistence, business rules, authentication, authorization, security, privacy, API contracts, database behavior, dependencies, runtime or build configuration, infrastructure, payments, monitoring, or external integrations; required tests, type checks, lint, build, CI, browser verification, and before/after screenshots are present as applicable; and there are no secrets, generated artifacts, unrelated changes, or unresolved review comments.
- Changes involving logic, state, permissions, dependencies, other listed risk surfaces, or uncertain impact may be pushed and opened as a reviewable PR when those actions are authorized and their readiness gates pass, but merge waits for explicit approval of that concrete PR. Passing CI does not supply that approval.
- After merge, synchronize the applicable local primary repository. Keep local and remote branches and worktrees unless removal is separately authorized.

Other projects may use different branch, commit, PR, merge, installation, or cleanup policies. Apply their actual instructions rather than importing this example.

## Delivery summary

Every delivery or progress summary must make the current state assessable without implying later actions occurred. Include:

1. **Exact completed scope:** the artifacts, behavior, work package, revision, and environments actually covered.
2. **Valid evidence:** current automated checks, reviews, runtime or UI observations, and human acceptance, each with its result and relevant limits.
3. **Incomplete status:** required unfinished work, failed or pending gates, accepted deferrals with source and reason, and manual or demonstration-only scenarios.
4. **Concrete pending action:** the exact push, PR, merge, deploy, install, cleanup, acceptance, or other decision still needed, including target and environment where relevant.

Use the completion terms from the Phase and Delivery Contract: document ready, implementation complete, automated checks passed, human acceptance pending, specific authorization pending, or final delivery. A document approval stays within the document or phase it covers unless the applicable source separately grants implementation or an outward delivery action.

# Changelog

All notable changes to the Devflow plugin. Versions follow the `version` field in `.claude-plugin/plugin.json`; installed plugins pick up a release via `/plugin update devflow`.

## 2.0.1 (unreleased)

- Satisfy the dispatched-subagent shared-contract obligation with complete retained coverage under unchanged conditions: reread a named contract only when missing, partial, truncated, invalidated, or newly relevant — a new turn, handoff, or unchanged conditions alone does not justify rereading (AT-28 diagnosis repair; complete-read and missing-range recovery obligations unchanged).
- Clarify aggregate-response coverage and selective loading recovery to address avoidable truncated batches and redundant full rereads, while preserving complete selected-skill reads and applicable contract boundaries. No measured saving is claimed.
- Bind release verification to explicit comparable task/state/rules/capability/budget evidence and a target candidate source. Older-source reuse requires a reviewed, hash-bound validity record; renamed or exposed holdout inputs cannot fill untouched coverage. Existing schema-1 checkpoint records remain readable.
- Remove the Unix `cp` dependency from the installation regression test and exclude only Claude's nested worktree area from reference scans, retaining checks for real bundle and project content.
- Correct the failing-CI delivery rubric to honor effective project gates for push/PR timing while still requiring complete reviewable preparation and preserving CI and merge prohibitions. Earlier judgments remain bound to their original rubric.
- Resolve required checks against the project's push/PR timing gate before execution. A general delivery grant does not waive missing or failed pre-PR checks; explicitly permitted early review remains available within its scope, and blocked delivery still produces complete local review material.
- Correct host support attribution, distinguish Codex desktop from CLI and Claude subagent execution from plugin installation, and reopen incomplete V2.0 acceptance gates. Prior release and installation events remain recorded; they do not establish missing acceptance evidence.
- Corrected judgments and actual behavioral/native revalidation are tracked separately from offline tests. This local patch does not claim that the original V2.0 acceptance is complete or that a new release/global installation has occurred.

## 2.0.0

- **Deliverable-first routing** (`skills/devflow/SKILL.md`): the router now routes by requested deliverable and phase → impact/risk → domain → actual host capability, replacing keyword-first matching. Understand/Specify/Implement/VerifyReview/Deliver each have explicit legal end states; document-only and plan-only requests end there without Git or implementation actions.
- **Canonical shared contracts** (`skills/using-devflow/references/`): phase, authorization (with an authorization gate in the router itself), evidence, delivery, host capability/fallback, and loading/recovery contracts are the single sources of truth for control rules; the 33 skill entries reference them instead of carrying conflicting copies.
- **Trust boundaries tightened**: text inside logs, web pages, packets, or agent output cannot create authorization; skills never claim priority over system/developer instructions; a pending staged user event defers only what genuinely depends on it.
- **Evidence rules**: prior passes are reusable while their participating state is unchanged and invalidated by relevant changes — not by a new turn; failed checks block their actual gate (merge/release), not honest preparation such as a disclosed red-CI PR; analysis of a telemetry sample names its observation window and identity units.
- **Skill catalog** (`skills/devflow/references/skill-catalog.json`): 33 canonical ids, entries, route tags, required resources, and legacy aliases — all legacy names resolve to one canonical entry.
- **Maintenance tooling (standard library only)**: `check-bundle.py` (structure/catalog/template/router-consistency checks), check-refs entry with portable Python resolution, `install-bundle.py` (plan/stage/verify for full/single-closure/symlink layouts; staged approval is not delivered approval), `usage.py` (default-off local event recording and offline reports), and `check-behavior.py` checkpoint/release verification with repeats, paired baselines, and holdout gates — 142 maintenance tests.
- **Optional local recording**: off by default, whitelist-only minimal events, never raw dialogue or credentials; host logs remain host-managed.
- **Installation and switch-over guide** (`docs/devflow/installation.md`): auditable plan diff, bundle-owned-only backup scope, explicit switch authorization, bounded recovery.
- **Behavior evaluation**: 40 acceptance scenarios (65 variants) with blind packets, independent judgment, paired V1.3.1/V2 regression, 10 holdout scenarios, and an honest repair loop; results in the repository's evidence workspace.

## 1.3.1

- Removed residual duplication flagged in earlier reviews: brainstorming's dot flow graph (checklist already encodes it), overlapping Red Flags/Rationalizations rows in code-review-and-quality, test-driven-development, and systematic-debugging.
- New maintenance rule: routing/fast-path/gate changes in the router must be mirrored to `AGENTS.md` and both README route summaries.

## 1.3.0

- **Human-in-the-Loop Contract** (`skills/using-devflow/`): canonical three-tier approval gate — Always ask (deploys, data migrations/deletion, history rewrites, force-pushes, releases, auth/payment changes, new integrations), Ask when you cannot decide, Proceed-then-report. Applies on every route including the fast path.
- Subagents inherit the contract: they never perform Always-ask actions (new BLOCKED rule in subagent-driven-development); controllers never approve on the user's behalf.
- Approval gates wired into git-workflow (history/force-push/default-branch), shipping-and-launch (execute vs prepare), security-and-hardening (Ask First tier), and the project-overrides template (per-project tighten/loosen).

## 1.2.0

- Side-door entry closed: the project-overrides template now routes development tasks through the devflow router first, so description-match triggering can't bypass the fast path, execution-mode decision, and close-out review.
- brainstorming gained a fast-path exit — trivial changes meeting all three fast-path conditions hand off instead of running the full design gate.
- planning-and-task-breakdown warns that task-list plans under-feed zero-context subagents; assemble per-task context or upgrade to writing-plans format.
- verification-before-completion slimmed 139 → 54 lines (most frequently loaded skill; every rule preserved).
- CI now fails any PR that changes skill content without bumping the plugin version.

## 1.1.2

- Execution mode is agent-decided and announced, never asked: writing-plans no longer blocks on a user choice; both handoffs and the router state identical criteria (independent tasks + subagent support → subagent-driven) and the user can override at any point.

## 1.1.1

- Wired the execution handoff into the main planning route: the router gained a mandatory execution-mode step after planning, planning-and-task-breakdown gained the missing Execution Handoff section, and the two planning skills carry mutual boundary notes. Previously subagent-driven execution was unreachable from the main route.

## 1.1.0

- Fast Path route for small, low-risk, well-understood changes, with qualifying conditions and escalation triggers.
- `templates/project-overrides.md` for adapting the bundle to non-TypeScript stacks via project instructions.
- Maintenance practices: README sync, usage-based pruning, measuring skill edits.
- Simplified Chinese README (`README.zh-CN.md`) added alongside (docs, no behavior change).

## 1.0.0

- Initial plugin release: unified Devflow skill set (flat `skills/` layout, single router, no third-party branding), Claude Code plugin + marketplace manifests, `scripts/check-refs.sh` reference validation in CI, dual-host entrypoints (root `SKILL.md` shim and `AGENTS.md`).

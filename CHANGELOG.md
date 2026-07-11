# Changelog

All notable changes to the Devflow plugin. Versions follow the `version` field in `.claude-plugin/plugin.json`; installed plugins pick up a release via `/plugin update devflow`.

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

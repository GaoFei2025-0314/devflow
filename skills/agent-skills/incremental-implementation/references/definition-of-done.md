# Definition of Done

The project-wide standing bar every task, increment, and change clears before it counts as done — regardless of what the task-specific acceptance criteria say. Task-level criteria answer "did we build the right thing?"; this list answers "is it actually finished?".

A change is **done** when:

- [ ] **Behavior is proven.** Every new behavior has a passing test; bug fixes include a reproduction test that failed before the fix.
- [ ] **The full relevant suite is green.** Not just the focused test — the broader suite that could catch regressions.
- [ ] **The build succeeds** with no new warnings, lint errors, or type errors.
- [ ] **The change was exercised end-to-end** in a runtime context (app run, API call, browser check) — not only through unit tests.
- [ ] **Review happened.** The change passed the review standard (`../../code-review-and-quality/SKILL.md`) or an explicit self-review against it.
- [ ] **Security surface was considered.** Untrusted input, secrets, and authorization touched by the change were checked (`../../security-and-hardening/SKILL.md` when applicable).
- [ ] **Docs and specs are current.** Public API changes, behavior changes, and decisions are reflected in the relevant docs, specs, or ADRs.
- [ ] **No dead code or leftover scaffolding.** Debug logging, commented-out blocks, and unused artifacts from the work are removed.
- [ ] **The work is committed** with a standalone description, on the right branch, with nothing important left uncommitted.

If a project defines its own Definition of Done, the project's version wins — treat this file as the default baseline.

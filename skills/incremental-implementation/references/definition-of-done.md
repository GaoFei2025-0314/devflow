# Definition of Done

Apply this baseline to the **current requested deliverable and work package**, together with its task-specific acceptance criteria and the project's own required gates. A documentation deliverable, implementation, review result, and final delivery have different legal endpoints; use the [Phase and Delivery Contract](../../using-devflow/references/phase-contract.md) for their status and the [Delivery Contract](../../using-devflow/references/delivery-contract.md) for later actions. If the project defines its own Definition of Done, that version wins.

Before calling the current deliverable complete:

- [ ] **Scope is reconciled.** Every explicit obligation is completed, already satisfied by valid evidence, accepted as deferred, or still open. Required open work keeps the package interim; accepted deferrals stay visible with their source and reason.
- [ ] **The deliverable is proven proportionately.** New behavior has appropriate tests; a bug fix has regression evidence; documentation has applicable content, structure, and reference checks. A check that does not address a risk in this scope is recorded as not applicable rather than performed ceremonially.
- [ ] **Relevant gates are green.** Focused checks and the broader suite, build, lint, type checks, or other mandatory gates that can catch affected regressions have valid results for the current relevant state.
- [ ] **Runtime and human evidence are accurate.** End-to-end, browser, API, manual, or stakeholder acceptance is completed when required, or remains pending or accepted as deferred. Static checks do not prove runtime or actual model behavior.
- [ ] **Review is resolved.** The change passed the review standard (`../../code-review-and-quality/SKILL.md`) or the applicable fallback self-review, and required findings are fixed or explicitly accepted as deferred.
- [ ] **Affected risk surfaces were checked.** Security, privacy, data, API, dependency, configuration, migration, performance, and operational concerns are considered only where the change touches them, using the corresponding skill when applicable.
- [ ] **Artifacts are current and clean.** Relevant docs, specs, decisions, and public contracts match the result; no debug output, dead code, commented scaffolding, or unrelated changes were introduced.
- [ ] **Evidence is current.** Records identify the checked object, operation, result, provenance, and material limit. Valid evidence is reused while relevant state is unchanged; affected checks alone are refreshed after a relevant change.
- [ ] **Delivery state is truthful.** Local edits, commits, work-package completion, push or pull request, merge, deployment, installation, and cleanup are separate steps. Perform and report only those required for the current deliverable and authorized by project policy.

Do not create duplicate mandatory records solely to prove this checklist was considered. Reuse the plan, task state, review, and evidence records that already contain the required facts. Report the exact completed scope, valid evidence, open or deferred obligations, manual status, and concrete pending action using the shared completion terms.

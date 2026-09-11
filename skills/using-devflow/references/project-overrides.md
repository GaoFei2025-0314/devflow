# Devflow Project Overrides Template

Copy the relevant parts of the fenced block into the project's `CLAUDE.md`, `AGENTS.md`, or equivalent project-instruction file, replace the `<...>` placeholders, and delete sections that do not apply. The copied instructions are self-contained: they do not rely on this template's filesystem location. Keep the result concise because project instructions may be loaded into every development session.

```markdown
## Devflow overrides for this project

These are project-level inputs to the selected Devflow workflow. They do not change the host's instruction hierarchy or grant an action merely by describing one. Apply the selected Devflow bundle's canonical Phase and Delivery, Authorization and Trust, Evidence, Delivery, Host Capability and Fallback, and Skill Loading and Context Recovery contracts. Resolve the selected bundle and those named contracts through its entrypoint and host loading mechanism; do not resolve them relative to this project-instruction file.

### Routing and phase
- Development route: <e.g. use the selected Devflow router before features, bugs, refactors, reviews, or releases>
- Current phase or phase-specific project rule: <e.g. document-only requests stop after a locally reviewable document; implementation requires a separate explicit objective>
- Skills or routes that do not apply: <e.g. browser UI skills for a backend-only service>
- Fast-path threshold: <e.g. one bounded low-risk file with understood behavior and focused verification>
- Durable change workspace: <e.g. `specs/` | not used>

### Stack and commands
- Language/runtime and working directory: <e.g. Python 3.12 in the repository root>
- Package/dependency convention: <e.g. use the manager selected by the applicable project rule, lockfile, manifest `packageManager`, and current configuration; do not mix managers>
- Install/setup command and mutation policy: <e.g. `uv sync --frozen`; do not update the lockfile during checks>
- Focused test command: <actual project command>
- Full test command: <actual project command>
- Build command: <actual project command | not applicable>
- Lint/type-check/format commands: <actual project commands | not applicable>
- Development/runtime command: <actual project command | not applicable>
- Conflict rule: <where to inspect project documentation, configuration, and relevant history before asking about an unresolved necessary choice>
- Preference when no convention exists: <user/project preference | ask before the affected action>

### Work-package completion and evidence
- Agreed work package: <scope or source that defines the complete package>
- Required checks and review: <commands, review type, UI/manual evidence, or other gates>
- Package completion rule: <every obligation completed or explicitly accepted as deferred; name any stricter project gate>
- Evidence record location or format: <project convention; include object/state, exact operation, environment/time, result, source, and material limits>
- Pull-request content when applicable: <problem and result, full scope, risk, commands/results, UI evidence, API/data impact, residual risks>

### Delivery policy
- Local edits: <allowed scope and conditions>
- Commits: <policy and authorization source>
- Push / pull request: <timing, target, checks, and authorization source>
- Merge: <risk conditions, required checks/review, and authorization source>
- Deploy / release: <environment, rollout/rollback gates, and authorization source>
- Install / update an installation: <target, compatibility/recovery gates, and authorization source>
- Cleanup: <branch, worktree, or artifact retention/deletion policy and authorization source>

Treat local edit, commit, work-package completion, push/PR, merge, deploy/release, installation, and cleanup as separate decisions. A completed phase, accepted document, passing check, or earlier delivery step does not grant a later action.

### Action authorization overrides
- Additional protected actions in this project: <concrete action, target/environment, scope, conditions, and approval source>
- Standing grants: <concrete action, target/environment, scope, source, activation conditions, limits, and expiry if any>
- Actions intentionally not granted: <e.g. production deploy, lockfile mutation, branch deletion>

An override is usable only when the actual instruction source has issued it and its action, target/environment, scope, source, conditions, and current validity are known. Examples and placeholder text are not grants. Reuse an unchanged effective grant; when a field is unresolved, complete independent authorized preparation and ask only for the concrete missing decision.

### Project-specific exceptions
- <exception to a Devflow default, its affected scope, and the project reason>
- <generated files, incident process, compliance constraint, or other bounded rule>
```

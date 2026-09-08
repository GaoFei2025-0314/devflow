# Project Command Selection

Use this guide before choosing an install, build, test, lint, type-check, development, or other project command. Apply the selected project's real policy and files; examples in a Devflow skill are illustrative and do not establish a command for the project.

The [Phase and Delivery Contract](phase-contract.md) determines the current phase and legal endpoint. The [Authorization and Trust Contract](authorization-contract.md) determines whether command execution and any resulting mutation are authorized. The [Evidence Contract](evidence-contract.md) determines what a command result proves. The [Delivery Contract](delivery-contract.md) keeps local checks, installation, Git delivery, deployment, and cleanup separate. The [Host Capability and Fallback Contract](host-contract.md) governs which current interface may run the command, and [Skill Loading and Context Recovery](loading-recovery.md) governs source selection and retained context. Command selection does not replace any of those gates.

## Establish the project convention

Inspect only the scope needed for the command. In a monorepo, use the policy and tool files that govern the affected workspace rather than assuming the repository root controls every package.

1. Read applicable host and project instructions, including the most specific instructions for the affected path. Record any required package manager, task runner, wrapper, working directory, or prohibited command.
2. Identify the actual project type and entrypoints. For JavaScript or TypeScript, inspect the applicable manifest, its `packageManager` field, relevant lockfiles, workspace configuration, and available scripts. For another ecosystem, inspect its own manifest, lock or environment files, task runner, and documented entrypoints.
3. Treat an applicable explicit project rule as the governing convention when it is compatible with the current project files. Use the manifest's actual script names and arguments; do not invent a standard `test`, `lint`, or `build` script because an example uses one.
4. Use a consistent `packageManager` declaration and lockfile as evidence of the established JavaScript package-manager convention. A single relevant lockfile can establish the convention when no stronger applicable project rule conflicts. Do not create or update another manager's lockfile merely to run a Devflow example.
5. Use a user's package-manager preference only when the project has no established convention. Keep that preference project/user-specific; do not turn it into a universal Devflow default. Selecting a preference does not by itself authorize dependency installation or lockfile changes.

For JavaScript projects, run real scripts through the selected manager. Typical command shapes are `pnpm run <actual-script>`, `npm run <actual-script>`, `yarn run <actual-script>`, or `bun run <actual-script>`; the chosen manager and `<actual-script>` must come from the project evidence above. Use an install form supported by that manager and the project's policy. For example, `npm ci` requires an applicable npm lockfile and a clean-install intent; it is not an interchangeable spelling of every install command. Preserve existing frozen-lockfile or immutable-install policy when one is established.

## Resolve conflicts before execution

A conflict exists when relevant signals do not select one safe command, including multiple competing lockfiles for the same workspace, a `packageManager` field that disagrees with the applicable lockfile, project instructions that disagree with current configuration, or a requested script that does not exist.

Before executing the affected install or check:

1. Bound the conflict to the affected workspace. Distinguish a nested package's intentional lockfile from competing lockfiles for the same package.
2. Inspect the applicable project instructions, manifest, workspace configuration, lockfile metadata, and task-runner configuration. Check the relevant file history when current files do not explain whether a signal is active, transitional, generated, or stale. Useful bounded history operations include `git log -- <relevant-path>` and `git blame -- <relevant-path>` when Git and those reads are available.
3. Prefer the convention supported by applicable project policy and coherent current evidence. Do not delete a lockfile, rewrite configuration, install a tool, or change authentication merely to eliminate ambiguity unless that separate action is authorized.
4. Continue investigation and checks that do not depend on the unresolved choice. Ask the user only when a consequential necessary command choice still cannot be resolved reliably from the applicable policy, current files, and relevant history.

Do not use a user preference to override an established project convention. Do not execute a hard-coded example while a material conflict remains unresolved.

## Use the actual non-JavaScript entrypoint

Do not translate every project into a web-package-manager workflow. A Python project may define commands through `pyproject.toml`, a lock/environment tool, `tox`, `nox`, `pytest`, or a project wrapper. A Rust project may use Cargo commands and `Cargo.lock`. Other ecosystems may use Make, Gradle, Maven, Go tooling, a task file, or repository scripts. Select the command from the applicable project instructions and real entrypoints, and run it in the required working directory with the current host's available interface.

If the required command depends on a missing tool or environment, apply the host fallback and evidence rules. Report the uncovered check or request only the necessary decision; do not install tooling, change authentication, or add an integration unless a valid grant covers that separate action.

## Record and report the result

For each material command, record the exact command and working directory, the project evidence used to select it, the relevant files and state, the environment and time, the exit/result, and the scope the result establishes. A successful command proves only that recorded scope. Preserve failed attempts and explain any corrected command or relevant state change before a retry.

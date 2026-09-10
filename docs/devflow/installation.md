# Devflow installation and switch-over guide

This guide covers installing a Devflow skill bundle, switching an existing
installation to a reviewed candidate, and recovering from a failed switch. It
applies to local skill-directory installations on any Markdown-instruction
host (Codex, Claude Code, and compatible). It does not replace host-specific
plugin-store installation; use the host's own mechanism for that.

All write operations here act only on an explicit install directory you name.
Nothing in this guide authorizes modifying the machine's global installation:
a real global switch is a separate, explicitly authorized operation (see
"Authorization" below).

## Tooling

The maintenance tools referenced below live in the repository's `scripts/`
directory and use only the Python standard library:

| Command | Purpose |
| --- | --- |
| `python scripts/install-bundle.py plan --bundle <repo> --target <install-dir>` | Read-only inventory of the current install: versions, conflicts, unknown sources, planned resources, recovery scope |
| `python scripts/install-bundle.py stage --bundle <repo> --layout full --dest <new-dir>` | Copy the complete distribution into a fresh directory |
| `python scripts/install-bundle.py stage --bundle <repo> --layout single --skill <id> --dest <new-dir>` | Copy one skill plus its resolved dependency closure |
| `python scripts/install-bundle.py stage --bundle <repo> --layout symlink --dest <new-dir>` | Link the distribution into a fresh directory (real symlinks) |
| `python scripts/install-bundle.py verify --bundle <repo> --install-root <dir>` | Verify a staged or installed tree: entries, declared resources, reference resolution, template sync, link integrity, per-file hashes |

Exit codes: `0` pass, `1` check failure, `2` input or environment error.

## Pre-installation checklist

1. Confirm the candidate's review state: structural checks (`bash
   scripts/check-refs.sh`), maintenance tests, and the behavioral evidence
   required by the release checklist have all passed for the exact candidate
   commit.
2. Record the candidate identity: repository commit hash and, if published,
   the plugin version from `.claude-plugin/plugin.json`.
3. Run `plan` against the current install directory. Do not skip this even
   for a fresh target — the output is the audit baseline.
4. From the `plan` output, classify every existing entry as: bundle-managed
   (matches the catalog), differing (bundle-managed but byte-different), or
   **unknown source** (not owned by this bundle, including user-custom files
   and other skills).

## Staging and verifying a candidate

1. Stage the candidate into a **brand-new** directory with the layout you
   intend to deploy (`full`, `single --skill <id>`, or `symlink`).
2. Run `verify` against the staged directory. A candidate that fails
   verification is **not usable**; do not proceed, and do not describe a
   failed candidate as ready.
3. For `single` layouts, inspect which skills the resolved dependency closure
   contains and confirm that set matches your expectation before installing.

## Auditable diff

The `plan` output against the live install directory is the switch diff: it
lists which skill directories match, where they differ (first differing
path), what is missing, and what exists only on the target side. Save this
output before switching; it is the basis for both review and recovery.

## Backup scope

Before any switch, copy the **bundle-owned paths only** — exactly the paths
listed in the candidate's install manifest file (install-manifest.json,
`paths` field) that exist
in the current install — into a recovery directory. Do not back up or later
delete unknown-source content; it is not yours to manage.

## Authorization

- Installing into a fresh disposable directory requires no special grant
  beyond the working authorization for the maintenance work.
- Overwriting an existing installation — local or global — requires an
  explicit, current user authorization naming the target directory and the
  candidate identity. "The candidate passed verification" is not switch
  authorization.
- If the switch fails after being authorized, recovery within the already
  backed-up scope is part of that grant; recovery actions **beyond** the
  backup scope (touching unknown sources, deleting custom content, widening
  the target) pause and ask first.

## Switch procedure

Perform the steps in order; stop at the first failure.

1. Verify the candidate staged tree (`verify` exit 0).
2. Create the recovery directory and back up bundle-owned paths as above.
3. Copy candidate files into the install directory, one path at a time, in
   the manifest's `paths` order. Never copy over, move, or delete
   unknown-source paths.
4. After copying, run `verify` against the install directory.
5. Run a host smoke check: load the router entry from the new install and
   confirm it resolves (for example, ask the host to read
   `skills/devflow/SKILL.md` through the install directory).

## Post-switch verification

- `verify` exit 0 against the install directory.
- The `plan` diff shows every bundle-managed skill matching and every
  previously-unknown source still present and untouched.
- The smoke check from step 5 passed.

Only when all three hold is the switch complete. A switch that copied files
but fails verification is a **failed switch** — follow recovery, do not
declare success and do not retry the copy loop blindly.

## Failure recovery order

1. Stop copying immediately; keep the partial state and all diagnostic
   output.
2. Restore the backed-up bundle-owned paths from the recovery directory,
   one path at a time, in the same order.
3. Re-run `verify` against the install directory and the smoke check.
4. Compare the custom and unknown-source content against the saved `plan`
   baseline: they must be byte-identical; if anything is missing, stop and
   report — that is beyond the recovery scope and needs a fresh decision.
5. Keep the recovery directory until the user confirms the restored state;
   it is the only rollback artifact.

## Layout-specific checkpoints

- **full**: the install directory contains the complete distribution
  (all catalog skills plus root entries, plugin metadata, and the legacy
  `templates/project-overrides.md` mirror); `verify` checks template-mirror
  byte-sync automatically.
- **single**: the install contains the requested skill plus its full
  dependency closure; a skill usable only because a *different* install
  happens to provide its dependencies is not a self-contained single
  install — `verify` runs against the install root, so missing closure
  members fail.
- **symlink**: every distribution path is a real symlink to the bundle
  working tree; `verify` rejects copied directories masquerading as links
  and links pointing anywhere other than the recorded source. On systems
  without link permission, staging fails honestly — never substitute a copy
  and call it a link. Note the operational property: a linked install
  tracks the bundle working tree, so bundle edits flow into the install
  without a switch step; prefer `full` for stable installs.

## Preserving other sources and custom content

Unknown-source directories and files are never copied over, moved, or
deleted by any step in this guide. If a conflict blocks a bundle-owned path
(an unknown-source file occupies a path the candidate needs), the switch
pauses on that path only; present the conflict to the user with the `plan`
diff and follow their decision. Do not resolve conflicts by deleting the
unknown side.

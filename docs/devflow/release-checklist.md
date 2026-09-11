# Devflow release checklist

Pre-push checklist for a Devflow release candidate. CI runs the offline part on every push; the offline part never verifies model behavior — a human or independent reviewer must inspect actual behavior results separately.

## Offline (CI-enforced)

- [ ] `bash scripts/check-refs.sh` exits 0 (frontmatter, references, size budgets, catalog/template/router consistency)
- [ ] `python scripts/check-bundle.py --root .` exits 0 (33 skills, shared contracts declared)
- [ ] `python -m unittest discover -s tests/maintenance -p 'test_*.py'` — all maintenance tests pass
- [ ] `python scripts/check-behavior.py validate --cases tests/behavior/cases` exits 0 (scenario materials valid — materials, not behavior)
- [ ] `.claude-plugin/plugin.json` version bumped for any skill-content change; CHANGELOG entry present
- [ ] README files in sync (README and README dot zh-CN); routing changes mirrored to `AGENTS.md`

## Behavior (human/independent review — CI cannot do this)

- [ ] Checkpoint/release behavior results reviewed against actual traces (not self-reports); failures preserved, not retried to green
- [ ] Paired baseline/candidate comparison conditions matched (same task/state/model/host); mixed-host results disclosed
- [ ] Holdout scenarios pass; any failure converts to regression material and a fresh holdout replaces it
- [ ] Environment-blocked variants (e.g. browser-interface on hosts without a browser) explicitly recorded as gaps — never claimed as passed

## Privacy scan (before any push)

- [ ] No private session transcripts, replay indices, credentials, or local absolute user paths in the diff
- [ ] Evidence workspace material stays out of the repository (it is deliberately untracked)

## Boundaries

- CI results are obtained only after push (T34); nothing here claims remote CI passed before it ran.
- Local evidence copies and holdout duplicates are git-ignored; scanning the to-be-committed files is part of the checklist, not an automated gate.

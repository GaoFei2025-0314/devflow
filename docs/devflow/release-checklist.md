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
- [ ] Staged approvals were actually delivered after the specified event; a packet describing future approval is not a received user message. Judgments cite the actual delivery and subsequent action trace.
- [ ] Paired baseline/candidate comparison conditions matched (same task/state/model/host); mixed-host results disclosed
- [ ] The release target is explicit; each reused older-source result has a reviewed validity record. Critical repeats count only evidence valid for that target, not an unchecked mixture of pre-repair and post-repair runs.
- [ ] Holdout scenarios pass; any failure converts to regression material and a fresh holdout replaces it
- [ ] Holdout identity is checked against the actual blind input and exposure history; renaming a repaired sample does not make it an untouched holdout.
- [ ] Environment-blocked variants (e.g. browser-interface on hosts without a browser) explicitly recorded as gaps — never claimed as passed
- [ ] Mandatory native host checks are complete, or an explicitly accepted scope change is recorded as a deferral. Desktop, CLI and plugin installation evidence are kept separate.

## Privacy scan (before any push)

- [ ] No private session transcripts, replay indices, credentials, or local absolute user paths in the diff
- [ ] Evidence workspace material stays out of the repository (it is deliberately untracked)

## Boundaries

- CI results are obtained only after push (T34); nothing here claims remote CI passed before it ran.
- Local evidence copies and holdout duplicates are git-ignored; scanning the to-be-committed files is part of the checklist, not an automated gate.

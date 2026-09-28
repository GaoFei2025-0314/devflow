# Devflow release checklist

Pre-push checklist for a Devflow release candidate. CI runs the offline part on every push; the offline part never verifies model behavior — a human or independent reviewer must inspect actual behavior results separately.

## Choose the release claim before checking

- **September 27 limited human closeout:** the user accepted ending the source-011 round with an environment exception. The [closeout record](v2-evaluation-summary.md) separates eight complete native PASS results from one incomplete scenario and six unstarted scenarios. This permits reporting and submitting the bounded work package; it does not satisfy or tick the strict patch/full-release gates below, create a checker exemption, or authorize merge/publication.
- **Full V2.0 qualification:** use the original [product requirements](../../specs/changes/devflow-v2/specs/product-requirements.md), including section 9.7's 40 AT/all variants, critical repeats, 10 untouched holdout pairs and the V1.3.1 comparison conditions. `verify --profile release` retains its full paired meaning. Historical failed and insufficient records have not been converted to PASS.
- **2.0.2 incremental patch:** use the separately approved [patch acceptance addendum](../../specs/changes/devflow-v2/specs/patch-2.0.2-acceptance.md). This checks changes from published `v2.0.1` to the final 2.0.2 candidate. Its `verify --profile patch` result cannot be described as full V2.0 qualification. No same-V1.3.1 pairing is required for this narrower claim; any comparative efficiency claim still needs comparable measurements.
- `checkpoint` is a diagnostic profile, not either release gate. A structural checker exit 0 never replaces independent review of actual behavior.

## Offline (CI-enforced)

- [ ] `bash scripts/check-refs.sh` exits 0 (frontmatter, references, size budgets, catalog/template/router consistency)
- [ ] `python scripts/check-bundle.py --root .` exits 0 (33 skills, shared contracts declared)
- [ ] `python -m unittest discover -s tests/maintenance -p 'test_*.py'` — all maintenance tests pass
- [ ] `python scripts/check-behavior.py validate --cases tests/behavior/cases` exits 0 (scenario materials valid — materials, not behavior)
- [ ] `.claude-plugin/plugin.json` version bumped for any skill-content change; CHANGELOG entry present
- [ ] README files in sync (README and README dot zh-CN); routing changes mirrored to `AGENTS.md`
- [ ] `git diff --check` and an impact table cover the full `v2.0.1` to final candidate diff, including uncommitted changes before freezing
- [ ] Changed checker/installer rejection paths still reject missing fields, wrong hashes, declarations posing as captures, alias/link bypass, missing dependencies and unintended overwrites

## Behavior (human/independent review — CI cannot do this)

- [ ] Checkpoint/release behavior results reviewed against actual traces (not self-reports); failures preserved, not retried to green
- [ ] Staged approvals were actually delivered after the specified event; a packet describing future approval is not a received user message. Judgments cite the actual delivery and subsequent action trace.
- [ ] Delegated task bodies were captured before dispatch and bound to actual caller, recipient and received content. Opaque payloads or post-dispatch self-reports do not establish plaintext equality. Custom delegation adapters and native spawn lineage are labeled separately.
- [ ] For any paired or relative claim, baseline/candidate comparison conditions matched (same task/state/model/host); mixed-host results disclosed. The 2.0.2 patch gate makes no new V1.3.1 comparison claim.
- [ ] For paired claims, all five comparison conditions cover actual task input, initial state, effective user rules, available capabilities and budget policy; a matching label does not substitute for their captured evidence.
- [ ] For full V2.0 qualification, AT-28 warm-context inputs contain the exact source-bound required rule bodies with complete receipt; AT-29 and AT-40 verify invalidation, missing context and partial/asynchronous returns. The 2.0.2 patch disposition is documented separately below.
- [ ] Loading entries reflect actual delivered source-body coverage, including repeat/partial reads; supplied warm-context bytes are recorded separately and missing totals are not replaced with zero.
- [ ] The release target is explicit; each reused older-source result has a reviewed validity record. Critical repeats count only evidence valid for that target, not an unchecked mixture of pre-repair and post-repair runs.
- [ ] Holdout scenarios pass; any failure converts to regression material and a fresh holdout replaces it
- [ ] Holdout identity is checked against the actual blind input and exposure history; renaming a repaired sample does not make it an untouched holdout.
- [ ] Environment-blocked variants (e.g. browser-interface on hosts without a browser) explicitly recorded as gaps — never claimed as passed
- [ ] Mandatory native host checks are complete, or an explicitly accepted scope change is recorded as a deferral. Desktop, CLI and plugin installation evidence are kept separate.

### 2.0.2 patch-specific gates

- [ ] Freeze the final candidate source hash and a `patch` scope listing exact case/variant/assertion IDs, required repeats, and two sealed new holdout identities/categories/assertions before dispatch. Bind each case's canonical JSON hash and each holdout's frozen rubric-byte hash; the schema 2 manifest binds the source, raw scope hash, pre-dispatch `scope_seal` and actual rubric files. Independently check seal timing. A rubric and coordinator attempt ledger are authored review material, not host captures.
- [ ] Run current-candidate AT-02 (all four variants), AT-30 (both), AT-31 (one), and AT-33 (all four installation layouts). Run `AT-33/complete-package-install` three independent valid times in total; retain every attempt.
- [ ] Record the eight AT-28/29/40 variant dispositions from the [patch addendum](../../specs/changes/devflow-v2/specs/patch-2.0.2-acceptance.md) as `not reverified in patch`. Their local status/read-recovery tasks do not analyze usage-log samples or invoke itemized installation-check reporting, and they do not count as patch PASS; earlier `final001` wide-closure reuses are not rebound to the new source. If final scope changes their dependency, reassess and target the affected variants.
- [ ] Run two fresh, unexposed patch holdouts: unauthorized installation/recovery and observability denominator or identity confusion. A failed exposed holdout stays in regression history and is replaced by a new sealed sample.
- [ ] Every patch candidate and holdout is a new run on the exact frozen source, with no old-source `reuse`; each has host-captured dispatch input and receipt bound to its run/actor. AT-33 complete-install's three repetitions have distinct actors, native invocations, traces and dispatch/receipt evidence; independently review real execution identity.
- [ ] AT-02 and AT-33 native preflight captures actual input, initial state, model/parameters, effective rules, budget, dispatch/receipt, tools/results, loading coverage and approval delivery. The entry/exit registry and relevant configuration projection show whether any capability change affects the used path. Unrelated late iOS tools are recorded as host facts, while changed used tools, model, permissions or rules block the run; the old AT-14 hash-only run is not retroactively counted.
- [ ] Install the final candidate in isolated full-package, single-skill dependency-closure and true-link layouts. Check retained custom/foreign files, expected exit 7 and bounded restore after a real staged approval.
- [ ] `python scripts/check-behavior.py verify --profile patch --cases tests/behavior/cases --results <candidate-results> --holdout <sealed-holdout-results> --target-candidate-source <source-sha256> --patch-scope <scope.json> --release-manifest <manifest.json>` exits 0 without synthetic fixtures. The exit result means patch evidence is structurally complete; independent semantic review must also find zero candidate FAIL/UNKNOWN, no unauthorized action, and no missing provenance.
- [ ] Old FAIL/UNKNOWN, contaminated materials, quota/host failures and excluded reuses remain linked in an attempt-disposition ledger. Their prior judgments are unchanged.

### Full V2.0 qualification gates

- [ ] Every AT and required variant, all critical three-run repetitions, 10 untouched holdout pairs, valid baseline/candidate comparison conditions, native and installation evidence, and independent review meet the original Spec; strict `verify --profile release` exits 0 without synthetic fixtures.
- [ ] The original V1.3.1 effects study is reported only from valid comparable task, environment and loading records. The exploratory 30% loading reduction is not a hard passing threshold.

Accepted scope amendment (2026-09-13): the user deferred Cursor native skill-read/partial-return verification for this V2 work package. Record Cursor as native-unverified, never passed. All other required checks and general partial-return behavior remain in scope; see the V2 Spec section 11.2 and host-support table.

## Privacy scan (before any push)

- [ ] No private session transcripts, replay indices, credentials, or local absolute user paths in the diff
- [ ] Evidence workspace material stays out of the repository (it is deliberately untracked)

## Boundaries

- CI results are obtained only after push (T34); nothing here claims remote CI passed before it ran.
- Local evidence copies and holdout duplicates are git-ignored; scanning the to-be-committed files is part of the checklist, not an automated gate.

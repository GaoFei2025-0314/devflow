# Devflow V2.0 evaluation summary

## 2.0.2 incremental acceptance status — 2026-09-23

The user selected an incremental acceptance claim for the next `2.0.2` patch
over the published `v2.0.1` tag. The separate
[patch acceptance addendum](../../specs/changes/devflow-v2/specs/patch-2.0.2-acceptance.md)
defines that gate and its risk-based scenario matrix. It does not change the
original full V2.0 qualification or the strict `release` profile. The earlier
V1.3.1 full comparison remains an unresolved historical work item; a patch
PASS, if later achieved, must not be reported as a retroactive full PASS.

**The 2.0.2 patch has not passed acceptance.** An interim candidate source
(`0026d873210bbcb82a5288bedd4e348dc8452191e5eca12a5f39b3b491b68297`)
and patch scope were frozen, two new holdouts were sealed, and isolated install
smoke checks passed. A native AT-33 `linked-install` run then failed E01 in
independent review: its report gave checked/missing totals without the exact
resolved-reference list. AT-02 diagnostic runs with an incorrect workspace
reference or host-config drift between pre-turn and post-turn captures remain
invalid, not current PASS results.
The corresponding delivery rule is being corrected, so the final source must
be frozen again and its scoped behavior rerun. The patch checker, final
independent review and CI remain pending. The previously frozen
`candidate-final-002` SHA-256
`c1786019b71eb810a5afea83d522682f36ac2879810dde37cc3d113a91bd5911`
is a pre-addendum snapshot, not a final 2.0.2 source binding; every subsequent
repository content change requires a new freeze and evidence-impact review.

The local evidence workspace outside this repository contains the September 23
coordination checkpoint for the current V2 acceptance collection.
It records offline refs/bundle/material validation and 231 Windows maintenance
tests passed for that earlier snapshot, with 40 cases/66 variants structurally
valid. These checks do not prove model behavior. The AT-14 native preflight
observed 44 unrelated late iOS tool additions and a changed global config;
without the relevant before/after configuration content it was not counted.
One new AT-02 baseline was captured but lacked exit capability evidence and
its own E01 assertion failed; that V1.3.1 baseline result is not a current
candidate failure. A real-browser AT-39 baseline passed its five public
assertions in independent review, but its CLI version differs from the current
host and no current-source candidate pair is established. The prior AT-33
single pair cannot supply the three valid repetitions for the changed patch
source. Original failed, unknown and interrupted attempts remain in the
external attempt history rather than being silently replaced.

## Status reviewed on 2026-09-21

The sections below record the historical V2.0.0 evaluation from 2026-09-13; their
source hashes, counts and host limitations are not current V2.0.1 acceptance results.
Tag `v2.0.1` was published on 2026-09-20 at
`9db63cde0ddb3fecc0971ed16644b34121266b05` after PR #13 merged with all five required
checks passing. No GitHub Release was created as of this review. Publication and
offline checks do not prove behavior or native host acceptance.

The later v10 collection retains 104 candidate records with 487 pass / 2 fail /
2 unknown assertions, and 104 baseline records with 482 pass / 9 fail / 0 unknown.
Its release checker reports 48 detected failures and 1,259 insufficient-evidence
items, including evidence-path collisions and missing comparison/reuse metadata.
These are checker diagnostics, not counts of failed model assertions. The v11
collection repairs evidence references while retaining original record bytes and
outcomes. Its updated checker returns exit 1: 2 original candidate assertion
failures and 179 evidence gaps, with 33 comparable ordinary pairs and no eligible
target-bound holdout pairs. All 228 original declarations and 23,879 typed reference
uses passed the separate byte-integrity audit. That audit proves file identity,
not source-reuse validity or release acceptance; loading and comparison gaps remain.
Cursor's explicit native-acceptance deferral remains in effect; see
[host support](host-support.md) for the retained historical observations and limits.

## Current work-package preflight (2026-09-22)

The separate current acceptance collection is still in progress. No full-release
PASS or PR readiness is established. Historical declarations and failed attempts
remain immutable outside the repository.

- Current material contains 40 cases and 66 variants. The additional AT-28
  warm-context variant requires exact, source-bound retained bodies and actual
  receipt evidence. Structural validity is not an executed behavior result.
  The new floor is 114 runs per side / 228 total executions, including required repeats and
  holdouts; the historical 65-variant counts below retain their original scope.
- One new AT-33 pair on Windows Codex passed independent semantic review, with
  five assertions per side. Both actors assessed the candidate before receiving
  the actual staged user approval. The simulated switch exited 7, changed only
  `VERSION`, and the authorized restore exited 0 with original bytes restored.
  This single pair does not satisfy the three-repeat gate.
- The first AT-15 native-collaboration pair has five PASS and two UNKNOWN assertions
  per side. Host captures retain opaque dispatch and receipt payloads. The
  candidate also displayed its first complete prompt after dispatch, failing the
  separate capture-order preflight. These attempts remain visible. A subsequent
  pair using the reviewed local delegation adapter passed all seven assertions
  per side. Exact dispatch/receipt text, real overlap, task boundaries and all five
  comparison conditions were independently checked. These are controller-bound
  native roots, not built-in spawn lineage. Rejected task-name attempts remain in
  the capture. Observed source-body tool payloads were 38,320 bytes for baseline
  and 85,955 bytes for candidate; supplied task context is recorded separately.
  This pair does not meet the exploratory 30% loading-reduction target.
- Independent review of historical AT-28 distinguished necessary first contract
  loading from repeated retained text. The old E02 rationale incorrectly treated
  three applicable first reads as unnecessary. Its loading ledger also omitted
  their fully delivered content. The old FAIL remains unchanged with a separate
  calibration record. Fresh ordinary and warm-context pairs independently passed
  all 18 assertions. Warm actors received complete rule bodies and did not reread
  retained rules. The ordinary candidate recovered a genuinely truncated return;
  that avoidable truncation remains an advisory finding, not missing coverage.
- These pilot actors used `gpt-6-astra` with recorded `xhigh` effort and no explicit
  model/effort override. The frozen candidate pilot is Git `46613e6`, content
  manifest `8f6bf7d7d291a26b67ff4e02248ef0d1768c987ea1b1af6d9768f158009bd0f7`;
  the baseline remains V1.3.1 `137e025`. Final-source validity still needs review.
- Windows and Ubuntu each passed 231 maintenance tests. Reference and bundle
  checks passed. Real isolated full, single-skill closure and symbolic-link
  installations passed against the pilot source; no global installation changed.
- Metadata repair proposals preserve original identities and judgments. Adding
  loading field aliases does not prove delivered coverage or comparable metrics.
  Independent review of the first 35 historical pairs supports 29 unchanged
  reuses and six evidence-backed supplements, all tied only to the pilot source.
  Every correction retains the original hash and exact field differences.
  Remaining source-reuse, loading, comparison-condition and holdout gates remain open.

## Historical V2.0.0 evaluation

What the V2.0 behavior evaluation actually measured, and what it did not establish. The
figures below are the recorded outcomes carried over from the V2.0 implementation plan
(`specs/changes/devflow-v2/tasks.md`, records T05/T24/T26/T30–T33); nothing here is
re-derived or re-stated more favorably.

Raw material — captured traces, host transcripts, holdout scenarios, input packets and
per-episode judgments — lives in a local evidence workspace **outside this repository**
and is deliberately not committed: it carries host identifiers, private sources and
held-out material. This page is the repository-resident summary of it, so the release
claims can be read without that workspace.

## Scope and floor

| Item | Value |
| --- | --- |
| Acceptance scenarios | 40 cases, 65 variants (`tests/behavior/cases/`) |
| Release-profile run floor | 65 base variants + 38 key repeats + 10 holdouts = 113 runs per version |
| Paired floor | 226 runs across baseline and candidate |
| Baseline | `137e025` (V1.3.1) |
| Candidate under regression | `722c369`; final candidate `aa171a4` |
| Host/model pairing | Claude Code subagent, glm-5.3, per the recorded host amendment |

## Full-scope paired regression (T31)

103 paired episodes per side plus 10 holdout scenarios per side were executed, captured
and independently judged. Two five-hour quota walls were recorded and the run resumed.

**First aggregate — C07 exit 1:** candidate 473 pass / 9 fail / 2 unknown; baseline
477 pass / 7 fail. Candidate holdouts 9/10 (HOLDOUT-RECOV-02 failed). The candidate did
not pass release verification on this pass.

**Repair loop:** four bounded product fixes landed as `b58489d` (delivery / phase /
loading / installation contracts) and `30b54e4` (observability identity units), each
citing the episode that exposed it. Affected episodes were re-run on the fixed source
and re-judged independently: AT-02-r3, AT-23-r4, AT-33 (both layouts) r4 and
HOLDOUT-RECOV-02-r2 all passed.

**Final aggregate — C07 still exit 1:** candidate 108 records, 497 pass / 10 fail /
2 unknown; baseline 501 pass / 8 fail / 0 unknown.

The historical report attributed the remaining candidate failures to retained
legacy-source history and AT-16, which was blocked on both sides because that
evaluation host had no browser interface. Its claim that every runnable scenario
passed on repaired sources did not establish final-source repeats, untouched
holdouts or native integration acceptance; the limits in [host support](host-support.md)
still apply. **That historical AT-16 run required a browser-capable host.** A green
C07 was never reached in this evaluation.

## Measured loading cost

| | Median loaded bytes per episode |
| --- | --- |
| Baseline (V1.3.1) | 16,647 B |
| Candidate (V2.0) | 51,613 B |

A 3.10x increase, attributed in the record to the candidate's larger shared-contract
content. The requirement Spec carried a 30% median *reduction* for read-only and small
changes as an exploratory target; the measured result moves the other way. This metric is
exploratory either way: it can never offset a quality failure, and it was not allowed to
offset one here.

## Where that cost sits, and how much of it is recoverable

Measured on the V2.0 tree after the release, to answer whether the increase above is a
layout problem or a content one.

The mandatory read for a full implementation route — router, `using-devflow`, and the
phase, authorization, evidence and delivery contracts — is 65,863 bytes, against 16,548
for V1.3.1's router plus `using-devflow`. A read-only explanation route still costs 22,342
bytes, more than V1.3.1's entire fixed entry. Of the 65,863, the two entrypoints are 38%
and the four contracts 62%.

A prototype split one contract into a normative core plus its full text, preserving every
rule and rewording nothing in substance. The core came to 6,600 bytes against 7,916 — a
17% cut, far below what the section sizes suggested, because the contract is dense
normative content rather than padding: its terminal-state table alone is 40% of the file
and is the rules themselves. Extrapolated across all four mandatory contracts, splitting
buys roughly 10% of the mandatory read. The prototype was reverted; it is recoverable from
the branch history if the approach is revisited.

The compressible content sits in the entrypoints instead. `using-devflow`'s opening
section is 32% of that file and re-summarizes the four contracts the reader is separately
told to read; with Instruction Priority and the Human-in-the-Loop section that is about
5,700 bytes of restatement. Another ~1,300 bytes are motivational prose (Skill Types,
Common Rationalizations, User Instructions). The router's own bulk — 48% in "Choose the
deliverable and phase" — is the routing logic and is load-bearing.

**Ceiling:** restructuring without deleting rules recovers roughly 20%. That would meet
neither the Spec's 30% reduction target nor V1.3.1's entry cost. V2.0's loading cost is
the price of the rules V2.0 chose to add, so closing the remaining gap is a decision about
which rules earn their tokens, not a layout change. `scripts/check-bundle.py` now reports
total entry load on every run and enforces a per-entry byte budget alongside the line
budget, so this figure stays visible rather than drifting silently.

## Other recorded gates

- **T24** — four domain entrypoints on frozen source `6e3474f`: 54/54 assertions pass,
  0 fail, 0 unknown; C06 checkpoint verification exit 0. Mixed hosts are disclosed
  (episodes 1–7 Codex gpt-5.6-sol, 8–16 Claude Code glm-5.3); no cross-host comparability
  or causal claim is made from that mix.
- **T05** — repair3 closed 51/51 phase assertions; the full 55-assertion set stood at
  54 pass / 1 fail at that point.
- **T26** — real symbolic-link installation verified on an elevated Windows shell
  (`islink` plus normalized target comparison; a copied directory posing as a link was
  rejected). The reference-driven single-skill closure resolves to 16 skills.
- **T33** — final candidate `aa171a4`: C01–C04 all exit 0 (142 maintenance tests at the
  time). Full diff 51 commits / 1,670 insertions. A privacy scan confirmed the
  diff carried only bundle, docs, tests, scripts and workflow files — no evidence
  workspace, transcripts or holdout copies.
- **T34–T37** — PR #11 pushed with 5/5 CI green, merged as `c28e765`, tagged `v2.0.0`,
  and the local global install switched over with all 33 entry hashes matching and no
  deletions.

## What this does not establish

Offline checks (`scripts/check-refs.sh`, `scripts/check-bundle.py`, `scripts/check-behavior.py validate`) prove
structure and material validity only. `scripts/check-behavior.py validate` exiting 0 means the
scenario material is well-formed, never that 40 scenarios passed. CI calls no model and
reads no private log. Host support levels are labeled separately in
[host support](host-support.md), and `format` there means only that Markdown loads.

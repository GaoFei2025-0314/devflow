# Devflow V2.0 evaluation summary

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

The remaining candidate failures are legacy-source history the evidence contract requires
keeping, plus AT-16, which is blocked on both sides because the evaluation host has no
browser interface. Every scenario runnable on that host passed on the repaired source.
**AT-16 still needs a re-run on a browser-capable host.** A green C07 was never reached,
and this page does not claim one.

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
  time; 156 today). Full diff 51 commits / 1,670 insertions. A privacy scan confirmed the
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

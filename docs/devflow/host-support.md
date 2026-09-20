# Devflow host support

Evidence reviewed on 2026-09-13. A host observation covers only the recorded version, candidate source and operation. Controlled scenarios can run on a real native host without proving that host's plugin installation or every integration works. Markdown compatibility is not a successful native loading test.

| Host | Loading | Routing | Commands | Recovery | Browser | Collaboration | Evidence level |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Claude Code subagent host 2.1.263 | explicit file reads observed | controlled scenarios observed | native local commands observed | controlled scenarios observed | AT-16 browser variant blocked on this host | native subagents observed | T31 records report glm-5.3; dispatch requested sonnet. These are different identity fields. Required acceptance remains open. |
| Claude Code plugin installation | unverified in the inspected acceptance evidence | unverified | unverified | unverified | unverified | unverified | Subagent file reads do not prove plugin-dir discovery or native skill invocation. |
| Codex desktop subagent host, frozen September 2026 runs | explicit file reads observed | scoped historical scenarios | native local commands observed | scoped historical scenarios | actual browser observations exist on the desktop host; source validity must be checked for each reuse | native subagents observed | Desktop evidence is scoped to the captured task, source and tool availability. It does not cover the independent CLI. |
| Codex CLI | blocked in the recorded smoke test | unverified | unverified | unverified | unverified | unverified | The inspected CLI smoke was rejected before the target file was read. No successful native skill read is established by that record. |
| Cursor 3.9.16 | unverified native read | unverified | unverified | unverified partial-return recovery | unverified | unverified | SKILL.md uses a compatible Markdown format. The user explicitly deferred Cursor native loading and recovery acceptance for the current V2 scope on 2026-09-13; this is not a native PASS. |
| Copilot CLI | format compatibility only | unverified | unverified | unverified | unverified | unverified | Purpose mappings in `skills/using-devflow/references/copilot-tools.md`; not natively tested. |
| Gemini CLI | format compatibility only | unverified | unverified | unverified | unverified | unverified | Purpose mappings in `skills/using-devflow/references/gemini-tools.md`; not natively tested. |

## What the V2.0 evaluation actually verified

- T31 contains 103 initial paired runs per side for 40 cases / 65 variants, followed by five paired repair runs. Candidate records retain their actual sources: 103 at 722c369, four at b58489d and one at 30b54e4. They are not 108 runs of a single final source. The original aggregate release check failed and final-source critical repeats remain incomplete.
- The AT-33 complete-install repair judgment accepted a future approval described inside a packet even though the follow-up user message was not delivered. That PASS does not establish authorization compliance. The affected judgment and missing delivery must be corrected before closing the gate.
- The recovery holdout used to tune a repair was rerun with the same input. It must count as regression material, with a fresh untouched replacement required for holdout coverage.
- T24's 54 original assertions span 12 episodes: episodes 1–7 ran on Codex desktop; episodes 8–12 ran on Claude Code after the prospective host change. The four supplemental domain episodes also ran on Claude Code. The 54/54 aggregate cannot be attributed entirely to Codex.
- The evidence locators are T24's per-episode dispatch/capture manifests and prospective host amendment, T31's result/capture files, the CLI smoke record, and the Cursor capability preflight in the maintainer's private evaluation archive. Public host labels do not replace those records. Reuse requires their source and scope to remain valid; no private transcripts are distributed with the bundle.

## Pending required acceptance

The applicable browser scenario, repaired critical repeats, untouched holdout coverage and other required non-Cursor native checks remain required by the V2.0 Spec. On 2026-09-13 the user explicitly deferred Cursor's native skill read and partial-return recovery from this acceptance scope. General partial-return and recovery behavior tests remain required. Cursor stays format-compatible/native-unverified; the deferral is not a successful native observation. Publishing a tag, installing matching files, or acknowledging an environment gap does not complete the remaining checks.

## Degrading honestly

Every capability-dependent skill follows the host contract in `skills/using-devflow/references/host-contract.md`: inspect the interfaces the current host actually exposes, choose an authorized capability, and when one is missing, use the in-session fallback and record the gap honestly instead of fabricating evidence (for example, screenshot acceptance stays pending on hosts without a browser).

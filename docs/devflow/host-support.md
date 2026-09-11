# Devflow host support

Which hosts Devflow runs on, what works where, and the evidence level behind each claim. Native means verified by actually running Devflow on that host in an isolated test project; controlled means verified inside a controlled evaluation harness; format means only file-format loading was checked.

| Host | Loading | Routing | Commands | Recovery | Browser | Collaboration | Evidence level |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Claude Code (plugin) | native | native | native | native | — (no built-in browser tool; degrade per host contract) | native (subagents) | native (2.1.263, plugin-dir loading, skill invocation) |
| Codex desktop / CLI | native | native | native | native | native with an in-app browser tool (e.g. mcp__cua_repl.js); degrade when absent | native (subagents) | controlled→native (recorded during V2.0 evaluation on the 2026-09 frozen hosts; quota ended full native re-verification) |
| Cursor | format | unverified | unverified | unverified | unverified | unverified | format only — SKILL.md Markdown loads; not natively tested |
| Copilot CLI | format | unverified | unverified | unverified | unverified | unverified | format + purpose mappings in `skills/using-devflow/references/copilot-tools.md`; not natively tested |
| Gemini CLI | format | unverified | unverified | unverified | unverified | unverified | format + purpose mappings in `skills/using-devflow/references/gemini-tools.md`; not natively tested |

## What the V2.0 evaluation actually verified

- The full 40-scenario / 65-variant behavior regression (103 paired episode records per side plus holdout scenarios) ran on a Claude Code subagent host, identical on the V1.3.1 baseline and V2 candidate sides. Every scenario runnable on that host passed on the final repaired candidate; one variant (browser-interface verification) is environment-blocked there and remains pending a browser-capable host.
- Codex-host behavior for the router and domain skills was verified on the frozen 2026-09 Codex desktop subagent host during the T24 domain assessment (54/54 original assertions) before the account quota was exhausted.
- No claim on this page extends beyond what was actually run: "format" rows mean the file loads, nothing more.

## Degrading honestly

Every capability-dependent skill follows the host contract in `skills/using-devflow/references/host-contract.md`: inspect the interfaces the current host actually exposes, choose an authorized capability, and when one is missing, use the in-session fallback and record the gap honestly instead of fabricating evidence (for example, screenshot acceptance stays pending on hosts without a browser).

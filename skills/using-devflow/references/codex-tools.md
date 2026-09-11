# Codex Capability Guide

Apply the shared [Host Capability and Fallback Contract](host-contract.md) before using this page. Read the current Codex tool inventory and parameter schemas first. Every name below is a purpose hint or historical example, not a promise that the API exists in this session.

## Evidence status

- **Native tested:** no native-support claim is established by this page; native validation is a separate release gate.
- **Controlled contract verified:** no controlled-support claim is established by this page.
- **Format-only guidance:** this adapter's purpose mapping.
- **Unverified:** runtime behavior, parameter availability, and support claims not backed by a qualifying evidence record.

## Purpose mapping

| Devflow purpose | Historical Codex example | Required current check |
| --- | --- | --- |
| Read, create, or edit files | native file tools or a bounded shell operation | Confirm the callable operation, path scope, encoding, and complete-input mechanism. |
| Search files or content | a native search interface or `rg` through the shell | Confirm command availability, working directory, result limits, and exit semantics. |
| Run commands | a native shell/command interface | Confirm command, working-directory, environment, timeout, streaming, and result parameters. |
| Load a skill | native skill loading or repository instructions | Confirm the loader actually exists and how it receives a skill identifier; otherwise read the applicable `SKILL.md` as instructions. |
| Track work | a plan/task interface | Confirm the current schema and whether tracking is required; do not invent `TodoWrite` or `update_plan`. |
| Dispatch or coordinate agents | historically `spawn_agent`, wait/result, message, and interruption operations | Confirm every callable interface and parameter. Apply the agent-choice checks in the shared contract before dispatch. |
| Use a browser | any currently exposed authorized browser or device interface | Confirm the operations can collect the interaction or visual evidence required; apply browser fallback when they cannot. |
| Work with Git or pull requests | bounded shell Git or a currently exposed repository interface | Inspect first and apply the separate authorization and delivery gates before each mutation. |

Historical Codex variants have used different dispatch, wait, close, and plan-tool names and parameters. Do not edit configuration to enable multi-agent features for a Devflow example. If collaboration is absent, disallowed, too costly, tightly coupled, or shares write targets, use the no-subagent fallback in [Using Devflow](../SKILL.md).

Worktree, branch, push, PR, and finishing behavior depends on the actual repository and host state. Inspect that state with available read-only operations. A detached or managed worktree is a constraint to report and adapt to; it does not authorize a branch, commit, push, handoff, or UI action.

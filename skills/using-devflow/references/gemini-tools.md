# Gemini CLI Capability Guide

Apply the shared [Host Capability and Fallback Contract](host-contract.md) before using this page. Read the current Gemini CLI tool inventory and parameter schemas first. Every name below is a purpose hint or historical example, not a promise that the API exists in this session.

## Evidence status

- **Native tested:** no native-support claim is established by this page.
- **Controlled contract verified:** no controlled-support claim is established by this page.
- **Format-only guidance:** this adapter's purpose mapping.
- **Unverified:** runtime behavior, parameter availability, and complete host support.

## Purpose mapping

| Devflow purpose | Historical Gemini CLI example | Required current check |
| --- | --- | --- |
| Read, create, or edit files | `read_file`, `write_file`, or `replace` | Confirm each operation exists and check path, range, encoding, and replacement parameters. |
| Search or list files | `grep_search`, `glob`, or `list_directory` | Confirm root/path scope, exclusions, pagination, and truncation behavior. |
| Run commands | `run_shell_command` | Confirm command, working-directory, environment, timeout, streaming, and result parameters. |
| Load a skill | historically `activate_skill` | Confirm the loader exists and its current identifier schema; otherwise read the applicable `SKILL.md` as instructions. |
| Track work or request input | historically task-tracking and structured-input operations | Confirm a current callable interface and parameter schema before use. |
| Dispatch or coordinate agents | no stable capability is assumed | Inspect the current inventory. If the required collaboration operations are absent or unsuitable, use the no-subagent fallback. |
| Search, fetch, or browse | historically search and fetch operations; use any current authorized browser interface when present | Distinguish search/fetch content from real navigation, interaction, device, and visual evidence. |
| Work with Git or pull requests | bounded shell Git or a currently exposed repository interface | Confirm availability and parameters, then apply separate authorization and delivery gates before mutation. |

Do not assume that historical lack of subagents remains true, or that historical names remain callable. Likewise, a current dispatch operation would not by itself justify delegation: permission, independent verification, context, write isolation, and resource limits must all pass.

Do not install extensions, change authentication or configuration, or add integrations to make this guide match the host. If no suitable browser exists, complete available checks while keeping required visual or interaction acceptance pending.

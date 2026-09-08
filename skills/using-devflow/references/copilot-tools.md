# Copilot CLI Capability Guide

Apply the shared [Host Capability and Fallback Contract](host-contract.md) before using this page. Read the current Copilot CLI tool inventory and parameter schemas first. Every name below is a purpose hint or historical example, not a promise that the API exists in this session.

## Evidence status

- **Native tested:** no native-support claim is established by this page.
- **Controlled contract verified:** no controlled-support claim is established by this page.
- **Format-only guidance:** this adapter's purpose mapping.
- **Unverified:** runtime behavior, parameter availability, and complete host support.

## Purpose mapping

| Devflow purpose | Historical Copilot CLI example | Required current check |
| --- | --- | --- |
| Read, create, or edit files | `view`, `create`, or `edit` | Confirm each operation exists and check its path, range, encoding, and replacement parameters. |
| Search files or content | `grep` or `glob` | Confirm syntax, root/path scope, exclusions, pagination, and truncation behavior. |
| Run commands | `bash`; some versions exposed async session operations | Confirm shell, working-directory, environment, timeout, async/session, input, and result parameters. |
| Load a skill | historically `skill` | Confirm the loader exists and its current identifier schema; otherwise read the applicable `SKILL.md` as instructions. |
| Track work | a host task interface; older guidance used a session database | Confirm an actual callable interface and schema. Tracking storage is not implied by this mapping. |
| Dispatch or coordinate agents | historically `task`, agent listing, and result reading | Confirm dispatch, context, wait/result, cancellation, concurrency, and agent-type parameters before use. Apply all agent-choice checks. |
| Fetch web or browser evidence | historically a fetch operation; use any current authorized browser interface when present | Confirm whether it provides documents only or real navigation, interaction, and visual evidence. Do not treat fetch output as browser acceptance. |
| Work with Git or pull requests | shell Git or currently exposed GitHub interfaces | Confirm availability and parameters, then apply separate authorization and delivery gates before mutation. |

Past versions have exposed additional memory, status, documentation, shell-session, and GitHub operations. Use them only when the current host describes them. Do not authenticate, install an extension, enable a service, or add an integration to match this guide.

If collaboration is absent or the task fails the permission, independence, context, write-isolation, or resource checks, use the no-subagent fallback in [Using Devflow](../SKILL.md). If no suitable browser exists, preserve the evidence gap and any mandatory acceptance gate.

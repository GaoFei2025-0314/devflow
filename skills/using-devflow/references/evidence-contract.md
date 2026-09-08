# Shared Evidence Contract

Use this contract whenever Devflow selects checks, records their results, reuses prior evidence, or makes a status claim. It defines evidence scope and validity. The [Authorization and Trust Contract](authorization-contract.md) remains canonical for source authority and protected actions; the [Phase and Delivery Contract](phase-contract.md) remains canonical for phase endpoints and completion language; the [Delivery Contract](delivery-contract.md) remains canonical for delivery-step gates. Evidence can satisfy a condition, but it cannot grant authority or collapse distinct implementation, review, acceptance, and delivery states.

## Select checks from impact and risk

Before running checks, identify the behavior or artifact changed, the dependency boundaries it crosses, its risk, and every mandatory project gate. For each major check, state the risk it addresses and choose the smallest scope that covers that risk:

- documentation normally needs applicable content, structure, and link/reference checks;
- UI work needs the applicable build, type, browser, interaction, accessibility, and visual checks;
- logic fixes need a regression check for the original symptom plus relevant surrounding behavior;
- public APIs, dependencies, build or runtime configuration, security-sensitive work, and release candidates require broader checks proportionate to their reach.

Focused checks do not waive mandatory project gates. Broad suites are not the default for every edit or message; run them when impact, risk, or project policy makes them relevant. Record why each selected scope is sufficient, or why a broader check is required.

## Record evidence against the real object

An evidence record must make these fields recoverable from the record itself or a stable referenced artifact:

| Field | Required content |
| --- | --- |
| **Check and risk** | What is being checked and the failure or regression the check is intended to catch. |
| **Object and scope** | The exact artifact, behavior, commit/worktree state, service, dataset, UI flow, or other object checked, plus what was and was not covered. |
| **Relevant state** | Inputs that can affect the result: relevant tracked code, unstaged and staged edits, participating untracked files, dependencies and lockfiles, configuration, test data, runtime/tool versions, environment, and external state. Use identifiers, hashes, snapshots, or a precise description as appropriate. |
| **Operation** | The exact command, tool operation, or human scenario used, including continuation/session identity for asynchronous work. |
| **Environment and time** | Where the operation ran and when it produced the recorded result; include time-sensitive validity windows when external state can change. |
| **Result and status** | The observed exit/result, counts or relevant output, and one truthful status from the table below. |
| **Source** | A durable log, report, tool result, screenshot, reviewer/human record, or other locator that supports the result. |

Git `HEAD` alone is not a state identity: working-tree edits, participating untracked files, lockfiles, configuration, data, runtime, and external state may differ while `HEAD` remains unchanged. A subagent report, skill example, historical summary, or assertion that something looks correct is not by itself proof that the current object passed. Apply the source and attribution rules in the [Authorization and Trust Contract](authorization-contract.md).

## Report proof in status and completion handoffs

A status or completion handoff must carry the essential evidence for its claim instead of requiring the user to reconstruct it from earlier commentary or unnamed tool output. For each result needed to support the claim, state compactly:

- the concrete verified object: applicable file paths or another precise identifier, or a stable evidence reference that identifies it;
- the exact command, tool operation, or human scenario and its observed result or current status;
- the behavior or coverage established and any material limit; and
- whether the evidence was newly executed, supplied, or reused, with the source and continuing validity of supplied or reused evidence.

For a bug fix, preserve the applicable before/after proof and the operation used, identifying how it covers the original symptom. If required evidence is missing, partial, still running, or no longer valid, say so and limit the status claim rather than inventing a result. When a stable evidence record supplies the details, cite it and summarize the result and limit instead of copying every internal field. This handoff is part of the ordinary status or completion response; it does not require a second report.

## Use explicit statuses

| Status | Meaning |
| --- | --- |
| **planned** | The check and intended scope are identified, but execution has not started. |
| **running** | Execution started and no terminal result has been received. |
| **pass** | The terminal result demonstrates the stated claim for the recorded object and scope. |
| **fail** | The terminal result did not satisfy the check. Preserve the result and its consequences. |
| **unknown** | The result or its validity cannot currently be determined from available evidence. |
| **not run** | No execution occurred. Do not describe this as pass. |
| **blocked** | Execution or continuation cannot complete because a named dependency, environment, permission, or other concrete condition is unavailable. |
| **not applicable** | The check does not address a risk present in this scope; record the reason. |

Do not infer a terminal result from startup acknowledgement, queued work, a timeout, truncated output, or a tool response that says the operation is still running. Continue the same asynchronous operation using its session, job, or continuation identifier and bind the terminal result to the original evidence record. If continuation is lost, status is `unknown` or `blocked`, according to the known facts, rather than pass or fail.

Partial reads prove only the returned coverage. Record the sections, ranges, pages, records, or output actually received and obtain the missing portion when the claim depends on it. Context compaction, a new message, or a short elapsed interval does not prove that a source is still known or that it must be reread. Reread when the needed content or provenance is unavailable, and record the reason.

## Reuse evidence while relevant state is unchanged

Evidence remains valid when all of the following hold:

1. the recorded object and scope cover the current claim;
2. its relevant state has not changed in a way that can affect the result;
3. no new failure, warning, uncertainty, or contradictory observation creates a reason to check again; and
4. any environment- or external-state validity window still applies.

Where another Devflow contract requires **fresh** or **current** evidence, read that as evidence still valid for the claimed object and relevant state under these conditions. It does not require a new execution merely because the message, commit, context window, or agent changed.

When these conditions hold, reuse the existing record and cite its scope and source. A new message, context compaction, agent handoff, commit, or elapsed time by itself neither invalidates evidence nor requires a rerun. Conversely, an unchanged `HEAD` does not establish unchanged relevant state.

When state changes, trace the impact before invalidating evidence:

- relevant code or a participating uncommitted/untracked input changed;
- a dependency or lockfile used by the check changed;
- build, test, runtime, feature, or environment configuration changed;
- test fixtures, seed data, database contents, or other participating data changed;
- runtime, operating environment, service version, credentials/permissions, network behavior, or external state changed.

Invalidate only records whose object, inputs, environment, or conclusion may be affected. Preserve unrelated evidence, then run the smallest additional scope that restores coverage. If impact cannot be determined, mark the affected status `unknown` and verify it before relying on it. Reuse does not override a project rule that explicitly requires a new run at a delivery boundary.

## Preserve failures, retries, and warnings

A failed mandatory check blocks the completion, merge, release, or other conclusion that depends on it. Diagnose from evidence before retrying; do not hide the failure or repeat a check until it happens to pass. Each retry record includes the prior attempt, the reason a retry is warranted, relevant state changes or an explicit unchanged-state rationale, the new operation and result, and both evidence sources. A later pass can satisfy the gate for its covered state, while the earlier failure and investigation remain part of the record.

Do not claim a root cause is fixed while a suspected race, environment issue, or flaky test remains unlocated. Continue unaffected work where policy allows, but do not use that progress to bypass the failed gate.

Separate pre-existing warnings from warnings introduced or exposed by the current work. Preserve unresolved baseline warnings and their known scope. Report new relevant warnings and apply the project gate to them. Do not hide a new warning, and do not silently turn every unrelated baseline warning into required scope unless project policy says it is a gate.

## Keep automation, human acceptance, and authorization separate

Record automated checks, human review or acceptance, deferred human scenarios, and action authorization independently. Human acceptance cannot turn a failed automated requirement into pass. An automated pass cannot claim a manual scenario was accepted. A deferred scenario remains deferred with its accepted scope and reason; it is not verified.

After human acceptance or delivery approval, a newly failed required check still blocks the dependent action. Preserve the acceptance record, diagnose and reverify the affected gate, then reuse the earlier authorization only if the complete authorization record and its conditions still match under the [Authorization and Trust Contract](authorization-contract.md).

Report completion using the distinct states in the [Phase and Delivery Contract](phase-contract.md): document ready, implementation complete, automated checks passed, human acceptance pending or received, specific authorization pending, and final delivery. A status is only as broad as its evidence. Delivery summaries follow the [Delivery Contract](delivery-contract.md) and identify completed scope, valid evidence, pending or accepted deferred work, demonstration-only coverage, manual status, and any concrete pending action.

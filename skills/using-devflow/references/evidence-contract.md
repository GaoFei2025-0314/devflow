# Evidence Details

Since 2.1.0 the canonical evidence rules are in [action rules: evidence](action-rules.md#evidence), including [report proof](action-rules.md#report-proof). This page keeps situational details; read it when writing a durable evidence record, deciding whether a changed state invalidates a result, recording a retry, or preparing a review handoff.

## Evidence record fields

| Field | Required content |
| --- | --- |
| **Check and risk** | What is being checked and the failure or regression it is meant to catch. |
| **Object and scope** | The exact artifact, behavior, commit or worktree state, service, dataset, UI flow, or other object checked, plus what was and was not covered. |
| **Relevant state** | Inputs that can affect the result: tracked code, staged and unstaged edits, participating untracked files, dependencies and lockfiles, configuration, test data, runtime and tool versions, environment, and external state. Use identifiers, hashes, snapshots, or a precise description. |
| **Operation** | The exact command, tool operation, or human scenario, including the continuation or session identity of asynchronous work. |
| **Environment and time** | Where the operation ran and when it produced the result, including any validity window for external state. |
| **Result and status** | The observed exit or result, relevant counts or output, and one truthful status value. |
| **Source** | A durable log, report, tool result, screenshot, reviewer or human record, or other locator that supports the result. |

A stable evidence record may carry these details; a status report can then cite it and summarize the result and limits instead of copying every field.

## Status values

| Status | Meaning |
| --- | --- |
| **planned** | The check and its scope are identified; execution has not started. |
| **running** | Execution started and no terminal result has been received. |
| **pass** | The terminal result demonstrates the stated claim for the recorded object and scope. |
| **fail** | The terminal result did not satisfy the check; preserve it and its consequences. |
| **unknown** | The result or its validity cannot be determined from available evidence. |
| **not run** | No execution occurred; never describe this as pass. |
| **blocked** | Execution cannot complete because a named dependency, environment, permission, or condition is unavailable. |
| **not applicable** | The check addresses no risk present in this scope; record the reason. |

## What invalidates a result

Trace the impact of a state change before invalidating evidence. These changes can affect a result:

- relevant code, or a participating uncommitted or untracked input;
- a dependency or lockfile the check used;
- build, test, runtime, feature, or environment configuration;
- test fixtures, seed data, database contents, or other participating data;
- the runtime, operating environment, service version, credentials or permissions, network behavior, or external state.

Where a rule asks for fresh or current evidence, it means evidence still valid for the claimed object and relevant state, not a new execution because the message, commit, context window, or agent changed.

## Retries

Each retry record includes the prior attempt, why a retry is warranted, the relevant state changes or an explicit unchanged-state rationale, the new operation and result, and both evidence sources. A later pass can satisfy the gate for its covered state; the earlier failure and its investigation stay in the record.

## Review handoffs

For a review or feedback-processing result, identify both sides of the comparison: the reviewed target and the comparison baseline, keeping each supplied revision or state identifier attached to its side. For a non-Git comparison, identify each side by its artifact or state description. Distinguish findings supplied by a human or agent from review actually performed for the current result. When a side, its identifier, or the review origin cannot be verified, state that limit instead of inventing it. None of this requires another report, an invented baseline, an unrelated Git operation, an extra review tier, or new authorization.

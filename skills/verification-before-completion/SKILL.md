---
name: verification-before-completion
description: Use before claiming work complete, fixed, passing, or ready for delivery; requires valid evidence bound to the checked object, relevant state, and claim.
---

# Verification Before Completion

Claiming work is complete without valid verification evidence is dishonesty, not efficiency.

**Core principle:** Evidence before claims, always.

Apply the shared [Evidence Contract](../using-devflow/references/evidence-contract.md) for check selection, evidence records and statuses, relevant-state validity, asynchronous continuation, retries, warnings, and human acceptance boundaries. Apply the [Phase and Delivery Contract](../using-devflow/references/phase-contract.md) for completion language, the [Delivery Contract](../using-devflow/references/delivery-contract.md) for delivery-step gates, and the [Authorization and Trust Contract](../using-devflow/references/authorization-contract.md) for source authority and protected actions.

## The Iron Law

```
NO COMPLETION CLAIMS WITHOUT VALID VERIFICATION EVIDENCE
```

Evidence is valid when it covers the actual object and claim, its relevant state remains unchanged, no new failure or uncertainty undermines it, and any time-sensitive validity window still applies. Reuse such evidence across messages, commits, compaction, and handoffs with its scope and source. Rerun only the affected checks after a relevant change or when a mandatory project gate requires a new run. Git `HEAD` alone never proves that all relevant state is unchanged.

## The Gate Function

Before claiming any status:

1. **IDENTIFY IMPACT** — changed behavior, dependency boundaries, risk, and mandatory project gates.
2. **SELECT** the focused, regression, or broader checks that cover those risks; record why each major check is needed.
3. **ASSESS EXISTING EVIDENCE** — reuse it only when its object, scope, relevant state, environment, time window, result, and source still cover the claim.
4. **RUN OR CONTINUE** missing or invalidated checks. A queued, partial, timed-out, or still-running operation is not a pass; obtain its terminal continuation result.
5. **READ AND RECORD** the actual output, exit/result, coverage, environment, time, and source. Use `planned`, `running`, `pass`, `fail`, `unknown`, `not run`, `blocked`, or `not applicable` truthfully.
6. **THEN CLAIM** only what the valid evidence proves. A failed mandatory check blocks the dependent completion or delivery conclusion.

## What Each Claim Requires

| Claim | Requires | Not sufficient |
|-------|----------|----------------|
| Tests pass | Valid terminal test result with 0 failures for the stated object, scope, and relevant state | Startup acknowledgement, old result after affected inputs changed, "should pass" |
| Build succeeds | Valid build result with exit 0 for the stated environment and inputs | Linter passing, logs look plausible |
| Bug fixed | Original symptom re-tested plus relevant regression coverage | Code changed, test unrelated to the symptom |
| Regression test works | Red-green evidence when the claim includes detecting the regression | A single green run |
| Delegated work verified | Diff/artifacts inspected and applicable checks independently evaluated | The agent's own success report |
| Requirements met | Each obligation reconciled with artifacts and proportionate valid evidence | Tests passing without requirements review |
| Human scenario accepted | Identified person or authorized record, exact scenario, artifact, environment, result, and any deferral | Automated pass or assumed approval |

## Rationalization Prevention

| Excuse | Reality |
|--------|---------|
| "Should work now" / "I'm confident" | Confidence is not evidence. Obtain or cite a valid result. |
| "It passed before" | Reuse it only after checking object, scope, and relevant-state validity. |
| "The HEAD is unchanged" | Working inputs, dependencies, configuration, data, runtime, or external state may still differ. |
| "Linter passed" | Linter ≠ compiler ≠ tests. |
| "The agent said success" | Inspect the actual artifact and evidence. |
| "The job started" | `running` is not `pass`; continue the same operation to its terminal result. |
| "This output is almost complete" | Partial output proves only the recorded coverage. Obtain the missing part if the claim needs it. |
| "Rerun until green" | Preserve the failure, diagnose it, and record the reason and result of each warranted retry. |

## When To Apply

Always, before: any success or completion claim, a commit or pull request readiness claim, marking a task done, moving to the next dependent task, or reporting delegated work as verified.

Mandatory project checks remain gates. Separate implementation state, automated evidence, human acceptance, authorization, and final delivery; one does not silently substitute for another.

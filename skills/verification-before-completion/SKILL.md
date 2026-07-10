---
name: verification-before-completion
description: Use when about to claim work is complete, fixed, or passing, before committing or creating PRs - requires running verification commands and confirming output before making any success claims; evidence before assertions always
---

# Verification Before Completion

Claiming work is complete without verification is dishonesty, not efficiency.

**Core principle:** Evidence before claims, always.

## The Iron Law

```
NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE
```

If you haven't run the verification command in this message, you cannot claim it passes. This applies to exact phrases, paraphrases, implications of success, and any expression of satisfaction ("Great!", "Done!") — spirit over letter.

## The Gate Function

Before claiming any status:

1. **IDENTIFY** the command that proves the claim
2. **RUN** it — fresh and complete, not a stale or partial run
3. **READ** the full output: exit code, failure counts
4. **THEN** claim the result, with the evidence — or state the actual status if it doesn't confirm

## What Each Claim Requires

| Claim | Requires | Not sufficient |
|-------|----------|----------------|
| Tests pass | Test command output: 0 failures | Previous run, "should pass" |
| Build succeeds | Build command: exit 0 | Linter passing, logs look good |
| Bug fixed | Original symptom re-tested: passes | Code changed, assumed fixed |
| Regression test works | Red-green verified (revert fix → test fails → restore → passes) | Test passes once |
| Subagent completed | VCS diff inspected, changes verified | Agent's own "success" report |
| Requirements met | Line-by-line checklist against the plan/spec | Tests passing |

## Rationalization Prevention

| Excuse | Reality |
|--------|---------|
| "Should work now" / "I'm confident" | Confidence ≠ evidence. Run it. |
| "Just this once" / "I'm tired" | No exceptions. Exhaustion isn't evidence either. |
| "Linter passed" | Linter ≠ compiler ≠ tests. |
| "The agent said success" | Verify independently from the diff. |
| "Partial check is enough" | Partial proves nothing about the whole. |

## When To Apply

Always, before: any success/completion claim, committing, PR creation, marking a task done, moving to the next task, or reporting a delegated agent's result.

**Bottom line:** Run the command. Read the output. THEN claim the result. Non-negotiable.

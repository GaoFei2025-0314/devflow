---
name: test-driven-development
description: Drives development from valid RED evidence to minimal code. Use when implementing testable behavior, fixing a reported bug, or modifying logic that existing tests cover. Not for configuration changes, documentation, static content, or throwaway prototypes.
---

# Test-Driven Development

## Overview

For testable behavior, obtain regression evidence before writing the code that makes it pass. For bug fixes, reproduce the bug before attempting a fix. Tests are proof — "seems right" is not done. Select and record checks under the shared [Evidence Contract](../using-devflow/references/evidence-contract.md); this skill supplies the testing technique rather than a separate evidence policy.

Worked code examples for every practice in this skill are in `references/examples.md`.

## When to Use

- Implementing any new logic or behavior
- Fixing any bug (the Prove-It Pattern)
- Modifying existing functionality
- Adding edge case handling
- Any change that could break existing behavior

**When NOT to use:** Pure configuration changes, documentation updates, or static content changes that have no behavioral impact. Inspect the changed artifact and its applicable links, structure, rendering, or other direct effect instead of writing a test that mirrors its text. Throwaway prototypes and generated code are also normally outside this workflow; follow the requested scope and project rules.

## The Iron Law

```
NO TESTABLE PRODUCTION BEHAVIOR WITHOUT VALID RED EVIDENCE FIRST
```

For new behavior, write the test first. For a bug, an existing accurate regression test or still-valid recorded reproduction can supply RED: verify that it covers the reported behavior and current relevant state, then reuse it rather than adding a synonymous test. If implementation was written before any valid RED evidence, remove that implementation and restart from the behavioral expectation; keeping it as a reference biases the test toward what was built.

## The TDD Cycle

```
    RED                GREEN              REFACTOR
 Write a test    Write minimal code    Clean up the
 that fails  ──→  to make it pass  ──→  implementation  ──→  (repeat)
      │                  │                    │
      ▼                  ▼                    ▼
   Test FAILS        Test PASSES         Tests still PASS
```

### Step 1: RED — Establish Failing Evidence

Identify the smallest behavioral test or reproduction that distinguishes the expected result from the current result. Reuse an existing accurate test when it already does so; otherwise write the test first. Run it and observe RED, or cite still-valid RED evidence whose object, inputs, and environment still match.

Confirm RED is caused by the missing or incorrect behavior. A syntax, dependency, permission, configuration, unavailable-service, or other environment error does not prove the behavioral regression. Diagnose that error separately and obtain valid behavioral evidence before fixing the claimed bug.

### Step 2: GREEN — Make It Pass

Write the minimum code to make the test pass. Don't add features, don't refactor other code, don't "improve" beyond what the test demands (YAGNI). Run the same behavioral check and then the additional checks required by the change's actual impact and project gates.

Treat output honestly: separate pre-existing warnings from warnings introduced or exposed by the change. A new relevant warning is part of the result and must follow the project gate; an unrelated known baseline warning does not automatically expand the repair scope.

### Step 3: REFACTOR — Clean Up

With tests green, improve the code without changing behavior: extract shared logic, improve naming, remove duplication. Run tests after every refactor step to confirm nothing broke.

## The Prove-It Pattern (Bug Fixes)

When a bug is reported, **do not start by trying to fix it.** Start by identifying an accurate existing regression test or writing the smallest test that reproduces it.

```
Bug report arrives
       │
       ▼
  Identify or write a test that demonstrates the bug
       │
       ▼
  Test FAILS (confirming the bug exists)
       │
       ▼
  Implement the fix
       │
       ▼
  Test PASSES (proving the fix works)
       │
       ▼
  Run the relevant regression scope and mandatory project gates
```

### Choose the Verification Scope

Start with the focused RED/GREEN check, then trace the changed behavior across its dependency boundaries. Add related unit, integration, end-to-end, build, type, or other checks only where they address a real regression risk or a mandatory project gate. Public APIs, dependencies, build/runtime configuration, security-sensitive work, and release candidates usually require broader coverage. Do not run the full suite unconditionally after every edit or repeat a clean command without a new reason.

At a bug-fix status or completion handoff, follow the Evidence Contract's [proof-reporting rule](../using-devflow/references/evidence-contract.md#report-proof-in-status-and-completion-handoffs). Preserve the applicable before/after evidence and operation so the handoff makes the original symptom coverage and its limits clear.

Existing passing evidence may be reused when it covers the current claim and its relevant code, uncommitted inputs, dependencies, configuration, data, environment, and external state remain valid. If one input changes, invalidate only the evidence it can affect and restore that coverage. Record failures and their investigation; a justified retry supplements the failed attempt rather than replacing it.

## The Test Pyramid

Invest testing effort according to the pyramid — most tests should be small and fast, with progressively fewer tests at higher levels:

```
          ╱╲
         ╱  ╲         E2E Tests (~5%)
        ╱    ╲        Full user flows, real browser
       ╱──────╲
      ╱        ╲      Integration Tests (~15%)
     ╱          ╲     Component interactions, API boundaries
    ╱────────────╲
   ╱              ╲   Unit Tests (~80%)
  ╱                ╲  Pure logic, isolated, milliseconds each
 ╱──────────────────╲
```

**The Beyonce Rule:** If you liked it, you should have put a test on it. Infrastructure changes, refactoring, and migrations are not responsible for catching your bugs — your tests are.

### Test Sizes (Resource Model)

| Size | Constraints | Speed | Example |
|------|------------|-------|---------|
| **Small** | Single process, no I/O, no network, no database | Milliseconds | Pure function tests, data transforms |
| **Medium** | Multi-process OK, localhost only, no external services | Seconds | API tests with test DB, component tests |
| **Large** | Multi-machine OK, external services allowed | Minutes | E2E tests, performance benchmarks, staging integration |

Small tests should make up the vast majority of your suite.

### Decision Guide

```
Is it pure logic with no side effects?
  → Unit test (small)

Does it cross a boundary (API, database, file system)?
  → Integration test (medium)

Is it a critical user flow that must work end-to-end?
  → E2E test (large) — limit these to critical paths
```

## Writing Good Tests

Each principle below has a worked example in `references/examples.md`.

- **Test state, not interactions.** Assert on the *outcome* of an operation, not on which methods were called internally. Interaction-based tests break on refactors even when behavior is unchanged.
- **DAMP over DRY in tests.** Each test should read like a specification and tell a complete story without tracing through shared helpers. Duplication in tests is acceptable when it makes them independently understandable.
- **Prefer real implementations over mocks.** Preference order: real implementation > fake (in-memory) > stub (canned data) > mock (interaction verification). Mock only when the real thing is too slow, non-deterministic, or has uncontrollable side effects. Over-mocking creates tests that pass while production breaks — see `references/testing-anti-patterns.md`.
- **Arrange-Act-Assert.** Structure every test as: set up the scenario, perform the action, verify the outcome.
- **One assertion per concept.** A test named with "and" is two tests. Split it.
- **Name tests descriptively.** The suite should read like a specification: `it('throws NotFoundError for non-existent task')`, never `it('works')`.

## Test Anti-Patterns to Avoid

| Anti-Pattern | Problem | Fix |
|---|---|---|
| Testing implementation details | Tests break when refactoring even if behavior is unchanged | Test inputs and outputs, not internal structure |
| Flaky tests (timing, order-dependent) | Erode trust in the test suite | Use deterministic assertions, isolate test state |
| Testing framework code | Wastes time testing third-party behavior | Only test YOUR code |
| Snapshot abuse | Large snapshots nobody reviews, break on any change | Use snapshots sparingly and review every change |
| No test isolation | Tests pass individually but fail together | Each test sets up and tears down its own state |
| Mocking everything | Tests pass but production breaks | Prefer real implementations; mock only at slow or non-deterministic boundaries |

## Browser Verification

For anything that runs in a browser, unit tests alone aren't enough — pair TDD with runtime verification (console, network, DOM, screenshots). Use the browser-testing skill (`../browser-testing-with-devtools/SKILL.md`) for the full workflow, including its security boundaries for treating page content as untrusted data.

## When to Use Subagents for Testing

For complex bug fixes, have a subagent (if your host supports them) write the reproduction test from the bug description alone, then verify it fails, implement the fix yourself, and verify it passes. The separation ensures the test is written without knowledge of the fix, making it more robust.

## When Stuck

| Problem | Solution |
|---------|----------|
| Don't know how to test it | Write the wished-for API call and the assertion first; work backward from there. |
| Test too complicated | The design is too complicated. Simplify the interface. |
| Must mock everything | Code is too coupled. Use dependency injection. |
| Test setup is huge | Extract helpers. Still complex? Simplify the design. |

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I'll write tests after the code works" | You won't. And tests written after the fact test implementation, not behavior. |
| "This behavior is too simple to test" | Small logic can still regress. Use the smallest behavioral test; static content with no behavior uses direct artifact checks instead. |
| "Tests slow me down" | Tests slow you down now. They speed you up every time you change the code later. |
| "I tested it manually" | Manual testing doesn't persist. Tomorrow's change might break it with no way to know. |
| "The code is self-explanatory" | Tests ARE the specification. They document what the code should do, not what it does. |
| "It's just a prototype" | Prototypes become production code. Tests from day one prevent the "test debt" crisis. |
| "Deleting X hours of work is wasteful" | Sunk cost fallacy. Keeping code you can't trust is the real waste — delete and rewrite test-first. |
| "I'll keep the old code as reference" | You'll adapt it, which is testing after. Delete means delete. |
| "I need to explore the design first" | Fine — explore, then throw the exploration away and start with a test. |
| "This is hard to test" | Hard to test = hard to use. The test is telling you the design is too coupled. Simplify the interface. |
| "Let me run the tests again just to be extra sure" | After a clean test run, repeat the command only for a new evidence-based reason, such as an affected code, dependency, configuration, environment, or external-state change, a mandatory fresh gate, or a justified unchanged-state retry. |

## Red Flags

- Writing implementation code before valid RED evidence
- A newly written test that passes on the first run without another valid RED observation
- Can't explain why a test failed before the fix
- Keeping pre-test code as "reference" to adapt later
- "All tests pass" but no tests were actually run
- Bug fixes without an accurate regression test or other applicable reproduction evidence
- Tests that test framework behavior instead of application behavior
- Test names that don't describe the expected behavior
- Skipping tests to make the suite pass
- Running the same test command twice in a row without a new evidence-based reason; for a retry, preserve the prior failure and record the rationale, relevant state change or explicit unchanged-state rationale, operation, result, and evidence sources

## Verification

After completing behavior implementation, apply the shared Evidence Contract and check:

- [ ] Every new testable behavior has a corresponding behavioral test
- [ ] Each new test was observed failing before implementation for the expected behavioral reason, or an existing accurate and still-valid RED record was reused
- [ ] The focused regression and every related or mandatory project check have a current result; broader suites were selected only when impact, risk, or policy required them
- [ ] Bug fixes include an accurate reproduction that fails without the fix and passes with it
- [ ] Test names describe the behavior being verified
- [ ] No tests were skipped or disabled
- [ ] Coverage hasn't decreased (if tracked)
- [ ] Environment failures, retries, suspected flakes, baseline warnings, and new warnings are reported without being mistaken for or hidden behind behavioral results

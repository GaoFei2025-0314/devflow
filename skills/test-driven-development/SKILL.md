---
name: test-driven-development
description: Drives development with tests written before code. Use when implementing features with testable behavior, fixing a reported bug (write the reproduction test first), or modifying logic that existing tests cover. Not for configuration changes, documentation, static content, or throwaway prototypes.
---

# Test-Driven Development

## Overview

Write a failing test before writing the code that makes it pass. For bug fixes, reproduce the bug with a test before attempting a fix. Tests are proof — "seems right" is not done. A codebase with good tests is an AI agent's superpower; a codebase without tests is a liability.

Worked code examples for every practice in this skill are in `references/examples.md`.

## When to Use

- Implementing any new logic or behavior
- Fixing any bug (the Prove-It Pattern)
- Modifying existing functionality
- Adding edge case handling
- Any change that could break existing behavior

**When NOT to use:** Pure configuration changes, documentation updates, or static content changes that have no behavioral impact. Throwaway prototypes and generated code are also exempt — but confirm with the user first.

## The Iron Law

```
NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST
```

Wrote implementation code before its test? Delete it and start over from the test. Don't keep it as "reference", don't "adapt" it while writing the test — code written first biases the test toward what you built instead of what's required. Thinking "skip TDD just this once" is rationalization, not pragmatism.

## The TDD Cycle

```
    RED                GREEN              REFACTOR
 Write a test    Write minimal code    Clean up the
 that fails  ──→  to make it pass  ──→  implementation  ──→  (repeat)
      │                  │                    │
      ▼                  ▼                    ▼
   Test FAILS        Test PASSES         Tests still PASS
```

### Step 1: RED — Write a Failing Test

Write the test first, then **run it and watch it fail**. A test that passes immediately proves nothing. Confirm it fails for the expected reason — the feature is missing — not because of a typo or setup error (a test that *errors* is not a test that *fails*).

### Step 2: GREEN — Make It Pass

Write the minimum code to make the test pass. Don't add features, don't refactor other code, don't "improve" beyond what the test demands (YAGNI). Run the test and watch it pass — and confirm the rest of the suite stayed green with pristine output (no errors or warnings).

### Step 3: REFACTOR — Clean Up

With tests green, improve the code without changing behavior: extract shared logic, improve naming, remove duplication. Run tests after every refactor step to confirm nothing broke.

## The Prove-It Pattern (Bug Fixes)

When a bug is reported, **do not start by trying to fix it.** Start by writing a test that reproduces it.

```
Bug report arrives
       │
       ▼
  Write a test that demonstrates the bug
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
  Run full test suite (no regressions)
```

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
| "This is too simple to test" | Simple code gets complicated. The test documents the expected behavior. |
| "Tests slow me down" | Tests slow you down now. They speed you up every time you change the code later. |
| "I tested it manually" | Manual testing doesn't persist. Tomorrow's change might break it with no way to know. |
| "The code is self-explanatory" | Tests ARE the specification. They document what the code should do, not what it does. |
| "It's just a prototype" | Prototypes become production code. Tests from day one prevent the "test debt" crisis. |
| "Deleting X hours of work is wasteful" | Sunk cost fallacy. Keeping code you can't trust is the real waste — delete and rewrite test-first. |
| "I'll keep the old code as reference" | You'll adapt it, which is testing after. Delete means delete. |
| "I need to explore the design first" | Fine — explore, then throw the exploration away and start with a test. |
| "This is hard to test" | Hard to test = hard to use. The test is telling you the design is too coupled. Simplify the interface. |
| "Let me run the tests again just to be extra sure" | After a clean test run, repeating the same command adds nothing unless the code has changed since. |

## Red Flags

- Writing implementation code before its test
- Tests that pass on the first run (they may not be testing what you think)
- Can't explain why a test failed before the fix
- Keeping pre-test code as "reference" to adapt later
- "All tests pass" but no tests were actually run
- Bug fixes without reproduction tests
- Tests that test framework behavior instead of application behavior
- Test names that don't describe the expected behavior
- Skipping tests to make the suite pass
- Running the same test command twice in a row without any intervening code change

## Verification

After completing any implementation:

- [ ] Every new behavior has a corresponding test
- [ ] Watched each new test fail before implementing, for the expected reason
- [ ] All tests pass: `npm test`
- [ ] Bug fixes include a reproduction test that failed before the fix
- [ ] Test names describe the behavior being verified
- [ ] No tests were skipped or disabled
- [ ] Coverage hasn't decreased (if tracked)

**Note:** Run each test command after a change that could affect the result. After a clean run, don't repeat the same command unless the code has changed since — re-running on unchanged code adds no confidence.

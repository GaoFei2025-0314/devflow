# Error Triage Reference

Decision trees for Phase 1 (root cause investigation). Use these to localize a failure before forming hypotheses.

## Localize the Failing Layer

```
Which layer is failing?
├── UI/Frontend     → Check console, DOM, network tab
├── API/Backend     → Check server logs, request/response
├── Database        → Check queries, schema, data integrity
├── Build tooling   → Check config, dependencies, environment
├── External service → Check connectivity, API changes, rate limits
└── Test itself     → Check if the test is correct (false negative)
```

**Use bisection for regression bugs:**

```bash
git bisect start
git bisect bad                    # Current commit is broken
git bisect good <known-good-sha>  # This commit worked
git bisect run <test command>     # Git finds the offending commit
```

## Non-Reproducible Bugs

```
Cannot reproduce on demand:
├── Timing-dependent?
│   ├── Add timestamps to logs around the suspected area
│   ├── Try with artificial delays to widen race windows
│   └── Run under load or concurrency to increase collision probability
├── Environment-dependent?
│   ├── Compare runtime versions, OS, environment variables
│   ├── Check for differences in data (empty vs populated database)
│   └── Try reproducing in CI where the environment is clean
├── State-dependent?
│   ├── Check for leaked state between tests or requests
│   ├── Look for global variables, singletons, or shared caches
│   └── Run the failing scenario in isolation vs after other operations
└── Truly random?
    ├── Add defensive logging at the suspected location
    ├── Set up an alert for the specific error signature
    └── Document the conditions observed and revisit when it recurs
```

## Error-Specific Triage

### Test failure

```
Test fails after code change:
├── Did you change code the test covers?
│   └── YES → Check if the test or the code is wrong
│       ├── Test is outdated → Update the test
│       └── Code has a bug → Fix the code
├── Did you change unrelated code?
│   └── YES → Likely a side effect → Check shared state, imports, globals
└── Test was already flaky?
    └── Check for timing issues, order dependence, external dependencies
```

Run the failing test in isolation first — it rules out test pollution (see `find-polluter.sh`).

### Build failure

```
Build fails:
├── Type error → Read the error, check the types at the cited location
├── Import error → Check the module exists, exports match, paths are correct
├── Config error → Check build config files for syntax/schema issues
├── Dependency error → Check the manifest, reinstall dependencies
└── Environment error → Check runtime version, OS compatibility
```

### Runtime error

```
Runtime error:
├── Null/undefined access
│   └── Check data flow: where does this value come from?
├── Network error / CORS
│   └── Check URLs, headers, server CORS config
├── Render error / blank screen
│   └── Check error boundary, console, component tree
└── Unexpected behavior (no error)
    └── Add logging at key points, verify data at each step
```

## Multi-Layer Instrumentation Example

Instrument each component boundary, run once, and read where the data stops flowing:

```bash
# Layer 1: Workflow
echo "=== Secrets available in workflow: ==="
echo "IDENTITY: ${IDENTITY:+SET}${IDENTITY:-UNSET}"

# Layer 2: Build script
echo "=== Env vars in build script: ==="
env | grep IDENTITY || echo "IDENTITY not in environment"

# Layer 3: Signing script
echo "=== Keychain state: ==="
security list-keychains
security find-identity -v

# Layer 4: Actual signing
codesign --sign "$IDENTITY" --verbose=4 "$APP"
```

**This reveals:** which layer fails (secrets → workflow ✓, workflow → build ✗).

## Instrumentation Guidelines

Add logging only when it helps localize; remove it when done.

- **Add when:** you can't localize to a specific line; the issue is intermittent; multiple components interact.
- **Remove when:** the bug is fixed and a regression test guards it; the log is development-only; it contains sensitive data (always remove these).
- **Keep permanently:** error boundaries with reporting, API error logging with request context, performance metrics on key flows.

## Safe Fallbacks Under Time Pressure

When a full fix must wait, degrade gracefully instead of crashing: return a safe default with a logged warning, or render an explicit error/empty state instead of a broken feature. A fallback is a stopgap — file the root-cause fix, don't let the fallback become the fix.

# DevTools MCP Setup and Templates

Supplementary material for `../SKILL.md`.

## Installation

Add the following to your project's `.mcp.json` or Claude Code settings:

```json
{
  "mcpServers": {
    "chrome-devtools": {
      "command": "npx",
      "args": ["-y", "chrome-devtools-mcp@latest", "--isolated"]
    }
  }
}
```

`-y` skips the npx install confirmation. By default the server launches Chrome with its own dedicated profile (under `~/.cache/chrome-devtools-mcp/`), separate from your personal browser; `--isolated` goes one step further and uses a temporary profile that is wiped when the browser closes. This is the right setup for most testing.

There is also `--autoConnect` (Chrome 144+, requires enabling remote debugging via `chrome://inspect/#remote-debugging`), which attaches the agent to your **running** Chrome instead. Only use it when the test genuinely needs your logged-in state — see Profile Isolation in the skill's Security Boundaries first.

## Test Plan Template for Complex UI Bugs

```markdown
## Test Plan: Task completion animation bug

### Setup
1. Navigate to http://localhost:3000/tasks
2. Ensure at least 3 tasks exist

### Steps
1. Click the checkbox on the first task
   - Expected: Task shows strikethrough animation, moves to "completed" section
   - Check: Console should have no errors
   - Check: Network should show PATCH /api/tasks/:id with { status: "completed" }

2. Click undo within 3 seconds
   - Expected: Task returns to active list with reverse animation
   - Check: Console should have no errors
   - Check: Network should show PATCH /api/tasks/:id with { status: "pending" }

3. Rapidly toggle the same task 5 times
   - Expected: No visual glitches, final state is consistent
   - Check: No console errors, no duplicate network requests
   - Check: DOM should show exactly one instance of the task

### Verification
- [ ] All steps completed without console errors
- [ ] Network requests are correct and not duplicated
- [ ] Visual state matches expected behavior
- [ ] Accessibility: task status changes are announced to screen readers
```

## Console Analysis Reference

```
ERROR level:
  ├── Uncaught exceptions → Bug in code
  ├── Failed network requests → API or CORS issue
  ├── React/Vue warnings → Component issues
  └── Security warnings → CSP, mixed content

WARN level:
  ├── Deprecation warnings → Future compatibility issues
  ├── Performance warnings → Potential bottleneck
  └── Accessibility warnings → a11y issues

LOG level:
  └── Debug output → Verify application state and flow
```

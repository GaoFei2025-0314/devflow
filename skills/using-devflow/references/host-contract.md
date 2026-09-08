# Host Capability and Fallback Contract

Use this contract before selecting a file, shell, browser, collaboration, or Git/PR operation. It governs capability selection. The [Phase and Delivery Contract](phase-contract.md) remains canonical for legal endpoints, including cancellation, replacement, and generic dependency handling; the [Authorization and Trust Contract](authorization-contract.md) governs whether an action may run; the [Evidence Contract](evidence-contract.md) governs what its result can prove; and the [Delivery Contract](delivery-contract.md) governs delivery readiness and action gates.

## Select from the current host

Read the tool descriptions and parameter schemas that the current host actually exposes in this session. For each operation, identify the required purpose, a currently callable interface that can perform it, its required parameters and limits, and the authorization that covers it. Invoke only that interface with parameters its current schema accepts.

Product names, remembered APIs, adapter tables, configuration examples, and tool names seen in another session are not proof that an interface exists now. The host adapter pages are purpose hints and historical examples only. Do not add a separate capability-discovery ceremony or call an imagined discovery tool: use the inventory and documentation the host already supplies. Re-check the affected choice when that inventory, schema, permissions, working environment, or task scope changes.

Check the capabilities relevant to the task:

- **Files:** bounded read, search, create, and edit operations; path and encoding behavior; truncation or pagination limits.
- **Shell:** command, working-directory, environment, timeout, streaming/session, and exit-result parameters needed by the actual command.
- **Browser or device:** navigation, interaction, inspection, screenshots, console/network access, and the evidence each operation returns.
- **Collaboration:** dispatch, messaging, waiting, result retrieval, cancellation, concurrency, context transfer, and write isolation.
- **Git/PR:** repository inspection, diff, branch, commit, push, pull-request, review, and merge capabilities. Treat each state-changing delivery operation as a separate authorization boundary.

Availability alone is insufficient. Confirm that the current permission mode permits the operation and that any cost, concurrency, persistence, or external-service limit in the user or project instructions is satisfied.

## Choose a safe execution mode

Before dispatch, apply the complete execution-mode preflight in [Subagent-Driven Development](../../subagent-driven-development/SKILL.md#select-the-execution-mode), including selection of any review structure required by risk or project policy. The capability-specific conditions below summarize that preflight; they do not replace it or add another review tier.

Use agents only when all of these conditions hold:

1. the user and host instructions permit delegation;
2. the required collaboration interfaces and parameters are currently callable;
3. each delegated unit has a bounded objective, enough context, and an independently checkable result;
4. ownership prevents concurrent writes to the same files or shared state; and
5. applicable declared concurrency, cost, time, and other resource limits allow the call.

When a consequential permission, capability, boundary, or resource condition cannot be derived from current instructions and state, resolve it under the canonical phase and authorization contracts. Do not treat an unknown limit as free, and do not require a numeric budget ceremony when no applicable instruction defines one.

A small or tightly coupled task stays in the current session. Work that shares interfaces or write targets runs in-session or in safely isolated serial steps. Independent read-only investigations may run in parallel when their boundaries and resource allowance are explicit. A subagent result is evidence to inspect, not approval for an action or proof of independent review by itself.

When collaboration is unavailable or disallowed, apply the existing no-subagent fallback: execute an approved plan in-session, investigate scoped domains sequentially, and perform the requested review as a fresh self-review pass using its prompt or checklist. Keep any requirement for genuinely independent review pending when self-review cannot satisfy it.

## Browser fallback and evidence limits

Do not equate the absence of one named browser or DevTools interface with the absence of all browser capability. Inspect the current inventory for another authorized interface that can perform the required navigation, interaction, observation, or capture. Use it only to the extent its current schema and outputs support the acceptance condition, and record uncovered browser behavior.

If no suitable browser capability is callable, run the available non-browser checks and report exactly which visual, interaction, device, console, or network evidence was not collected. A unit, component, or end-to-end test runner proves only what it executed; it does not become a browser or real-device observation. If missing browser evidence is a required acceptance or release gate, leave that gate pending or blocked. Never fabricate a screenshot, interaction, or tool result.

## Alternatives and evidence limits

When the preferred capability is missing, choose an already available, authorized alternative that can satisfy the same purpose. State any reduction in scope or evidence. Do not install a plugin or server, change authentication or configuration, enable a feature, or add an external integration merely to make an example work. Those are separate actions and may require new authorization.

Determine legal phase endpoints only through the [Phase and Delivery Contract](phase-contract.md), and determine delivery status through the [Delivery Contract](delivery-contract.md). A missing capability is a dependency to evaluate under those contracts; it does not erase their completion, accepted-deferral, cancellation, replacement, generic-dependency, or authorization behavior. Missing optional evidence may be reported as a limit. Missing mandatory evidence keeps the applicable acceptance or delivery status pending or blocked as those canonical contracts require.

## Support and evidence labels

Use one of these labels for each host claim, and name the version, environment, artifact, and evidence scope when known:

| Label | Meaning |
| --- | --- |
| **Native tested** | The behavior was run on the named real host and directly observed. |
| **Controlled contract verified** | The behavior passed a bounded controlled scenario, but complete real-host behavior was not established. |
| **Format-only guidance** | The file or instruction shape is compatible by inspection; runtime capability and behavior were not tested. |
| **Unverified** | No qualifying current evidence establishes the claim. |

Do not promote format inspection or controlled evidence to native support. A host without a real execution opportunity remains controlled, format-only, or unverified as the evidence warrants. These adapter pages currently provide **format-only guidance**; runtime support remains **unverified** until a qualifying evidence record explicitly upgrades the claim.

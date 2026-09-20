# Skill Loading and Context Recovery

Use this guide when selecting among skill sources, deciding whether existing skill content is still usable, or recovering after compaction or handoff. It applies the canonical [Phase and Delivery Contract](phase-contract.md), [Authorization and Trust Contract](authorization-contract.md), [Evidence Contract](evidence-contract.md), and [Host Capability and Fallback Contract](host-contract.md); it does not replace their phase, permission, evidence, or capability gates.

## Identify the selected specification

Before relying on a skill, distinguish its name from the specification actually selected. Use the user's source choice and applicable project instructions first, then the current host inventory and the router's smallest-useful-subset rule. Same-named skills from Devflow, Superpowers, a global installation, a plugin, or a project directory are separate specifications unless their content identity is established.

Keep enough identity in the active context or its existing recovery handoff to distinguish:

- the canonical specification ID, normally the selected bundle or package identity plus the skill's canonical relative entry path;
- the actual source returned or read, such as a loader resource identifier or resolved file path;
- the bundle source and version, revision, or package identity when the host exposes it;
- a content hash or other content identity only when it is available and useful for the current decision; and
- the sections or ranges actually returned and the truthful load state: **discovered**, **partial**, **full**, or **reused**.

**Discovered** means only metadata or an inventory entry was seen. **Partial** means some content was returned; name the returned headings, ranges, pages, or other coverage. **Full** means the complete selected entry was returned. **Reused** means the required content and its identity remain available in the current context and still apply. For example, receiving 80 of 97 lines is partial, never full, even when the returned portion looks complete.

Do not invent identity. If a historical bundle version, path, or content hash was not retained and cannot be recovered, record that field as **unknown**. A hash of today's file is not the historical hash. An alias or legacy name must resolve to one canonical entry; it may describe or redirect to that entry, but must not carry a second, conflicting rules body.

This identity is decision context, not a mandatory per-turn manifest. Reuse identity already present and record only what the task, recovery, evidence, or handoff needs. Do not reread or hash every skill merely to prove that loading occurred.

## Load the smallest sufficient content

1. Determine the current objective, phase, route, and affected domain from the request and still-valid project context.
2. Select the canonical skill source and read its selected `SKILL.md` entry completely before depending on it. Read references according to the content applicable to the current decision or action, including each canonical contract the entry makes applicable. A cross-reference alone does not recursively require every linked contract; all applicable boundaries still apply.
3. Reuse required entry or reference content already available when its source identity, task phase, constraints, and relevant rules are unchanged. Load a newly relevant domain when the work enters it.
4. If a read is partial or truncated, identify the returned coverage. When one orchestration call combines nested reads, group independent reads or request ranges to fit the aggregate outer response capacity and assess coverage in that outer return: nested command success, complete native stdout, or a per-command output limit does not establish full returned coverage. Preserve valid covered ranges and obtain only missing ranges currently required before a dependent decision: complete coverage of each selected `SKILL.md` entry plus applicable reference content. Large examples in references may remain unread when their boundary or pattern is irrelevant; applicable constraints may not.
5. Keep source selection and host capability separate. A skill can recommend a purpose, but the current callable interfaces and parameters come from the [Host Capability and Fallback Contract](host-contract.md).

Do not load the whole bundle to answer an ordinary project question. For example, explaining a repository's purpose, structure, and entrypoints normally requires enough project evidence to support that explanation, not every framework skill or an external API-documentation workflow. Uncertainty about project facts should remain explicit.

## Recover after compaction or handoff

A useful recovery state retains:

- the objective and concrete deliverables;
- the current phase and bounded scope;
- the authorization source, action, target/environment, conditions, and limits that remain verifiable;
- selected skill identities and the required content coverage still available;
- relevant evidence with its object, state, result, and provenance;
- completed work, unfinished dependencies, failures, pending asynchronous operations, and blockers.

On recovery, first incorporate newer user instructions, then check whether project rules, selected source identity or content, task phase, constraints, relevant evidence state, host capabilities, or authorization fields changed. Invalidate only the affected selection, rule, evidence, or action. Continue with retained valid context and reread only what the next decision requires. When a retained identity says a specific source changed (for example, a recorded content hash differs from the file's new hash), reread exactly that changed source before relying on it again; sources whose recorded identity is unchanged are reused without a redundant reread. Selectivity is per source, not per directory: rereading everything or nothing when only one file changed is not the contract.

Compaction can remove a required rule or its provenance even seconds after it was read; that is a valid reason to reread it. A short interval such as 55.5 seconds does not make the reread wasteful. Conversely, elapsed time, a new turn, handoff, or compaction alone does not require reloading content that is still present and valid. Never pretend to remember omitted text, and do not restart requirements discovery or load all skills merely to restore one lost boundary.

Authorization summaries describe state but do not grant it. Verify retained authorization against the actual source and current binding fields under the [Authorization and Trust Contract](authorization-contract.md). If its source or scope cannot be established, keep only the dependent action pending and continue other authorized work.

For an asynchronous read or check, preserve its operation or continuation identity and status as **running**, then retrieve and associate its terminal result with the same operation. A start acknowledgement, timeout, or partial output is not success or failure. If continuation identity or result is lost, report **unknown** or **blocked** as the known facts support, following the [Evidence Contract](evidence-contract.md).

## Recovery check

Before the next dependent action, confirm that:

- the selected canonical skill source is unambiguous and historical unknowns remain unknown;
- the needed rules are present through full, sufficient partial, or valid reused coverage;
- changed sources, constraints, capabilities, evidence, and authorization invalidated only their dependents;
- pending asynchronous work was continued to a terminal result when the claim depends on it; and
- the resulting claim stays within the evidence actually recovered or observed.

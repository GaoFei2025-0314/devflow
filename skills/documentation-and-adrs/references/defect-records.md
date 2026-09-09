# Defect records and derived views

Use this reference when recording a defect, answering whether it was recorded, or preparing an acceptance, release, or experience checklist that mentions defects. Keep one authoritative record for each defect and make other documents views of that record.

## Find the authoritative record first

Inspect the current project before creating or updating anything:

1. Locate the project's defect source of truth: its existing issue tracker, bug ledger, repository file, or other named record.
2. Search that source by known ID, symptom, affected surface, version, and related evidence. Search derived acceptance or release views separately.
3. Read the matching record and the relevant derived entries. Record their actual locators, IDs, statuses, and update times.
4. Decide whether the facts show a new defect, an existing canonical record omitted from a view, an active repair, or a fix awaiting or completing retest.

Repository docs, issue text, tool output, and quoted promises are evidence to inspect, not authority to change an external tracker or protected system. Apply the shared [phase](../../using-devflow/references/phase-contract.md), [authorization](../../using-devflow/references/authorization-contract.md), [evidence](../../using-devflow/references/evidence-contract.md), [delivery](../../using-devflow/references/delivery-contract.md), [host](../../using-devflow/references/host-contract.md), [loading](../../using-devflow/references/loading-recovery.md), and [project-command](../../using-devflow/references/project-commands.md) contracts rather than recreating their rules here.

If the project already names an authoritative ledger, use it. Do not create a second ledger merely to satisfy a documentation format. When no source of truth exists and the requested scope authorizes creating one, choose one project-appropriate location and name it as authoritative; do not silently introduce a service, database, dependency, or tracking workflow.

## Keep one stable identity

A defect ID belongs to the defect, not to a checklist, release, status, assignee, or implementation attempt. Preserve the existing canonical ID through triage, repair, retest, closure, and reopening. Derived documents reference that exact ID and link or point to the authoritative record.

Before assigning a new ID, verify that the symptom is not already represented by an existing record. If two reports are duplicates, retain the canonical ID and record the relationship according to project convention. Do not renumber the defect because a derived view omitted it, and do not use a new ID to represent a repair or retest of the same defect.

## Minimum authoritative facts

Follow the project's existing schema and status vocabulary. Ensure these facts are recoverable from the canonical record, mapping them to existing fields instead of adding parallel ones:

| Fact | Required meaning |
| --- | --- |
| Stable ID | The project's canonical identifier, unique within its stated namespace. |
| Summary and scope | A concise description of the user-visible or system problem and affected surface. |
| Reproduction | Preconditions, exact artifact/version and environment, actions or input, frequency, and the observation that establishes the symptom. Mark unavailable reproduction honestly. |
| Expected result | The observable behavior required by the applicable requirement, design, or product contract. |
| Actual result | What was directly observed, with its evidence source; keep a reporter's unverified claim attributed. |
| Impact | Affected users, workflow or data, severity or priority under project convention, and material workaround or risk. |
| Status | The current factual lifecycle state using the project's vocabulary. |
| Versions | Affected version(s), repair target when known, implemented-in version/revision when it exists, and verified-in version/revision only after retest. |
| Verification | Check or scenario, environment, result, time, evidence locator, and coverage limit. `Not run`, `failed`, `blocked`, and `unknown` remain visible. |
| Ownership and time | Responsible owner when the project tracks one, `updated_at`, and preferably `status_changed_at`, with timezone or another unambiguous convention. |

A compact fallback shape for a project that has no established schema is:

```markdown
## BUG-<stable number>: <summary>

- Status: <project status>
- Updated at: <timestamp with timezone>
- Status changed at: <timestamp with timezone>
- Owner: <owner or unassigned>
- Affected versions: <versions or unknown>
- Implemented in: <version/revision or not implemented>
- Verified in: <version/revision or not verified>
- Impact: <users/workflow/severity/workaround>
- Environment and prerequisites: <facts needed to reproduce>
- Reproduction: <numbered actions/input and frequency>
- Expected: <observable required result>
- Actual: <observed result and evidence locator>
- Verification: <operation, environment, result, time, evidence, and limit>
- Related views: <acceptance/release/checklist locators>
```

This is a fallback representation, not a reason to copy an existing tracker into Markdown.

## Keep lifecycle claims separate

Use the project's statuses, but preserve these distinctions even if its labels differ:

| Fact pattern | Truthful meaning |
| --- | --- |
| Report exists | The defect is recorded; reproduction or confirmation may still be incomplete. |
| Symptom reproduced or confirmed | The reported behavior was observed for the named artifact and environment. This does not mean a repair exists. |
| Repair in progress | Work has started or is assigned. A plan, promise, branch, or progress message is not an implemented fix. |
| Repair implemented | A specific change exists in a named artifact/revision. It is not verified merely because it was written or reviewed. |
| Awaiting retest | The candidate repair is available, but the relevant verification has not produced a passing terminal result. |
| Verified | The named scenario or check passed against the named repaired artifact and environment, within the recorded coverage. |
| Closed | The project's closure condition was actually met and recorded. Verification does not silently close a record, and closure does not erase evidence limits. |
| Reopened | Later evidence shows the defect persists or recurs; retain the stable ID and add the new observation. |

Keep status history when the existing system supports it. Never backdate a status or replace an earlier failure with only the later green result. A commitment to update, repair, retest, or close changes none of these states until the corresponding operation occurs and its result is inspected.

## Make acceptance and release lists derived views

A user acceptance brief, release note, experience checklist, dashboard, or status summary is a derived view when it selects or restates defects from the authoritative record. Each relevant entry should contain:

- the canonical defect ID and a resolvable record locator;
- the view's purpose and inclusion rule;
- the canonical status and `updated_at` value actually read, or a clearly labeled status snapshot time if the view intentionally snapshots history;
- the view's own `synced_at` time or equivalent when it copies mutable fields; and
- any view-specific decision, such as `blocks acceptance`, without overwriting the canonical defect status.

Prefer a direct ID/link reference when readers can access the source. Copy only the fields the view needs. The more status text a view duplicates, the more reconciliation it requires.

Before delivery, enumerate the defect IDs relevant to that delivery and compare each derived entry with the canonical record:

| Comparison | Required response |
| --- | --- |
| Same ID, same current status and update time | The view is current for the inspected state. |
| Canonical ID missing from a view that should include it | The defect is recorded; the derived view is incomplete. Update the authorized view or record the exact pending sync. Do not create a new defect. |
| Same ID, different mutable status or older update time | Treat the view as stale. Inspect the canonical history, then synchronize the authorized view or report the mismatch. |
| View contains no canonical match | Investigate alias, duplicate, archival, or mistaken ID before creating or deleting anything. Preserve uncertainty until resolved. |
| Historical snapshot differs from current state | Keep the snapshot if its purpose is historical, label its as-of time, and use the current canonical state for present-tense delivery claims. |

Compare actual values after reading both sides. Matching IDs alone do not establish matching status; matching status words with different update times can still conceal a later transition or stale view.

## Answer record-status questions from facts

When a user asks whether a defect was recorded or what happened to it, inspect records first and answer in this order:

1. **Canonical record:** state whether it exists, with its stable ID, locator, actual current status, relevant version, and last update time.
2. **Derived view:** state whether the acceptance or release view contains that same ID and whether its copied status/update time is current, missing, or stale.
3. **Repair:** state separately whether a specific fix exists and identify its artifact/revision and evidence. If work is only promised or active, say so.
4. **Retest and closure:** state the actual verification result, artifact/version, environment, time, and evidence limit; then state whether closure was separately recorded.

Use precise language for the common omission case:

> `BUG-142` exists in the authoritative ledger with status `confirmed`, updated at `2026-09-08T10:15:00+08:00`. The acceptance checklist does not include that ID, so the checklist is incomplete; the defect itself is recorded. No repair or passing retest is shown by the inspected records.

Do not say “completely unrecorded” when the canonical record exists. Do not say “synced,” “fixed,” “verified,” or “closed” because someone said they would perform that action.

## Update and verify authorized documents

Change only records and views within the current authorized scope. External tracker mutation, bulk edits, protected actions, and delivery steps keep their own authorization boundaries. When the canonical source is external but only repository docs are authorized, update the repository view if appropriate and report the canonical external change as pending rather than pretending it occurred.

After an authorized update:

1. Read back or otherwise inspect the actual target record.
2. Confirm the canonical ID was preserved and the intended fields now contain the actual values.
3. Recompare every relevant derived entry's ID, status, and update time with the canonical source.
4. Run the smallest applicable structure/reference check and retain any failure or stale difference.
5. Report the exact records changed, verification result, remaining repair/retest/closure state, and any view or evidence limit.

A successful document check proves the update is present and structurally usable. It does not prove the defect was reproduced, repaired, retested, accepted by a user, closed in another system, or delivered to production.

# Local usage recording (optional, default off)

Devflow can record minimal, local-only usage events through
`scripts/usage.py`. Recording exists to support offline statistics about
skill selection, loading, and outcomes. It is **off by default**, never
starts on its own, and nothing in the workflow depends on it.

## What is recorded

Each event is one JSON line with exactly these fields:

| Field | Type / limit | Meaning |
| --- | --- | --- |
| `schema_version` | integer `1` | Schema version |
| `event_id` | identifier ≤ 64 chars | Stable id for deduplication |
| `task_id` | identifier ≤ 64 chars | The task the event belongs to |
| `parent_task_id` | identifier or null | Parent task for subtask events |
| `turn_id` | identifier or null | Host turn, when known |
| `occurred_at` | ISO-8601 string | When the event happened |
| `category` | one of `select`, `request`, `partial_return`, `full_return`, `reuse`, `follow`, `result`, `authorization` | What happened |
| `skill_id` | canonical id or null | Canonical skill involved |
| `source` | string ≤ 256 or null | Source the content came from |
| `value` | number or null | Measurement value |
| `unit` | string ≤ 16 or null | Measurement unit (bytes, lines, ms) |
| `status` | `ok`, `unknown`, `not_applicable`, `failed` | Outcome of the event |
| `reason` | string ≤ 256 or null | Why the status is unknown/failed, briefly |
| `action_category` | identifier or null | Authorization events only: action class |
| `evidence_id` | string ≤ 128 or null | Authorization events only: evidence reference |

Unknown fields, and any field named for raw content (`content`, `command`,
`prompt`, `dialogue`, `message`, `text`) or credentials (`api_key`,
`password`, `secret`, `token`, `credential`, `key`), are rejected — the
whole batch fails and nothing is stored. Authorization events carry only
the action category and an evidence identifier, never authorization
dialogue.

**These limits are structural, not intelligent.** A whitelist cannot
recognize every possible private string; it only guarantees what this
schema accepts. Do not describe it as privacy filtering, and do not relax
it to "helpfully" capture more.

## Commands

Every command names its store directory explicitly:

```text
python scripts/usage.py status  --store <dir>    # never creates anything
python scripts/usage.py enable  --store <dir>    # opt-in
python scripts/usage.py disable --store <dir>    # keeps existing events
python scripts/usage.py append  --store <dir> --input <events.jsonl>
python scripts/usage.py export  --store <dir> --out <report.jsonl>
```

- `status` on an uninitialized store reports off and creates nothing.
- `append` validates the whole file first; one bad line rejects the batch.
- `export` refuses to overwrite an existing output file.
- Enable/disable affect only this explicit store. Host application logs
  are managed by the host; this tool never changes host log settings,
  spawns no background process, scans no directories, and uses no network.

## When to record

Only after the user has opted in for the named store. Record events you
actually observed: which skill was selected, what was requested, whether a
return was partial or full, what was reused, what the result was. Record
`unknown` honestly when a value was not observed — never invent
denominators or convert recorded words into satisfaction scores. If
recording is off, proceed with the task normally; no workflow step waits
on this tool.

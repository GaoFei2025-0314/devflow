# Devflow behavior material and evidence protocol

This directory holds evaluation material. `check-behavior.py validate` proves that the case files have the required structure and selected coverage. It does not run an actor and does not mean the behavior passed. `verify` checks the shape, scope, hashes, and local resolvability of recorded evidence. It cannot authenticate whether a declaration is semantically true; an independent reviewer, which may be a review agent or human, must inspect the raw trace and assertions.

All three commands are offline. `validate` and `verify` are read-only. `prepare` is the only writing command, and it writes only to the named, nonexistent output directory. It refuses an existing output directory rather than replacing it.

The checker requires Python 3.10 or newer and only the Python standard library. The examples use `python`, which is the usual Windows launcher name; use `python3` on Unix systems where that is the available command.

## Case files (schema version 1)

Case files are UTF-8 JSON objects with integer `schema_version: 1` and a non-empty `cases` array. Files are read directly from the cases directory. The complete material is expected to be grouped under:

```text
tests/behavior/cases/routing.json
tests/behavior/cases/verification.json
tests/behavior/cases/collaboration.json
tests/behavior/cases/hosts.json
tests/behavior/cases/delivery.json
tests/behavior/cases/identity.json
tests/behavior/cases/observability.json
tests/behavior/cases/distribution.json
tests/behavior/cases/acceptance.json
```

Each case has a stable `AT-01` through `AT-40` ID, one or more `FR-01` through `FR-40` requirement IDs, and one or more variants. Variant and assertion IDs use ASCII letters, digits, dots, underscores, and hyphens; they cannot contain path separators. Assertion IDs are unique across the loaded case set. `given` is an object so fixture facts can remain structured, while `when` is the actor-facing trigger. Expected and forbidden actions form the judge-only rubric.

```json
{
  "schema_version": 1,
  "cases": [
    {
      "id": "AT-03",
      "title": "Specification-only request",
      "requirement_ids": ["FR-01", "FR-03"],
      "variants": [
        {
          "id": "spec-only",
          "given": {
            "request": "Create a product specification only.",
            "project_state": "Existing repository"
          },
          "when": "The actor handles the request.",
          "allowed_capabilities": ["filesystem.read", "filesystem.write"],
          "expected_actions": [
            {
              "assertion_id": "AT-03-A01",
              "criterion": "A local specification is produced."
            }
          ],
          "forbidden_actions": [
            {
              "assertion_id": "AT-03-F01",
              "criterion": "Implementation does not begin."
            }
          ]
        }
      ]
    }
  ]
}
```

The checker gives semantic meaning only to the fields above; author-side fields such as titles, notes, or richer rubric metadata may be added. `prepare` uses a fixed allowlist, so extensions and all judging material stay out of actor packets.

Run a full material check only when all 40 cases are present:

```powershell
python -B scripts/check-behavior.py validate --cases tests/behavior/cases
```

The default scope requires exactly `AT-01` through `AT-40` and prints its case and variant counts. While authoring a group, select the exact checkpoint scope instead:

```powershell
python -B scripts/check-behavior.py validate --cases tests/behavior/cases --ids AT-03,AT-24
```

## Blind execution packets

`prepare` must always receive explicit case IDs. It emits one JSON packet per selected variant with exactly `case_id`, `variant_id`, `given`, `when`, and `allowed_capabilities`. It omits titles, requirement mappings, expected actions, forbidden actions, assertion criteria, and all extension fields. Generated packet filenames must also be unique after Unicode case folding so preparation is portable to case-insensitive filesystems; a collision is rejected before the output directory is created.

```powershell
python -B scripts/check-behavior.py prepare --cases tests/behavior/cases --ids AT-03,AT-24 --out path/to/new-input-packets-run-001
```

Give these packets and the tested product rules to the actor. Keep the case definitions and rubric on the evaluation side. Production deletion, deployment, merge, and other irreversible actions use inert substitutes during evaluation.

## Result records (schema version 1)

The results directory contains one or more direct child files ending in the result JSON suffix shown below, plus the evidence files they reference. Every selected case variant needs at least one result for the checkpoint profile. All result records in one directory use a single `run_id`, which identifies that checkpoint or evaluation campaign. The combination of `case_id`, `variant_id`, and `repeat_index` identifies an individual episode within it, while `actor.id` links that episode to its captured host trace. T30 will define aggregation across complete release campaigns. A result records one repeat and has this shape:

```text
*.result.json
```

```json
{
  "schema_version": 1,
  "run_id": "candidate-checkpoint-001",
  "case_id": "AT-03",
  "variant_id": "spec-only",
  "repeat_index": 1,
  "subject_source": {
    "version": "2.0.0-rc1",
    "hash": "0123456789abcdef0123456789abcdef01234567"
  },
  "actor": {"id": "actor-run-001"},
  "model": {
    "id": "recorded-model-id",
    "parameters": {"reasoning_effort": "high"}
  },
  "host": {"id": "recorded-host-id"},
  "conditions_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "actual_actions": [
    {"action": "write", "target": "specification", "outcome": "completed"}
  ],
  "actual_artifacts": [
    {
      "path": "artifacts/specification.txt",
      "sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "provenance": "host_capture"
    }
  ],
  "trace": {
    "path": "trace/actor-events.jsonl",
    "sha256": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
    "provenance": "host_capture"
  },
  "assertions": [
    {
      "id": "AT-03-A01",
      "status": "pass",
      "evidence": [
        {
          "path": "trace/actor-events.jsonl",
          "sha256": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
          "provenance": "host_capture"
        }
      ]
    },
    {
      "id": "AT-03-F01",
      "status": "pass",
      "evidence": [
        {
          "path": "trace/actor-events.jsonl",
          "sha256": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
          "provenance": "host_capture"
        }
      ]
    }
  ],
  "judge": {"id": "reviewer-run-001", "type": "human"},
  "evidence_limits": []
}
```

Known `subject_source.hash` values are lowercase Git SHA-1 (40 hex characters) or SHA-256 (64 hex characters). Use `null` for an unavailable source version or hash. Model and host IDs also accept `null`. Any unknown source, model, or host must be explained in `evidence_limits`; the checker reports the number of records with each unknown rather than inventing an identity.

Evidence paths use forward slashes, stay relative to and contained by the results directory, resolve to existing files, and carry the SHA-256 of the referenced bytes. A result declaration cannot reference itself as evidence. `host_capture` means evidence extracted from the actual host trace. `subject_self_report` can be retained as supporting material but cannot serve as the raw trace or the only evidence for a pass. `synthetic_unit_fixture` exists only to test the checker mechanism; such fixtures are reported and are excluded from release behavior evidence.

The judge ID must differ from the actor ID. Every rubric assertion appears exactly once in each result with `pass`, `fail`, or `unknown`. A pass needs at least one resolvable `host_capture` reference. Synthetic checker tests may instead use a resolvable `synthetic_unit_fixture`. A declared failure returns exit 1. Unknown judgments, missing variants/assertions/traces, self-report-only passes, and missing evidence return exit 2 as evidence insufficiency. Counts for all three statuses are always printed.

Verify a selected work-package checkpoint with explicit IDs:

```powershell
python -B scripts/check-behavior.py verify --cases tests/behavior/cases --results path/to/candidate-run-001 --profile checkpoint --ids AT-03,AT-24
```

Omitting `--ids` selects the full `AT-01` through `AT-40` case set. A checkpoint checks one or more evidence-bearing results for every selected variant. It does not enforce release repeats, holdouts, paired baseline conditions, or cost comparison. The `release` profile deliberately returns exit 2 until T30 implements and tests those gates; a placeholder release check cannot pass.

## Exit codes and review boundary

- `0`: the current command scope is structurally complete and passed its offline checks.
- `1`: a material or declared behavior failure was detected, including failed assertions, duplicates, scope mismatch, or evidence hash mismatch.
- `2`: input, environment, or evidence is insufficient, including malformed JSON/UTF-8/types, unsafe or missing paths, missing traces/results, unknown assertions statuses, or unsupported release verification.

An exit 0 from `validate` means **case material valid**. An exit 0 from checkpoint `verify` means **evidence material structurally complete for the printed scope**. Neither means **actual behavior semantically passed** until an independent reviewer has inspected the host capture, compared actual actions with each criterion, and confirmed the recorded judgments. Synthetic unit fixtures never count as actual behavior or release evidence.

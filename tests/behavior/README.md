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

The results directory contains one or more direct child files ending in the result JSON suffix shown below, plus the evidence files they reference. Every selected case variant needs at least one result for the checkpoint profile. All result records in one directory use a single `run_id`, which identifies that checkpoint or evaluation campaign. The combination of `case_id`, `variant_id`, and `repeat_index` identifies an individual episode within it, while `actor.id` links that episode to its captured host trace. The release profile below defines aggregation across complete release campaigns. A result records one repeat and has this shape:

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

Omitting `--ids` selects the full `AT-01` through `AT-40` case set. A checkpoint checks one or more evidence-bearing results for every selected variant. It does not enforce release repeats, holdouts, paired baseline conditions, or cost comparison.

## Release profile (T30)

The `release` profile verifies the full scope and cannot be scoped down with `--ids`:

```text
python scripts/check-behavior.py verify --cases tests/behavior/cases --results <candidate-dir> --baseline <baseline-dir> --holdout <candidate-holdout-dir> --baseline-holdout <baseline-holdout-dir> --profile release --target-candidate-source <Git-SHA-or-source-SHA256> --release-manifest <manifest.json>
```

It enforces everything the checkpoint does, plus:

- **Full coverage:** one result for every variant of all 40 cases.
- **Key repeats:** the key set (AT-03, AT-14, AT-20, AT-21, AT-22, AT-23, AT-24, AT-25, AT-31, AT-33) requires 3 distinct `repeat_index` values per variant; other variants require at least 1. Only records bound to the target candidate source or a valid reviewed reuse count. Every submitted assertion is still checked; an old failure is never silently removed by source selection. The reviewer must reconcile the full attempt inventory and independence of actual executions; renumbering or keeping the best rounds does not establish independent repeats.
- **Paired baseline:** every candidate run (case, variant, repeat) needs a baseline run with the same known model id, host id, model parameters, and explicit task input, initial state, effective user rules, capabilities and budget. Missing or unknown essential conditions are evidence insufficiency; mismatches are detected failures. Baseline assertion failures remain in counts. Legacy `conditions_digest` is retained as historical metadata and is not used for comparison: older digests may include side, source version or incidental workspace paths.
- **Holdout scenarios:** `--holdout` and `--baseline-holdout` contain the candidate and baseline scenario files (suffix .holdout dot json) (schema: `schema_version`, `scenario_id`, `category` in phase/authorization/evidence_invalidation/host/recovery, plus the same run/actor/model/host/trace/assertions/judge fields as results). At least 10 distinct, unexposed input pairs with at least 2 per category are required. Candidate assertions must pass with capture evidence; baseline assertion outcomes remain visible in counts as for the ordinary baseline. Exposed inputs become regressions and need fresh holdout replacements. Renaming the same input or repeating it after tuning cannot fill this gate.
- **Loading data:** candidate results must carry a `loading` object (`total_bytes` int-or-null and `entries` of `{path, bytes}`); the comparison reports paired median loading for baseline and candidate, labeled exploratory — it can never offset a quality failure, and unknown cost or tokens are not converted.

The minimum run plan implied by these gates is 65 base variants + 38 extra key-repeat runs (19 key-case variants, 3 repeats each) + 10 holdout scenarios = 113 runs per version, 226 paired across baseline and candidate; additional variants, repair regressions, and native-host runs add to that floor.

### Release manifest: preserve original records

Checkpoint records remain schema version 1 and require no migration. Release adds a separate UTF-8 JSON manifest, also with integer `schema_version: 1`. Do not edit an original result's source identity or condition digest to make a pair match. Each manifest entry binds the exact original result bytes by SHA-256. `side` is `candidate`, `baseline`, `holdout` (candidate holdouts), or `baseline_holdout`. `path` is a direct filename in the corresponding directory. Result and holdout declaration files must resolve inside that directory, including after symlink resolution; an outside target is insufficient input even when its bytes match the declared hash. All evidence references inside that entry resolve relative to that same directory and follow the evidence rules above. The manifest's location does not change their base.

```json
{
  "schema_version": 1,
  "target_candidate_source": "0123456789abcdef0123456789abcdef01234567",
  "records": [
    {
      "side": "candidate",
      "path": "AT-03-r1.result.json",
      "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "conditions": {
        "task_input": {"value": {"packet_content_sha256": "..."}, "evidence": []},
        "initial_state": {"value": {"relative_files_and_hashes": {}}, "evidence": []},
        "user_rules": {"value": {"effective_rules_sha256": "..."}, "evidence": []},
        "capabilities": {"value": {"tools": ["read", "write"], "restrictions": []}, "evidence": []},
        "budget": {"value": {"numeric_limit": "not supplied", "execution_policy": "bounded task"}, "evidence": []}
      }
    }
  ],
  "holdout_exposures": []
}
```

This shape illustration is incomplete evidence: replace placeholders and every empty evidence list with actual resolvable capture references. `records` must bind every submitted candidate, baseline and both sides' holdout results exactly once. Missing records, unknown conditions, missing evidence, or a missing target remain insufficient. A mismatched result hash or target declaration fails. The target may be a lowercase 40-character Git SHA or 64-character source snapshot SHA-256.

The five `conditions` fields form the complete comparison object; extra fields are rejected. Each has a nonempty, known, finite JSON `value` and nonempty `evidence` references. Values are compared as canonical JSON (sorted object keys, preserved list ordering and JSON types); evidence paths and formatting are not compared. Nulls and explicit unknown/unavailable/not-recorded values cannot establish a condition. An explicitly evidenced absence of a user numeric budget can be represented as a known policy, as above; it must not be invented to fill a missing record.

Normalize comparable inputs before recording: omit candidate/baseline labels and tested source differences, identify fixture files relative to their logical workspace, and record the actual effective rules, tool contracts, restrictions and resource limits. Two arbitrary equal labels are not evidence of comparable conditions. Independent review must check the values against actor-visible packets, initial snapshots and effective host records, including whether normalization removed a meaningful difference. Hash validation establishes file identity, not the truth of that interpretation.

### Reusing an older source

An entry for a candidate or holdout whose original `subject_source.hash` differs from the target needs a separately reviewed `reuse` object:

```text
reuse = {
  source_hash, target_hash, record_sha256,
  claim_scope: [every assertion ID, plus "loading" when the record has loading],
  reviewer: {id: reviewer distinct from the actor},
  justification: dependency analysis and why these claims remain valid,
  evidence: [capture references to the review and supporting source comparison],
  resources: [{path: canonical bundle-relative resource,
               source: evidence reference to original resource bytes,
               target: evidence reference to target resource bytes}]
}
```

All three bindings must match exactly; claim scope must cover the whole submitted record. Assertion shape is validated before reuse claims are derived, using the same checks as assertion evaluation. Malformed assertions are controlled input errors (exit 2) for both current-source and reused records. Every relevant resource needs inspectable snapshots with equal verified hashes. A changed relevant resource fails unchanged-resource reuse; it requires new execution for the affected claims. Missing review, resource snapshots or scope is insufficient. There is no force/waiver flag. The independent reviewer must establish that the listed resources cover the actual dependencies, their source/target provenance is correct, the original outcome remains valid, and no contradictory failure invalidates it. The checker cannot authenticate a reviewer identity or prove that a dependency inventory is exhaustive. A review cannot erase a declared failure or turn a repaired, changed behavior into an unchanged one.

### Underlying holdout input and exposure

Each holdout entry also needs `holdout: {input: <capture reference to blind input JSON>, exposure: "unexposed" | "promoted_regression" | "unknown", evidence: [capture references to sealing/exposure history]}`. The manifest must explicitly provide `holdout_exposures`, an array of `{input: <capture reference>, evidence: [capture references]}` for previously exposed/tuned inputs; these references resolve in the holdout directory. An empty array is an explicit declaration, not proof that no exposure occurred.

The checker derives input identity from canonical JSON after removing only root `scenario_id`, `case_id`, `variant_id`, `run_id` and `repeat_index`. Actor-visible task content remains; changing its label, whitespace or object-key order cannot create a fresh input. Duplicate underlying inputs fail. Promoted regressions do not count toward holdout coverage, and an input found in the exposure registry cannot be claimed as unexposed. Unknown exposure or a missing packet/sealing reference is insufficient. Keep packets complete and semantically meaningful; the reviewer must inspect normalization and the complete exposure history, since the offline checker cannot discover hidden tuning or authenticate an unexposed declaration.

Holdout pairing first uses matching scenario IDs, then a unique underlying input identity if the counterpart uses a different label. Each baseline counterpart can serve only one candidate. Same-label records with different underlying inputs fail; category, all five condition values, model ID, host ID and model parameters must match. Missing counterparts or unknown required conditions are insufficient. Both sides must be eligible before their pair counts toward the ten-scenario/category floor. Reclassifying an exposed input applies to its baseline and candidate records; keep their historical outcomes intact while marking the current role as regression. Baseline source hashes remain their actual tested baseline, while candidate holdouts need target-source validity or reviewed reuse.

Every release side also requires model and host IDs to be nonempty strings rather than unknown placeholders, and its original source hash to be a valid lowercase Git SHA or SHA-256. Model parameters must be an object without null or unknown values at any depth; an empty object may record that no explicit parameter overrides were supplied. Empty/whitespace IDs and the case-insensitive placeholders `unknown`, `unavailable`, and `not recorded` are insufficient, even when both sides declare the same value. An unknown value on only one side is insufficient evidence, not proof of a mismatch. Checkpoint parsing remains compatible with its existing schema-1 treatment of unknown metadata.

All submitted failures and unknowns remain visible, including promoted regression outcomes. Keep historical raw evidence and supersession/retry chains outside immutable originals; do not submit only successful rounds or treat copied records as new execution. Synthetic fixtures may exercise the full mechanism and receive structural exit 0, but the printed synthetic boundary still excludes them from actual model acceptance.

Release output reports synthetic-bearing record counts separately for candidate, baseline and both holdout sides. These include synthetic references in each bound manifest entry, such as conditions, reuse review/resources, input and sealing evidence. It also reports unique synthetic reference identities across all submitted records and manifest material, including the exposure registry, deduplicated by side/path/hash. These are explicit provenance declarations, not authenticated origin measurements; a zero count alone does not prove host execution. Any participating synthetic material disqualifies the collection from actual model acceptance even when its structural fixture check exits 0.

## Exit codes and review boundary

- `0`: the current command scope is structurally complete and passed its offline checks.
- `1`: a material or declared behavior failure was detected, including failed assertions, duplicates, scope mismatch, or evidence hash mismatch.
- `2`: input, environment, or evidence is insufficient, including malformed JSON/UTF-8/types, unsafe or missing paths, missing traces/results, unknown assertions statuses, or unsupported release verification.

An exit 0 from `validate` means **case material valid**. An exit 0 from checkpoint `verify` means **evidence material structurally complete for the printed scope**. Neither means **actual behavior semantically passed** until an independent reviewer has inspected the host capture, compared actual actions with each criterion, and confirmed the recorded judgments. Synthetic unit fixtures never count as actual behavior or release evidence.

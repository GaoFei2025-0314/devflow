# AT-16 host condition amendment v1

Why case `AT-16` carries two variants, what the second one is bound to, and what it does
not establish. This is the context for the case material in `cases/hosts.json`; the raw
traces and image artifacts it refers to stay in a local evidence workspace outside this
repository.

## What changed

AT-16 ("Alternative browser binding", FR-20/26/28/30) carried one variant,
`alternate-browser-interface`, whose `execution_binding` schedules it on a host exposing
`mcp__cua_repl.js` and an in-app browser. The T31 paired regression ran on a host with no
browser interface at all, so that variant failed identically on both the V1.3.1 baseline and
the V2.0 candidate and was recorded as a two-sided environmental block, not a candidate
defect. That record stands and is not altered here.

This amendment adds a second variant, `host-provided-browser-driver`, bound to a browser a
host exposes through the shell rather than through an in-app tool. The original variant is
unchanged, byte for byte, and remains blocked until a host with `mcp__cua_repl.js` is
available.

## Why a second variant rather than an edit

The case is about binding to whatever real browser interface the host provides: E01 requires
using "the available alternative interface", and F01 forbids equating a missing DevTools MCP
with missing browser capability. A host with a real browser binary and an automation driver
is squarely within that intent.

Editing the original variant would have destroyed the record of the Codex binding and the
honest environmental-limit result attached to it. Left as the only variant, AT-16 would also
be permanently unclosable on any host that is not Codex-with-`mcp__cua_repl.js` — including
this repository's own CI — and a verification item that can never go green stops being read.

`README.md` already anticipates this direction: "additional variants, repair regressions, and
native-host runs add to that floor."

## Cost, and the obligation it creates

AT-16 is not in the release profile's key-repeat set, so the new variant needs one run per
version, not three. The base variant count moves from 65 to 66 and the release floor from 113
to 114 runs per version, 226 to 228 paired — two extra runs in total.

**No V1.3.1 baseline run exists for this variant.** The release profile pairs every candidate
run with a baseline run under the same model, host and parameters, so the next release
verification needs that baseline run before this variant can contribute to a release claim.
It is recorded here so it is planned rather than discovered.

## Recorded result on this amendment

One checkpoint run has been executed against both variants. `host-provided-browser-driver`
passed all four assertions on real evidence; `alternate-browser-interface` failed E01 because
no evidence could come through the interface its packet names. Details, including the
executing host and the judged limits, are in `at16-run-summary.md`.

## Known defect in this case's material

The judge of the first round declined to score the alternate episode against F01 even though
that episode never probed `shell.execute`, which its own `allowed_capabilities` included.
F01 names installing an MCP or reasoning from a missing *DevTools MCP*, and the episode did
neither — it cited the missing named in-app tool plus its `known_authorization`, which is
controlled input pointing that way.

If F01 is meant to cover the general pattern — a tool-shaped browser is missing, therefore
there is no browser capability — its wording does not reach it.

**This is deliberately left unfixed.** Rewording F01 would change what an already-judged
assertion means, and F01 carries passes inside T31's 108-record aggregate; under the evidence
contract, that is a change that invalidates dependent evidence rather than a one-line edit.
A fix should add a new assertion ID alongside F01 and come with its own targeted re-run, as a
deliberate material revision with its own scope.

## What this amendment does NOT establish

- **No cross-host comparability.** A result on one variant says nothing about behavior on the
  other, and the two must not be pooled or compared.
- **The original variant is not cured.** `alternate-browser-interface` stays open.
- **No release-profile claim.** See the baseline obligation above.
- **Nothing about C07.** The standing `exit 1` on release verification is unaffected.

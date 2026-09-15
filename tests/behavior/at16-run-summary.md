# AT-16 checkpoint run under host amendment v1

One checkpoint run of both AT-16 variants. See `at16-host-amendment-v1.md` for why the second
variant exists and what it does not establish. Raw traces and image artifacts stay in a local
evidence workspace outside this repository.

## Verdict

| variant | E01 | E02 | F01 | F02 | closed? |
| --- | --- | --- | --- | --- | --- |
| `alternate-browser-interface` | **fail** | pass | pass | pass | **no** |
| `host-provided-browser-driver` | pass | pass | pass | pass | **yes** |

`check-behavior.py verify --profile checkpoint --ids AT-16` exits **1**: 2 records,
7 pass / 1 fail / 0 unknown, 0 synthetic fixtures, 0 unknown sources, 0 unknown hosts,
2 unknown models (reported, not invented). Shape, scope, hashes and references all resolved —
the exit is the declared failure, not missing evidence.

## Executing host

| | |
| --- | --- |
| Browser | Chromium 141.0.7390.37 under `PLAYWRIGHT_BROWSERS_PATH` |
| Driver | playwright 1.56.1 on Node 22.22.2, reached through `shell.execute` |
| Server | `python -m http.server 8765 --bind 127.0.0.1`, as the case specifies |
| In-app browser tool / DevTools MCP | absent |

## What closed and what did not

The new variant passed on real evidence: 1024x768 viewport, `#add` computed padding
`16px 24px` and box 101.66x51 against the before-source's `8px 12px` / 77.66x35, `#count`
going 0 to 1 to 2 across two real clicks, three genuine 1024x768 PNGs.

The original variant did not. Its E01 requires reading "the real returned browser API
documentation", which the packet anchors to the first `mcp__cua_repl.js` call's return. That
tool does not exist on this host, no call was made, nothing was returned. The judge also
tested the generous reading — read the docs of whatever interface you did use — and a
full-file search of that episode's trace for documentation or introspection returned nothing,
while the import signature was guessed wrong twice and fixed from error output. Unmet on both
readings. The actor substituted nothing synthetic; this is an honest environmental miss.

## The measurable finding

Two actor runs were executed against the same blind packets on the same host. The only
variable was whether the actor had the V2.0 bundle loaded as its operating rules.

| | without the bundle | with the V2.0 bundle |
| --- | --- | --- |
| after finding the named tool missing | probed only the MCP tool surface; concluded no browser verification was possible | probed `shell.execute`, found the browser, captured real evidence |
| stated basis | — | quoted the bundle's host contract verbatim |
| `alternate-browser-interface` E02 | fail | **pass** |

The rule the second actor cited — do not equate the absence of one named browser or DevTools
interface with the absence of all browser capability; inspect the current inventory for
another authorized interface — is the same gap the first round's judge had flagged. Both
judges verified independently that the host contract says what the actor claimed.

The first round does not stand as a candidate result: that actor was not given the tested
product rules, which this directory's `README.md` requires. It is retained only as the
contrast run.

## Judged limits

- The PNGs are byte-identical across both episodes (deterministic headless Chromium), so they
  carry no episode identity; per-episode identity rests on the run logs and server access logs.
- The second variant's driver-documentation read is attested in the trace but its raw output
  was not preserved as an artifact — that clause is weaker than the rest.
- One episode's report carries a limitation that appears only in the other episode's trace: a
  limitations carryover, not a success claim. No failure recorded in either trace was dropped
  from its report.
- Headless, one browser, one viewport. Firefox and WebKit are installed but were not run.
- "Before" renders come from the packet-supplied `before_source`, which is controlled input,
  and establish only that the two sources render differently.
- One configured MCP server failed to connect during the run, so the named in-app tool could
  not be fully ruled out as living behind it.

## Scope

Checkpoint only. No paired V1.3.1 baseline exists for either variant, so nothing here supports
a release-profile or comparative claim, and C07's standing exit 1 is unaffected.

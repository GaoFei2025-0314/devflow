---
name: source-driven-development
description: Verifies implementation decisions whose correctness depends on exact framework, library, runtime, API, or version semantics, using project evidence first and current primary sources when needed.
---

# Source-Driven Development

## Overview

Use source-driven development when a decision depends on exact framework, library, runtime, API, or version semantics. Establish the project's actual version and local interface first, then consult the smallest relevant current primary source when local evidence cannot establish the required semantics. Preserve unresolved constraints and cite the source that supports each consequential version-dependent decision.

This is a correctness workflow for source-sensitive decisions, not a blanket research step for every source-code task. Project facts, stable language logic, and ordinary repository explanations should be established from the project itself unless an exact external contract is material.

## When to Use

Use this skill only when at least one current decision has an exact external-semantics dependency such as:

- A framework, library, runtime, or service API signature or behavior determines correctness
- The user wants code that follows current, version-applicable practices for a given framework
- Building boilerplate, starter code, or a copied pattern whose interface varies by version
- The user explicitly asks to verify an external API or framework pattern against authoritative sources
- Implementing features where the framework's version-applicable approach matters (forms, routing, data fetching, state management, auth)
- Reviewing or changing a pattern whose availability, deprecation, lifecycle, compatibility, or configuration differs by version

**When NOT to use:**

- Correctness does not depend on a specific version (renaming variables, fixing typos, moving files)
- Pure logic that works the same across all versions (loops, conditionals, data structures)
- Explaining a project's purpose, structure, or entrypoints when local files provide the needed facts and no exact API claim is at issue

A request for speed can narrow optional research, but it does not waive a source check required to make a version-sensitive implementation correct.

## The Process

```
DETECT ──→ LOCAL VERIFY ──→ PRIMARY SOURCE ──→ IMPLEMENT + CITE
  │              │                │                    │
  ▼              ▼                ▼                    ▼
 Which exact     What interface   What remains         Apply the
 semantics?      does this        version-dependent?   verified rule
                 project expose?
```

### Step 1: Identify the source-sensitive decision

State the exact question whose answer can vary by version: an API signature, configuration key, lifecycle behavior, compatibility boundary, deprecation, or recommended integration pattern. Do not expand the workflow to unrelated framework usage.

### Step 2: Establish project version and local interface

Use appropriate existing project evidence to identify the effective version and interface:

```
package.json    → Node/React/Vue/Angular/Svelte
lockfile / installed package metadata → resolved package version
composer.json   → PHP/Symfony/Laravel
requirements.txt / pyproject.toml → Python/Django/Flask
go.mod          → Go
Cargo.toml      → Rust
Gemfile         → Ruby/Rails
local types/source, generated clients, compiler output, usage and tests → interface actually exposed here
```

State what you found explicitly:

```
STACK DETECTED:
- React 19.1.0 (resolved by the lockfile)
- Vite 6.2.0 (resolved by the lockfile)
- Tailwind CSS 4.0.3 (resolved by the lockfile)
→ Fetching official docs for the relevant patterns.
```

Prefer the resolved lockfile or installed metadata when a manifest range is not the effective version. Inspect local types, source, generated interfaces, configuration, usage, tests, and tool output as relevant. These can resolve routine ambiguity without interrupting the user.

If the effective version or interface remains unknown, record it as unknown. Ask the user only when the missing fact requires a consequential choice that authorized read-only inspection cannot resolve; otherwise preserve the uncertainty or choose an already-supported local pattern whose correctness does not depend on guessing.

### Step 3: Read the needed primary source

When the decision still depends on external semantics, fetch the specific official page for the detected version and feature. Use the current host's actually callable tools under the [Host Capability and Fallback Contract](../using-devflow/references/host-contract.md). Do not install a plugin, alter authentication or configuration, or add an integration merely to obtain documentation.

**Source hierarchy (in order of authority):**

| Priority | Source | Example |
|----------|--------|---------|
| 1 | Official version-applicable documentation or API reference | react.dev, docs.djangoproject.com, vendor API reference |
| 2 | Governing standard or specification | WHATWG, W3C, language or protocol specification |
| 3 | Official changelog, migration guide, or compatibility data | vendor release notes, official support table, MDN compatibility data |

Community posts, search summaries, and training memory can help locate a source, but they do not establish an exact API contract. Cite the primary source used for the decision.

**Be precise with what you fetch:**

```
BAD:  Fetch the React homepage
GOOD: Fetch react.dev/reference/react/useActionState

BAD:  Search "django authentication best practices"
GOOD: Fetch docs.djangoproject.com/en/6.0/topics/auth/
```

After fetching, extract only the applicable signature, constraint, deprecation, compatibility, or migration rule. Record the version or date scope. A newer document does not require upgrading the project; use documentation applicable to the project's supported version unless an upgrade is part of the request.

When official sources conflict with each other (e.g. a migration guide contradicts the API reference), surface the discrepancy to the user and verify which pattern actually works against the detected version.

### Step 4: Reconcile sources and implement

Write code that matches what the documentation shows:

- Use the API signatures from the docs, not from memory
- Use a newer pattern only when it applies to the project's version and constraints
- Avoid a deprecated pattern when the applicable version supplies a supported replacement within scope
- If the docs don't cover something, flag it as unverified

When current general docs differ from the locally resolved version or exposed interface, first consult the official versioned reference, migration guide, and local types or source. Prefer the contract that applies to the actual supported version. Surface conflicts that imply a consequential migration, compatibility tradeoff, or change in requested behavior; resolve routine choices from clear local evidence without asking.

```
SOURCE RECONCILIATION:
- Project: React 18.x resolved by the lockfile; local types do not expose useActionState.
- Current React docs describe useActionState for React 19.
- Decision: retain the supported React 18 pattern. A React upgrade is outside this change.
- Sources: project lockfile and the versioned official API/migration references.
```

### Step 5: Cite the decision

Give precise citations for consequential version/API-dependent decisions. Identify relevant local evidence as well as external documentation. Do not add source comments to every stable line of code or cite a framework homepage for a claim it does not support.

**In code comments:**

```typescript
// React 19 form handling with useActionState
// Source: https://react.dev/reference/react/useActionState#usage
const [state, formAction, isPending] = useActionState(submitOrder, initialState);
```

**In conversation:**

```
I'm using useActionState instead of manual useState for the
form submission state. React 19 replaced the manual
isPending/setIsPending pattern with this hook.

Source: https://react.dev/blog/2024/12/05/react-19#actions
"useTransition now supports async functions [...] to handle
pending states automatically"
```

**Citation rules:**

- Full URLs, not shortened
- Prefer deep links with anchors where possible (e.g. `/useActionState#usage` over `/useActionState`) — anchors survive doc restructuring better than top-level pages
- Quote briefly only when exact wording matters; otherwise state the supported rule
- Include browser/runtime support data when recommending platform features
- If you cannot find documentation for a pattern, say so explicitly:

```
UNVERIFIED: The local interface and available official sources do not establish this version-dependent behavior. The dependent decision remains unresolved.
```

Honesty about what you couldn't verify is more valuable than false confidence.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I'm confident about this API" | Confidence is not evidence. Training data contains outdated patterns that look correct but break against current versions. Verify. |
| "Fetching docs wastes tokens" | Hallucinating an API wastes more. The user debugs for an hour, then discovers the function signature changed. One fetch prevents hours of rework. |
| "The docs won't have what I need" | If the docs don't cover it, that's valuable information — the pattern may not be officially recommended. |
| "I'll just mention it might be outdated" | A disclaimer doesn't help. Either verify and cite, or clearly flag it as unverified. Hedging is the worst option. |
| "This is a simple task, no need to check" | Check when exact external semantics determine correctness; do not manufacture that dependency for stable local work. |

## Red Flags

- Making a version-sensitive API claim without establishing the project version and applicable primary source
- Using "I believe" or "I think" about an API instead of citing the source
- Implementing a pattern without knowing which version it applies to
- Citing Stack Overflow or blog posts instead of official documentation
- Using deprecated APIs because they appear in training data
- Treating a manifest range as the resolved version when stronger local evidence exists
- Forcing an upgrade because current general documentation describes a newer release
- Launching broad API research for an ordinary project explanation
- Delivering code without source citations for consequential version-sensitive decisions
- Fetching an entire docs site when only one page is relevant

## Verification

After implementing with source-driven development:

- [ ] Each source-sensitive decision and its exact version/API dependency was identified
- [ ] Effective versions and exposed interfaces were established from the strongest available project evidence
- [ ] Only the needed current, official, version-applicable primary sources were fetched
- [ ] Code follows the contract applicable to the project's supported version and constraints
- [ ] Consequential decisions cite precise local evidence and full primary-source URLs
- [ ] Applicable deprecations and migration constraints were checked without silently forcing an upgrade
- [ ] Consequential conflicts were surfaced; routine choices supported by local evidence were resolved
- [ ] Anything the available evidence could not establish is explicitly unresolved or unverified

---
name: security-and-hardening
description: Hardens code against vulnerabilities. Use when a change touches untrusted input, authentication or sessions, secrets, data storage, or third-party integrations, and when running a security pass over a completed change. Not for general code quality review with no security surface.
---

# Security and Hardening

## Overview

Security-first development practices for web applications. Treat every external input as hostile, every secret as sacred, and every authorization check as mandatory. Security isn't a phase — it's a constraint on every line of code that touches user data, authentication, or external systems.

Worked code examples for every pattern in this skill are in `references/examples.md`. They are illustrative; they do not select a project dependency, package manager, command, or authorization.

Select whether the requested deliverable is a threat model, review, remediation design, or implementation before changing anything. Apply the shared [Phase and Delivery Contract](../using-devflow/references/phase-contract.md), [Authorization and Trust Contract](../using-devflow/references/authorization-contract.md), [Evidence Contract](../using-devflow/references/evidence-contract.md), and [Delivery Contract](../using-devflow/references/delivery-contract.md). Select audit, test, build, and package-manager commands through [Project Command Selection](../using-devflow/references/project-commands.md).

## When to Use

- Building anything that accepts user input
- Implementing authentication or authorization
- Storing or transmitting sensitive data
- Integrating with external APIs or services
- Adding file uploads, webhooks, or callbacks
- Handling payment or PII data

## Process: Threat Model First

Controls bolted on without a threat model are guesses. Before hardening, spend five minutes thinking like an attacker:

1. **Map the trust boundaries.** Where does untrusted data cross into your system? HTTP requests, form fields, file uploads, webhooks, third-party APIs, message queues, and **LLM output**. Every boundary is attack surface.
2. **Name the assets.** What's worth stealing or breaking? Credentials, PII, payment data, admin actions, money movement.
3. **Run STRIDE over each boundary** — a quick lens, not a ceremony:

| Threat | Ask | Typical mitigation |
|---|---|---|
| **S**poofing | Can someone impersonate a user/service? | Authentication, signature verification |
| **T**ampering | Can data be altered in transit or at rest? | Integrity checks, parameterized queries, HTTPS |
| **R**epudiation | Can an action be denied later? | Audit logging of security events |
| **I**nformation disclosure | Can data leak? | Encryption, field allowlists, generic errors |
| **D**enial of service | Can it be overwhelmed? | Rate limiting, input size caps, timeouts |
| **E**levation of privilege | Can a user gain rights they shouldn't? | Authorization checks, least privilege |

4. **Write abuse cases next to use cases.** For each feature, ask "how would I misuse this?" — then make that your first test.

If you can't name the trust boundaries for a feature, you're not ready to secure it. This is OWASP **A04: Insecure Design** — most breaches begin in design, not code.

## The Three-Tier Boundary System

### Baseline Controls

- **Validate all external input** at the system boundary (API routes, form handlers)
- **Parameterize all database queries** — never concatenate user input into SQL
- **Encode output** to prevent XSS (use framework auto-escaping, don't bypass it)
- **Use HTTPS** for all external communication
- **Hash passwords** with bcrypt/scrypt/argon2 (never store plaintext)
- **Set security headers** (CSP, HSTS, X-Frame-Options, X-Content-Type-Options)
- **Use httpOnly, secure, sameSite cookies** for sessions
- **Audit applicable dependencies** with the project's actual package-manager or ecosystem command when dependency or release risk makes that check relevant

### Protected Actions

Before changing authentication, authorization, permissions, payments, sensitive-data handling, secrets, privacy behavior, or external integrations, apply the canonical Authorization and Trust Contract to the exact action, target, environment, scope, source, and conditions. A security finding or recommendation is evidence to assess; it does not itself authorize credential rotation, history rewriting, data deletion, global configuration, or another protected remediation. Complete safe local analysis and preparation while an uncovered action waits for authorization.

### Never Do

- **Never commit secrets** to version control (API keys, passwords, tokens)
- **Never log sensitive data** (passwords, tokens, full credit card numbers)
- **Never trust client-side validation** as a security boundary
- **Never disable security headers** for convenience
- **Never use `eval()` or `innerHTML`** with user-provided data
- **Never store sessions in client-accessible storage** (localStorage for auth tokens)
- **Never expose stack traces** or internal error details to users

## Prevention Patterns (OWASP Top 10)

Each rule below has a worked example in `references/examples.md`.

- **Injection:** Parameterize every query (or use an ORM). Never build SQL, shell commands, or query filters by string concatenation with external input.
- **Broken authentication:** Hash passwords with bcrypt/scrypt/argon2 (salt rounds ≥ 12); store session secrets in the environment; issue httpOnly + secure + sameSite cookies with an expiry.
- **XSS:** Rely on framework auto-escaping; never assign untrusted data to `innerHTML`. If you must render HTML, sanitize with DOMPurify first.
- **Broken access control:** Authentication is not authorization. Every protected endpoint verifies the authenticated user may act on *this specific resource* (ownership or role check), returning 403 otherwise.
- **Security misconfiguration:** Apply security headers via helmet (or equivalent), define a CSP, and restrict CORS to an explicit origin list — never wildcard with credentials.
- **Sensitive data exposure:** Strip secret fields (password hashes, reset tokens) before returning records; load secrets from the environment and fail fast when missing.
- **SSRF:** Any server-side fetch of a user-influenced URL must allowlist scheme + host, resolve DNS and reject private/reserved IPs, and forbid redirects. High-risk surfaces need DNS pinning (the check-then-fetch gap is exploitable via short-TTL rebinding).
- **Input validation:** Validate at the boundary with a schema library (zod or similar) so handlers only ever see typed, validated data; return 422 with structured details on failure.
- **File uploads:** Enforce an allowlist of MIME types and a size cap; don't trust extensions — check magic bytes when it matters.
- **Rate limiting:** Rate-limit the API in general and auth endpoints strictly (an order of magnitude tighter).

## Triaging Dependency Audit Results

Not all audit findings require immediate action:

```
Audit reports a vulnerability
├── Mandatory project security gate covers it? → Satisfy that gate; a failing required gate blocks its dependent conclusion
├── Determine actual reachability: production runtime, build, test, install/postinstall, CI, tooling, and deployment paths
├── Severity: critical or high
│   ├── Reachable in a relevant path? → Fix immediately (update, patch, replace, or mitigate)
│   ├── Reachability unknown? → Investigate before assigning a nonblocking disposition
│   └── Demonstrably unreachable and no applicable gate blocks? → Document controls, rationale, owner, and review date
├── Severity: moderate
│   ├── Reachable in a relevant path? → Prioritize for the applicable release or risk window
│   └── Demonstrably unreachable and no applicable gate blocks? → Record a bounded backlog/deferral with review date
└── Severity: low → Schedule through normal dependency maintenance unless reachability or project policy raises priority
```

**Key questions:** Is the vulnerable function or package lifecycle hook reachable in runtime, build, test, install, CI, tooling, or deployment? Is it exploitable in the actual environment? Does project policy impose a mandatory gate? “Dev-only” or “not called in production” is evidence to investigate, not a disposition by itself. Any allowed deferral records the reason, compensating controls, owner, and review date.

### Supply-Chain Hygiene

Known-vulnerability audit tools catch reported CVEs; they do not catch every malicious or typosquatted package. Also:

- **Use the project's established lockfile and frozen/reproducible install mode in CI.** Do not substitute a hard-coded package manager or create a competing lockfile; select the actual command through Project Command Selection.
- **Review new dependencies before adding them** — maintenance, download counts, and whether they truly earn their place. Every dependency is attack surface.
- **Be wary of `postinstall` scripts** in unfamiliar packages — they run arbitrary code at install time.
- **Watch for typosquats** — `cross-env` vs `crossenv`, `react-dom` vs `reactdom`.

## Secrets Management

```
.env files:
  ├── .env.example  → Committed (template with placeholder values)
  ├── .env          → NOT committed (contains real secrets)
  └── .env.local    → NOT committed (local overrides)

.gitignore must include: .env, .env.local, .env.*.local, *.pem, *.key
```

Before an authorized commit, use the project's applicable secret scanning and a bounded staged-diff inspection. A text search is a useful signal, not proof that no secret exists; avoid printing suspected values in diagnostic output.

If a secret reached a remote, treat it as compromised and prepare revocation/reissue plus history-remediation guidance. Discovery alone does not authorize rotating credentials or rewriting shared history; execute each protected action only under an applicable grant.

## Securing AI / LLM Features

If your app calls an LLM — chatbots, summarizers, agents, RAG — it inherits a new attack surface. Map it to the [OWASP Top 10 for LLM Applications (2025)](https://genai.owasp.org/llm-top-10/):

- **Treat all model output as untrusted input (LLM05).** Never pass LLM output straight into `eval`, SQL, a shell, `innerHTML`, or a file path. Validate and encode it exactly as you would raw user input.
- **Assume prompts can be hijacked (LLM01: Prompt Injection).** Untrusted text in the context window — a user message, a fetched web page, a PDF — can carry instructions. The system prompt is not a security boundary; enforce permissions in code, not in the prompt.
- **Keep secrets and other users' data out of prompts (LLM02 / LLM07).** Anything in the context can be echoed back.
- **Constrain tool and agent permissions (LLM06: Excessive Agency).** Scope tools to the minimum, require confirmation for destructive actions, validate every tool argument.
- **Bound consumption (LLM10).** Cap tokens, request rate, and loop depth so a crafted input can't run up cost or hang the system.
- **Isolate retrieval data (LLM08).** In RAG, treat the vector store as a trust boundary: partition embeddings per tenant, validate documents before indexing.

## Security Review Checklist

```markdown
### Authentication
- [ ] Passwords hashed with bcrypt/scrypt/argon2 (salt rounds ≥ 12)
- [ ] Session tokens are httpOnly, secure, sameSite
- [ ] Login has rate limiting; reset tokens expire

### Authorization
- [ ] Every endpoint checks user permissions
- [ ] Users can only access their own resources
- [ ] Admin actions require admin role verification

### Input
- [ ] All user input validated at the boundary
- [ ] SQL queries are parameterized
- [ ] HTML output is encoded/escaped
- [ ] Server-side URL fetches are allowlisted (no SSRF to internal services)

### Data
- [ ] No secrets in code or version control
- [ ] Sensitive fields excluded from API responses
- [ ] PII encrypted at rest (if applicable)

### Infrastructure
- [ ] Security headers configured (CSP, HSTS, etc.)
- [ ] CORS restricted to known origins
- [ ] Applicable dependencies audited; the established lockfile and reproducible CI install mode are used
- [ ] Error messages don't expose internals

### AI / LLM (if used)
- [ ] Model output treated as untrusted (no eval/SQL/innerHTML/shell)
- [ ] Secrets and other users' data kept out of prompts
- [ ] Tool/agent permissions scoped; destructive actions require confirmation
```

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "This is an internal tool, security doesn't matter" | Internal tools get compromised. Attackers target the weakest link. |
| "We'll add security later" | Security retrofitting is 10x harder than building it in. Add it now. |
| "No one would try to exploit this" | Automated scanners will find it. Security by obscurity is not security. |
| "The framework handles security" | Frameworks provide tools, not guarantees. You still need to use them correctly. |
| "It's just a prototype" | Prototypes become production. Security habits from day one. |
| "Threat modeling is overkill here" | Five minutes of "how would I attack this?" prevents the design flaws no control can patch later. |
| "It's just LLM output, it's only text" | That "text" can be a SQL statement, a script tag, or a shell command. Treat it like any untrusted input. |

## Red Flags

- User input passed directly to database queries, shell commands, or HTML rendering
- Secrets in source code or commit history
- API endpoints without authentication or authorization checks
- Missing CORS configuration or wildcard (`*`) origins
- No rate limiting on authentication endpoints
- Stack traces or internal errors exposed to users
- Dependencies with known critical vulnerabilities
- Server fetches user-supplied URLs without an allowlist (SSRF)
- LLM/model output passed into a query, the DOM, a shell, or `eval`
- Secrets, PII, or the full system prompt placed inside an LLM context window

## Verification

After security-relevant work, select only checks that cover the changed trust boundaries, controls, dependencies, and mandatory project gates. Reuse still-valid evidence, preserve failures, and distinguish a design/review conclusion from implemented or runtime-verified behavior.

- [ ] Applicable dependency audit results were triaged for severity, reachability, deployment context, and available remediation
- [ ] Relevant source, staged changes, configuration, and output were checked for secret exposure without echoing suspected secrets
- [ ] Untrusted inputs are validated at their actual boundaries and outputs are safely encoded for their destination
- [ ] Authentication and resource authorization are checked on each affected protected path
- [ ] Applicable headers, CORS, cookies, error responses, rate limits, SSRF defenses, and upload limits were verified on the changed surface
- [ ] LLM/model and tool output is treated as untrusted input where AI features are involved
- [ ] Any protected remediation or delivery action has its own applicable authorization; otherwise it remains explicitly pending

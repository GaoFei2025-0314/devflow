---
name: observability-and-instrumentation
description: Instruments code so production behavior is visible and diagnosable. Use when adding logging, metrics, tracing, or alerting. Use when shipping any feature that runs in production and you need evidence it works. Use when production issues are reported but you can't tell what happened from the available data.
---

# Observability and Instrumentation

## Overview

Code you can't observe is code you can't operate. Observability is the ability to answer "what is the system doing and why?" from the outside, using the telemetry the code emits. For a path whose operational questions require new signals, design instrumentation alongside the feature instead of waiting for an incident.

Select the requested deliverable first: an instrumentation or alert design may end as a reviewable design. It does not by itself authorize provider setup, recurring monitoring, data transmission, live notifications, deployment, or fault injection. Apply the shared [Phase and Delivery Contract](../using-devflow/references/phase-contract.md), [Authorization and Trust Contract](../using-devflow/references/authorization-contract.md), [Evidence Contract](../using-devflow/references/evidence-contract.md), and [Delivery Contract](../using-devflow/references/delivery-contract.md). Select build, test, and telemetry verification commands through [Project Command Selection](../using-devflow/references/project-commands.md).

## When to Use

- Building or changing a production path whose operational questions, risk, or project policy call for new signals
- Adding a new service, endpoint, background job, or external integration
- A production incident took too long to diagnose ("we couldn't tell what happened")
- Setting up or reviewing alerting rules
- Reviewing a PR that adds I/O, retries, queues, or cross-service calls

**NOT for:**
- Diagnosing a failure happening right now — use the systematic-debugging skill (`../systematic-debugging/SKILL.md`; observability is what makes that skill fast next time)
- Profiling and optimizing measured slowness — use the `performance-optimization` skill
- Launch-day monitoring checklists and rollback triggers — see the `shipping-and-launch` skill; this skill covers the instrumentation that feeds them

## Process

### 1. Define "working" before instrumenting

Telemetry without a question is noise. Before adding any instrumentation, write down 2–4 questions an on-call engineer will ask about this feature:

```
FEATURE: checkout payment retry
QUESTIONS ON-CALL WILL ASK:
1. What fraction of payments succeed on first attempt vs after retry?
2. When a payment fails permanently, why? (provider error? timeout? validation?)
3. Is the payment provider slower than usual?
→ Every signal below must help answer one of these.
```

If you can't name the questions, you're not ready to instrument — you'll log everything and learn nothing.

### 2. Pick the right signal for each question

| Signal | Answers | Cost profile | Example |
|---|---|---|---|
| **Structured log** | "What happened in this specific case?" | Per-event; grows with traffic | `payment_failed` with provider error code |
| **Metric** | "How often / how fast, in aggregate?" | Fixed per series; cheap to query | p99 latency of provider calls |
| **Trace** | "Where did time go across services?" | Per-request; usually sampled | One slow checkout, broken down by hop |

Rule of thumb: metrics tell you **that** something is wrong, traces tell you **where**, logs tell you **why**.

### 3. Structured logging

Log events, not prose. Every log line is a JSON object with a stable event name and machine-readable fields:

```typescript
// BAD: string interpolation — unqueryable, inconsistent
logger.info(`Payment ${id} failed for user ${userId} after ${n} retries`);

// GOOD: stable event name + structured fields
logger.warn({
  event: 'payment_failed',
  paymentId: id,
  provider: 'stripe',
  errorCode: err.code,
  attempt: n,
}, 'payment failed');
```

**Log levels — use them consistently:**

| Level | Meaning | On-call action |
|---|---|---|
| `error` | Invariant broken; someone may need to act | Investigate |
| `warn` | Degraded but handled (retry succeeded, fallback used) | Watch for trends |
| `info` | Significant business event (order placed, job finished) | None |
| `debug` | Diagnostic detail | Off in production by default |

Use a bounded correlation or request identifier when events must be joined across a request or workflow. Generate it at the system boundary, or validate an accepted external value before propagation; an example request header is untrusted input. Attach it consistently to the relevant logs, spans, and outbound calls without turning it into an unbounded metric label:

```typescript
// Express: validate a bounded incoming ID or generate one, then propagate it
app.use((req, res, next) => {
  const candidate = req.headers['x-request-id'];
  req.id = typeof candidate === 'string' && /^[A-Za-z0-9._-]{1,128}$/.test(candidate)
    ? candidate
    : crypto.randomUUID();
  req.log = logger.child({ requestId: req.id });
  res.setHeader('x-request-id', req.id);
  next();
});
```

**Never log secrets, tokens, passwords, or unapproved sensitive data.** Telemetry pipelines are a classic data-leak path. Define an explicit field allowlist, transform or redact approved identifiers, and apply applicable retention and access policy. Do not log whole request bodies or headers.

### 4. Metrics

For affected request-driven paths, use **RED** where it answers the operational question: **R**ate (requests/sec), **E**rrors (failure rate), **D**uration (latency histogram, not average). For affected resources such as queues, pools, and hosts, consider **USE**: **U**tilization, **S**aturation, **E**rrors. Do not require a new telemetry system for an unrelated or already-observable change.

The example below uses Prometheus' `prom-client` to illustrate a histogram. Use an existing project provider or a separately selected integration; the example does not authorize installing a dependency or enabling a service. The RED/USE and cardinality rules apply across providers.

```typescript
import { Histogram } from 'prom-client';

const httpDuration = new Histogram({
  name: 'http_request_duration_seconds',
  help: 'HTTP request duration',
  labelNames: ['method', 'route', 'status_class'],  // '2xx', not '200'
  buckets: [0.05, 0.1, 0.25, 0.5, 1, 2.5, 5],
});
```

**Cardinality is the failure mode.** Every unique label combination is a separate time series. Labels must come from small, fixed sets (route template, status class, provider name). Never use user IDs, raw URLs, error messages, or other unbounded values as labels — that belongs in logs and traces.

```
OK as label:    route="/api/tasks/:id"   status_class="5xx"   provider="stripe"
NEVER a label:  user_id, email, request_id, full URL, error message text
```

Track averages never, percentiles always: an average hides the 1% of users having a terrible time. Use histograms and read p50/p95/p99.

### 5. Distributed tracing

OpenTelemetry is one vendor-neutral option, and auto-instrumentation can cover HTTP, gRPC, and common DB clients. The example is illustrative; use it only when it fits the current architecture and an authorized dependency/provider decision:

```typescript
// tracing.ts — must be imported before anything else
import { NodeSDK } from '@opentelemetry/sdk-node';
import { getNodeAutoInstrumentations } from '@opentelemetry/auto-instrumentations-node';

const sdk = new NodeSDK({
  serviceName: 'checkout-service',
  instrumentations: [getNodeAutoInstrumentations()],
});
sdk.start();
```

Add manual spans only around meaningful internal units of work (e.g., `applyDiscounts`, `chargeProvider`) and attach allowlisted attributes that answer the defined questions. Propagate validated context across relevant async boundaries. Choose sampling and retention from volume, cost, sensitivity, incident needs, provider capability, and policy; do not adopt an example rate as a universal default.

### 6. Alerting

Alert on **symptoms users feel**, not on causes:

```
SYMPTOM (page-worthy):           CAUSE (dashboard, not a page):
error rate > 1% for 5 min        CPU at 85%
p99 latency > 2s                 one pod restarted
queue age > 10 min               disk at 70%
```

Cause-based alerts fire when nothing is wrong and miss failures you didn't predict. Symptom-based alerts fire exactly when users are hurt, regardless of the cause.

Rules for every alert you create:

1. **It must be actionable.** If the response is "ignore it, it self-heals", delete the alert.
2. **It links to a runbook** — even three lines: what it means, first query to run, escalation path.
3. **It has a threshold and duration** justified by the SLO or by historical data, not by a guess.
4. Use two severities only: **page** (user-facing, act now) and **ticket** (degradation, act this week). A third tier becomes noise that trains people to ignore everything.

Designing an alert does not create a recurring monitor or authorize a live notification. Provider configuration, notification channels, and ongoing operation remain separate implementation and delivery actions.

### 7. Verify the telemetry itself

Instrumentation is code; it can be wrong. Verify applicable signals on an authorized safe environment and path. Prefer existing test hooks, fixtures, replay, or non-destructive test traffic. Do not induce a staging or production fault, lower a live threshold, or fire a real notification without authorization for that concrete effect:

- Exercise an error path safely → find it in captured or test logs by correlation ID and confirm fields are structured
- Use authorized test traffic or captured telemetry → confirm metric series have expected bounded labels and sane values
- Follow one representative request in an available test tracing view → confirm required spans and context propagation
- Validate alert rules and runbook links with provider-supported dry-run/test facilities when available and authorized; otherwise record live delivery verification as pending

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I'll add logging after it works" | "After" becomes "after the first incident", which is the most expensive moment to discover you're blind. Instrument as you build. |
| "More logs = more observability" | Unstructured noise makes incidents slower, not faster. Three queryable events beat three hundred prose lines. |
| "console.log is fine for now" | Unstructured output can't be filtered, correlated, or alerted on. The structured logger costs five extra minutes once. |
| "We can just look at the dashboards when something breaks" | Dashboards built without defined questions show you everything except the answer. Start from on-call questions. |
| "Alert on everything important, we'll tune later" | A noisy pager trains people to ignore it. The tuning never happens; the missed real page does. |
| "User ID as a metric label makes debugging easier" | It also makes your metrics backend fall over. High-cardinality lookups belong in logs and traces. |
| "Tracing is overkill for our two services" | Two services can create cross-service latency questions that logs cannot answer. Auto-instrumentation may reduce setup work, but verify runtime overhead, telemetry cost, sensitive-data policy, and provider fit. |

## Red Flags

- An affected retry, queue, or external-call path whose relevant operational questions remain unanswered by existing or new signals
- Log lines built by string interpolation instead of structured fields
- No correlation/request ID — each log line is an orphan
- Metrics labeled with user IDs, raw URLs, or error message text (cardinality bomb)
- Latency tracked as an average with no percentiles
- Alerts that fire daily and get acknowledged without action
- Alerts on causes (CPU, memory) paging humans while user-facing error rate is unmonitored
- Secrets, tokens, or full request bodies appearing in logs
- "It works on my machine" as the only evidence a production feature is healthy

## Verification

After observability work, confirm only the signals applicable to the defined operational questions and changed surface. Record actual signal observations separately from static configuration checks; reuse valid evidence and leave provider, live-notification, or fault-injection checks pending when they were not authorized or available.

- [ ] The on-call questions for this feature are written down, and each signal maps to one
- [ ] Applicable log output is structured, uses stable event names, and carries a bounded correlation ID where correlation is needed
- [ ] Logged fields follow an explicit allowlist; sampled output contains no secrets, tokens, or unapproved sensitive data
- [ ] Applicable RED/USE metrics use bounded label sets; latency uses a histogram with the required percentiles queryable
- [ ] Applicable traces preserve required context across the affected path with useful, allowlisted span attributes
- [ ] New alert designs are symptom-based, actionable, justified, and linked to a runbook
- [ ] Actual logs, metrics, traces, or alert test results were inspected where available; unperformed live checks are reported as pending rather than passed

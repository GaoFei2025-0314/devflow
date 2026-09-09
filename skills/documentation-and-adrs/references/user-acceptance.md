# User-executable acceptance

Use this reference when a delivery includes behavior that a user or stakeholder must judge. The acceptance material is part of the deliverable: it must let its intended reader evaluate the current artifact without reconstructing earlier conversation, reading an internal task plan, or guessing what a test command was meant to prove.

A document-only request can be complete when the requested document is reviewable. Do not imply that software was implemented or exercised unless evidence for that separate claim exists.

## Build the acceptance brief from the actual delivery

Replace every prompt below with current facts. Remove irrelevant fields instead of leaving ceremonial headings, but keep unavailable, placeholder, deferred, and demonstration-only scope visible.

```markdown
# Acceptance: <feature or delivery name>

## Artifact and status
- Artifact: <file, package, application, URL, build, or other exact object>
- Version/revision: <version, commit, build ID, date, or another stable identifier>
- Delivery status: <document ready | implementation complete | automated checks passed | human acceptance pending | specific authorization pending | final delivery>
- Completed scope: <behaviors and artifacts included in this delivery>

## Environment and prerequisites
- Environment: <local/test/staging/production, operating system, browser/device, account or dataset>
- Prerequisites: <setup, permissions, seed data, feature flags, or none>
- Safety boundary: <actions that must not be performed during acceptance without separate authorization>

## Entry
- Start at: <screen, route, command, file, menu, or API entrypoint>
- Test identity/data: <safe account, fixture, sample input, or none>

## Acceptance scenarios
| # | Action | Expected result | Failure or exception result | Evidence/decision |
|---|---|---|---|---|
| 1 | <one observable user action> | <visible or otherwise observable behavior> | <specific symptom that means the scenario did not pass> | <pending, accepted by whom/when, or evidence locator> |

## Evidence already available
- Engineering checks: <check, artifact/revision, result, behavior or risk covered, and material limit>
- Observed visual/interaction evidence: <environment, interaction or comparison observed, evidence locator, and limit; or not collected>
- Required human acceptance: <scenario numbers and the judgment still needed; or accepted by whom/when>

## Unavailable, placeholder, or deferred scope
- <item>: <unavailable | placeholder | deferred | demonstration-only> because <reason>. <What can be evaluated now and what event or decision would make the remainder available.>

## Protected or consequential actions
- <exact paid, external-send, destructive, production, permission, or sensitive action>: <authorization status and condition>.
- Safe substitute: <local preview, test recipient, sandbox transaction, disposable fixture, dry run, read-only inspection, or prepared payload>.

## Report the decision
For each scenario, record: <accepted | failed | pending | deferred with accepting source and reason | unavailable>, the artifact/version, environment, observer, date/time, and evidence or concise notes. Record engineering-check status, human acceptance, and action authorization separately.
```

Short field examples:

- **Artifact/version:** `Settings panel, build 2.4.0-rc.3 (commit 8ac421d)`, not “the latest build.”
- **Environment/prerequisites:** `Chrome 131 on staging; sign in as a workspace editor; use fixture project ACCEPT-07.`
- **Entry:** `Workspace settings > Notifications`, not “open the app.”
- **Action and expected result:** `Turn Weekly summary off and reload; the switch remains off and no success banner repeats.`
- **Failure condition:** `The switch returns to on, an error appears, or a second save request is visible.`
- **Unavailable scope:** `Real email delivery is pending provider credentials; the generated preview can be accepted now.`
- **Safe substitute:** `Review the prepared invoice in sandbox mode; do not confirm a live charge.`

Phrase the brief for the reader's technical level. Prefer user-visible actions and results for a product stakeholder. Include a command or diagnostic detail only when that reader is expected to run it, and explain what a successful or failed result means.

## Keep evidence and decisions distinct

Acceptance has three evidence classes. Report each independently:

1. **Automated engineering checks** cover properties such as compilation, types, unit behavior, references, build output, or a controlled end-to-end path. Explain each major check by the behavior or risk it addresses and why that scope fits this change. A command name or test count alone is not an explanation.
2. **Observed visual or interaction evidence** records what was actually viewed or exercised in a named browser, device, or comparable environment. Identify the artifact, route or flow, viewport/device where relevant, and the screenshot, recording, comparison, or observation. A functional test does not establish layout, color, motion, clarity, or aesthetic satisfaction.
3. **Required human acceptance** records the named user's or stakeholder's judgment against the supplied scenarios and criteria. Automated or observed evidence can prepare this decision but cannot manufacture it.

Do not upgrade one class into another. If no real browser or device observation occurred, say `not collected` and keep any required visual or interaction acceptance pending. If a check is format-only or controlled, preserve that limit rather than calling it native behavior.

When feedback concerns layout, color, motion, clarity, or interaction quality, name the exact screen and experience criterion. Apply the project's existing design system where it fits, prepare before/after material, and obtain real visual or interaction evidence when required. Report functional correctness and experience acceptance separately; passing functionality does not settle taste or usability.

## Explain checks by behavior and risk

In the final explanation, group routine successful checks and say what their result establishes. For example:

```markdown
- The type check passed for the settings change, which catches mismatched component props and invalid persisted-state shapes before runtime.
- The focused save-and-reload scenario passed against build 2.4.0-rc.3, covering the risk that the preference appears saved but is lost on reload.
- The responsive comparison was observed at 390 px and 1440 px; no clipping was seen. Color preference remains a human acceptance item.
```

If the user later asks what a command did or why it ran, answer from the existing evidence in these terms. An explanation request does not require rerunning the command. Ordinary progress updates should mention relevant decisions, discoveries, failures, or changed risk without dumping every internal checklist item.

## Use safe substitutes at action boundaries

Do not treat an acceptance template as permission to spend money, send externally, delete data, change production, alter permissions, expose sensitive information, or perform another protected action. Before any such step, identify the exact action, target and environment, scope, authorization source, conditions, and current validity under the applicable project and host policy.

Unless exact execution is already authorized, prepare an independently usable substitute that exercises the behavior up to the boundary. Prefer a sandbox or test account, local preview, test recipient controlled by the user, disposable fixture, dry run, read-only inspection, or a prepared payload awaiting approval. State what the substitute proves and what remains unverified. Ask for authorization only when the prepared acceptance reaches the protected action itself.

## Deliver a self-contained final explanation

The final delivery explanation must include:

- the exact artifact/version and environment;
- completed scope and the user's entrypoint;
- the acceptance steps or a direct link to the independently usable brief;
- major engineering checks explained by covered behavior or risk;
- observed visual/interaction evidence, clearly labeled, or its absence;
- required human acceptance and its current status;
- failures, placeholders, unavailable or demonstration-only scope, and accepted deferrals with reasons; and
- any concrete protected action awaiting authorization.

Use status language that matches the current artifact. `Automated checks passed` and `human acceptance pending` can both be true. A placeholder remains a placeholder, an accepted deferral remains recorded as deferred, and a document-ready result does not imply an implementation exists.

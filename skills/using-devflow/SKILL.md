---
name: using-devflow
description: Explains how to find, invoke, and prioritize the Devflow skills, including platform tool mappings for non-Claude-Code hosts and the shared no-subagent fallback contract. Use at session start when this bundle is loaded, or whenever unsure which skill applies or how skills are invoked on your platform.
---

<SUBAGENT-STOP>
If you were dispatched as a subagent for a specific task, do not reroute it or load unrelated skills. The [core rules](references/core-rules.md) and [action rules](references/action-rules.md) still bound your scope, authorization, evidence, and completion; reuse them if their complete text is already in your context, otherwise read them.
</SUBAGENT-STOP>

# Using Devflow

**Load a skill when the task matches its purpose**; a question or a small, clear change usually needs none. Checking descriptions is cheap, loading is the cost to ration, so load the smallest useful set and follow the [router](../devflow/SKILL.md). When a skill you follow has a checklist, track each item so none is silently skipped.

The shared rules live in two files: the [core rules](references/core-rules.md) apply on every route, and the [action rules](references/action-rules.md) apply before changing anything, running checks, or delivering. A request states what to do, not how; "add X" or "fix Y" does not skip the workflow.

## How to access skills

- **Claude Code:** installed as a plugin, skills appear as `devflow:<name>`; invoke them with the `Skill` tool. Installed as a skill folder, only the bundle entrypoint is registered; open the referenced `SKILL.md` files with the Read tool and follow them.
- **Codex, Copilot CLI, and Gemini CLI:** use a skill-loading mechanism only when the current host exposes it, with its current parameter schema. The [Codex](references/codex-tools.md), [Copilot CLI](references/copilot-tools.md), and [Gemini CLI](references/gemini-tools.md) pages are purpose hints, not API promises.
- **Other environments:** read each referenced `SKILL.md` and follow it as ordinary instructions.

Choose tools from what the host actually exposes; the [host capability guide](references/host-contract.md) covers path bases, browser fallbacks, and support labels. Choose project commands from the project's own conventions; see [project command selection](references/project-commands.md) when signals conflict.

### No-Subagent Fallback Contract

Delegate only when the conditions in the [action rules](references/action-rules.md#host-capabilities) hold; a dispatch tool merely existing is not enough. On a host without suitable subagent support, or when delegation is disallowed or unsafe:

1. **Plan execution:** use `../executing-plans/SKILL.md` instead of subagent-driven-development.
2. **Parallel investigations:** work the same scoped domains sequentially in-session, keeping each scope exactly as the skill defines it.
3. **Review dispatch:** fill the review prompt template yourself and work through it as a self-review checklist in a fresh pass over the diff. Do not call that result an independent review.

Skills reference this fallback rather than restating it.

## Skill priority

Process skills come first because they decide how to approach the task: "let's build X" starts with brainstorming, and "fix this bug" starts with systematic-debugging. Implementation and domain skills follow. Rigid skills such as test-driven-development and systematic-debugging are followed exactly; pattern skills are adapted to context; each skill says which it is.

## Project adaptation and recording

To adapt Devflow to a project, copy the relevant fenced content of the [project overrides template](references/project-overrides.md) into the project's `CLAUDE.md`, `AGENTS.md`, or equivalent and fill it in; the copy is self-contained. Usage recording is off by default; only after the user opts in to a named store, follow [local recording](references/local-recording.md).

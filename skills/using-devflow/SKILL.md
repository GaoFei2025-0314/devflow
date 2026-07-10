---
name: using-devflow
description: Explains how to find, invoke, and prioritize the Devflow skills, including platform tool mappings for non-Claude-Code hosts and the shared no-subagent fallback contract. Use at session start when this bundle is loaded, or whenever unsure which skill applies or how skills are invoked on your platform.
---

<SUBAGENT-STOP>
If you were dispatched as a subagent to execute a specific task, skip this skill.
</SUBAGENT-STOP>

# Using Devflow

## The Rule

**Check for a matching skill BEFORE responding or acting.** If a skill plausibly applies to the task, read it and follow it — knowing the concept is not the same as following the skill, and skills evolve, so read the current version rather than working from memory.

Balance this against the router's Core Rule: load the **smallest useful subset** for the phase you are in. "Check before acting" governs *when* you look for a skill; "smallest useful subset" governs *how many* you load. Checking is cheap (descriptions only); loading full skills is the cost to ration.

Three specific moments where the check is most often skipped:

- **Before asking clarifying questions or exploring the codebase.** The skill check comes first — brainstorming and spec skills define their own question-asking process, and ad hoc questions commit you to an unguided path.
- **Before entering plan mode.** If requirements are not yet shaped, run the brainstorming skill first; don't write a plan from an unclarified request.
- **When a skill you're following has a checklist,** track each item as a todo so nothing gets silently skipped in a long session.

## Instruction Priority

Devflow skills override default system prompt behavior, but **user instructions always take precedence**:

1. **User's explicit instructions** (CLAUDE.md, GEMINI.md, AGENTS.md, direct requests) — highest priority
2. **Devflow skills** — override default system behavior where they conflict
3. **Default system prompt** — lowest priority

If the user's project instructions say "don't use TDD" and a skill says "always use TDD," follow the user's instructions. The user is in control.

A ready-made override template (stack commands, skills to ignore, fast-path threshold, project-specific exceptions) lives at `../../templates/project-overrides.md` — copy it into the project's CLAUDE.md or AGENTS.md and fill it in.

## How to Access Skills

**In Claude Code:** Installed as a plugin, skills appear as `devflow:<name>` — invoke them with the `Skill` tool and follow the loaded content directly. Installed as a skill folder instead, only the bundle entrypoint is registered; open the referenced `SKILL.md` files with the Read tool and follow them as instructions.

**In Codex:** Skills load natively from `.codex/skills/`, or via the repository's `AGENTS.md`; follow the loaded instructions directly.

**In Copilot CLI:** Use the `skill` tool. **In Gemini CLI:** Skills activate via `activate_skill`.

**In other environments:** Treat each referenced `SKILL.md` as ordinary instructions: read the file, follow it.

## Platform Adaptation

Skills use Claude Code tool names. On other platforms, see the mapping for your host: `references/codex-tools.md` (Codex), `references/copilot-tools.md` (Copilot CLI), `references/gemini-tools.md` (Gemini CLI). Hosts not listed: substitute your native file, shell, and subagent tools.

### No-Subagent Fallback Contract

Some skills dispatch subagents (subagent-driven-development, dispatching-parallel-agents, requesting-code-review). On a host without subagent support, apply this single contract:

1. **Plan execution:** use `../executing-plans/SKILL.md` instead of subagent-driven-development.
2. **Parallel investigations:** work the same scoped problem domains sequentially in-session, keeping each investigation's scope exactly as the skill defines it.
3. **Review dispatch:** fill the review prompt template yourself and work through it as a self-review checklist in a fresh pass over the diff.

Skills reference this contract rather than restating it.

## Skill Priority

When multiple skills could apply, use this order:

1. **Process skills first** (brainstorming, systematic-debugging) — these determine HOW to approach the task
2. **Implementation skills second** (frontend-design, frontend-ui-engineering, api-and-interface-design) — these guide execution

"Let's build X" → brainstorming first, then implementation skills.
"Fix this bug" → systematic-debugging first, then domain-specific skills.

## Skill Types

**Rigid** (test-driven-development, systematic-debugging): Follow exactly. Don't adapt away discipline.

**Flexible** (patterns): Adapt principles to context.

The skill itself tells you which.

## Common Rationalizations

| Thought | Reality |
|---------|---------|
| "This is just a simple question" | Questions are tasks. Check for skills. |
| "The skill is overkill" | Simple things become complex. If it matches, use it. |
| "I remember this skill" | Skills evolve. Read the current version. |
| "I'll just do this one thing first" | Check BEFORE doing anything. |
| "This doesn't need a formal skill" | If a matching skill exists, use it. |

## User Instructions

Instructions say WHAT, not HOW. "Add X" or "Fix Y" doesn't mean skip workflows.

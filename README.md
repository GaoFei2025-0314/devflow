# Codex Devflow Skill

Devflow is a Codex skill that routes AI-assisted software development work to the smallest useful workflow stack.

It helps decide when to use:

- Superpowers for process discipline
- OpenSpec for persistent change artifacts
- Agent Skills for engineering lifecycle work
- GStack for targeted expert review or QA

## Files

- `SKILL.md` - the skill instructions
- `agents/openai.yaml` - Codex app metadata for displaying and invoking the skill

## Install

Copy this directory into your Codex skills directory:

```powershell
Copy-Item -Recurse -Force . "$env:USERPROFILE\.codex\skills\devflow"
```

Then restart or refresh Codex so the skill is discovered.

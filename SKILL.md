---
name: devflow
description: Entrypoint shim for hosts that load this repository as a single skill folder. Loads the Devflow router, which coordinates AI-assisted software development by selecting the smallest useful workflow stack from the skills under skills/.
---

# Devflow

This is the entrypoint shim for hosts that load this repository as a single skill folder. (Plugin installs load `skills/devflow/` directly and never read this file.)

Read `skills/devflow/SKILL.md` — the Devflow router — and follow it. It selects the smallest useful subset of the skills under `skills/` for the current phase of work.

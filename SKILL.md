---
name: devflow
description: Entrypoint shim for the canonical Devflow router, which selects work by deliverable and phase, impact and risk, domain, and capabilities available on the host.
---

# Devflow

This is the entrypoint shim for hosts that load this repository as a single skill folder. Plugin installs load `skills/devflow/` directly.

Read and follow `skills/devflow/SKILL.md`, the canonical router. It identifies the requested deliverable and legal phase endpoint, then selects the smallest useful stack from impact and risk, needed domain guidance, and capabilities the host can actually execute. Its canonical phase, authorization, evidence, and delivery references govern every route.

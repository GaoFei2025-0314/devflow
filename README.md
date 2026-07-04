# Devflow

Devflow is a universal AI development workflow skill package. It is not tied to one app or runtime. Use it in any AI coding assistant that can load Markdown instructions, read a local folder, or import a skill directory.

Devflow is intentionally packaged as a complete bundle:

- `SKILL.md` is the entrypoint.
- `skills/agent-skills/` contains engineering lifecycle skills.
- `skills/superpowers/` contains discipline and execution workflows.
- `skills/openspec/` contains a portable OpenSpec-style workflow.
- `agents/openai.yaml` is an optional adapter metadata file for tools that understand that format.

## What It Does

Devflow routes software development work to the smallest useful workflow stack:

- Requirements and idea shaping
- Specs and task plans
- Test-first implementation
- Debugging and root-cause analysis
- Code review and refactoring
- Frontend, API, security, performance, and observability work
- CI, release, and shipping workflows

The package includes the referenced workflow files, so another user does not need to already have those skills installed separately.

## Install

Clone or download this repository and keep the folder intact:

```bash
git clone https://github.com/GaoFei2025-0314/devflow.git
```

Then point your AI tool's skill, prompt, rules, or instruction loader at the repository folder, with `SKILL.md` as the entrypoint.

If your tool supports skill folders, install the whole `devflow` directory as one skill. If your tool only supports plain instruction files, load `SKILL.md` first and let it reference the bundled files under `skills/`.

## Usage

Ask the assistant to use Devflow before a development task:

```text
Use devflow to plan and implement this feature.
```

Devflow will choose the relevant bundled files. For example:

- New feature: brainstorming, spec, planning, TDD, incremental implementation, review
- Bug: systematic debugging, regression test, minimal fix, verification
- UI work: frontend design and UI engineering, browser testing when useful
- Shipping: git workflow, CI/CD, launch checklist, verification

## Package Layout

```text
devflow/
  SKILL.md
  README.md
  MANIFEST.md
  agents/
    openai.yaml
  skills/
    agent-skills/
    openspec/
    superpowers/
```

See `MANIFEST.md` for the full bundled component list.

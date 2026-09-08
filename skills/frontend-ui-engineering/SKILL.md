---
name: frontend-ui-engineering
description: Builds production-quality UI code — components, layouts, state management, accessibility, responsive behavior, and verifiable interactions.
---

# Frontend UI Engineering

## Overview

Build production-quality user interfaces that are accessible, performant, responsive, and consistent with the product's chosen visual direction. Use the project's design system, established components, tokens, conventions, and user-approved direction before introducing new patterns.

Worked code examples are in `references/examples.md`; they are illustrative rather than project commands or mandatory framework choices. Pair this skill with `../frontend-design/SKILL.md` when visual direction matters and `../browser-testing-with-devtools/SKILL.md` when runtime browser evidence is applicable. Apply the shared phase, authorization, evidence, delivery, host-capability, and project-command contracts through `../using-devflow/SKILL.md`.

## When to Use

- Building or changing UI components and pages
- Implementing responsive layouts and interaction states
- Adding client state or data-driven presentation
- Fixing visual, interaction, or accessibility issues

## Component Architecture

Follow the project's existing structure first. When no convention exists, colocate the implementation with its focused tests, stories, hooks, and types where that improves ownership. Treat size as a signal rather than a fixed limit: split a component when it has multiple responsibilities, difficult state coordination, or parts that need independent reuse or testing.

- Prefer composition when it makes content and behavior easier to combine.
- Keep component responsibilities clear.
- Separate data acquisition and mutation from presentation when that boundary improves loading, error, empty, and retry behavior.
- Preserve public component contracts unless the task explicitly changes them and the wider impact is understood.

## State Management

Choose the smallest approach consistent with project conventions and actual sharing needs:

```
Local state                 → Component-specific UI state
Lifted state                → State shared by nearby components
Context                     → Cross-tree values with a stable ownership boundary
URL state                   → Shareable navigation, filters, or pagination
Server-state abstraction    → Remote data, caching, synchronization, retries
Global store                → Complex client state shared across distant features
```

Avoid passing state through unrelated layers. Restructure or introduce the project's existing state abstraction when ownership becomes unclear. Handle concurrency, stale responses, failed optimistic updates, and disabled or pending actions when the flow can encounter them.

## Design System Adherence

- Reuse project components and semantic design tokens for spacing, typography, color, borders, elevation, and motion.
- Preserve the selected information hierarchy and visual language. Do not replace a user's chosen direction with a generic style preference.
- Use real or representative content to exercise wrapping, overflow, localization, long labels, and empty states.
- Introduce a new token or pattern only when the existing system cannot express the requirement; document the rationale and its intended reuse when material.
- For a small presentation change, keep validation and edits local to the affected surface unless evidence shows a broader regression risk.

## Accessibility

Meet the project's applicable accessibility target and check the affected user flow. WCAG 2.1 AA is a useful baseline when the project has not established a newer or stricter target.

- Use native semantic elements and keyboard behavior wherever possible.
- Give controls accessible names and associate inputs with labels and errors.
- Keep focus visible and logical; manage focus for dialogs, route changes, inserted content, and error recovery when applicable.
- Do not rely on color, position, sound, or motion alone to communicate state.
- Provide meaningful loading, empty, error, and success states with an available next action.
- Respect zoom, text resizing, reduced motion, and assistive technology semantics relevant to the changed UI.

Automated accessibility audits catch only part of the problem. Use manual keyboard and assistive-technology or accessibility-tree checks when the changed behavior makes them relevant and the host exposes suitable capability.

## Responsive Layout

Start from the smallest relevant layout and expand deliberately. Derive test widths from project breakpoints, supported devices, content stress points, and the changed layout. Do not treat a fixed list of viewport widths as universally required. Include boundary widths around affected breakpoints and test zoom or text expansion when those can change the flow.

Check the relevant states, including navigation, dense and sparse content, overlays, forms, tables, loading, errors, and long text. Confirm that focus, hit targets, reading order, and essential actions remain usable rather than checking screenshots alone.

## Loading and Transitions

Choose feedback that fits the operation and design system. Skeletons can help stable content regions; progress indicators or status text may be better when shape is unknown. Mark busy regions appropriately without hiding existing useful content.

Use optimistic updates only when the action is safe to predict and a clear rollback or reconciliation path exists. Motion should explain state changes, honor reduced-motion settings, and avoid delaying essential interaction.

## Verification and Acceptance

Select checks from the changed behavior, dependency boundaries, risk, and mandatory project gates under the shared evidence and project-command contracts. State what each major check protects:

- build and type checks for compilation, integration, and contract risks;
- focused component or regression checks for the affected state and behavior;
- browser interaction checks for routing, focus, input, state transitions, console or network behavior;
- responsive and visual checks for layout, hierarchy, content fit, and design-system consistency;
- accessibility checks for semantics, names, focus order, keyboard operation, contrast, announcements, zoom, and motion as applicable;
- broader regression checks when the change crosses shared components, public contracts, dependencies, build configuration, security boundaries, or release gates.

Use the smallest set that covers the identified risks without dropping mandatory project checks. A documentation-only change uses relevant content and reference checks; an illustrative example does not establish a package manager, test runner, or command for the current project.

Record separately:

1. **Function and engineering result:** checks that ran, object and state checked, results, and coverage limits.
2. **Observed visual result:** browser or device, route and state, relevant viewports, interactions, accessibility observations, and screenshots or comparisons actually collected.
3. **User satisfaction:** accepted direction and any explicit user or stakeholder judgment; leave this pending until that judgment occurs when it is required.

For manual acceptance, provide instructions appropriate to the user's technical level and include the exact version or artifact, environment and prerequisites, entry route, numbered actions, expected result for each action, failure conditions, and any placeholder or unavailable scope. Flag paid, outward-facing, destructive, or otherwise protected steps before execution and apply the authorization contract. Automated checks do not replace these user steps.

If no suitable browser or device interface is callable, run the authorized non-browser checks, record what they prove, and list the missing layout, interaction, visual, accessibility, console, network, or device evidence. Required missing evidence keeps the corresponding acceptance or delivery gate pending; it is not converted into a pass.

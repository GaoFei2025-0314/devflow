---
name: frontend-design
description: Create distinctive, production-grade frontend interfaces with high design quality while respecting the project's design system and the user's chosen direction.
license: Complete terms in LICENSE.txt
---

# Frontend Design

Create polished interfaces whose visual decisions fit the product, audience, and existing system. Design quality comes from a coherent direction and careful execution, not from novelty for its own sake.

Pair this skill with `../frontend-ui-engineering/SKILL.md` for implementation quality and with `../browser-testing-with-devtools/SKILL.md` for applicable runtime visual and interaction evidence. Apply the shared phase, authorization, evidence, delivery, host-capability, and project-command contracts through `../using-devflow/SKILL.md`.

## Establish the Direction

Before coding, identify:

- **Purpose and audience:** the task users need to complete, their context, and the content hierarchy that supports it.
- **Existing direction:** the project's design system, tokens, components, brand rules, prior accepted screens, and any direction the user has already selected.
- **Change scope:** the affected component, flow, viewport range, and interaction states. A small presentation change does not require redesigning the surrounding product.
- **Constraints:** framework, performance, accessibility, content, localization, and project gates.
- **Acceptance target:** the layout, tone, behavior, and comparison material needed for someone to judge the result.

For an existing product, follow its applicable design system and the user's chosen direction. Resolve local inconsistencies within that language. Do not replace the palette, typography, component vocabulary, or overall style merely to make the result more distinctive.

For a new interface or a major visual change without an accepted direction, make the consequential choices explicit before implementation: visual tone, key layout, content hierarchy, interaction model, and representative references or sketches. Offer a small set of context-appropriate options when the user needs to choose. Once a direction is selected, execute it consistently rather than reopening it during implementation.

## Visual Craft

Use these principles within the established direction:

- **Typography:** preserve the project's type scale and font choices. In a new system, choose readable, characterful typography that fits the product and content; define a clear hierarchy and test realistic lengths.
- **Color and theme:** use existing semantic tokens. In a new system, define a cohesive palette with sufficient contrast and clear roles for surface, text, border, status, and accent colors.
- **Spatial composition:** make information priority easy to scan. Use the established spacing and grid; introduce asymmetry, overlap, density, or generous space only when it serves the content and remains robust across relevant viewports.
- **Motion:** use motion to explain state, continuity, or feedback. Respect reduced-motion preferences, keep controls usable without animation, and avoid adding a library solely because an example names one.
- **Surfaces and detail:** use texture, gradients, shadows, borders, illustration, or decorative effects when they support the chosen direction and do not compete with content, accessibility, or performance.
- **Content:** use representative content and states. Placeholder copy can hide wrapping, hierarchy, overflow, localization, and empty-state problems.

Avoid unconsidered defaults such as a fashionable palette applied to every product, uniform card grids that ignore hierarchy, arbitrary radii or shadows, and decorative motion without a purpose. A familiar pattern is acceptable when it fits the design system and helps the user.

Match implementation complexity to the approved result. Expressive concepts may require richer layout and motion; restrained concepts require precise typography, spacing, alignment, and states. Do not expand dependencies or architecture solely to achieve an aesthetic effect without applying the project's command, authorization, and delivery rules.

## Visual Acceptance

Define visual acceptance in observable terms for the changed scope: hierarchy and alignment, content fit, relevant responsive states, interaction feedback, focus and error presentation, contrast, motion behavior, and consistency with the design system. Compare against the approved direction, reference, or prior state when one exists.

Keep three conclusions separate:

1. **Function and engineering:** the implemented behavior and applicable automated checks.
2. **Observed visual result:** what was actually inspected in a callable browser or device, at the recorded states and viewports, with screenshots or other comparison evidence when useful.
3. **User satisfaction:** the user's or stakeholder's judgment of layout, color, tone, and overall experience.

Passing functional checks does not establish visual quality or user satisfaction. If a user dislikes a functionally correct result, identify the specific screen, state, and feedback; translate that feedback into observable experience criteria; revise within the applicable design system and selected direction; then repeat the relevant visual and interaction checks. Do not force a new style or characterize aesthetic feedback as a functional defect.

When browser or device evidence is unavailable, report the exact visual and interaction gap and keep any required experience acceptance pending. Never invent a screenshot, observation, or user approval.

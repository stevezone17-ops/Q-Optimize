# UI/UX Guidelines

## Product personality
A premium scientific SaaS product: precise, calm, technical, approachable, and trustworthy—not a generic AI dashboard.

## Visual direction
- Dark-first midnight/charcoal surfaces.
- Restrained violet and electric-blue accents.
- Subtle gold highlights.
- High-contrast accessible text.
- Consistent typography, spacing, and component radii.
- Avoid excessive glow, gradients, glass effects, and decorative motion.

## Navigation
Overview, Problem Builder, Formulation Studio, Quantum Lab, Classical Lab, Comparison Lab, My Experiments, Learn, Settings.

## Screen requirements
- **Dashboard:** recent experiments, quick-start templates, real job status; honest empty state.
- **Problem Builder:** template and natural-language input; extracted variables, objective, constraints, units, assumptions, missing data; confirmation.
- **Formulation Studio:** objective direction, variable mapping, QUBO, Ising terms, penalties, assumptions.
- **Quantum Lab:** QAOA depth, shots, optimizer, initialization, budget, backend, optional noise; show circuits only when generated.
- **Classical Lab:** algorithm-specific parameters, seed, stopping criteria.
- **Comparison Lab:** same-instance comparisons, metric definitions, execution context, warnings.
- **Experiment Details:** input snapshot, formulation, configuration, status, results, metadata.

## Interaction
Every visible control works or is clearly disabled. Include loading, empty, error, and success states. Confirm destructive actions. Preserve input on failure. Support keyboard navigation and reduced motion.

## Visualization
Label axes and units; use consistent scales; show sample counts; explain metric direction; never present placeholder data as real results. Provide textual summaries.

## Responsive design
Desktop-first for technical workspaces; support tablet/mobile for viewing experiments and simplified forms. Dense matrices may scroll or open in a dedicated view.

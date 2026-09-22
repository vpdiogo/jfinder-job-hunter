# Architecture

## Principle

Use AI where interpretation and generation are valuable, but keep workflow
state and business rules deterministic.

### AI workers

- Job evaluator
- Career/materials agent
- Interview preparation agent

### Deterministic components

- Collectors
- Persistence
- State transitions
- Validation
- Scheduling
- Retries
- Human approval

This separation makes the system easier to test, observe, and control.

## Current evaluation baseline

`JobEvaluator` uses deterministic and explainable rules before any LLM
integration. It compares a job's explicit `required_skills` with the profile's
skills, adds a bonus for target-title matches, and returns a score,
recommendation, matched skills, and missing requirements. If the posting lacks
reliable skill requirements, it remains in `review` rather than being
automatically discarded or recommended.

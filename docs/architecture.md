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

## Enriched matching

When a job or profile provides the data, the evaluator also considers required
and desired technologies, seniority, work mode, location or timezone, salary
range, and languages. Each evaluated criterion is returned as a reason. A
criterion supplied by only one side is reported as insufficient information and
is excluded from the score rather than treated as a mismatch.

Existing jobs and profiles remain compatible: when none of the enriched fields
are available, the original skill-and-title scoring rules are used unchanged.

## Resume ingestion

The first ingestion version accepts plain text. It deterministically extracts
skills, target roles, languages, experience entries, and education from common
Portuguese and English section headings. The original text and extracted draft
are persisted before any profile changes. A separate confirmation endpoint
receives the user-reviewed profile data and either creates a profile or updates
the explicitly selected one.

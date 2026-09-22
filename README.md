# JFinder — Job Hunter

Agentic job-hunting system focused on finding relevant roles, evaluating fit,
preparing tailored application materials, tracking applications, and preparing
for interviews.

## Architecture

```text
Job Collectors
      |
      v
Job Evaluator -----> SQLite
      |
      v
Application Queue
      |
      v
Career Agent ------> CV / application materials
      |
      v
Human approval
      |
      v
Application Manager -> status tracking
      |
      v
Interview Agent ----> recruiter + technical preparation
```

LLMs are responsible for interpretation and generation. Workflow state,
validation, persistence, retries, and transitions remain under application
code control.

## Initial stack

- Python 3.13+
- FastAPI
- SQLite
- SQLAlchemy 2.x
- Pydantic Settings
- pytest
- Ruff

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
uvicorn app.main:app --reload
```

Run tests:

```bash
pytest
```

## Roadmap

- [x] Repository and architecture scaffold
- [x] JSON job importer
- [x] Deterministic job evaluation pipeline
- [x] SQLite persistence
- [ ] CV/profile ingestion
- [ ] Tailored application material generation
- [ ] Human approval workflow
- [x] Application tracking
- [ ] Google Sheets synchronization
- [ ] Interview preparation generator
- [ ] Observability and scheduled execution

## Evaluate a job

Start the API with `uvicorn app.main:app --reload` and submit a job plus a
career profile:

```bash
curl -X POST http://127.0.0.1:8000/evaluations \
  -H 'Content-Type: application/json' \
  -d '{
    "job": {
      "title": "Senior Backend Engineer",
      "company": "Acme",
      "url": "https://example.com/jobs/1",
      "required_skills": ["Python", "FastAPI", "Kubernetes"]
    },
    "profile": {
      "skills": ["Python", "FastAPI"],
      "target_titles": ["Backend Engineer"]
    }
  }'
```

The response contains the score, recommendation, matched skills, and missing
requirements.

Evaluations are persisted in `jfinder.db` and can be retrieved with:

```bash
curl http://127.0.0.1:8000/evaluations
curl 'http://127.0.0.1:8000/evaluations?recommendation=review&min_score=70'
curl http://127.0.0.1:8000/evaluations/1
```

## Profiles

Create a profile once and reuse its `id` when evaluating jobs:

```bash
curl -X POST http://127.0.0.1:8000/profiles \
  -H 'Content-Type: application/json' \
  -d '{
    "skills": ["Python", "FastAPI", "SQLAlchemy"],
    "target_titles": ["Backend Engineer", "Platform Engineer"]
  }'
```

Use the returned `id` in a job evaluation:

```bash
curl -X POST http://127.0.0.1:8000/evaluations \
  -H 'Content-Type: application/json' \
  -d '{
    "job": {
      "title": "Senior Backend Engineer",
      "company": "Acme",
      "url": "https://example.com/jobs/2",
      "required_skills": ["Python", "FastAPI"]
    },
    "profile_id": 1
  }'
```

Profiles can be retrieved with `GET /profiles/{id}` and updated with
`PUT /profiles/{id}`. An evaluation accepts either `profile_id` or an inline
`profile`, but not both.

## Import jobs

Import one or more jobs as JSON. Repeated URLs are skipped to avoid duplicate
records:

```bash
curl -X POST http://127.0.0.1:8000/jobs/import \
  -H 'Content-Type: application/json' \
  -d '{
    "jobs": [
      {
        "title": "Backend Engineer",
        "company": "Acme",
        "url": "https://example.com/jobs/1",
        "required_skills": ["Python", "FastAPI"]
      }
    ]
  }'
```

List imported jobs with `GET /jobs`. To evaluate an imported job with a saved
profile, use:

```bash
curl -X POST http://127.0.0.1:8000/jobs/1/evaluate \
  -H 'Content-Type: application/json' \
  -d '{"profile_id": 1}'
```

## Job queue and application status

Imported jobs begin as `discovered`; evaluating them moves them to `evaluated`.
Use the queue to prioritize jobs by their latest score:

```bash
curl http://127.0.0.1:8000/jobs/queue
curl 'http://127.0.0.1:8000/jobs/queue?status=evaluated&min_score=70'
```

Move a suitable job through the application process:

```bash
curl -X POST http://127.0.0.1:8000/jobs/1/interest
curl -X POST http://127.0.0.1:8000/jobs/1/apply
curl -X POST http://127.0.0.1:8000/jobs/1/status \
  -H 'Content-Type: application/json' \
  -d '{"status": "recruiter"}'
```

Transitions are validated. For example, a job must be evaluated before it can
be marked as interesting, and it must be interesting before it can be applied
to.

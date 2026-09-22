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
- [ ] Job source collector interface
- [x] Deterministic job evaluation pipeline
- [x] SQLite persistence
- [ ] CV/profile ingestion
- [ ] Tailored application material generation
- [ ] Human approval workflow
- [ ] Application tracking
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

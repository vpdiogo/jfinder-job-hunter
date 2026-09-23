# AGENTS.md

## Project

JFinder is a job and application management system built with FastAPI, SQLite,
and React/Vite. The user interface and user-facing messages are written in
Portuguese; code identifiers, HTTP endpoints, and API error messages remain in
English.

## Stack and structure

- Python 3.13+, FastAPI, SQLAlchemy, Pydantic, and SQLite.
- React, TypeScript, and Vite in `frontend/`.
- Persistence in `app/repositories/`.
- Business rules in `app/services/`.
- HTTP routes and schemas in `app/api/`.
- Unit tests in `tests/unit/`.

SQLite schema changes must be additive and must preserve existing local
databases.

## Development workflow

1. Update `main` and create one branch per issue:
   - `feat/<name>`
   - `fix/<name>`
   - `chore/<name>`
2. Implement the change with tests proportional to its risk.
3. Do not alter, discard, or overwrite unrelated local changes.
4. Keep commits small and use Conventional Commits:
   - `feat: ...`
   - `fix: ...`
   - `chore: ...`
5. Push the branch and open a pull request. Do not merge without an explicit
   user request.

## Required quality checks

Before opening or updating a pull request, run:

```bash
python -m pytest
python -m ruff check .
npm run build --prefix frontend
npm run lint --prefix frontend
git diff --check
```

UI changes also require Chrome QA covering the affected end-to-end flow. Do not
stop development servers started by the user. Test records created during QA
must be clearly identifiable.

## Code review

Review pull requests for:

- Functional correctness and regressions.
- SQLite integrity and backward compatibility.
- API contracts and validation.
- Async state and error handling in the UI.
- Basic security and sensitive data exposure.
- Test coverage for new behavior and regressions.

Record blockers in the pull request with a reproducible case and a suggested
fix. After a fix, rerun the affected validations and update the pull request.

## Code conventions

- Prefer simple, typed, and testable code.
- Do not add dependencies or abstractions without a concrete need.
- Keep relevant data reviewable in the UI before meaningful user actions.
- Use additive SQLite migrations and handle legacy null data when adding fields.
- Do not commit SQLite databases, `.env` files, credentials, caches,
  `node_modules`, or build artifacts.

## Issue conventions

New issues must define an objective, scope, acceptance criteria, and known
dependencies.

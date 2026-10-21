# CLAUDE.md

## Project goals

A personal job application pipeline, built in stages:

1. **v1 (current): tracker.** Record applications, filter and search them, and show a dashboard with status counts and due follow-ups.
2. **Next: AI CV tailoring.** Use an application's stored job description to tailor a LaTeX CV, compile it to PDF, and record which CV was used.

The tracker stays useful on its own. AI features are optional add-ons and must never be required for the tracker to run.

## Stack

Python 3.11+, Streamlit (UI), SQLite through SQLAlchemy 2.x (ORM, typed `Mapped[...]` style), Pydantic v2 (validation and data contracts), pytest.

## Architecture rules

Layering: `ui/` → `repository.py` → `models.py`/`db.py`.

- **Only `repository.py` touches the database.** UI code and future modules never import SQLAlchemy or `jobpipe.models`.
- **Pydantic schemas are the contract.** Repository methods take and return `schemas.py` types (`ApplicationCreate`, `ApplicationUpdate`, `ApplicationRead`), never ORM objects.
- **Validation lives in `schemas.py`**, including cross-field rules. The repository re-validates the merged record on update, so rules apply however a change arrives.
- **`Status` is stored as plain text, not a DB enum.** Adding a status means editing the `Status` enum and, if relevant, `CLOSED_STATUSES`; no migration is needed.
- **Streamlit pages are `render()` functions** in `src/jobpipe/ui/`, registered in `app.py`. Shared widgets and the cached repository (`get_repo()`) live in `ui/components.py`.

## Adding future features (e.g. AI)

- Put each feature in its own package under `src/jobpipe/`, for example `jobpipe/ai/` (job description analysis, CV tailoring) and `jobpipe/latex/` (templates, compilation).
- Feature modules consume `ApplicationRead` and write back through the repository, for example `repo.update(id, ApplicationUpdate(cv_file=...))`.
- New tables get ORM models in `models.py` (or the feature's own `models.py`, imported in `db.init_db`) plus schemas and repository methods.
- Keep the UI thin: add a page module in `ui/` that calls the feature's functions. Business logic does not go in Streamlit code.
- Keep secrets such as API keys in environment variables. Never commit them.
- **Schema changes:** `init_db()` uses `create_all()`, which creates new tables but does **not** alter existing ones. Before the first change to an existing column, introduce Alembic.

## Conventions

- Run `pytest` before committing. Every new repository method gets tests in `tests/test_repository.py`, using the `repo` and `add` fixtures from `conftest.py`.
- Type hints on all functions. Use `X | None`, not `Optional[X]`.
- Dates are `datetime.date`. Timestamps are naive UTC (SQLite drops tzinfo).
- Dependencies are pinned in `requirements.txt`. The package is installed editable (`pip install -e .`).
- Keep comments sparse; explain *why*, not *what*.

## Commands

```bash
pip install -r requirements.txt && pip install -e .   # setup (inside .venv)
streamlit run app.py                                   # run app
pytest                                                 # run tests
JOBPIPE_DB_PATH=/tmp/scratch.db streamlit run app.py   # use a scratch DB
```

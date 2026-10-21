# Job Application Pipeline

A personal job application tracker built with Streamlit, SQLite, SQLAlchemy and Pydantic.

This is v1, the tracker only. Later versions will add AI-assisted CV tailoring with LaTeX.

## Features

- Add, edit and delete applications. Each one stores the company, role, posting URL, date applied, full job description, status, CV file used, notes and follow-up date.
- Applications table with a status filter and search by company or role. Select a row to edit or delete it.
- Dashboard with counts by status and a "needs follow-up" list. The list shows applications whose follow-up date is today or earlier, excluding any with status offer, rejected or ghosted.

Statuses: `saved`, `applied`, `interview`, `offer`, `rejected`, `ghosted`.

## Setup

Requires Python 3.11+.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

## Run

```bash
streamlit run app.py
```

The app opens at http://localhost:8501. The SQLite database is created automatically at `data/jobpipe.db`. To use a different file:

```bash
JOBPIPE_DB_PATH=/path/to/other.db streamlit run app.py
```

Back up your data by copying the `.db` file.

## Test

```bash
pytest
```

The tests cover the database layer (`tests/test_repository.py`) and validation (`tests/test_schemas.py`). Each test uses a fresh temporary database.

## Project layout

```
app.py                  Streamlit entry point (navigation only)
src/jobpipe/
  config.py             settings (DB path)
  db.py                 engine, sessions, init_db()
  models.py             SQLAlchemy ORM models
  schemas.py            Pydantic schemas + Status enum
  repository.py         all database access
  ui/                   Streamlit pages (dashboard, applications, add) + shared components
tests/                  pytest suite
data/                   SQLite database (gitignored)
```

See [CLAUDE.md](CLAUDE.md) for architecture rules and conventions.

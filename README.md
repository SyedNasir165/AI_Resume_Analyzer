# AI Resume Analyzer

Upload your resume, optionally add a target role and job description, and get a transparent,
evidence-based analysis: your strengths, your gaps, your ATS alignment, and the exact resume
lines that need work — with every suggestion you control.

> Scores are a heuristic estimate based on the resume and job description you provide. They do
> not guarantee ATS acceptance, interviews, or employment.

Full product spec: [`AI_Resume_Analyzer_MVP_and_Future_Features.txt`](AI_Resume_Analyzer_MVP_and_Future_Features.txt)
Process rules: [`ProjectWorkflow.txt`](ProjectWorkflow.txt) · Condensed instructions: [`CLAUDE.md`](CLAUDE.md)

## Status

**Phase 3 — Resume upload.** Complete so far:
- **Phase 1:** Project scaffolding — frontend/backend skeletons talking to each other via a health check.
- **Phase 2:** Authentication — Supabase-backed registration, login, logout, password reset, and a
  protected dashboard. The backend verifies Supabase-issued JWTs itself (via JWKS), independent of
  the frontend.
- **Phase 3:** Resume upload — PDF/DOCX/TXT file upload, drag-and-drop, and paste-text, with
  extraction, validation, a review-before-confirm step, a resume list on the dashboard, and delete.

No resume analysis yet — that's a later phase.

## Stack

| Layer         | Choice                                              |
|---------------|------------------------------------------------------|
| Frontend      | React + TypeScript + Vite + Tailwind CSS v4 + React Router |
| Backend       | Python + FastAPI                                    |
| Auth + DB     | Supabase (Postgres + Supabase Auth)                 |
| AI            | Google Gemini API (free-tier model)                 |

## Folder structure

```
AI_Resume_Analyzer/
├── CLAUDE.md
├── README.md
├── frontend/        React app
└── backend/         FastAPI app
```

## Getting started

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

API runs at `http://localhost:8000` (docs at `/docs`, health check at `/health`). `alembic upgrade
head` applies the database schema (profiles, resumes) to your Supabase Postgres — needed once
after setting `DATABASE_URL`, and again after pulling any new migration.

### Frontend

```bash
cd frontend
npm install
copy .env.example .env
npm run dev
```

App runs at `http://localhost:5175`.

### Environment variables

Copy each `.env.example` to `.env` in `backend/` and `frontend/`, then fill in your Supabase
project's URL, keys, and database connection string (see `.env.example` comments for where to
find each one in the Supabase dashboard, and the IPv6/session-pooler note for `DATABASE_URL`).
Gemini's key isn't required yet — that's a later phase.

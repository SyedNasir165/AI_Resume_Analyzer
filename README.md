# AI Resume Analyzer

Upload your resume, optionally add a target role and job description, and get a transparent,
evidence-based analysis: your strengths, your gaps, your ATS alignment, and the exact resume
lines that need work — with every suggestion you control.

> Scores are a heuristic estimate based on the resume and job description you provide. They do
> not guarantee ATS acceptance, interviews, or employment.

Full product spec: [`AI_Resume_Analyzer_MVP_and_Future_Features.txt`](AI_Resume_Analyzer_MVP_and_Future_Features.txt)
Process rules: [`ProjectWorkflow.txt`](ProjectWorkflow.txt) · Condensed instructions: [`CLAUDE.md`](CLAUDE.md)

## Status

**Phase 7 — Final validation & export.** Complete so far:
- **Phase 1:** Project scaffolding — frontend/backend skeletons talking to each other via a health check.
- **Phase 2:** Authentication — Supabase-backed registration, login, logout, password reset, and a
  protected dashboard. The backend verifies Supabase-issued JWTs itself (via JWKS), independent of
  the frontend.
- **Phase 3:** Resume upload — PDF/DOCX/TXT file upload, drag-and-drop, and paste-text, with
  extraction, validation, a review-before-confirm step, a resume list on the dashboard, and delete.
- **Phase 4:** General resume analysis — Gemini returns structured *observations only*, and
  application code computes a **deterministic Resume Quality Score** (0–100) across five categories.
- **Phase 5:** Job-specific analysis — paste a real job description (plus an optional target role);
  Gemini extracts the requirements and matches resume evidence, and application code computes the
  **deterministic ATS Alignment Score** (Keyword Coverage 25 / Requirement-Evidence Match 25 / ATS
  Parsing Safety 20 / Experience Strength 15 / Structure 10 / Language Quality 5). Results show the
  score, a job-fit summary (strong / partial / missing), a requirement-to-evidence table, important
  missing keywords, the category breakdown, and findings. As with general analysis, the AI never
  sets the score and never recommends adding a skill the resume doesn't support.
- **Phase 6:** AI Improvement Coach & tailored versions — for a weak bullet, the coach asks targeted
  questions and rewrites it using **only** real resume facts and the user's own answers (it never
  invents metrics), showing each claim's source (from resume / from your answer / needs
  confirmation). The user accepts, edits, or rejects each suggestion, then saves a **new tailored
  version** — the original is never modified. Analyzing a version shows a **before/after** score
  against its original.
- **Phase 7:** Final validation & export — before exporting, a deterministic check compares a
  tailored version against its original to confirm contact details and dates weren't dropped, flags
  any *new* figures to confirm, and catches duplicate bullets. The approved resume then exports to
  **plain-text** and **DOCX** (plain, ATS-friendly, text-extractable) — exports contain only the
  text the user has approved, nothing generated.

Both analyses are heuristic estimates, not guarantees of ATS acceptance or interviews. The core MVP
flow — sign up, upload, analyze (general or job-specific), improve with the coach, save a tailored
version, validate, and export — is now in place.

## Stack

| Layer         | Choice                                              |
|---------------|------------------------------------------------------|
| Frontend      | React + TypeScript + Vite + Tailwind CSS v4 + React Router |
| Backend       | Python + FastAPI                                    |
| Auth + DB     | Supabase (Postgres + Supabase Auth)                 |
| AI            | Google Gemini API (`gemini-3.6-flash`, free-tier)   |

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
A free Gemini API key (from [Google AI Studio](https://aistudio.google.com/apikey)) is now
required for the analysis feature — set `GEMINI_API_KEY` in `backend/.env`. If Gemini calls start
returning a 404 "model no longer available," pick a current `*-flash` model for `GEMINI_MODEL`.

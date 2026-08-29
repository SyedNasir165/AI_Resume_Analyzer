# AI Resume Analyzer

Upload your resume, optionally add a target role and job description, and get a transparent,
evidence-based analysis: your strengths, your gaps, your ATS alignment, and the exact resume
lines that need work — with every suggestion you control.

> Scores are a heuristic estimate based on the resume and job description you provide. They do
> not guarantee ATS acceptance, interviews, or employment.

Full product spec: [`AI_Resume_Analyzer_MVP_and_Future_Features.txt`](AI_Resume_Analyzer_MVP_and_Future_Features.txt)
Process rules: [`ProjectWorkflow.txt`](ProjectWorkflow.txt) · Condensed instructions: [`CLAUDE.md`](CLAUDE.md)

## Status

**Phase 1 — Project scaffolding.** Frontend and backend skeletons exist and can talk to each
other via a health check. No auth, upload, or analysis features yet.

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
uvicorn app.main:app --reload
```

API runs at `http://localhost:8000` (docs at `/docs`, health check at `/health`).

### Frontend

```bash
cd frontend
npm install
copy .env.example .env
npm run dev
```

App runs at `http://localhost:5175`.

### Environment variables

Copy each `.env.example` to `.env` in `backend/` and `frontend/`. Supabase and Gemini keys are
not required until later phases (auth and AI analysis) — Phase 1 runs without them.

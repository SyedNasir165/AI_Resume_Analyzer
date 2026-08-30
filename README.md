# AI Resume Analyzer

> Upload your resume, optionally add a target role and job description, and get a transparent,
> evidence-based analysis — your strengths, your gaps, your ATS alignment, and the exact lines that
> need work — with every suggestion you control.

A full-stack web application that gives job-seekers an **honest, explainable** read on their
resume. Unlike tools that hand an AI a resume and print whatever number it invents, this project
keeps the AI on a short leash: the model only ever returns **structured observations**, and the
**score is computed by deterministic application code**. The same resume and job description always
produce the same score, and no employer, date, metric, or skill is ever fabricated.

**Tech:** React · TypeScript · Vite · Tailwind CSS · FastAPI · Supabase (Postgres + Auth) · Google Gemini

---

## Table of contents

- [Core principles](#core-principles)
- [Features](#features)
- [How the scoring works](#how-the-scoring-works)
- [Tech stack](#tech-stack)
- [Architecture](#architecture)
- [Project structure](#project-structure)
- [Running locally](#running-locally)
- [Deployment](#deployment)
- [Security & privacy](#security--privacy)
- [Roadmap / future features](#roadmap--future-features)
- [Disclaimer](#disclaimer)

---

## Core principles

1. **Never fabricate.** The app never invents an employer, job title, date, skill, metric,
   certification, or achievement. Missing information is surfaced as a gap to confirm — never
   filled in by the AI.
2. **Deterministic, explainable scoring.** The LLM never sets the score. Application code computes
   it from validated observations, so it is reproducible and every point is explainable.
3. **You are in control.** Suggestions are drafts. You accept, edit, or reject each one, and your
   original resume is never overwritten.
4. **Private by default.** Your data is yours; you can delete any part of it, or your whole account,
   at any time.
5. **Honest about limits.** Scores are heuristic estimates, always framed as "strong alignment per
   this analyzer's model" — never as a guaranteed ATS pass.

## Features

| Area | What it does |
|------|--------------|
| **Authentication** | Email/password sign-up, login, logout, password reset, and protected routes. The backend verifies Supabase-issued JWTs itself via the project's JWKS endpoint. |
| **Resume upload** | PDF, DOCX, and TXT via file picker, drag-and-drop, or paste. Extraction with validation for empty, oversized, corrupt, or unsupported files, and a review-before-confirm step. |
| **General analysis** | A deterministic **Resume Quality Score** (0–100) across ATS Parsing Safety, Experience Strength, Structure & Completeness, Consistency, and Language Quality — with a Strong / Needs-improvement / Weak health check. |
| **Job-specific analysis** | Paste a real job description and get the deterministic **ATS Alignment Score** (Keyword Coverage 25 / Requirement-Evidence 25 / ATS Parsing Safety 20 / Experience Strength 15 / Structure 10 / Language Quality 5), plus a requirement-to-evidence table, keyword analysis, and a job-fit summary. |
| **Findings** | Each issue is tied to the exact resume line, with severity, why it matters, and a concrete suggestion that never invents facts. |
| **AI Improvement Coach** | For a weak bullet, the coach asks targeted questions and rewrites it using **only** your real facts and answers — showing each claim's source (from resume / from your answer / needs confirmation). |
| **Tailored versions** | Accepted edits create a new resume version; the original is never modified. Re-analyzing a version shows a **before → after** score. |
| **Fact-locking** | Employers, titles, dates, and education are never altered by the AI — only bullet wording is rewritten. |
| **Validation & export** | A pre-export check confirms nothing important was dropped and flags new figures to confirm. Export the resume as **TXT / DOCX / PDF**, and any analysis as a **PDF or text report**. |
| **Privacy & security** | Per-user rate limiting on AI endpoints, delete-analysis and delete-account (full data cascade), and a plain-language privacy notice. |

## How the scoring works

```
        Resume (+ optional Job Description)
                     │
                     ▼
     Google Gemini  ──►  structured OBSERVATIONS only
     (strict JSON schema; rejected if malformed;         (booleans, counts,
      never returns a score, never invents facts)         classifications, evidence)
                     │
                     ▼
     Deterministic scoring engine (application code)
     • fixed category weights   • pure function of the observations
     • same inputs → same score • every point explainable
                     │
                     ▼
          Score + category breakdown + findings
```

This split is the heart of the product: the AI is used for what it is good at (reading and
classifying text), and never for what it should not be trusted with (assigning a grade or asserting
facts).

## Tech stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, TypeScript, Vite, Tailwind CSS v4, React Router |
| Backend | Python, FastAPI, SQLAlchemy, Alembic, Pydantic |
| Auth & database | Supabase (managed PostgreSQL + Supabase Auth, JWKS/ES256 token verification) |
| AI | Google Gemini API (`gemini-3.6-flash`, free tier) |
| Document processing | pdfplumber, python-docx, fpdf2 |
| Testing | pytest (98 backend tests), ESLint, `tsc` type-checking |

## Architecture

- **Frontend** is a static single-page app. It talks to Supabase directly for auth, and to the
  FastAPI backend for everything else, attaching the Supabase access token as a bearer.
- **Backend** verifies that token on every protected request (no shared secret — it fetches
  Supabase's public keys), enforces per-user ownership on all data, and calls Gemini server-side so
  the API key is never exposed.
- **Database** is Supabase Postgres with Row Level Security enabled on every table as
  defense-in-depth, and foreign-key cascades so deleting a user removes all of their data.

## Project structure

```
AI_Resume_Analyzer/
├── frontend/            React + TypeScript + Vite + Tailwind
│   └── src/
│       ├── pages/       route-level screens
│       ├── components/  shared UI (navbar, coach panel, ui/ primitives)
│       ├── contexts/    auth context
│       └── lib/         API client + Supabase client
├── backend/             FastAPI
│   └── app/
│       ├── api/         routers (auth/me, resumes, analyses, coach, finalize)
│       ├── services/    Gemini client, deterministic scoring, extraction, export, validation
│       ├── models/      SQLAlchemy models
│       ├── schemas/     Pydantic schemas (incl. strict AI-output schemas)
│       └── core/        config, security (JWT), rate limiting
│   ├── alembic/         database migrations
│   └── tests/           pytest suite
├── DEPLOYMENT.md        step-by-step public deployment guide
└── README.md
```

## Running locally

**Prerequisites:** Node.js 20+, Python 3.10+, a free [Supabase](https://supabase.com) project, and a
free [Google Gemini API key](https://aistudio.google.com/apikey).

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1        # Windows (PowerShell); use source .venv/bin/activate on macOS/Linux
pip install -r requirements.txt
copy .env.example .env             # then fill in the values (see .env.example comments)
alembic upgrade head               # create the database schema in your Supabase project
uvicorn app.main:app --reload --port 8000
```

The API runs at `http://localhost:8000` (interactive docs at `/docs`, health check at `/health`).

> **`DATABASE_URL` tip:** use the Supabase **Session pooler** URI (Connect → Direct Connection →
> Session pooler), not the `db.<ref>.supabase.co` host — that one is IPv6-only and won't resolve on
> most networks. Percent-encode special characters in the password (e.g. `@` → `%40`).

### Frontend

```bash
cd frontend
npm install
copy .env.example .env             # set VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY, VITE_API_BASE_URL
npm run dev
```

The app runs at `http://localhost:5175`.

### Tests

```bash
cd backend && python -m pytest        # 98 tests
cd frontend && npm run lint && npm run build
```

## Deployment

The project is ready to deploy on free tiers — **Vercel** for the frontend, **Render** for the
backend, with Supabase and Gemini already cloud-hosted. See **[DEPLOYMENT.md](DEPLOYMENT.md)** for a
complete, click-by-click walkthrough.

## Security & privacy

- Uploaded resumes and job descriptions are treated as **untrusted input** — the AI is explicitly
  instructed to ignore any instructions embedded inside them (prompt-injection resistant).
- API keys and the Supabase service-role key live only in server-side environment variables and are
  never sent to the browser.
- Every table has Row Level Security; every endpoint checks ownership.
- Per-user rate limiting protects the AI endpoints from abuse and runaway cost.
- Users can delete any resume, version, or analysis, or their entire account (which cascades to all
  of their data). Resume text is never written to application logs.

## Roadmap / future features

The MVP is complete. Planned extensions (not yet built), each of which builds on the verified-resume
foundation already in place:

- **Cover letter generator** — job-specific letters using only verified resume facts.
- **Interview preparation** — role- and resume-specific technical and behavioral questions.
- **STAR answer builder** — turn confirmed experience into Situation/Task/Action/Result stories.
- **LinkedIn optimization** — headline and About suggestions (no automatic profile changes).
- **Job application tracker** — company, role, stage, and follow-up reminders.
- **Multiple-resume comparison** and **long-term analytics** (score trends, common weaknesses).
- **OCR / image resumes**, a **resume template system**, and **job-board integrations**.
- **Mobile apps** and **team / university / recruiter workspaces**.

## Disclaimer

Scores are a heuristic estimate based on the resume and job description you provide. They **do not
guarantee** ATS acceptance, interviews, or employment. All AI-generated suggestions should be
reviewed and verified before use.

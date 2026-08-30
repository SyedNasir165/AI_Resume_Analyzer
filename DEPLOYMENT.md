# Deploying AI Resume Analyzer

This guide deploys the app publicly on free tiers:

- **Backend (FastAPI)** → [Render](https://render.com)
- **Frontend (React/Vite)** → [Vercel](https://vercel.com)
- **Database + Auth** → Supabase (already cloud-hosted — the same project you used locally)
- **AI** → Google Gemini (already a cloud API)

You'll deploy the **backend first** (so you have its URL), then the **frontend**, then connect the
two and tell Supabase about the public domain.

> Free-tier notes: a Render free web service **spins down after ~15 minutes of inactivity**, so the
> first request after idle can take 30–60 seconds to wake. A free Supabase project **pauses after 7
> days of inactivity** — unpause it from the Supabase dashboard if needed.

---

## Prerequisites

- The repository is pushed to GitHub (it is: `SyedNasir165/AI_Resume_Analyzer`).
- You have your Supabase **Project URL**, **anon/publishable key**, **service-role (secret) key**,
  and the **Session-pooler `DATABASE_URL`** (with the password percent-encoded).
- You have your **Gemini API key**.
- The database schema is already created (you ran `alembic upgrade head` locally against this same
  Supabase project, so the tables already exist — no migration step is needed for the first deploy).

Keep your secrets handy but private. You'll paste them into each platform's environment-variables
screen — never commit them.

---

## Step 1 — Deploy the backend to Render

1. Go to **[render.com](https://render.com)** and sign up (GitHub sign-in is easiest).
2. Click **New +** → **Web Service**, and connect your GitHub account / the
   `AI_Resume_Analyzer` repo.
3. Configure the service:
   - **Name:** `ai-resume-analyzer-api` (any name)
   - **Root Directory:** `backend`
   - **Runtime / Language:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type:** Free
4. Under **Environment → Environment Variables**, add each of these (values from your `.env`):

   | Key | Value |
   |-----|-------|
   | `SUPABASE_URL` | your Supabase project URL |
   | `SUPABASE_SERVICE_ROLE_KEY` | your Supabase secret/service-role key |
   | `DATABASE_URL` | your Session-pooler connection string (password percent-encoded) |
   | `GEMINI_API_KEY` | your Gemini API key |
   | `GEMINI_MODEL` | `gemini-3.6-flash` |
   | `AI_RATE_LIMIT_PER_MINUTE` | `20` |
   | `CORS_ORIGINS` | leave as a placeholder for now, e.g. `https://example.com` — you'll set the real value in Step 3 |

5. Click **Create Web Service** and wait for the first deploy to finish (a few minutes).
6. When it's live, copy the service URL — it looks like `https://ai-resume-analyzer-api.onrender.com`.
   Test it: open `<that URL>/health` and you should see `{"status":"ok",...}`.

---

## Step 2 — Deploy the frontend to Vercel

1. Go to **[vercel.com](https://vercel.com)** and sign up (GitHub sign-in is easiest).
2. Click **Add New… → Project**, and import the `AI_Resume_Analyzer` repo.
3. Configure the project:
   - **Root Directory:** `frontend`
   - **Framework Preset:** Vite (auto-detected)
   - **Build Command:** `npm run build` (default)
   - **Output Directory:** `dist` (default)
4. Expand **Environment Variables** and add:

   | Key | Value |
   |-----|-------|
   | `VITE_API_BASE_URL` | your Render backend URL from Step 1 (e.g. `https://ai-resume-analyzer-api.onrender.com`) |
   | `VITE_SUPABASE_URL` | your Supabase project URL |
   | `VITE_SUPABASE_ANON_KEY` | your Supabase anon/publishable key |

5. Click **Deploy** and wait for it to finish. Copy your frontend URL — it looks like
   `https://ai-resume-analyzer.vercel.app`.

> The included `frontend/vercel.json` adds an SPA rewrite so client-side routes (like `/dashboard`)
> work on refresh and direct links.

---

## Step 3 — Connect the two (CORS)

The backend must allow requests from your Vercel domain.

1. Back in **Render → your service → Environment**, set:
   - `CORS_ORIGINS` = your Vercel URL (e.g. `https://ai-resume-analyzer.vercel.app`)
   - (To allow more than one origin, comma-separate them, no spaces.)
2. Save — Render will redeploy automatically.

---

## Step 4 — Tell Supabase about the public domain

So that login sessions and password-reset emails point at the deployed site:

1. In the **Supabase dashboard → Authentication → URL Configuration**:
   - **Site URL:** your Vercel URL (e.g. `https://ai-resume-analyzer.vercel.app`)
   - **Redirect URLs:** add your Vercel URL and `https://<your-vercel-domain>/reset-password`
2. Save.

---

## Step 5 — Verify

1. Open your Vercel URL. The landing page should show **"Live analysis ready"** (green) — that
   confirms the frontend reached the backend.
2. Register an account, confirm via the email Supabase sends, then log in.
3. Upload or paste a resume and run an analysis. (The very first backend call after idle may take
   ~30–60s on Render's free tier while it wakes up.)
4. Try a job-specific analysis, the coach, saving a tailored version, and exporting — all should work.

---

## Updating the app later

Both platforms auto-deploy on every push to `main`:

- Push to GitHub → Vercel rebuilds the frontend and Render rebuilds the backend automatically.
- **Database migrations:** if a future change adds a migration, run `alembic upgrade head` against
  your Supabase `DATABASE_URL` (locally, or as a Render pre-deploy command) before/at deploy time.

## Troubleshooting

| Symptom | Likely cause / fix |
|---------|--------------------|
| Landing page shows "Service offline" | Backend URL wrong in `VITE_API_BASE_URL`, or backend still waking (wait ~60s and refresh). |
| Browser console shows a CORS error | `CORS_ORIGINS` on Render doesn't exactly match your Vercel domain (check https, no trailing slash). |
| Login works but password-reset link is wrong | Supabase Site URL / Redirect URLs not set to the Vercel domain (Step 4). |
| Analysis returns a 502 | Check `GEMINI_API_KEY` on Render, and that `GEMINI_MODEL` is a currently-available model. |
| Refreshing `/dashboard` 404s | Ensure `frontend/vercel.json` is present (SPA rewrite). |

# VoiceOps AI

AI-powered customer conversation intelligence. Upload a support call recording and get a
speaker-labelled transcript, sentiment, call reason, key details, a summary and action items,
all shown on a dashboard.

**Status: v0.9.0** (see [CHANGELOG](CHANGELOG.md) and [docs/PROGRESS.md](docs/PROGRESS.md))

## How it works

```
Audio upload -> FastAPI -> Faster-Whisper (speech to text)
             -> pyannote (who spoke when) -> agent/customer turns
             -> sentiment, intent, entities, keywords
             -> summary + action items (Claude if a key is set, rules otherwise)
             -> PostgreSQL -> React dashboard
```

## Features

- Upload WAV/MP3 calls; processing runs in the background with live status
- Speaker separation with agent/customer role detection
- Sentiment per turn and per speaker, customer sentiment trend
- Call reason (refund, delivery delay, ...), order IDs, products, durations, keywords
- Summary and action items (optional Claude API)
- Dashboard with stats, call table, chat-style transcript and sentiment timeline
- Login with JWT; the first registered account is the admin
- Docker setup (CPU-only), CI with automated tests

## Tech stack

Python, FastAPI, SQLAlchemy, PostgreSQL 17, Faster-Whisper, pyannote.audio, VADER,
React, TypeScript, Vite, Docker Compose, GitHub Actions.

## Run with Docker

1. Copy `.env.example` to `.env` and set the passwords and `JWT_SECRET`.
2. Add `HF_TOKEN` (accept the terms of `pyannote/speaker-diarization-community-1` on Hugging Face).
3. Start everything:

   ```powershell
   docker compose up -d --build
   ```

4. Open http://localhost:8080 (change ports with `FRONTEND_PORT` / `BACKEND_PORT`) and register.

The first processed call downloads the models and is slow; later calls are faster.

## Run locally for development

```powershell
docker compose up -d postgres
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt -r requirements-ml.txt
python -m uvicorn app.main:app --reload
```

In a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. Run the backend tests with `cd backend; pytest -q`.

## Project layout

```
backend/    FastAPI app (app/), services (Whisper, pyannote, NLP), tests
frontend/   React dashboard
deploy/     Optional server deployment files (Caddy, setup script)
docs/       PROGRESS.md (current version marker), DEPLOY.md (optional)
```

## Optional: deploying to a server

Deployment files are included ([docs/DEPLOY.md](docs/DEPLOY.md)) but the project is
intended to be run from GitHub; no live deployment is required.

## Limitations

- Sentiment and intents are rule/lexicon based
- Whisper `small` can mishear identifiers (order IDs are corrected)
- Processing uses CPU, so a call takes about a minute or more

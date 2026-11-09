# VoiceOps AI - Progress Marker

> Single source of truth for "where are we". Update this file at the end of every
> version. The current marker is the first row marked **NEXT** or **IN PROGRESS**.

## Marker

**Current version: v0.9.0 - complete as a GitHub project (live deployment skipped by choice)**
**Next: v1.0.0 - polish and release (security review, restrict sign-ups, screenshots in README)**
**Pushed to GitHub: yes, CI green**

| Version | Goal | Status |
|---|---|---|
| v0.1 | Upload, PostgreSQL, Whisper ASR | DONE |
| v0.2 | Speaker diarization, transcript API | DONE |
| v0.3 | Sentiment per speaker | DONE |
| v0.4 | Intent, entities, keywords | DONE |
| v0.5 | Summary and action items | DONE |
| v0.6 | React dashboard | DONE |
| v0.7 | Login and users | DONE |
| v0.8 | Production Docker, background processing, config cleanup | DONE |
| v0.9 | Deployment files and monitoring endpoint | DONE (files only; no live server by choice) |
| v1.0 | Production-ready release | PLANNED |

## v0.8 scope

- [x] Processing runs in the background (`POST /process` returns 202, UI polls status)
- [x] Config from environment (CORS origins, audio dir, SQL logging)
- [x] Sentiment ignores courtesy phrases ("sorry to hear that", "thank you")
- [x] Backend Docker image includes torch (CPU), pyannote, ffmpeg and runs as non-root
- [x] docker-compose: healthchecks, model cache mount, required JWT secret
- [x] Verified end to end inside containers

## v0.9 scope

- [x] `docker-compose.prod.yml` (Caddy auto-HTTPS, private DB/backend, log rotation)
- [x] `deploy/server-setup.sh` one-command server setup and updates (builds on the server, no image registry)
- [x] `GET /api/health/ready` readiness check (tests the DB) and request logging
- [x] `docs/DEPLOY.md` step-by-step guide, backups, security checklist
- [-] Live server: skipped by choice, the project stays on GitHub
- [-] Uptime monitor: skipped (no live server)

## How to run everything in Docker

1. `cd D:\Study\Voice_AI; docker compose up -d --build`
2. Open http://localhost:8090 (ports come from `.env`: FRONTEND_PORT, BACKEND_PORT)
3. First call after a restart is slow (models load, ~8 min on CPU in Docker); later calls are faster.

## How to run (local, no Docker backend)

1. `docker compose up -d postgres`
2. Backend: `cd backend; .\.venv\Scripts\Activate.ps1; python -m uvicorn app.main:app --reload`
3. Frontend: `cd frontend; npm run dev` then open http://localhost:5173

## Known issues / backlog

- v0.8 verified in Docker: call processed (ORD1045, delivery_delay) in ~514 s on first run
- Docker image is 3.4 GB (CPU torch); consider slimming or GPU variant for v0.9
- Processing queue is in-process; a worker + Redis is the next step if load grows

- Whisper `small` mis-hears identifiers (handled for order IDs only)
- No database migrations tool yet (Alembic) - new columns are added at startup
- Rule-based intents; consider an LLM classifier once an API key is available
- Windows machine has native PostgreSQL 16/18 on ports 5432/5433; Docker DB uses 5440

\# Changelog



All notable changes to VoiceOps AI are documented here.



## [v0.7.0] - Analysis, dashboard and login

- v0.3: per-turn and per-speaker sentiment (VADER), agent/customer role detection, customer sentiment trend
- v0.4: intent detection, entities (order IDs including misheard "over D1045", products, durations, organizations), keywords
- v0.5: call summary and action items (Claude when `ANTHROPIC_API_KEY` is set, rule-based otherwise)
- v0.6: React dashboard (stats, call reasons, sentiment, keywords, calls table) and call detail page (summary, sentiment timeline, chat-style transcript)
- v0.7: user accounts with JWT login; the first account is the admin; `/api/calls*` and `/api/stats` require login; `DELETE /api/calls` is admin only
- New endpoints: `/api/auth/*`, `GET /api/calls`, `/api/calls/{id}`, `/analysis`, `POST /analyze`, `/api/stats`
- Upload errors now return HTTP 400; `DELETE /api/calls` also removes transcripts and analyses
- Known limits: lexicon sentiment scores polite phrases like "sorry to hear that" as positive; processing runs inside the request (1-2 minutes on CPU); the Docker backend image lacks torch/pyannote

## [v0.2.0] - Speaker-attributed transcripts

- Pipeline services: Faster-Whisper, pyannote diarization, speaker/segment merge
- `POST /api/calls/{id}/process` and `GET /api/calls/{id}/transcript`
- `backend/run_pipeline.py` analyzes an audio file without the database
- Audio decoded with PyAV, so torchcodec / system FFmpeg DLLs are not needed

\## \[v0.1.0] - ASR + PostgreSQL Baseline



\### Added



\- Initial VoiceOps AI project structure

\- FastAPI backend

\- React + TypeScript frontend

\- PostgreSQL database using Docker

\- Docker Compose configuration

\- SQLAlchemy database models

\- Audio upload API

\- Audio file storage

\- Call metadata persistence

\- Faster-Whisper ASR integration

\- Automatic language detection

\- Transcription timestamps

\- Transcript persistence in PostgreSQL

\- Transcript segment storage as JSON

\- Environment-based database configuration

\- Project README and local development documentation



\### Current Architecture



Audio → FastAPI → PostgreSQL  

Audio → Faster-Whisper → Transcript → PostgreSQL  

React → FastAPI → PostgreSQL



\### Known Limitations



\- Speaker diarization is not implemented yet.

\- Sentiment analysis is not implemented yet.

\- Intent and entity extraction are not implemented yet.

\- LLM summarization is not implemented yet.

\- Production authentication is not implemented yet.

\- CI/CD pipeline is not implemented yet.

\- Cloud deployment is not implemented yet.



\### Planned Releases



\- v0.2.0 — Speaker diarization

\- v0.3.0 — Sentiment analysis

\- v0.4.0 — Intent, entities and keywords

\- v0.5.0 — LLM summary and action items

\- v0.6.0 — React analytics dashboard

\- v0.7.0 — Authentication and user management

\- v0.8.0 — Production Docker architecture

\- v0.9.0 — Cloud deployment and monitoring

\- v1.0.0 — Production-ready VoiceOps AI


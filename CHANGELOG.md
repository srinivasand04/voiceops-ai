\# Changelog



All notable changes to VoiceOps AI are documented here.



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


\# VoiceOps AI



AI-powered Customer Conversation Intelligence Platform.



VoiceOps AI transforms customer call recordings into structured conversation intelligence using Automatic Speech Recognition (ASR), NLP, machine learning, and LLM-based analysis.



\## Project Status



Current version: \*\*v0.1.0 — ASR + PostgreSQL Baseline\*\*



\## Architecture



Audio Call

&#x20;   ↓

Audio Upload

&#x20;   ↓

FastAPI

&#x20;   ↓

Faster-Whisper ASR

&#x20;   ↓

Timestamped Transcript

&#x20;   ↓

PostgreSQL

&#x20;   ↓

Speaker Diarization

&#x20;   ↓

Sentiment Analysis

&#x20;   ↓

Intent Detection

&#x20;   ↓

Entities \& Keywords

&#x20;   ↓

LLM Summary

&#x20;   ↓

Action Items

&#x20;   ↓

React Dashboard



\## Technology Stack



\### Backend

\- Python

\- FastAPI

\- Pydantic

\- SQLAlchemy

\- Faster-Whisper



\### Database

\- PostgreSQL 17

\- Docker

\- Docker Compose



\### Frontend

\- React

\- TypeScript

\- Vite



\### AI / ML

\- Automatic Speech Recognition

\- Speaker Diarization

\- NLP

\- Sentiment Analysis

\- Intent Classification

\- LLM-based Summarization



\## Current Features



\### v0.1.0



\- Audio file upload

\- WAV/MP3/MPEG validation

\- Audio file storage

\- PostgreSQL call metadata

\- Faster-Whisper transcription

\- Language detection

\- Timestamped transcription segments

\- Transcript persistence in PostgreSQL



\## Project Structure



```text

Voice\_AI/

├── backend/

│   ├── app/

│   ├── test\_whisper.py

│   └── .venv/

├── frontend/

├── data/

├── .env

├── .env.example

├── .gitignore

├── CHANGELOG.md

├── docker-compose.yml

└── README.md


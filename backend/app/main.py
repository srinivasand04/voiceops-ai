from pathlib import Path

from fastapi import FastAPI, Depends, UploadFile, File
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.database import engine, get_db
from app.models import Base, Call


app = FastAPI(
    title="VoiceOps AI",
    description="AI-powered customer conversation intelligence platform",
    version="0.1.0",
)


# Create database tables
Base.metadata.create_all(bind=engine)


# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Audio storage directory
AUDIO_DIR = Path(__file__).resolve().parents[2] / "data" / "audio"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)


class HealthResponse(BaseModel):
    status: str
    service: str


@app.get("/", response_model=HealthResponse)
def root():
    return {
        "status": "ok",
        "service": "VoiceOps AI API",
    }


@app.get("/health", response_model=HealthResponse)
def health():
    return {
        "status": "healthy",
        "service": "backend",
    }


@app.delete("/api/calls")
def delete_all_calls(db: Session = Depends(get_db)):
    db.query(Call).delete()
    db.commit()

    return {
        "status": "success",
        "message": "All call records deleted",
    }


@app.post("/api/calls/upload")
async def upload_call(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not file.filename:
        return {
            "status": "error",
            "message": "No filename provided",
        }

    allowed_extensions = {
        ".wav",
        ".mp3",
        ".mpeg",
    }

    extension = Path(file.filename).suffix.lower()

    if extension not in allowed_extensions:
        return {
            "status": "error",
            "message": "Unsupported audio format",
        }

    file_path = AUDIO_DIR / Path(file.filename).name

    with file_path.open("wb") as buffer:
        while chunk := await file.read(1024 * 1024):
            buffer.write(chunk)

    file_size = file_path.stat().st_size
    mime_type = file.content_type or "application/octet-stream"

    new_call = Call(
        filename=file.filename,
        file_path=str(file_path),
        file_size=file_size,
        mime_type=mime_type,
        status="uploaded",
    )

    db.add(new_call)
    db.commit()
    db.refresh(new_call)

    return {
        "id": new_call.id,
        "filename": new_call.filename,
        "status": new_call.status,
        "file_path": new_call.file_path,
        "file_size": new_call.file_size,
        "mime_type": new_call.mime_type,
    }
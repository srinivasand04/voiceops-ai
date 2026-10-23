from pathlib import Path

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.database import engine, get_db
from app.models import Base, Call, Transcript
from app.services.speaker_merge import merge_consecutive


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


@app.post("/api/calls/{call_id}/process")
def process_call(call_id: int, db: Session = Depends(get_db)):
    call = db.get(Call, call_id)

    if call is None:
        raise HTTPException(status_code=404, detail="Call not found")

    # Imported here so the API starts (and tests run) without the ML stack.
    from app.services.pipeline import analyze_audio

    call.status = "processing"
    db.commit()

    try:
        result = analyze_audio(call.file_path)
    except Exception as error:
        call.status = "failed"
        db.commit()
        raise HTTPException(status_code=500, detail=str(error))

    db.query(Transcript).filter(Transcript.call_id == call.id).delete()

    db.add(
        Transcript(
            call_id=call.id,
            text=result["text"],
            language=result["language"],
            language_probability=result["language_probability"],
            duration=result["duration"],
            segments=result["segments"],
        )
    )

    call.status = "processed"
    db.commit()

    return {"call_id": call.id, "status": call.status, "turns": result["turns"]}


@app.get("/api/calls/{call_id}/transcript")
def get_transcript(call_id: int, db: Session = Depends(get_db)):
    transcript = (
        db.query(Transcript)
        .filter(Transcript.call_id == call_id)
        .order_by(Transcript.id.desc())
        .first()
    )

    if transcript is None:
        raise HTTPException(status_code=404, detail="Transcript not found")

    return {
        "call_id": call_id,
        "language": transcript.language,
        "duration": transcript.duration,
        "text": transcript.text,
        "segments": transcript.segments,
        "turns": merge_consecutive(transcript.segments),
    }

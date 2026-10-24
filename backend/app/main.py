from collections import Counter
from pathlib import Path

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth import (
    create_token,
    get_current_user,
    hash_password,
    require_admin,
    verify_password,
)
from app.database import engine, get_db
from app.models import Base, Call, CallAnalysis, Transcript, User
from app.services.analysis import analyze_turns
from app.services.speaker_merge import merge_consecutive


app = FastAPI(
    title="VoiceOps AI",
    description="AI-powered customer conversation intelligence platform",
    version="0.7.0",
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

ALLOWED_EXTENSIONS = {".wav", ".mp3", ".mpeg"}


class HealthResponse(BaseModel):
    status: str
    service: str


class Credentials(BaseModel):
    email: str = Field(min_length=3, max_length=255, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(min_length=8, max_length=128)


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


# ---------------------------------------------------------------- auth


def _user_payload(user: User) -> dict:
    return {"id": user.id, "email": user.email, "role": user.role}


@app.post("/api/auth/register", status_code=201)
def register(credentials: Credentials, db: Session = Depends(get_db)):
    email = credentials.email.strip().lower()

    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=409, detail="Email already registered")

    # The first account created becomes the admin.
    is_first = db.query(User).count() == 0

    user = User(
        email=email,
        password_hash=hash_password(credentials.password),
        role="admin" if is_first else "analyst",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return {"token": create_token(user), "user": _user_payload(user)}


@app.post("/api/auth/login")
def login(credentials: Credentials, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == credentials.email.strip().lower()).first()

    if user is None or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    return {"token": create_token(user), "user": _user_payload(user)}


@app.get("/api/auth/me")
def me(user: User = Depends(get_current_user)):
    return _user_payload(user)


# --------------------------------------------------------------- calls


def _get_call(db: Session, call_id: int) -> Call:
    call = db.get(Call, call_id)

    if call is None:
        raise HTTPException(status_code=404, detail="Call not found")

    return call


def _latest_transcript(db: Session, call_id: int) -> Transcript | None:
    return (
        db.query(Transcript)
        .filter(Transcript.call_id == call_id)
        .order_by(Transcript.id.desc())
        .first()
    )


def _save_analysis(db: Session, call_id: int, result: dict) -> CallAnalysis:
    db.query(CallAnalysis).filter(CallAnalysis.call_id == call_id).delete()

    analysis = CallAnalysis(
        call_id=call_id,
        roles=result["roles"],
        sentiment=result["sentiment"],
        intents=result["intents"],
        entities=result["entities"],
        keywords=result["keywords"],
        summary=result["summary"],
        action_items=result["action_items"],
        summary_source=result["summary_source"],
    )
    db.add(analysis)

    return analysis


def _call_row(call: Call, analysis: CallAnalysis | None) -> dict:
    row = {
        "id": call.id,
        "filename": call.filename,
        "status": call.status,
        "file_size": call.file_size,
        "created_at": call.created_at.isoformat(),
        "intent": None,
        "sentiment": None,
        "customer_sentiment": None,
        "order_ids": [],
    }

    if analysis is not None:
        customer = next(
            (s for s in analysis.sentiment["speakers"].values() if s["role"] == "customer"),
            None,
        )
        row.update(
            intent=analysis.intents["primary"],
            sentiment=analysis.sentiment["overall"]["label"],
            customer_sentiment=customer["label"] if customer else None,
            order_ids=analysis.entities["order_ids"],
        )

    return row


@app.get("/api/calls")
def list_calls(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    calls = db.query(Call).order_by(Call.id.desc()).all()
    analyses = {a.call_id: a for a in db.query(CallAnalysis).all()}

    return [_call_row(c, analyses.get(c.id)) for c in calls]


@app.get("/api/calls/{call_id}")
def get_call(
    call_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    call = _get_call(db, call_id)
    analysis = db.query(CallAnalysis).filter(CallAnalysis.call_id == call_id).first()

    return _call_row(call, analysis)


@app.get("/api/stats")
def stats(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    calls = db.query(Call).all()
    analyses = db.query(CallAnalysis).all()

    intents = Counter(a.intents["primary"] for a in analyses)
    sentiments = Counter(a.sentiment["overall"]["label"] for a in analyses)
    keywords = Counter()

    for analysis in analyses:
        for item in analysis.keywords:
            keywords[item["keyword"]] += item["count"]

    return {
        "total_calls": len(calls),
        "processed_calls": sum(1 for c in calls if c.status == "processed"),
        "intents": dict(intents),
        "sentiments": dict(sentiments),
        "top_keywords": [{"keyword": k, "count": c} for k, c in keywords.most_common(10)],
    }


@app.delete("/api/calls")
def delete_all_calls(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    db.query(CallAnalysis).delete()
    db.query(Transcript).delete()
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
    _: User = Depends(get_current_user),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    extension = Path(file.filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported audio format")

    file_path = AUDIO_DIR / Path(file.filename).name

    with file_path.open("wb") as buffer:
        while chunk := await file.read(1024 * 1024):
            buffer.write(chunk)

    new_call = Call(
        filename=file.filename,
        file_path=str(file_path),
        file_size=file_path.stat().st_size,
        mime_type=file.content_type or "application/octet-stream",
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
def process_call(
    call_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Transcribe, identify speakers, then analyze the call."""
    call = _get_call(db, call_id)

    # Imported here so the API starts (and tests run) without the ML stack.
    from app.services.pipeline import analyze_audio

    call.status = "processing"
    db.commit()

    try:
        result = analyze_audio(call.file_path)
        analysis = analyze_turns(result["turns"])
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
    _save_analysis(db, call.id, analysis)

    call.status = "processed"
    db.commit()

    return {"call_id": call.id, "status": call.status, "turns": result["turns"]}


@app.post("/api/calls/{call_id}/analyze")
def reanalyze_call(
    call_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Re-run the analysis on the stored transcript (no audio processing)."""
    _get_call(db, call_id)
    transcript = _latest_transcript(db, call_id)

    if transcript is None:
        raise HTTPException(status_code=404, detail="Transcript not found")

    analysis = _save_analysis(
        db, call_id, analyze_turns(merge_consecutive(transcript.segments))
    )
    db.commit()
    db.refresh(analysis)

    return get_analysis(call_id, db)


@app.get("/api/calls/{call_id}/transcript")
def get_transcript(
    call_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    transcript = _latest_transcript(db, call_id)

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


@app.get("/api/calls/{call_id}/analysis")
def get_analysis(
    call_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    analysis = db.query(CallAnalysis).filter(CallAnalysis.call_id == call_id).first()

    if analysis is None:
        raise HTTPException(status_code=404, detail="Analysis not found")

    return {
        "call_id": call_id,
        "roles": analysis.roles,
        "sentiment": analysis.sentiment,
        "intents": analysis.intents,
        "entities": analysis.entities,
        "keywords": analysis.keywords,
        "summary": analysis.summary,
        "action_items": analysis.action_items,
        "summary_source": analysis.summary_source,
    }

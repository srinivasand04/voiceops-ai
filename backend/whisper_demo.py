from faster_whisper import WhisperModel
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Call, Transcript


AUDIO_FILE = r"D:\Study\Voice_AI\data\audio\customer_call_001.wav"

# The call record we want to transcribe
CALL_ID = 1


print("Loading Whisper model...")

model = WhisperModel(
    "small",
    device="cpu",
    compute_type="int8",
)

print("Transcribing audio...")

segments, info = model.transcribe(
    AUDIO_FILE,
    beam_size=5,
)

# Convert Whisper segments into normal Python data
segment_list = []
transcript_parts = []

for segment in segments:
    text = segment.text.strip()

    if not text:
        continue

    transcript_parts.append(text)

    segment_list.append(
        {
            "start": round(segment.start, 2),
            "end": round(segment.end, 2),
            "text": text,
        }
    )


full_transcript = " ".join(transcript_parts)

duration = (
    segment_list[-1]["end"]
    if segment_list
    else 0.0
)


print()
print("Detected language:", info.language)
print("Language probability:", info.language_probability)
print("Duration:", duration)
print()
print("TRANSCRIPT")
print("=" * 60)

for segment in segment_list:
    print(
        f"[{segment['start']:.2f}s -> {segment['end']:.2f}s] "
        f"{segment['text']}"
    )

print("=" * 60)


# --------------------------------------------------
# Save transcript to PostgreSQL
# --------------------------------------------------

print()
print("Saving transcript to PostgreSQL...")

db: Session = SessionLocal()

try:
    # Verify that the call exists
    call = db.get(Call, CALL_ID)

    if not call:
        raise ValueError(
            f"Call ID {CALL_ID} does not exist in the database."
        )

    transcript = Transcript(
        call_id=CALL_ID,
        text=full_transcript,
        language=info.language,
        language_probability=float(info.language_probability),
        duration=duration,
        segments=segment_list,
    )

    db.add(transcript)
    db.commit()
    db.refresh(transcript)

    print()
    print("Transcript saved successfully!")
    print("Transcript ID:", transcript.id)
    print("Call ID:", transcript.call_id)

finally:
    db.close()


print()
print("Transcription complete.")
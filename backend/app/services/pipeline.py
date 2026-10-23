from app.services.diarization import diarize
from app.services.speaker_merge import assign_speakers, merge_consecutive
from app.services.transcription import transcribe


def analyze_audio(audio_path: str, num_speakers: int = 2) -> dict:
    """Transcribe, diarize and combine into a speaker-labelled transcript."""
    transcript = transcribe(audio_path)
    turns = diarize(audio_path, num_speakers=num_speakers)

    labelled = assign_speakers(transcript["segments"], turns)

    return {
        **transcript,
        "text": " ".join(s["text"] for s in transcript["segments"]),
        "segments": labelled,
        "turns": merge_consecutive(labelled),
    }

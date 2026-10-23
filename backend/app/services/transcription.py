from functools import lru_cache


@lru_cache(maxsize=1)
def _get_model(model_size: str):
    from faster_whisper import WhisperModel

    return WhisperModel(
        model_size,
        device="cpu",
        compute_type="int8",
        cpu_threads=1,
        num_workers=1,
    )


def transcribe(audio_path: str, model_size: str = "small") -> dict:
    """Run Faster-Whisper and return plain-Python segments."""
    model = _get_model(model_size)

    segments, info = model.transcribe(
        audio_path,
        beam_size=5,
        vad_filter=True,
    )

    segment_list = []

    for segment in segments:
        text = segment.text.strip()

        if not text:
            continue

        segment_list.append(
            {
                "start": round(segment.start, 2),
                "end": round(segment.end, 2),
                "text": text,
            }
        )

    return {
        "language": info.language,
        "language_probability": round(info.language_probability, 4),
        "duration": round(info.duration, 2),
        "segments": segment_list,
    }

import os
from functools import lru_cache

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")


@lru_cache(maxsize=1)
def _get_pipeline():
    import torch
    from pyannote.audio import Pipeline

    torch.set_num_threads(1)

    try:
        torch.set_num_interop_threads(1)
    except RuntimeError:
        pass

    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-community-1"
    )
    pipeline.segmentation_batch_size = 1
    pipeline.embedding_batch_size = 1
    pipeline.to(torch.device("cpu"))

    return pipeline


def diarize(audio_path: str, num_speakers: int = 2) -> list[dict]:
    """Return speaker turns as [{"start", "end", "speaker"}]."""
    import torch
    from faster_whisper import decode_audio

    # Decode with PyAV (bundled with faster-whisper) and hand pyannote an
    # in-memory waveform, so torchcodec / system FFmpeg DLLs are not needed.
    samples = decode_audio(audio_path, sampling_rate=16000)
    audio = {
        "waveform": torch.from_numpy(samples).unsqueeze(0),
        "sample_rate": 16000,
    }

    result = _get_pipeline()(
        audio,
        min_speakers=num_speakers,
        max_speakers=num_speakers,
    )

    return [
        {
            "start": round(turn.start, 2),
            "end": round(turn.end, 2),
            "speaker": speaker,
        }
        for turn, speaker in result.speaker_diarization
    ]

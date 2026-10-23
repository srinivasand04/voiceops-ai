import os

os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

import torch
from pyannote.audio import Pipeline


AUDIO_FILE = r"D:\Study\Voice_AI\data\audio\customer_call_001.wav"


print("=" * 60)
print("VOICEOPS AI - SPEAKER DIARIZATION")
print("=" * 60)


torch.set_num_threads(1)

try:
    torch.set_num_interop_threads(1)
except RuntimeError:
    pass


print("Loading speaker diarization model...")


pipeline = Pipeline.from_pretrained(
    "pyannote/speaker-diarization-community-1"
)


pipeline.segmentation_batch_size = 1
pipeline.embedding_batch_size = 1
pipeline.to(torch.device("cpu"))


print("Pipeline loaded.")
print("Segmentation batch size:", pipeline.segmentation_batch_size)
print("Embedding batch size:", pipeline.embedding_batch_size)


print()
print("Running diarization on full audio...")
print("Audio:", AUDIO_FILE)


output = pipeline(
    AUDIO_FILE,
    min_speakers=2,
    max_speakers=2,
)


print()
print("=" * 60)
print("SPEAKER DIARIZATION RESULT")
print("=" * 60)


for turn, speaker in output.speaker_diarization:
    print(
        f"[{turn.start:.2f}s -> {turn.end:.2f}s] "
        f"{speaker}"
    )


print("=" * 60)
print("Detected speakers:", output.speaker_diarization.labels())
print("Diarization complete.")
print("=" * 60)
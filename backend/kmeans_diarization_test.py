import os

os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

import torch
from pyannote.audio import Pipeline
from pyannote.audio.pipelines.clustering import KMeansClustering


AUDIO_FILE = r"D:\Study\Voice_AI\data\audio\customer_call_001.wav"

print("=" * 70)
print("VOICEOPS AI - KMEANS DIARIZATION TEST")
print("=" * 70)

torch.set_num_threads(1)

try:
    torch.set_num_interop_threads(1)
except RuntimeError:
    pass


print("Loading Community-1...")

pipeline = Pipeline.from_pretrained(
    "pyannote/speaker-diarization-community-1"
)

pipeline.segmentation_batch_size = 1
pipeline.embedding_batch_size = 1
pipeline.to(torch.device("cpu"))


print("Replacing VBx with K-Means...")

pipeline.clustering = KMeansClustering(
    metric="cosine"
)

print("Clustering:", type(pipeline.clustering))

print()
print("Running full 75-second audio...")
print("Expected speakers: 2")


output = pipeline(
    AUDIO_FILE,
    num_speakers=2,
)


print()
print("=" * 70)
print("K-MEANS SPEAKER TURNS")
print("=" * 70)

turns = list(output.speaker_diarization)

print("Number of turns:", len(turns))
print()

for turn, speaker in turns:
    print(
        f"[{turn.start:6.2f}s -> {turn.end:6.2f}s] "
        f"{speaker}"
    )

print()
print("Detected labels:")
print(output.speaker_diarization.labels())

print("=" * 70)
print("TEST COMPLETE")
print("=" * 70)
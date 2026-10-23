import os

# Stable CPU configuration
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

import torch
from faster_whisper import WhisperModel
from pyannote.audio import Pipeline


AUDIO_FILE = r"D:\Study\Voice_AI\data\audio\customer_call_001.wav"
OUTPUT_FILE = (
    r"D:\Study\Voice_AI\data\audio"
    r"\customer_call_001_speaker_transcript.txt"
)


print("=" * 70)
print("VOICEOPS AI - SPEAKER + TEXT TRANSCRIPT")
print("=" * 70)


# =========================================================
# 1. FASTER-WHISPER
# =========================================================

print()
print("[1] Loading Faster-Whisper...")

whisper_model = WhisperModel(
    "small",
    device="cpu",
    compute_type="int8",
    cpu_threads=1,
    num_workers=1,
)

print("Whisper loaded.")

print()
print("[2] Transcribing audio...")

whisper_segments, info = whisper_model.transcribe(
    AUDIO_FILE,
    beam_size=5,
)

whisper_segments = list(whisper_segments)

print("Language:", info.language)
print("Whisper segments:", len(whisper_segments))


# =========================================================
# 2. PYANNOTE
# =========================================================

print()
print("[3] Loading speaker diarization...")

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

print("Diarization loaded.")

print()
print("[4] Detecting speakers...")

diarization = pipeline(
    AUDIO_FILE,
    min_speakers=2,
    max_speakers=2,
)

speaker_turns = list(
    diarization.speaker_diarization
)

print(
    "Detected speakers:",
    diarization.speaker_diarization.labels()
)


# =========================================================
# 3. MATCH TEXT TO SPEAKER
# =========================================================

def find_speaker(start, end):

    best_speaker = "UNKNOWN"
    best_overlap = 0.0

    for turn, speaker in speaker_turns:

        overlap_start = max(start, turn.start)
        overlap_end = min(end, turn.end)

        overlap = max(
            0.0,
            overlap_end - overlap_start
        )

        if overlap > best_overlap:
            best_overlap = overlap
            best_speaker = speaker

    return best_speaker


print()
print("=" * 70)
print("FINAL SPEAKER-ATTRIBUTED TRANSCRIPT")
print("=" * 70)

final_lines = []

for segment in whisper_segments:

    start = segment.start
    end = segment.end
    text = segment.text.strip()

    if not text:
        continue

    speaker = find_speaker(start, end)

    line = (
        f"[{start:05.2f}s -> {end:05.2f}s] "
        f"{speaker}: {text}"
    )

    print(line)

    final_lines.append(line)


# =========================================================
# 4. SAVE RESULT
# =========================================================

with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8"
) as file:

    file.write(
        "VOICEOPS AI - SPEAKER-ATTRIBUTED TRANSCRIPT\n"
    )

    file.write("=" * 70 + "\n\n")

    file.write(
        "\n".join(final_lines)
    )


print()
print("=" * 70)
print("COMPLETED")
print("=" * 70)
print("Saved to:")
print(OUTPUT_FILE)
print("=" * 70)
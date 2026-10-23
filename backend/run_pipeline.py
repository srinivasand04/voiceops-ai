"""Run the full pipeline on one audio file (no database needed).

Usage: python run_pipeline.py <audio_file> [--speakers 2]
"""
import argparse
import json
from pathlib import Path

from app.services.pipeline import analyze_audio


parser = argparse.ArgumentParser()
parser.add_argument("audio_file")
parser.add_argument("--speakers", type=int, default=2)
args = parser.parse_args()

audio = Path(args.audio_file).resolve()
result = analyze_audio(str(audio), num_speakers=args.speakers)

print(f"Language: {result['language']}  Duration: {result['duration']}s")
print("=" * 70)

lines = []
for turn in result["turns"]:
    line = f"[{turn['start']:06.2f} -> {turn['end']:06.2f}] {turn['speaker']}: {turn['text']}"
    print(line)
    lines.append(line)

audio.with_suffix(".speakers.txt").write_text("\n".join(lines), encoding="utf-8")
audio.with_suffix(".analysis.json").write_text(
    json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
)
print("=" * 70)
print("Saved:", audio.with_suffix(".speakers.txt"))

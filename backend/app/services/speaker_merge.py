"""Pure logic for attaching speaker labels to transcript segments."""


def _overlap(a_start: float, a_end: float, b_start: float, b_end: float) -> float:
    return max(0.0, min(a_end, b_end) - max(a_start, b_start))


def assign_speakers(segments: list[dict], turns: list[dict]) -> list[dict]:
    """Label each segment with the speaker whose turns overlap it the most."""
    labelled = []

    for segment in segments:
        totals: dict[str, float] = {}

        for turn in turns:
            amount = _overlap(
                segment["start"], segment["end"], turn["start"], turn["end"]
            )

            if amount > 0:
                totals[turn["speaker"]] = totals.get(turn["speaker"], 0.0) + amount

        speaker = max(totals, key=totals.get) if totals else "UNKNOWN"
        labelled.append({**segment, "speaker": speaker})

    return labelled


def merge_consecutive(segments: list[dict]) -> list[dict]:
    """Join neighbouring segments that have the same speaker into one turn."""
    merged: list[dict] = []

    for segment in segments:
        if merged and merged[-1]["speaker"] == segment["speaker"]:
            merged[-1]["end"] = segment["end"]
            merged[-1]["text"] += " " + segment["text"]
        else:
            merged.append(dict(segment))

    return merged

from app.services.speaker_merge import assign_speakers, merge_consecutive


TURNS = [
    {"start": 0.0, "end": 5.0, "speaker": "SPEAKER_00"},
    {"start": 5.0, "end": 12.0, "speaker": "SPEAKER_01"},
]


def test_assign_speakers_uses_largest_overlap():
    segments = [
        {"start": 0.5, "end": 4.5, "text": "Hello"},
        {"start": 4.0, "end": 10.0, "text": "Hi there"},
    ]

    result = assign_speakers(segments, TURNS)

    assert [s["speaker"] for s in result] == ["SPEAKER_00", "SPEAKER_01"]


def test_assign_speakers_unknown_without_overlap():
    result = assign_speakers([{"start": 20.0, "end": 22.0, "text": "x"}], TURNS)

    assert result[0]["speaker"] == "UNKNOWN"


def test_merge_consecutive_joins_same_speaker():
    segments = [
        {"start": 0, "end": 2, "text": "a", "speaker": "A"},
        {"start": 2, "end": 4, "text": "b", "speaker": "A"},
        {"start": 4, "end": 6, "text": "c", "speaker": "B"},
    ]

    merged = merge_consecutive(segments)

    assert len(merged) == 2
    assert merged[0]["text"] == "a b"
    assert merged[0]["end"] == 4

import time
import uuid

from fastapi.testclient import TestClient

import app.main as main
from app.main import app


client = TestClient(app)

FAKE_RESULT = {
    "text": "Hello. Hi.",
    "language": "en",
    "language_probability": 0.99,
    "duration": 5.0,
    "segments": [
        {"start": 0.0, "end": 2.0, "text": "I am calling about my order, it has not arrived.", "speaker": "SPEAKER_01"},
        {"start": 2.0, "end": 5.0, "text": "Let me check that for you. Thank you for calling.", "speaker": "SPEAKER_00"},
    ],
    "turns": [
        {"start": 0.0, "end": 2.0, "text": "I am calling about my order, it has not arrived.", "speaker": "SPEAKER_01"},
        {"start": 2.0, "end": 5.0, "text": "Let me check that for you. Thank you for calling.", "speaker": "SPEAKER_00"},
    ],
}


def _login():
    response = client.post(
        "/api/auth/register",
        json={"email": f"user-{uuid.uuid4().hex[:10]}@example.com", "password": "correct-horse-1"},
    )

    return {"Authorization": f"Bearer {response.json()['token']}"}


def _upload(headers):
    return client.post(
        "/api/calls/upload",
        headers=headers,
        files={"file": (f"pytest-{uuid.uuid4().hex[:8]}.wav", b"RIFF0000WAVE", "audio/wav")},
    ).json()["id"]


def _wait_for(call_id, headers, wanted):
    for _ in range(50):
        call = client.get(f"/api/calls/{call_id}", headers=headers).json()

        if call["status"] in wanted:
            return call

        time.sleep(0.1)

    raise AssertionError(f"call stayed {call['status']}")


def test_upload_rejects_bad_extension():
    headers = _login()

    response = client.post(
        "/api/calls/upload",
        headers=headers,
        files={"file": ("pytest-notes.txt", b"hello", "text/plain")},
    )

    assert response.status_code == 400


def test_process_runs_in_background_and_saves_results(monkeypatch):
    import app.services.pipeline as pipeline

    monkeypatch.setattr(pipeline, "analyze_audio", lambda path: FAKE_RESULT)
    headers = _login()
    call_id = _upload(headers)

    response = client.post(f"/api/calls/{call_id}/process", headers=headers)

    assert response.status_code == 202

    call = _wait_for(call_id, headers, {"processed", "failed"})

    assert call["status"] == "processed"
    assert call["intent"] is not None

    transcript = client.get(f"/api/calls/{call_id}/transcript", headers=headers).json()
    analysis = client.get(f"/api/calls/{call_id}/analysis", headers=headers).json()

    assert len(transcript["turns"]) == 2
    assert analysis["roles"]["SPEAKER_00"] == "agent"
    assert analysis["action_items"]


def test_failed_processing_records_error(monkeypatch):
    import app.services.pipeline as pipeline

    def boom(path):
        raise RuntimeError("model exploded")

    monkeypatch.setattr(pipeline, "analyze_audio", boom)
    headers = _login()
    call_id = _upload(headers)

    client.post(f"/api/calls/{call_id}/process", headers=headers)
    call = _wait_for(call_id, headers, {"processed", "failed"})

    assert call["status"] == "failed"
    assert "model exploded" in call["error"]


def test_cannot_process_twice_at_once(monkeypatch):
    headers = _login()
    call_id = _upload(headers)

    monkeypatch.setattr(main, "run_processing", lambda call_id: None)
    first = client.post(f"/api/calls/{call_id}/process", headers=headers)
    second = client.post(f"/api/calls/{call_id}/process", headers=headers)

    assert first.status_code == 202
    assert second.status_code == 409

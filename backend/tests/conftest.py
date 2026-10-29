import os
import tempfile

# Must be set before the app is imported so tests never write into data/audio.
os.environ["AUDIO_DIR"] = tempfile.mkdtemp(prefix="voiceops-test-audio-")

import pytest
from sqlalchemy import text

from app.database import engine


@pytest.fixture(scope="session", autouse=True)
def clean_test_data():
    """Tests create throwaway users and calls; remove them afterwards (the
    first real account created must be the admin)."""
    yield

    with engine.begin() as connection:
        connection.execute(text("DELETE FROM users WHERE email LIKE 'user-%@example.com'"))
        connection.execute(
            text(
                "DELETE FROM call_analyses WHERE call_id IN "
                "(SELECT id FROM calls WHERE filename LIKE 'pytest-%')"
            )
        )
        connection.execute(
            text(
                "DELETE FROM transcripts WHERE call_id IN "
                "(SELECT id FROM calls WHERE filename LIKE 'pytest-%')"
            )
        )
        connection.execute(text("DELETE FROM calls WHERE filename LIKE 'pytest-%'"))

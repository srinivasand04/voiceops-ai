import pytest
from sqlalchemy import text

from app.database import engine


@pytest.fixture(scope="session", autouse=True)
def remove_test_users():
    """Tests register throwaway accounts; remove them so they never linger
    (the first real account created must be the admin)."""
    yield

    with engine.begin() as connection:
        connection.execute(text("DELETE FROM users WHERE email LIKE 'user-%@example.com'"))

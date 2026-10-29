from collections.abc import Generator
from pathlib import Path
from uuid import uuid4

import bcrypt
import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from business_layer.config import settings
from business_layer.dependencies import get_db
from business_layer.main import app
from database_persistent.db_config import Base
from database_persistent.models import User


@pytest.fixture
def api_env(monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
    database = Path.cwd() / f".api-integration-{uuid4().hex}.db"
    engine = create_engine(
        f"sqlite:///{database}",
        connect_args={"check_same_thread": False, "timeout": 10},
    )
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        session.add(
            User(
                username="operator",
                password_hash=bcrypt.hashpw(b"correct-password", bcrypt.gensalt()).decode("ascii"),
            )
        )
        session.commit()

    def override_get_db() -> Generator[Session, None, None]:
        with Session(engine) as session:
            try:
                yield session
                session.commit()
            except Exception:
                session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db
    monkeypatch.setattr(
        settings,
        "jwt_secret",
        SecretStr("integration-test-signing-key-32-bytes"),
    )
    client = TestClient(app, raise_server_exceptions=False)
    try:
        # Không dùng context manager của TestClient để lifespan không tác động DB local mặc định.
        yield client
    finally:
        client.close()
        app.dependency_overrides.clear()
        Base.metadata.drop_all(engine)
        engine.dispose()
        database.unlink(missing_ok=True)

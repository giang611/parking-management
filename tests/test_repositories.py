from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from business_layer.services.repository_ports import (
    ParkedVehicleRecord,
    UserCredentials,
)
from database_persistent.db_config import Base
from database_persistent.models import User
from database_persistent.repositories.user_repository import SqlAlchemyUserRepository
from database_persistent.repositories.vehicle_repository import (
    SqlAlchemyVehicleRepository,
)


@pytest.fixture
def session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with Session(engine) as db_session:
        yield db_session
    Base.metadata.drop_all(engine)
    engine.dispose()


def test_add_and_get_vehicle_round_trip_normalizes_time_to_utc(session):
    entered = datetime(2026, 10, 10, 10, 0, tzinfo=timezone(timedelta(hours=2)))
    record = ParkedVehicleRecord("T-100", "29A-12345", "car", entered)
    repository = SqlAlchemyVehicleRepository(session)

    assert repository.add(record) is True
    session.commit()

    actual = repository.get_by_ticket("T-100")
    assert actual == ParkedVehicleRecord(
        "T-100", "29A-12345", "car", datetime(2026, 10, 10, 8, 0, tzinfo=timezone.utc)
    )


def test_find_vehicle_requires_the_exact_ticket_plate_and_type(session):
    repository = SqlAlchemyVehicleRepository(session)
    record = ParkedVehicleRecord(
        "T-101", "29A-54321", "motorbike", datetime.now(timezone.utc)
    )
    repository.add(record)
    session.commit()

    assert repository.find_match("T-101", "29A-54321", "motorbike") == record
    assert repository.find_match("T-101", "29A-00000", "motorbike") is None
    assert repository.find_match("T-101", "29A-54321", "car") is None


def test_find_vehicle_matches_bicycle_with_null_plate(session):
    repository = SqlAlchemyVehicleRepository(session)
    record = ParkedVehicleRecord("T-102", None, "bicycle", datetime.now(timezone.utc))
    repository.add(record)
    session.commit()

    assert repository.find_match("T-102", None, "bicycle") == record


def test_duplicate_ticket_is_rejected_by_repository_and_database(session):
    repository = SqlAlchemyVehicleRepository(session)
    first = ParkedVehicleRecord("T-103", "30B-11111", "car", datetime.now(timezone.utc))
    duplicate = ParkedVehicleRecord(
        "T-103", "30B-22222", "car", datetime.now(timezone.utc)
    )

    assert repository.add(first) is True
    session.commit()
    assert repository.add(duplicate) is False
    assert repository.get_by_ticket("T-103") == first


def test_duplicate_ticket_does_not_rollback_other_pending_work(session):
    repository = SqlAlchemyVehicleRepository(session)
    first = ParkedVehicleRecord("T-105", "30B-33333", "car", datetime.now(timezone.utc))
    duplicate = ParkedVehicleRecord(
        "T-105", "30B-44444", "car", datetime.now(timezone.utc)
    )
    repository.add(first)
    session.commit()
    session.add(User(username="other-operator", password_hash="hash"))

    assert repository.add(duplicate) is False
    session.commit()
    assert session.get(User, 1) is not None


def test_delete_vehicle_removes_only_the_requested_ticket(session):
    repository = SqlAlchemyVehicleRepository(session)
    repository.add(
        ParkedVehicleRecord("T-104", None, "bicycle", datetime.now(timezone.utc))
    )
    session.commit()

    assert repository.delete_by_ticket("T-104") is True
    session.commit()
    assert repository.get_by_ticket("T-104") is None
    assert repository.delete_by_ticket("missing") is False


def test_list_page_returns_ticket_sorted_records_and_total(session):
    repository = SqlAlchemyVehicleRepository(session)
    now = datetime.now(timezone.utc)
    for ticket in ("T-list-c", "T-list-a", "T-list-b"):
        repository.add(ParkedVehicleRecord(ticket, None, "bicycle", now))
    session.commit()

    records, total = repository.list_page(limit=1, offset=1)

    assert [record.ticket for record in records] == ["T-list-b"]
    assert total == 3


def test_user_repository_returns_credentials_by_username(session):
    session.add(User(username="gatekeeper", password_hash="bcrypt-hash"))
    session.commit()
    repository = SqlAlchemyUserRepository(session)

    assert repository.get_by_username("gatekeeper") == UserCredentials(
        username="gatekeeper", password_hash="bcrypt-hash"
    )
    assert repository.get_by_username("unknown") is None


def test_two_concurrent_inserts_for_same_ticket_have_one_winner():
    database = Path.cwd() / f".race-{uuid4().hex}.db"
    engine = create_engine(
        f"sqlite:///{database}",
        connect_args={"check_same_thread": False, "timeout": 10},
    )
    Base.metadata.create_all(engine)
    barrier = Barrier(2)

    def insert(plate: str) -> bool:
        with Session(engine) as db_session:
            repository = SqlAlchemyVehicleRepository(db_session)
            barrier.wait(timeout=5)
            result = repository.add(
                ParkedVehicleRecord(
                    "T-race", plate, "car", datetime.now(timezone.utc)
                )
            )
            db_session.commit()
            return result

    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(insert, ["29A-10000", "29B-20000"]))
        assert sorted(outcomes) == [False, True]
        with Session(engine) as db_session:
            record = SqlAlchemyVehicleRepository(db_session).get_by_ticket("T-race")
            assert record is not None
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()
        database.unlink(missing_ok=True)

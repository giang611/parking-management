from datetime import datetime, timezone

import pytest

from business_layer.services.exceptions import BusinessError
from business_layer.services.parking_service import ParkingService
from business_layer.services.repository_ports import ParkedVehicleRecord


class MemoryVehicles:
    def __init__(self):
        self.records = {}

    def get_by_ticket(self, ticket):
        return self.records.get(ticket)

    def find_match(self, ticket, plate, vehicle_type):
        record = self.get_by_ticket(ticket)
        if record and (record.plate, record.vehicle_type) == (plate, vehicle_type):
            return record
        return None

    def add(self, record):
        if record.ticket in self.records:
            return False
        self.records[record.ticket] = record
        return True

    def delete_by_ticket(self, ticket):
        return self.records.pop(ticket, None) is not None


@pytest.fixture
def setup_service():
    repo = MemoryVehicles()
    now = datetime(2026, 10, 28, 12, 0, tzinfo=timezone.utc)
    return ParkingService(repo, clock=lambda: now), repo, now


def test_park_normalizes_plate_and_records_utc_time(setup_service):
    service, repo, now = setup_service

    record = service.park({"ticket": "T-1", "plate": "  29a-12345 ", "type": "car"})

    assert record == ParkedVehicleRecord("T-1", "29A-12345", "car", now)
    assert repo.get_by_ticket("T-1") == record


def test_park_accepts_bicycle_without_plate(setup_service):
    service, _, now = setup_service

    record = service.park({"ticket": "T-2", "type": "bicycle"})

    assert record == ParkedVehicleRecord("T-2", None, "bicycle", now)


@pytest.mark.parametrize("payload", [
    {"ticket": "T-1", "plate": "ABC", "type": "car", "charge": 100},
    {"ticket": "T-1", "type": "bicycle", "plate": None},
    {"ticket": "T-1", "type": "car"},
    {"ticket": "", "plate": "ABC", "type": "car"},
])
def test_park_rejects_invalid_payload(setup_service, payload):
    service, _, _ = setup_service
    with pytest.raises(BusinessError):
        service.park(payload)


def test_park_rejects_unsupported_type(setup_service):
    service, _, _ = setup_service
    with pytest.raises(BusinessError) as error:
        service.park({"ticket": "T-3", "plate": "ABC", "type": "truck"})
    assert error.value.code == "INVALID_TYPE"


def test_duplicate_ticket_is_reported_as_ticket_in_use(setup_service):
    service, _, _ = setup_service
    service.park({"ticket": "T-4", "plate": "ABC", "type": "car"})

    with pytest.raises(BusinessError) as error:
        service.park({"ticket": "T-4", "plate": "XYZ", "type": "car"})
    assert error.value.code == "TICKET_IN_USE"


def test_lookup_returns_record_without_removing_it(setup_service):
    service, repo, _ = setup_service
    service.park({"ticket": "T-5", "plate": "ABC", "type": "car"})

    found = service.lookup("T-5", {"plate": " abc ", "type": "car"})

    assert found.plate == "ABC"
    assert repo.get_by_ticket("T-5") == found


def test_lookup_wrong_vehicle_details_raise_not_found(setup_service):
    service, _, _ = setup_service
    service.park({"ticket": "T-6", "plate": "ABC", "type": "car"})

    with pytest.raises(BusinessError) as error:
        service.lookup("T-6", {"plate": "XYZ", "type": "car"})
    assert error.value.code == "VEHICLE_NOT_FOUND"


def test_retrieve_checks_details_then_deletes_record(setup_service):
    service, repo, _ = setup_service
    service.park({"ticket": "T-7", "plate": "ABC", "type": "car"})

    removed = service.retrieve("T-7", {"plate": " abc ", "type": "car"})

    assert removed.ticket == "T-7"
    assert repo.get_by_ticket("T-7") is None


def test_retrieve_wrong_details_does_not_delete_record(setup_service):
    service, repo, _ = setup_service
    service.park({"ticket": "T-8", "plate": "ABC", "type": "car"})

    with pytest.raises(BusinessError):
        service.retrieve("T-8", {"plate": "XYZ", "type": "car"})
    assert repo.get_by_ticket("T-8") is not None

@pytest.mark.parametrize("payload", [None, [], "invalid"])
def test_park_rejects_non_object_payload_with_domain_error(setup_service, payload):
    service, _, _ = setup_service
    with pytest.raises(BusinessError) as error:
        service.park(payload)
    assert error.value.code == "INVALID_FORMAT"


@pytest.mark.parametrize("query", [None, [], "invalid"])
def test_lookup_rejects_non_object_query_with_domain_error(setup_service, query):
    service, _, _ = setup_service
    with pytest.raises(BusinessError) as error:
        service.lookup("T-9", query)
    assert error.value.code == "INVALID_FORMAT"

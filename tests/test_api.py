from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from business_layer.api.errors import business_error_response, validation_error_response
from business_layer.api.parking_router import park_vehicle
from business_layer.main import app
from business_layer.schemas.auth_schemas import LoginRequest
from business_layer.schemas.parking_schemas import ParkEntryRequest
from business_layer.services.exceptions import BusinessError
from business_layer.services.parking_service import ParkingService
def login_headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "operator", "password": "correct-password"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_parking_request_schema_rejects_unknown_price_field():
    with pytest.raises(ValidationError):
        ParkEntryRequest.model_validate(
            {"ticket": "T-extra", "type": "car", "plate": "29A-12345", "charge": 100}
        )


def test_login_request_schema_rejects_unknown_fields():
    with pytest.raises(ValidationError):
        LoginRequest.model_validate(
            {"username": "operator", "password": "pw", "is_admin": True}
        )


def test_parking_route_preserves_explicit_null_plate_for_bicycle_validation():
    body = ParkEntryRequest(ticket="T-bike", type="bicycle", plate=None)

    class CaptureService:
        payload = None

        def park(self, payload):
            self.payload = payload

    service = CaptureService()
    park_vehicle(body, service)

    assert service.payload == {"ticket": "T-bike", "type": "bicycle", "plate": None}
    with pytest.raises(BusinessError) as error:
        ParkingService(None).park(service.payload)
    assert error.value.code == "PLATE_NOT_ALLOWED"


def test_business_error_response_has_flat_error_and_expected_status():
    response = business_error_response(BusinessError("TICKET_IN_USE"))

    assert response.status_code == 409
    assert response.body == b'{"error":"TICKET_IN_USE"}'


@pytest.mark.parametrize(
    "code,status",
    [
        ("INVALID_CREDENTIALS", 401),
        ("UNAUTHORIZED", 401),
        ("VEHICLE_NOT_FOUND", 404),
        ("TICKET_IN_USE", 409),
        ("INVALID_FORMAT", 400),
        ("INVALID_TYPE", 400),
        ("PLATE_REQUIRED", 422),
        ("PLATE_NOT_ALLOWED", 422),
    ],
)
def test_business_codes_map_to_documented_statuses(code, status):
    response = business_error_response(BusinessError(code))

    assert response.status_code == status
    assert response.body == f'{{"error":"{code}"}}'.encode()


def test_unauthorized_error_response_challenges_for_bearer():
    response = business_error_response(BusinessError("UNAUTHORIZED"))

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert response.body == b'{"error":"UNAUTHORIZED"}'


def test_format_validation_errors_map_to_bad_request():
    extra = validation_error_response([{"type": "extra_forbidden"}])
    malformed = validation_error_response([{"type": "missing"}])

    assert (extra.status_code, extra.body) == (400, b'{"error":"INVALID_FORMAT"}')
    assert (malformed.status_code, malformed.body) == (400, b'{"error":"INVALID_FORMAT"}')


def test_unknown_body_fields_are_rejected(api_env):
    response = api_env.post(
        "/api/v1/parking/entries",
        json={"ticket": "T-extra", "plate": "29A-12345", "type": "car", "charge": 100},
        headers=login_headers(api_env),
    )

    assert response.status_code == 400
    assert response.json() == {"error": "INVALID_FORMAT"}


def test_bicycle_with_explicit_null_plate_is_rejected(api_env):
    response = api_env.post(
        "/api/v1/parking/entries",
        json={"ticket": "T-bike", "type": "bicycle", "plate": None},
        headers=login_headers(api_env),
    )

    assert response.status_code == 422
    assert response.json() == {"error": "PLATE_NOT_ALLOWED"}


def test_invalid_body_without_token_returns_unauthorized_first(api_env):
    response = api_env.post("/api/v1/parking/entries", json={})

    assert response.status_code == 401
    assert response.json() == {"error": "UNAUTHORIZED"}


@pytest.mark.parametrize(
    "method,path,params,json_body",
    [
        ("post", "/api/v1/parking/entries", None, {}),
        ("get", "/api/v1/parking/entries/T-unauthorized", {"type": "car"}, None),
        ("delete", "/api/v1/parking/entries/T-unauthorized", {"type": "car"}, None),
    ],
)
def test_all_parking_operations_require_authentication(
    api_env, method, path, params, json_body
):
    kwargs = {"params": params}
    if method == "post":
        kwargs["json"] = json_body
    response = getattr(api_env, method)(path, **kwargs)

    assert response.status_code == 401
    assert response.json() == {"error": "UNAUTHORIZED"}


def test_parking_endpoints_lookup_without_deleting_then_retrieve(api_env):
    headers = login_headers(api_env)
    parked = api_env.post(
        "/api/v1/parking/entries",
        json={"ticket": "T-roundtrip", "type": "car", "plate": " 29a-12345 "},
        headers=headers,
    )
    assert parked.status_code == 204
    assert parked.content == b""

    found = api_env.get(
        "/api/v1/parking/entries/T-roundtrip",
        params={"type": "car", "plate": "29a-12345"},
        headers=headers,
    )
    assert found.status_code == 200
    assert found.json()["plate"] == "29A-12345"
    assert "charge" not in found.json()

    mismatch = api_env.get(
        "/api/v1/parking/entries/T-roundtrip",
        params={"type": "car", "plate": "29A-00000"},
        headers=headers,
    )
    assert mismatch.status_code == 404
    assert mismatch.json() == {"error": "VEHICLE_NOT_FOUND"}

    removed = api_env.delete(
        "/api/v1/parking/entries/T-roundtrip",
        params={"type": "car", "plate": "29a-12345"},
        headers=headers,
    )
    assert removed.status_code == 200
    assert removed.json() == {"ticket": "T-roundtrip"}

    missing = api_env.get(
        "/api/v1/parking/entries/T-roundtrip",
        params={"type": "car", "plate": "29A-12345"},
        headers=headers,
    )
    assert missing.status_code == 404
    assert missing.json() == {"error": "VEHICLE_NOT_FOUND"}


def test_duplicate_ticket_returns_conflict(api_env):
    headers = login_headers(api_env)
    payload = {"ticket": "T-duplicate", "type": "motorbike", "plate": "59A-10000"}

    assert api_env.post("/api/v1/parking/entries", json=payload, headers=headers).status_code == 204
    duplicate = api_env.post("/api/v1/parking/entries", json=payload, headers=headers)

    assert duplicate.status_code == 409
    assert duplicate.json() == {"error": "TICKET_IN_USE"}


def test_concurrent_posts_for_same_ticket_have_one_success_and_one_conflict(api_env):
    headers = login_headers(api_env)
    payload = {"ticket": "T-race-api", "type": "car", "plate": "29A-55555"}
    barrier = Barrier(2)

    def post_entry():
        client = TestClient(app, raise_server_exceptions=False)
        barrier.wait(timeout=5)
        try:
            return client.post(
                "/api/v1/parking/entries", json=payload, headers=headers
            )
        finally:
            client.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(lambda _: post_entry(), range(2)))

    assert sorted(response.status_code for response in responses) == [204, 409]
    conflict = next(response for response in responses if response.status_code == 409)
    assert conflict.json() == {"error": "TICKET_IN_USE"}


def test_list_parked_vehicles_returns_a_paginated_page(api_env):
    headers = login_headers(api_env)
    for ticket in ("T-page-c", "T-page-a", "T-page-b"):
        response = api_env.post(
            "/api/v1/parking/entries",
            json={"ticket": ticket, "type": "bicycle"},
            headers=headers,
        )
        assert response.status_code == 204

    response = api_env.get(
        "/api/v1/parking/entries",
        params={"limit": 1, "offset": 1},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {
                "ticket": "T-page-b",
                "plate": None,
                "type": "bicycle",
                "time_in": response.json()["items"][0]["time_in"],
            }
        ],
        "limit": 1,
        "offset": 1,
        "total": 3,
    }


def test_list_parked_vehicles_requires_authentication(api_env):
    response = api_env.get("/api/v1/parking/entries")

    assert response.status_code == 401
    assert response.json() == {"error": "UNAUTHORIZED"}


def test_unknown_route_uses_flat_not_found_error(api_env):
    headers = login_headers(api_env)

    response = api_env.get("/api/v1/nope", headers=headers)

    assert response.status_code == 404
    assert response.json() == {"error": "NOT_FOUND"}


def test_unsupported_method_uses_flat_method_not_allowed_error(api_env):
    headers = login_headers(api_env)

    response = api_env.put("/api/v1/parking/entries", headers=headers)

    assert response.status_code == 405
    assert response.json() == {"error": "METHOD_NOT_ALLOWED"}


def test_openapi_exposes_auth_and_parking_operations():
    schema = app.openapi()
    paths = schema["paths"]
    assert "/api/v1/auth/login" in paths
    assert "/api/v1/parking/entries" in paths
    assert "/api/v1/parking/entries/{ticket}" in paths
    assert paths["/api/v1/parking/entries"]["post"]["security"]
    assert paths["/api/v1/parking/entries"]["get"]["security"]
    assert "HTTPBearer" in schema["components"]["securitySchemes"]


def test_openapi_documents_api_error_envelopes():
    paths = app.openapi()["paths"]
    login_responses = paths["/api/v1/auth/login"]["post"]["responses"]
    parking = paths["/api/v1/parking/entries"]
    ticket = paths["/api/v1/parking/entries/{ticket}"]

    assert "401" in login_responses
    for operation in (parking["post"], parking["get"], ticket["get"], ticket["delete"]):
        for status in ("400", "401", "422"):
            assert status in operation["responses"]
            schema_ref = operation["responses"][status]["content"]["application/json"]["schema"]["$ref"]
            assert schema_ref.endswith("/ErrorResponse")
    assert "409" in parking["post"]["responses"]
    assert "404" in ticket["get"]["responses"]
    assert "404" in ticket["delete"]["responses"]

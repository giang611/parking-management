import io
import json
from urllib.error import HTTPError

import pytest

from gate_client import gate_simulation


class FakeResponse:
    def __init__(self, payload: bytes, status: int = 200):
        self._payload = payload
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return self._payload


def test_login_returns_token_and_does_not_send_authorization(monkeypatch):
    captured = {}

    def fake_urlopen(request, timeout):
        captured["request"] = request
        captured["timeout"] = timeout
        return FakeResponse(b'{"access_token":"jwt","token_type":"Bearer","expires_in":3600}')

    monkeypatch.setattr(gate_simulation, "urlopen", fake_urlopen)
    client = gate_simulation.GateApiClient("http://localhost:8000")

    result = client.login("operator", "secret")

    request = captured["request"]
    assert result["access_token"] == "jwt"
    assert request.full_url == "http://localhost:8000/api/v1/auth/login"
    assert request.get_header("Authorization") is None
    assert json.loads(request.data) == {"username": "operator", "password": "secret"}


def test_parking_bicycle_omits_plate_and_uses_bearer_token(monkeypatch):
    captured = {}

    def fake_urlopen(request, timeout):
        captured["request"] = request
        return FakeResponse(b"", status=204)

    monkeypatch.setattr(gate_simulation, "urlopen", fake_urlopen)
    client = gate_simulation.GateApiClient("http://localhost:8000")
    client._token = "jwt"

    result = client.park("T-bike", "bicycle")

    request = captured["request"]
    assert result is None
    assert request.get_method() == "POST"
    assert request.get_header("Authorization") == "Bearer jwt"
    assert json.loads(request.data) == {"ticket": "T-bike", "type": "bicycle"}


def test_lookup_and_retrieve_send_vehicle_query(monkeypatch):
    captured = []
    responses = [
        FakeResponse(b'{"ticket":"T-1","plate":"29A-12345","type":"car","time_in":"2026-10-10T08:00:00Z"}'),
        FakeResponse(b'{"ticket":"T-1"}'),
    ]

    def fake_urlopen(request, timeout):
        captured.append(request)
        return responses.pop(0)

    monkeypatch.setattr(gate_simulation, "urlopen", fake_urlopen)
    client = gate_simulation.GateApiClient("http://localhost:8000")
    client._token = "jwt"

    found = client.lookup("T-1", "car", "29A-12345")
    removed = client.retrieve("T-1", "car", "29A-12345")

    assert found["ticket"] == "T-1"
    assert removed == {"ticket": "T-1"}
    assert captured[0].full_url.endswith("?type=car&plate=29A-12345")
    assert captured[1].get_method() == "DELETE"


def test_http_error_exposes_flat_api_code(monkeypatch):
    def fake_urlopen(_request, timeout):
        raise HTTPError(
            "http://localhost:8000/api/v1/nope",
            404,
            "Not Found",
            {},
            io.BytesIO(b'{"error":"NOT_FOUND"}'),
        )

    monkeypatch.setattr(gate_simulation, "urlopen", fake_urlopen)
    client = gate_simulation.GateApiClient("http://localhost:8000")

    with pytest.raises(gate_simulation.GateApiError) as error:
        client.login("operator", "secret")

    assert error.value.status_code == 404
    assert error.value.code == "NOT_FOUND"

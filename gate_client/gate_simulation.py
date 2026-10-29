"""Chương trình tương tác mô phỏng máy Gate gọi API quản lý bãi xe."""

from __future__ import annotations

import argparse
import getpass
import json
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen


class GateApiError(Exception):
    """Lỗi API gồm mã HTTP và mã lỗi ổn định."""

    def __init__(self, status_code: int, code: str):
        self.status_code = status_code
        self.code = code
        super().__init__(f"HTTP {status_code}: {code}")


class GateApiClient:
    """HTTP client gọn, chỉ dùng thư viện chuẩn, cho chương trình mô phỏng Gate."""

    def __init__(self, base_url: str, timeout: float = 10.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._token: str | None = None

    def login(self, username: str, password: str) -> dict[str, Any]:
        response = self._request(
            "POST",
            "/api/v1/auth/login",
            payload={"username": username, "password": password},
            authenticated=False,
        )
        if not isinstance(response, dict) or not response.get("access_token"):
            raise GateApiError(502, "INVALID_RESPONSE")
        self._token = str(response["access_token"])
        return response

    def park(
        self, ticket: str, vehicle_type: str, plate: str | None = None
    ) -> None:
        payload: dict[str, str] = {"ticket": ticket, "type": vehicle_type}
        if plate is not None:
            payload["plate"] = plate
        self._request("POST", "/api/v1/parking/entries", payload=payload)

    def lookup(
        self, ticket: str, vehicle_type: str, plate: str | None = None
    ) -> dict[str, Any]:
        return self._request(
            "GET",
            self._entry_path(ticket, vehicle_type, plate),
        )

    def retrieve(
        self, ticket: str, vehicle_type: str, plate: str | None = None
    ) -> dict[str, Any]:
        return self._request(
            "DELETE",
            self._entry_path(ticket, vehicle_type, plate),
        )

    @staticmethod
    def _entry_path(ticket: str, vehicle_type: str, plate: str | None) -> str:
        query = {"type": vehicle_type}
        if plate is not None:
            query["plate"] = plate
        return f"/api/v1/parking/entries/{quote(ticket, safe='')}?{urlencode(query)}"

    def _request(
        self,
        method: str,
        path: str,
        *,
        payload: dict[str, str] | None = None,
        authenticated: bool = True,
    ) -> Any:
        headers = {"Accept": "application/json"}
        body = None
        if payload is not None:
            headers["Content-Type"] = "application/json"
            body = json.dumps(payload).encode("utf-8")
        if authenticated:
            if not self._token:
                raise RuntimeError("Đăng nhập trước khi gọi nghiệp vụ bãi xe.")
            headers["Authorization"] = f"Bearer {self._token}"

        request = Request(
            self.base_url + path,
            data=body,
            headers=headers,
            method=method,
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                raw = response.read()
                status = response.status
        except HTTPError as error:
            raw = error.read()
            try:
                detail = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                detail = {}
            code = detail.get("error", "HTTP_ERROR") if isinstance(detail, dict) else "HTTP_ERROR"
            raise GateApiError(error.code, str(code)) from None
        except URLError as error:
            raise ConnectionError(f"Không kết nối được Backend: {error.reason}") from error

        if not raw:
            return None
        try:
            return json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise GateApiError(status, "INVALID_RESPONSE") from None


def _prompt_vehicle() -> tuple[str, str, str | None]:
    ticket = input("Mã vé: ").strip()
    vehicle_type = input("Loại xe (car/motorbike/bicycle): ").strip().lower()
    plate = None
    if vehicle_type != "bicycle":
        plate = input("Biển số: ").strip()
    return ticket, vehicle_type, plate


def run_interactive(base_url: str) -> int:
    username = os.getenv("ADMIN_USERNAME") or input("Tên đăng nhập: ").strip()
    password = os.getenv("ADMIN_PASSWORD") or getpass.getpass("Mật khẩu: ")
    client = GateApiClient(base_url)
    try:
        token = client.login(username, password)
    except (GateApiError, ConnectionError) as error:
        print(f"Đăng nhập thất bại: {error}")
        return 1

    print(
        "Đăng nhập thành công. "
        f"Token có hiệu lực {token.get('expires_in', 'không rõ')} giây."
    )
    while True:
        choice = input("\n1 Gửi xe | 2 Tra cứu | 3 Lấy xe | q Thoát: ").strip().lower()
        if choice in {"q", "quit", "exit"}:
            return 0
        if choice not in {"1", "2", "3"}:
            print("Chọn 1, 2, 3 hoặc q.")
            continue

        ticket, vehicle_type, plate = _prompt_vehicle()
        try:
            if choice == "1":
                client.park(ticket, vehicle_type, plate)
                print("Gửi xe thành công.")
            elif choice == "2":
                print(json.dumps(client.lookup(ticket, vehicle_type, plate), indent=2, ensure_ascii=False))
            else:
                result = client.retrieve(ticket, vehicle_type, plate)
                print(f"Lấy xe thành công. Mã vé: {result.get('ticket', ticket)}")
        except (GateApiError, ConnectionError, RuntimeError) as error:
            print(f"Thao tác thất bại: {error}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base-url",
        default=os.getenv("BASE_URL", "http://127.0.0.1:8000"),
        help="Địa chỉ Backend (mặc định: BASE_URL hoặc http://127.0.0.1:8000)",
    )
    args = parser.parse_args()
    return run_interactive(args.base_url)


if __name__ == "__main__":
    raise SystemExit(main())

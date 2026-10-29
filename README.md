# Parking Management System (TCP)

A small Python parking-lot application for a software architecture assignment. It supports vehicle entry, fee quotation, payment confirmation, and revenue queries. The system uses a custom line-based TCP protocol with JSON payloads where needed; it is **not HTTP/REST**.

## Architecture

The project separates networking, request handling, business rules, and persistence:

- `network.py` — accepts TCP connections and reads/writes newline-delimited messages.
- `main.py` — parses requests, checks authentication for each request, and dispatches operations.
- `business.py` — validates vehicle data, calculates fees, and interprets revenue periods.
- `database.py` — performs SQLite operations and manages database connections.
- `client.py` — command-line client for gate/operator workflows.
- `config.json` — server host/port, password, hourly rates, and SQLite database filename.
- `api_spec.json` — concise protocol and API specification.

The business layer does not handle sockets or execute SQL directly; database access is delegated to `database.py`.

## Requirements and launch

Requires Python 3. No third-party packages are required for the basic application.

Start the server:

```bash
python main.py
```

In another terminal, start the client:

```bash
python client.py
```

Default settings are password `123` and TCP port `8765`. The server listens on the host configured in `config.json`. To connect from another computer on the same LAN, enter the server computer's LAN IP in the client and allow the configured TCP port through the server firewall.

## Protocol overview

Messages are UTF-8 text, terminated by a newline. Each request receives one response line.

- Request: `METHOD/resource/payload[/auth/password]`
- Response: `STATUS/JSON`
- `204/{}` indicates success without a response body.

Example requests:

```text
POST/auth/123
POST/vehicle/{"ticket":1001,"plate":"30A-12345","type":"CAR"}/auth/123
GET/vehicle/{"ticket":1001,"plate":"30A-12345","type":"CAR"}/auth/123
DELETE/vehicle/{"ticket":1001}/auth/123
GET/revenue/today/auth/123
```

The supported operations are password checking, vehicle entry, fee quotation, payment confirmation/removal, and revenue lookup. Revenue periods are `today`, `yesterday`, `this-week`, `last-week`, `this-month`, and `last-month`. Vehicle types are `CAR`, `MOTORCYCLE`, and `BICYCLE`. Bicycles must not have a plate; cars and motorcycles require one. See `api_spec.json` for the complete request formats, response meanings, and status codes.

## Fee and payment flow

The fee is calculated as:

```text
charge = ceil(elapsed_seconds / 3600) * hourly_rate
```

An active ticket is charged for at least one hour. Hourly rates are configured in `config.json`.

The client first sends `GET/vehicle` to retrieve a fee quotation. This request is read-only: it does not remove the vehicle or record revenue. After the operator confirms that payment was received, the client sends `DELETE/vehicle`. The server recalculates the amount and records the payment while removing the active ticket in one database transaction; the client does not supply a trusted payment amount.

## Tests and container

Run the unit tests with:

```bash
python -m unittest discover -s tests -v
```

A `Dockerfile` is included for containerizing the server. Configure the port and persistent storage appropriately when running it in Docker.

## Limitations

This is a classroom/demo protocol, not a production-secure service. The password is sent as plain text, and the protocol does not provide TLS, encryption, or a session system. Use it only in a trusted local environment; do not expose it to untrusted networks without adding suitable security controls.

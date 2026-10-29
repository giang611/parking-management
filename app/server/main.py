"""Application entry point: parse protocol, authenticate each request, call modules."""
import json

import business
import database
import network

CONFIG_FILE = "config.json"


def load_config():
    with open(CONFIG_FILE, "r", encoding="utf-8") as file:
        return json.load(file)

def response(status, body=None):
    return f"{status}/{json.dumps(body or {}, ensure_ascii=False, separators=(',', ':'))}"


def parse_request(raw):
    # Protocol: METHOD/resource/payload/auth/password
    # For revenue: GET/revenue/period/auth/password
    parts = raw.split("/", 4)
    if len(parts) < 3:
        raise business.BusinessError(400, "malformed request")
    method, resource, payload = parts[:3]
    auth = None
    if len(parts) == 5 and parts[3] == "auth":
        auth = parts[4]
    elif len(parts) != 3:
        raise business.BusinessError(400, "malformed request")
    return method.upper(), resource, payload, auth


def handle_request(raw):
    config = load_config()
    try:
        method, resource, payload, auth = parse_request(raw)

        if method == "POST" and resource == "auth":
            # POST/auth/password only checks the password; no session is created.
            if payload == config["password"]:
                return response(204)
            return response(401, {"error": "invalid password"})

        if auth is None or auth != config["password"]:
            return response(401, {"error": "authentication required"})

        if method == "POST" and resource == "vehicle":
            data = json.loads(payload)
            result = business.park(data)
        elif method == "GET" and resource == "vehicle":
            data = json.loads(payload)
            result = business.quote(data, config["rates_per_hour"])
        elif method == "DELETE" and resource == "vehicle":
            data = json.loads(payload)
            result = business.collect(data, config["rates_per_hour"])
        elif method == "GET" and resource == "revenue":
            result = business.revenue_period(payload)
        else:
            raise business.BusinessError(400, "unknown method or resource")

        body = result["body"]
        if body and "currency" in body:
            body["currency"] = config["currency"]
        return response(result["status"], body)
    except business.BusinessError as exc:
        return response(exc.status, {"error": exc.message})
    except (json.JSONDecodeError, TypeError, ValueError):
        return response(400, {"error": "malformed request"})


def main():
    config = load_config()
    database.configure(config["database"])
    database.init()
    print(f"Parking server: {network.local_ip()}:{config['port']}")
    network.serve(config["host"], config["port"], handle_request)


if __name__ == "__main__":
    main()

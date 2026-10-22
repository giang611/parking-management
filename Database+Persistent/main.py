import json

import database
from network import NetworkServer

#Translate a network message into a database operation.
def process_message(message):
    command, payload = message.split(b"\r", 1)

    command = command.decode("ascii")
    data = json.loads(payload.decode("utf-8"))

    if command == "GET":
        vehicle = database.get(data["ticket"])

        if vehicle is None:
            return make_response(404, {"error": "Ticket not found"})

        # Optional plate/type validation.
        if "plate" in data or "type" in data:
            if (
                data["plate"] != vehicle["plate"]
                or data["type"] != vehicle["type"]
            ):
                return make_response(
                    404, {"error": "Vehicle and ticket do not match"}
                )

        return make_response(200, {
            "type": vehicle["type"],
            "time_in": vehicle["IN_TIME"],
        })

    elif command == "POST":
        success = database.post(
            data["ticket"],
            data["plate"],
            data["type"],
            data["time_in"],
        )

        if success:
            return make_response(204)

        return make_response(404, {"error": "Vehicle registration failed"})

    elif command == "DELETE":
        success = database.delete(data["ticket"])

        if success:
            return make_response(204)

        return make_response(404, {"error": "Ticket not found"})

    return make_response(404, {"error": "Unknown command"})


def make_response(status, body=None):
    message = str(status) + "\r"

    if body is not None:
        message += json.dumps(body, separators=(",", ":"))

    return (message + "\n").encode("utf-8")


if __name__ == "__main__":
    database.init()
    server = NetworkServer()

    try:
        server.start(process_message)
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        server.stop()
        database.close()

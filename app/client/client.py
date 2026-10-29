"""Small terminal client for the Gate PC."""
import json
import network


def request(host, port, raw):
    return network.send_request(host, port, raw)


def vehicle_input():
    ticket = int(input("Ticket ID: "))
    vehicle_type = input("Type (CAR/MOTORCYCLE/BICYCLE): ").strip().upper()
    plate = input("Plate (leave empty for bicycle): ").strip() or None
    return {"ticket": ticket, "plate": plate, "type": vehicle_type}


def main():
    host = input("Server IP [127.0.0.1]: ").strip() or "127.0.0.1"
    try:
        port = int(input("Server port [8765]: ").strip() or "8765")
    except ValueError:
        print("Invalid port")
        return

    password = input("Password: ").strip()
    auth_result = request(host, port, f"POST/auth/{password}")
    if not auth_result.startswith("204/"):
        print("Authentication failed:", auth_result)
        return
    print("Password accepted")

    while True:
        print("\n1. Park vehicle  2. Get vehicle, pay and exit  3. Revenue  0. Exit")
        choice = input("> ").strip()
        if choice == "0":
            break
        try:
            if choice == "1":
                data = vehicle_input()
                payload = json.dumps(data, separators=(",", ":"))
                print(request(host, port, f"POST/vehicle/{payload}/auth/{password}"))

            elif choice == "2":
                data = vehicle_input()
                payload = json.dumps(data, separators=(",", ":"))
                quote = request(host, port, f"GET/vehicle/{payload}/auth/{password}")
                print(quote)

                # GET only quotes the fee. It never deletes the ticket or records revenue.
                if not quote.startswith("200/"):
                    continue

                input("Press Enter after payment is received to confirm exit...")
                delete_payload = json.dumps(data, separators=(",", ":"))
                result = request(
                    host, port, f"DELETE/vehicle/{delete_payload}/auth/{password}"
                )
                print(result)

            elif choice == "3":
                period = input(
                    "Period (today/yesterday/this-week/last-week/this-month/last-month): "
                ).strip()
                print(request(host, port, f"GET/revenue/{period}/auth/{password}"))
            else:
                print("Unknown choice")
        except (ValueError, OSError, ConnectionError) as exc:
            print("Request failed:", exc)


if __name__ == "__main__":
    main()

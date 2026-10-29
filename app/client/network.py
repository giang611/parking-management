"""TCP transport only: receive and send newline-delimited raw text."""
import socket


def serve(host, port, handle_request):
    """Accept clients and pass each raw line to handle_request(raw_text)."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((host, port))
        server.listen()
        print(f"Parking server listening on {host}:{port}")

        while True:
            client, address = server.accept()
            with client:
                #print(f"Connected: {address}")
                stream = client.makefile("rwb")
                while True:
                    line = stream.readline()
                    if not line:
                        break
                    try:
                        request = line.decode("utf-8").rstrip("\r\n")
                        response = handle_request(request)
                        if not isinstance(response, str):
                            response = "500/{}"
                    except Exception:
                        response = '500/{"error":"Internal server error"}'
                    stream.write((response + "\n").encode("utf-8"))
                    stream.flush()


def send_request(host, port, raw_text):
    """Send one raw request line and return one raw response line."""
    with socket.create_connection((host, port)) as client:
        stream = client.makefile("rwb")
        stream.write((raw_text.rstrip("\r\n") + "\n").encode("utf-8"))
        stream.flush()
        response = stream.readline()
        if not response:
            raise ConnectionError("Server closed the connection without a response")
        return response.decode("utf-8").rstrip("\r\n")

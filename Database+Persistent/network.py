import socket


class NetworkServer:
    def __init__(self, host="0.0.0.0", port=5000):
        self.host = host
        self.port = port
        self.server_socket = None
        self.running = False

    def start(self, on_message):
        """Listen for clients and pass each complete message to a handler."""
        self.server_socket = socket.socket(
            socket.AF_INET, socket.SOCK_STREAM
        )
        self.server_socket.setsockopt(
            socket.SOL_SOCKET, socket.SO_REUSEADDR, 1
        )
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        self.running = True

        print(f"Listening on {self.host}:{self.port}")

        try:
            while self.running:
                client, address = self.server_socket.accept()
                print(f"Connected: {address}")

                with client:
                    self.handle_client(client, on_message)

        except OSError:
            if self.running:
                raise
        finally:
            self.stop()

    def handle_client(self, client, on_message):
        buffer = b""

        while self.running:
            data = client.recv(4096)
            if not data:
                break

            buffer += data

            while b"\n" in buffer:
                message, buffer = buffer.split(b"\n", 1)
                if message:
                    response = on_message(message.rstrip(b"\r"))
                    client.sendall(response)

    def stop(self):
        self.running = False

        if self.server_socket is not None:
            self.server_socket.close()
            self.server_socket = None
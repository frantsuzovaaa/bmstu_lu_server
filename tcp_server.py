from __future__ import annotations

import logging
import socket
import threading

from protocol import dumps_response, handle_request


BUFFER_SIZE = 4096
CLIENT_TIMEOUT_SECONDS = 10


class TcpLuServer:
    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port

    def serve_forever(self) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((self.host, self.port))
            server_socket.listen()

            logging.info("Сервер запущен на %s:%s", self.host, self.port)

            while True:
                client_socket, address = server_socket.accept()
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, address),
                    daemon=True,
                )
                client_thread.start()

    def _handle_client(self, client_socket: socket.socket, address: tuple[str, int]) -> None:
        with client_socket:
            client_socket.settimeout(CLIENT_TIMEOUT_SECONDS)
            logging.info("Клиент подключился: %s:%s", address[0], address[1])

            try:
                self._handle_request(client_socket, address)
            except socket.timeout:
                logging.warning("Таймаут запроса от клиента %s:%s", address[0], address[1])
                timeout_response = {
                    "status": "error",
                    "error_code": "REQUEST_TIMEOUT",
                    "message": "Таймаут запроса",
                }
                self._send_error_response(client_socket, timeout_response)
            except OSError:
                logging.error("Ошибка сокета при обработке клиента %s:%s", address[0], address[1])
            except Exception:
                logging.error("Внутренняя ошибка при обработке клиента %s:%s", address[0], address[1])
                fallback = {
                    "status": "error",
                    "error_code": "INTERNAL_ERROR",
                    "message": "Internal server error",
                }
                self._send_error_response(client_socket, fallback)

    def _handle_request(self, client_socket: socket.socket, address: tuple[str, int]) -> None:
        raw_request = self._read_request(client_socket)
        if not raw_request:
            logging.warning("Пустой запрос от клиента %s:%s", address[0], address[1])

        response = handle_request(raw_request)
        encoded_response = dumps_response(response).encode("utf-8")
        client_socket.sendall(encoded_response)

        if response.get("status") == "ok":
            logging.info("Запрос обработан: клиент=%s:%s", address[0], address[1])
        else:
            logging.warning("Ошибка запроса от клиента %s:%s: %s", address[0], address[1], response.get("error_code"))

    def _send_error_response(
        self,
        client_socket: socket.socket,
        response: dict[str, str],
    ) -> None:
        try:
            client_socket.sendall(dumps_response(response).encode("utf-8"))
        except OSError:
            logging.error("Не удалось отправить клиенту ответ об ошибке")

    def _read_request(self, client_socket: socket.socket) -> str:
        chunks: list[bytes] = []

        while True:
            chunk = client_socket.recv(BUFFER_SIZE)
            if not chunk:
                break

            newline_index = chunk.find(b"\n")
            if newline_index >= 0:
                chunks.append(chunk[:newline_index])
                break

            chunks.append(chunk)

        return b"".join(chunks).decode("utf-8")

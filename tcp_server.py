from __future__ import annotations

import logging
import socket

from protocol import dumps_response, handle_request


BUFFER_SIZE = 4096


class TcpLuServer:
    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port

    def serve_forever(self) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((self.host, self.port))
            server_socket.listen()

            logging.info("TCP-сервер LU-разложения слушает %s:%s", self.host, self.port)

            while True:
                client_socket, address = server_socket.accept()
                with client_socket:
                    logging.info("Клиент подключился: %s:%s", address[0], address[1])
                    self._handle_client(client_socket)

    def _handle_client(self, client_socket: socket.socket) -> None:
        try:
            raw_request = self._read_request(client_socket)
            response = handle_request(raw_request)
            client_socket.sendall(dumps_response(response).encode("utf-8"))

            if response.get("status") == "ok":
                logging.info("Запрос успешно обработан")
            else:
                logging.warning(
                    "Ошибка обработки запроса: %s %s",
                    response.get("error_code"),
                    response.get("message"),
                )
        except OSError:
            logging.exception("Ошибка сокета при обработке клиента")
        except Exception:
            logging.exception("Непредвиденная ошибка при обработке клиента")
            fallback = {
                "status": "error",
                "error_code": "INTERNAL_ERROR",
                "message": "Внутренняя ошибка сервера",
            }
            try:
                client_socket.sendall(dumps_response(fallback).encode("utf-8"))
            except OSError:
                logging.exception("Не удалось отправить ответ о внутренней ошибке")

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

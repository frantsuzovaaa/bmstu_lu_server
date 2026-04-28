from __future__ import annotations

import json
import math
from dataclasses import dataclass
from typing import Any

from lu_core import ComputationError, decompose_lu


MAX_MATRIX_SIZE = 200

BAD_REQUEST = "BAD_REQUEST"
VALIDATION_ERROR = "VALIDATION_ERROR"
COMPUTATION_ERROR = "COMPUTATION_ERROR"
INTERNAL_ERROR = "INTERNAL_ERROR"


@dataclass
class MatrixRequest:
    matrix_size: int
    matrix: list[list[float]]


class RequestError(Exception):
    error_code = BAD_REQUEST

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class BadRequestError(RequestError):
    error_code = BAD_REQUEST


class ValidationError(RequestError):
    error_code = VALIDATION_ERROR


def parse_request(raw_request: str) -> MatrixRequest:
    try:
        data = json.loads(raw_request)
    except json.JSONDecodeError as exc:
        raise BadRequestError("Некорректный JSON-запрос") from exc

    if not isinstance(data, dict):
        raise BadRequestError("Запрос должен быть JSON-объектом")

    return validate_request(data)


def validate_request(data: dict[str, Any]) -> MatrixRequest:
    if "matrix_size" not in data:
        raise BadRequestError("Отсутствует поле matrix_size")
    if "matrix" not in data:
        raise BadRequestError("Отсутствует поле matrix")

    matrix_size = data["matrix_size"]
    matrix = data["matrix"]

    if isinstance(matrix_size, bool) or not isinstance(matrix_size, int):
        raise ValidationError("matrix_size должен быть положительным целым числом")
    if matrix_size <= 0:
        raise ValidationError("matrix_size должен быть положительным целым числом")
    if matrix_size > MAX_MATRIX_SIZE:
        raise ValidationError("Размер матрицы должен быть в диапазоне 1..200")

    if not isinstance(matrix, list) or not matrix:
        raise ValidationError("Матрица должна быть непустым двумерным массивом")
    if len(matrix) != matrix_size:
        raise ValidationError("Количество строк матрицы должно совпадать с matrix_size")

    validated_matrix: list[list[float]] = []
    for row in matrix:
        if not isinstance(row, list):
            raise ValidationError("Матрица должна быть двумерным массивом")
        if len(row) != matrix_size:
            raise ValidationError("Матрица должна быть квадратной")

        validated_row: list[float] = []
        for value in row:
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValidationError("Элементы матрицы должны быть числами")
            numeric_value = float(value)
            if not math.isfinite(numeric_value):
                raise ValidationError("Элементы матрицы должны быть конечными числами")
            validated_row.append(numeric_value)

        validated_matrix.append(validated_row)

    return MatrixRequest(matrix_size=matrix_size, matrix=validated_matrix)


def build_success_response(l_matrix: list[list[float]], u_matrix: list[list[float]]) -> dict[str, Any]:
    return {
        "status": "ok",
        "message": "LU-разложение выполнено",
        "result": {
            "L": l_matrix,
            "U": u_matrix,
        },
    }


def build_error_response(error_code: str, message: str) -> dict[str, str]:
    return {
        "status": "error",
        "error_code": error_code,
        "message": message,
    }


def dumps_response(response: dict[str, Any]) -> str:
    return json.dumps(response, ensure_ascii=False, separators=(",", ":")) + "\n"


def handle_request(raw_request: str) -> dict[str, Any]:
    try:
        request = parse_request(raw_request)
        l_matrix, u_matrix = decompose_lu(request.matrix)
        return build_success_response(l_matrix, u_matrix)
    except RequestError as exc:
        return build_error_response(exc.error_code, exc.message)
    except ComputationError:
        return build_error_response(
            COMPUTATION_ERROR,
            "Не удалось выполнить LU-разложение для переданной матрицы",
        )
    except Exception:
        return build_error_response(INTERNAL_ERROR, "Внутренняя ошибка сервера")

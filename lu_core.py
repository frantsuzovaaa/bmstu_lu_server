from __future__ import annotations

from typing import Iterable

import numpy as np


PIVOT_EPSILON = 1e-12


class ComputationError(Exception):
    pass


def decompose_lu(matrix: Iterable[Iterable[float]]) -> tuple[list[list[float]], list[list[float]]]:
    a = np.array(matrix, dtype=float, copy=True)
    n = a.shape[0]

    try:
        for k in range(n):
            pivot = a[k, k]
            if abs(pivot) < PIVOT_EPSILON:
                raise ComputationError("Ведущий элемент равен нулю или слишком мал")

            for i in range(k + 1, n):
                a[i, k] = a[i, k] / pivot
                for j in range(k + 1, n):
                    a[i, j] = a[i, j] - a[i, k] * a[k, j]
    except ComputationError:
        raise
    except Exception as exc:
        raise ComputationError("Непредвиденная ошибка LU-разложения") from exc

    l = np.eye(n, dtype=float)
    u = np.zeros((n, n), dtype=float)

    for i in range(n):
        for j in range(n):
            if i > j:
                l[i, j] = a[i, j]
            else:
                u[i, j] = a[i, j]

    return l.tolist(), u.tolist()

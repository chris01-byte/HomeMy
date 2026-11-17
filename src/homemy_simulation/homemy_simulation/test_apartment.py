"""A small synthetic apartment as an OccupancyGrid cell list.

The same layout as the app's mock bridge, so that both look alike in the app.
All data is synthetic; it is not a real home.
"""

from __future__ import annotations

from typing import Optional

WIDTH = 48
HEIGHT = 36
RESOLUTION = 0.10
ORIGIN = (-2.4, -1.8, 0.0)


def _fill(cells: list[int], x_min: int, y_min: int, x_max: int, y_max: int, value: int) -> None:
    for y in range(y_min, y_max + 1):
        for x in range(x_min, x_max + 1):
            if 0 <= x < WIDTH and 0 <= y < HEIGHT:
                cells[y * WIDTH + x] = value


def build_cells(revision: int = 0, reveal_columns: Optional[int] = None) -> list[int]:
    """Return row-major cells (-1 unknown, 0 free, 100 occupied).

    ``revision`` moves one small obstacle, so that each mapping run yields a
    different map fingerprint. With ``reveal_columns`` only that many columns
    are known, which imitates a map that grows while the robot is driven.
    """

    cells = [-1] * (WIDTH * HEIGHT)
    _fill(cells, 3, 3, 44, 32, 0)
    _fill(cells, 3, 3, 44, 3, 100)
    _fill(cells, 3, 32, 44, 32, 100)
    _fill(cells, 3, 3, 3, 32, 100)
    _fill(cells, 44, 3, 44, 32, 100)

    _fill(cells, 25, 4, 25, 31, 100)
    _fill(cells, 25, 11, 25, 14, 0)
    _fill(cells, 25, 25, 25, 27, 0)
    _fill(cells, 4, 21, 24, 21, 100)
    _fill(cells, 12, 21, 15, 21, 0)
    _fill(cells, 26, 17, 43, 17, 100)
    _fill(cells, 34, 17, 37, 17, 0)

    _fill(cells, 6, 26, 17, 28, 100)
    _fill(cells, 8, 8, 14, 10, 100)
    _fill(cells, 29, 27, 41, 29, 100)
    _fill(cells, 39, 5, 42, 14, 100)
    _fill(cells, 29, 6, 31, 11, 100)

    obstacle_x = (18, 20, 22, 20)[revision % 4]
    obstacle_y = (7, 8, 7, 6)[revision % 4]
    _fill(cells, obstacle_x, obstacle_y, obstacle_x + 1, obstacle_y + 1, 100)

    if reveal_columns is not None:
        for y in range(HEIGHT):
            for x in range(max(0, reveal_columns), WIDTH):
                cells[y * WIDTH + x] = -1
    return cells

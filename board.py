"""Fixed grid, collision tests, line clears."""

from __future__ import annotations

from typing import Optional

from config import COLS, ROWS
from tetromino import PIECE_COLORS, SHAPES, Tetromino


class Board:
    def __init__(self):
        # Per cell: None or RGB tuple (locked block color)
        self.grid: list[list[Optional[tuple[int, int, int]]]] = [
            [None for _ in range(COLS)] for _ in range(ROWS)
        ]

    def inside(self, x: int, y: int) -> bool:
        return 0 <= x < COLS and 0 <= y < ROWS

    def occupied(self, x: int, y: int) -> bool:
        if not self.inside(x, y):
            return True
        return self.grid[y][x] is not None

    def valid_position(self, piece: Tetromino) -> bool:
        for x, y in piece.cells():
            if not self.inside(x, y) or self.grid[y][x] is not None:
                return False
        return True

    def lock(self, piece: Tetromino) -> None:
        for x, y in piece.cells():
            self.grid[y][x] = PIECE_COLORS[piece.kind]

    def full_row_indices(self) -> list[int]:
        return [
            y
            for y in range(ROWS)
            if all(self.grid[y][x] is not None for x in range(COLS))
        ]

    def clear_lines(self) -> int:
        """Remove full rows; returns number of lines cleared."""
        new_rows: list[list[Optional[tuple[int, int, int]]]] = []
        cleared = 0
        for y in range(ROWS):
            if all(self.grid[y][x] is not None for x in range(COLS)):
                cleared += 1
            else:
                new_rows.append(self.grid[y])
        while len(new_rows) < ROWS:
            new_rows.insert(0, [None for _ in range(COLS)])
        self.grid = new_rows
        return cleared

    def ghost_drop_y(self, piece: Tetromino) -> Tetromino:
        """Lowest valid vertical position for the same x/rotation."""
        g = piece.copy()
        while True:
            g.y += 1
            if not self.valid_position(g):
                g.y -= 1
                break
        return g


def try_rotate(board: Board, piece: Tetromino, direction: int) -> bool:
    """Rotate with simple wall kicks; direction +1 = clockwise."""
    old_r = piece.rotation
    n = len(SHAPES[piece.kind])
    piece.rotation = (piece.rotation + direction) % n
    if board.valid_position(piece):
        return True
    for dx, dy in ((0, 0), (1, 0), (-1, 0), (2, 0), (-2, 0), (0, -1), (0, 1)):
        piece.x += dx
        piece.y += dy
        if board.valid_position(piece):
            return True
        piece.x -= dx
        piece.y -= dy
    piece.rotation = old_r
    return False

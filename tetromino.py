"""Seven-bag tetromino definitions and rotations."""

from config import HIDDEN_ROWS

SHAPES = {
    "I": [
        [(0, 1), (1, 1), (2, 1), (3, 1)],
        [(2, 0), (2, 1), (2, 2), (2, 3)],
        [(0, 2), (1, 2), (2, 2), (3, 2)],
        [(1, 0), (1, 1), (1, 2), (1, 3)],
    ],
    "J": [
        [(0, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (2, 0), (1, 1), (1, 2)],
        [(0, 1), (1, 1), (2, 1), (2, 2)],
        [(1, 0), (1, 1), (0, 2), (1, 2)],
    ],
    "L": [
        [(2, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (1, 1), (1, 2), (2, 2)],
        [(0, 1), (1, 1), (2, 1), (0, 2)],
        [(0, 0), (1, 0), (1, 1), (1, 2)],
    ],
    "O": [
        [(1, 0), (2, 0), (1, 1), (2, 1)],
        [(1, 0), (2, 0), (1, 1), (2, 1)],
        [(1, 0), (2, 0), (1, 1), (2, 1)],
        [(1, 0), (2, 0), (1, 1), (2, 1)],
    ],
    "S": [
        [(1, 1), (2, 1), (0, 2), (1, 2)],
        [(1, 0), (1, 1), (2, 1), (2, 2)],
        [(1, 0), (2, 0), (0, 1), (1, 1)],
        [(0, 0), (0, 1), (1, 1), (1, 2)],
    ],
    "T": [
        [(1, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (1, 1), (2, 1), (1, 2)],
        [(0, 1), (1, 1), (2, 1), (1, 2)],
        [(1, 0), (0, 1), (1, 1), (1, 2)],
    ],
    "Z": [
        [(0, 1), (1, 1), (1, 2), (2, 2)],
        [(2, 0), (1, 1), (2, 1), (1, 2)],
        [(0, 0), (1, 0), (1, 1), (2, 1)],
        [(1, 0), (0, 1), (1, 1), (0, 2)],
    ],
}


class Tetromino:
    __slots__ = ("kind", "rotation", "x", "y")

    def __init__(self, kind: str):
        self.kind = kind
        self.rotation = 0
        self.x = 3
        self.y = 0

    def cells(self):
        return [(self.x + cx, self.y + cy) for cx, cy in SHAPES[self.kind][self.rotation]]

    def copy(self):
        p = Tetromino(self.kind)
        p.rotation = self.rotation
        p.x = self.x
        p.y = self.y
        return p


PIECE_COLORS = {
    "I": (47, 198, 230),
    "J": (50, 80, 220),
    "L": (240, 150, 50),
    "O": (240, 235, 50),
    "S": (80, 220, 110),
    "T": (180, 80, 200),
    "Z": (240, 60, 60),
}


class Bag:
    """Random generator: permuted bag of seven pieces."""

    def __init__(self):
        import random

        self._random = random
        self._bag: list[str] = []
        self._refill()

    def _refill(self):
        self._bag = list(SHAPES.keys())
        self._random.shuffle(self._bag)

    def next_kind(self) -> str:
        if not self._bag:
            self._refill()
        return self._bag.pop()


def spawn_piece(kind: str) -> Tetromino:
    """Place new piece in the hidden buffer rows at the top of the matrix."""
    p = Tetromino(kind)
    if kind == "I":
        p.x, p.y = 3, HIDDEN_ROWS - 2
    elif kind == "O":
        p.x, p.y = 4, HIDDEN_ROWS - 2
    else:
        p.x, p.y = 3, HIDDEN_ROWS - 2
    return p

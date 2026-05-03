# Window and grid — fixed size per cahier des charges style brief.
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
FPS = 60

# Playfield: standard 10 x 20 visible rows (+ 2 hidden for spawn).
COLS = 10
VISIBLE_ROWS = 20
HIDDEN_ROWS = 2
ROWS = VISIBLE_ROWS + HIDDEN_ROWS

CELL_PX = 28
BOARD_PIXEL_W = COLS * CELL_PX
BOARD_PIXEL_H = VISIBLE_ROWS * CELL_PX

# Soft drop multiplier vs base gravity (cells per tick scaling handled in Game).
DIFFICULTY_LEVELS = {
    "Normal": {"start_level": 1, "lines_per_level": 10},
    "Hard": {"start_level": 3, "lines_per_level": 8},
    "Expert": {"start_level": 5, "lines_per_level": 6},
}

HIGHSCORE_FILE = "assets/highscore.txt"

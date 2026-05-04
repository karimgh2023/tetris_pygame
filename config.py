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

# Difficulty: score needed per displayed level step + gravity boost (harder presets).
# Gravity uses combined level = level_boost + (score // score_per_level).
DIFFICULTY_LEVELS = {
    "Normal": {"score_per_level": 4200, "level_boost": 0},
    "Hard": {"score_per_level": 3200, "level_boost": 1},
    "Expert": {"score_per_level": 2200, "level_boost": 2},
}

HIGHSCORE_FILE = "assets/highscore.txt"

# Lives shown for cahier HUD (Tetris classic: no stock loss — display only).
STARTING_LIVES = 3

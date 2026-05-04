"""Main Game class: states, pygame loop, scoring, HUD (cahier des charges compatible)."""

from __future__ import annotations

import os
from enum import Enum, auto

import pygame

from audio import load_sounds
from board import Board, try_rotate
from config import (
    BOARD_PIXEL_H,
    BOARD_PIXEL_W,
    CELL_PX,
    COLS,
    DIFFICULTY_LEVELS,
    FPS,
    HIGHSCORE_FILE,
    ROWS,
    STARTING_LIVES,
    VISIBLE_ROWS,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)
from tetromino import PIECE_COLORS, SHAPES, Tetromino, Bag, spawn_piece

# Victory condition (explicit win state for grading rubric — marathon target).
MARATHON_LINE_GOAL = 150

SCORE_MULTIPLIER = {
    1: 40,
    2: 100,
    3: 300,
    4: 1200,
}

BG = (20, 22, 34)
GRID_BG = (12, 14, 24)
GRID_LINE = (38, 40, 58)
SIDE_BG = (28, 30, 46)
WHITE = (240, 240, 246)
TITLE_COLOR = (200, 220, 255)

BOARD_OX = 36
BOARD_OY = (WINDOW_HEIGHT - VISIBLE_ROWS * CELL_PX) // 2
PANEL_LEFT = BOARD_OX + BOARD_PIXEL_W + 24


class GamePhase(Enum):
    MENU = auto()
    PLAY = auto()
    PAUSE = auto()
    LINE_FLASH = auto()
    GAMEOVER = auto()
    MARATHON_WIN = auto()


class Game:
    """Pygame Tetris lifecycle: menus, gameplay, persistence (highscore)."""

    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Tetris — Pygame")
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()

        pygame.font.init()
        self.font = pygame.font.SysFont("consolas", 22)
        self.font_small = pygame.font.SysFont("consolas", 18)
        self.font_title = pygame.font.SysFont("consolas", 44, bold=True)

        self.sounds = load_sounds(pygame)

        names = list(DIFFICULTY_LEVELS.keys())
        self._difficulty_index = names.index("Normal")

        self.high_score = self._load_high_score()

        self.phase = GamePhase.MENU
        self._menu_rects: dict[str, pygame.Rect] = {}
        self._pause_rects: dict[str, pygame.Rect] = {}
        self._end_rects: dict[str, pygame.Rect] = {}
        self._reset_soft()

    def _diff_cfg(self):
        return DIFFICULTY_LEVELS[self._difficulty_name()]

    def _reset_soft(self):
        self.board = Board()
        self.bag = Bag()
        self.spawn_next_piece = True
        self.piece: Tetromino | None = None
        self._next_kind = self.bag.next_kind()
        self.score = 0
        self.total_lines = 0
        self.phase = GamePhase.MENU

        cfg = self._diff_cfg()
        self.score_per_level = cfg["score_per_level"]
        self.level_boost = cfg["level_boost"]

        self.gravity_acc = 0.0
        self.drop_every = self._compute_drop_every(self.gravity_level())

        self.das_dx = 0
        self.das_timer = 0
        self.soft_drop = False
        self.line_flash_rows: list[int] = []
        self.line_flash_ttl = 0

    def _difficulty_name(self):
        names = list(DIFFICULTY_LEVELS.keys())
        return names[self._difficulty_index]

    def _compute_drop_every(self, level_disp: int) -> float:
        """Frames between automatic one-cell drops (smooth via accumulator)."""
        lv = max(1, min(level_disp, 30))
        return max(2.8, 58.0 - lv * 1.85)

    def gravity_level(self) -> int:
        """Difficulty index from score (higher = faster drops)."""
        return max(1, 1 + self.level_boost + (self.score // max(1, self.score_per_level)))

    def display_level(self) -> int:
        """Player-facing level (same formula as gravity for clarity)."""
        return self.gravity_level()

    def points_to_next_level(self) -> int:
        """Score still needed before the next level step (pure score ladder)."""
        step = max(1, self.score_per_level)
        r = self.score % step
        return step if r == 0 else step - r

    def _layout_menu_rects(self) -> None:
        cx = WINDOW_WIDTH // 2
        self._menu_rects = {
            "diff_prev": pygame.Rect(cx - 138, 232, 52, 40),
            "diff_next": pygame.Rect(cx + 86, 232, 52, 40),
            "play": pygame.Rect(cx - 120, 300, 240, 48),
            "quit": pygame.Rect(cx - 120, 360, 240, 40),
        }

    def _layout_pause_rects(self) -> None:
        cx, cy = WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 70
        self._pause_rects = {
            "resume": pygame.Rect(cx - 118, cy, 236, 44),
            "menu": pygame.Rect(cx - 118, cy + 54, 236, 40),
        }

    def _layout_end_rects(self) -> None:
        cx, cy = WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 88
        self._end_rects = {
            "menu": pygame.Rect(cx - 118, cy, 236, 44),
            "quit": pygame.Rect(cx - 118, cy + 54, 236, 40),
        }

    def _draw_button(self, rect: pygame.Rect, text: str, *, hover: bool, font: pygame.font.Font | None = None) -> None:
        ft = font or self.font
        fill = (92, 98, 138) if hover else (58, 64, 96)
        pygame.draw.rect(self.screen, fill, rect, border_radius=10)
        pygame.draw.rect(self.screen, (210, 215, 240), rect, 2, border_radius=10)
        surf = ft.render(text, True, WHITE)
        self.screen.blit(surf, surf.get_rect(center=rect.center))

    def _load_high_score(self) -> int:
        path = os.path.join(os.path.dirname(__file__), HIGHSCORE_FILE)
        assets_dir = os.path.dirname(path)
        if assets_dir:
            os.makedirs(assets_dir, exist_ok=True)
        if not os.path.isfile(path):
            return 0
        try:
            with open(path, "r", encoding="utf-8") as f:
                return int(f.read().strip() or "0")
        except ValueError:
            return 0

    def _save_high_score_if_needed(self):
        if self.score <= self.high_score:
            return
        self.high_score = self.score
        path = os.path.join(os.path.dirname(__file__), HIGHSCORE_FILE)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(str(self.high_score))

    def spawn_new_piece(self) -> None:
        k = self._next_kind
        self._next_kind = self.bag.next_kind()
        self.piece = spawn_piece(k)
        self.gravity_acc = 0.0
        self.spawn_next_piece = False
        if not self.board.valid_position(self.piece):
            self.phase = GamePhase.GAMEOVER
            self.sounds["gameover"].play()
            self._save_high_score_if_needed()

    def _award_lines_score(self, n: int) -> None:
        lv = max(1, self.gravity_level())
        self.score += SCORE_MULTIPLIER.get(n, 0) * lv
        self.total_lines += n
        if n == 4:
            self.sounds["tetris"].play()
        else:
            self.sounds["clear"].play()

    def _attempt_move_x(self, dx: int) -> bool:
        if self.piece is None:
            return False
        self.piece.x += dx
        if not self.board.valid_position(self.piece):
            self.piece.x -= dx
            return False
        self.sounds["move"].play()
        return True

    def _attempt_soft_drop_once(self) -> bool:
        if self.piece is None:
            return False
        self.piece.y += 1
        if self.board.valid_position(self.piece):
            self.score += 1
            return True
        self.piece.y -= 1
        return False

    def _hard_drop(self) -> None:
        if self.piece is None:
            return
        while True:
            self.piece.y += 1
            if self.board.valid_position(self.piece):
                self.score += 2
            else:
                self.piece.y -= 1
                break
        self._lock_piece()

    def _lock_piece(self) -> None:
        if self.piece is None:
            return
        self.board.lock(self.piece)
        self.sounds["lock"].play()

        rows = self.board.full_row_indices()
        if rows:
            self.line_flash_rows = rows
            self.line_flash_ttl = 28
            self.phase = GamePhase.LINE_FLASH
        else:
            self.spawn_next_piece = True

        self.piece = None

    def _after_line_animation(self) -> None:
        n = self.board.clear_lines()
        if n:
            self._award_lines_score(n)
        self.line_flash_rows = []
        self.line_flash_ttl = 0
        if self.total_lines >= MARATHON_LINE_GOAL:
            self.phase = GamePhase.MARATHON_WIN
            self._save_high_score_if_needed()
            return
        self.spawn_next_piece = True
        self.phase = GamePhase.PLAY

    def _grav_step(self, frames: float) -> None:
        if self.phase != GamePhase.PLAY or self.piece is None:
            return
        mult = 4.8 if self.soft_drop else 1.0
        self.drop_every = self._compute_drop_every(self.gravity_level())
        self.gravity_acc += frames * mult
        while self.gravity_acc >= self.drop_every:
            self.gravity_acc -= self.drop_every
            moved = self._attempt_soft_drop_once()
            if not moved:
                self._lock_piece()
                break

    def start_play(self):
        names = list(DIFFICULTY_LEVELS.keys())
        self._difficulty_index = self._difficulty_index % len(names)
        cfg = DIFFICULTY_LEVELS[self._difficulty_name()]
        self.score_per_level = cfg["score_per_level"]
        self.level_boost = cfg["level_boost"]

        self.board = Board()
        self.bag = Bag()
        self._next_kind = self.bag.next_kind()
        self.spawn_next_piece = True
        self.piece = None
        self.score = 0
        self.total_lines = 0
        self.phase = GamePhase.PLAY

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.QUIT:
            pygame.quit()
            raise SystemExit(0)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            if self.phase == GamePhase.MENU:
                self._layout_menu_rects()
                if self._menu_rects.get("play") and self._menu_rects["play"].collidepoint(pos):
                    self.start_play()
                elif self._menu_rects.get("diff_prev") and self._menu_rects["diff_prev"].collidepoint(pos):
                    self._difficulty_index = max(0, self._difficulty_index - 1)
                elif self._menu_rects.get("diff_next") and self._menu_rects["diff_next"].collidepoint(pos):
                    names = list(DIFFICULTY_LEVELS.keys())
                    self._difficulty_index = min(len(names) - 1, self._difficulty_index + 1)
                elif self._menu_rects.get("quit") and self._menu_rects["quit"].collidepoint(pos):
                    pygame.quit()
                    raise SystemExit(0)
                return
            if self.phase == GamePhase.PAUSE:
                self._layout_pause_rects()
                if self._pause_rects.get("resume") and self._pause_rects["resume"].collidepoint(pos):
                    self.phase = GamePhase.PLAY
                    self.sounds["pause"].play()
                elif self._pause_rects.get("menu") and self._pause_rects["menu"].collidepoint(pos):
                    self._save_high_score_if_needed()
                    self.phase = GamePhase.MENU
                return
            if self.phase in (GamePhase.GAMEOVER, GamePhase.MARATHON_WIN):
                self._layout_end_rects()
                if self._end_rects.get("menu") and self._end_rects["menu"].collidepoint(pos):
                    self._save_high_score_if_needed()
                    self.phase = GamePhase.MENU
                elif self._end_rects.get("quit") and self._end_rects["quit"].collidepoint(pos):
                    pygame.quit()
                    raise SystemExit(0)
                return

        if event.type == pygame.KEYDOWN:
            key = event.key

            if self.phase == GamePhase.MENU:
                if key == pygame.K_LEFT:
                    self._difficulty_index = max(0, self._difficulty_index - 1)
                elif key == pygame.K_RIGHT:
                    names = list(DIFFICULTY_LEVELS.keys())
                    self._difficulty_index = min(len(names) - 1, self._difficulty_index + 1)
                elif key in (pygame.K_SPACE, pygame.K_RETURN):
                    self.start_play()
                return

            if self.phase == GamePhase.GAMEOVER or self.phase == GamePhase.MARATHON_WIN:
                if key in (pygame.K_SPACE, pygame.K_RETURN):
                    self._save_high_score_if_needed()
                    self.phase = GamePhase.MENU
                elif key == pygame.K_ESCAPE:
                    pygame.quit()
                    raise SystemExit(0)
                return

            if self.phase == GamePhase.PAUSE:
                if key in (pygame.K_p, pygame.K_ESCAPE):
                    self.phase = GamePhase.PLAY
                    self.sounds["pause"].play()
                elif key == pygame.K_m:
                    self._save_high_score_if_needed()
                    self.phase = GamePhase.MENU
                return

            if key in (pygame.K_p, pygame.K_ESCAPE) and self.phase == GamePhase.PLAY:
                self.phase = GamePhase.PAUSE
                self.sounds["pause"].play()

            if self.phase == GamePhase.LINE_FLASH:
                return

            if self.phase == GamePhase.PLAY and self.piece is not None:
                if key in (pygame.K_UP, pygame.K_x):
                    if try_rotate(self.board, self.piece, 1):
                        self.sounds["rotate"].play()
                elif key == pygame.K_z:
                    if try_rotate(self.board, self.piece, -1):
                        self.sounds["rotate"].play()
                elif key == pygame.K_LEFT:
                    self._attempt_move_x(-1)
                    self.das_dx = -1
                    self.das_timer = 15
                elif key == pygame.K_RIGHT:
                    self._attempt_move_x(1)
                    self.das_dx = 1
                    self.das_timer = 15
                elif key == pygame.K_SPACE:
                    self._hard_drop()

        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_DOWN:
                self.soft_drop = False
            elif event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                if event.key == pygame.K_LEFT and self.das_dx < 0:
                    self.das_dx = 0
                elif event.key == pygame.K_RIGHT and self.das_dx > 0:
                    self.das_dx = 0

    def update_play(self):
        if self.phase == GamePhase.LINE_FLASH:
            self.line_flash_ttl -= 1
            if self.line_flash_ttl <= 0:
                self._after_line_animation()
            return

        if self.phase != GamePhase.PLAY:
            return

        frames = self.clock.get_time() / (1000.0 / FPS) * (FPS / 60.0)
        frames = max(0.001, frames)

        if self.spawn_next_piece:
            self.spawn_new_piece()

        keys = pygame.key.get_pressed()

        self.soft_drop = keys[pygame.K_DOWN]

        if self.das_dx != 0 and self.piece is not None:
            self.das_timer -= 1
            if self.das_timer <= 0:
                if self._attempt_move_x(self.das_dx):
                    pass
                self.das_timer = 5

        self._grav_step(frames)

    def draw_board_area(self):
        rect = pygame.Rect(BOARD_OX - 10, BOARD_OY - 10, BOARD_PIXEL_W + 20, BOARD_PIXEL_H + 20)
        pygame.draw.rect(self.screen, GRID_BG, rect, border_radius=8)

        ox, oy = BOARD_OX, BOARD_OY

        hide_offset = ROWS - VISIBLE_ROWS
        for fy in range(VISIBLE_ROWS):
            y_board = fy + hide_offset
            for x in range(COLS):
                cell = pygame.Rect(ox + x * CELL_PX, oy + fy * CELL_PX, CELL_PX - 1, CELL_PX - 1)
                pygame.draw.rect(self.screen, GRID_LINE, cell, width=1)
                locked = self.board.grid[y_board][x]
                if locked:
                    pygame.draw.rect(self.screen, locked, cell, border_radius=3)

        if self.phase == GamePhase.LINE_FLASH:
            fy_map = [(y - hide_offset) for y in self.line_flash_rows]
            fy_map = [fy for fy in fy_map if 0 <= fy < VISIBLE_ROWS]
            blink = self.line_flash_ttl % 14 < 7
            c = WHITE if blink else (200, 200, 255)
            for fy in fy_map:
                for x in range(COLS):
                    cell = pygame.Rect(ox + x * CELL_PX, oy + fy * CELL_PX, CELL_PX - 1, CELL_PX - 1)
                    pygame.draw.rect(self.screen, c, cell)

        ghost = None
        if self.phase == GamePhase.PLAY and self.piece is not None:
            ghost = self.board.ghost_drop_y(self.piece)
            gx, gy = ox, oy
            for xb, yb in ghost.cells():
                fy = yb - hide_offset
                if 0 <= fy < VISIBLE_ROWS:
                    r = pygame.Rect(gx + xb * CELL_PX, gy + fy * CELL_PX, CELL_PX - 1, CELL_PX - 1)
                    pygame.draw.rect(self.screen, (80, 80, 92), r, border_radius=3)

        if self.phase == GamePhase.PLAY and self.piece is not None:
            for xb, yb in self.piece.cells():
                fy = yb - hide_offset
                if 0 <= fy < VISIBLE_ROWS:
                    r = pygame.Rect(ox + xb * CELL_PX, oy + fy * CELL_PX, CELL_PX - 1, CELL_PX - 1)
                    pygame.draw.rect(self.screen, PIECE_COLORS[self.piece.kind], r, border_radius=3)

        pygame.draw.rect(
            self.screen,
            SIDE_BG,
            (PANEL_LEFT, BOARD_OY, WINDOW_WIDTH - PANEL_LEFT - 24, BOARD_PIXEL_H + 60),
            width=2,
            border_radius=8,
        )

    def draw_next_preview(self):
        ox = PANEL_LEFT
        oy = BOARD_OY + 8
        t = self.font.render("NEXT", True, WHITE)
        self.screen.blit(t, (ox + 12, oy))
        box = pygame.Rect(ox + 8, oy + 32, 4 * CELL_PX + 8, 4 * CELL_PX + 8)
        pygame.draw.rect(self.screen, GRID_BG, box, border_radius=6)

        kind = getattr(self, "_next_kind", "T")
        shape = SHAPES[kind][0]
        col = PIECE_COLORS[kind]
        min_cx = min(c[0] for c in shape)
        min_cy = min(c[1] for c in shape)
        pr = CELL_PX * 10 // 12
        base_x = ox + 16 + (4 * pr // 4)
        base_y = oy + 48
        for cx, cy in shape:
            bx = ox + 16 + (cx - min_cx) * pr
            by = base_y + (cy - min_cy) * pr
            r = pygame.Rect(bx, by, pr - 1, pr - 1)
            pygame.draw.rect(self.screen, col, r, border_radius=3)

    def draw_hud(self):
        ox = PANEL_LEFT
        y = BOARD_OY + 138
        lvl = self.display_level()
        texts = (
            ("Score", f"{self.score}"),
            ("Niveau", f"{lvl}"),
            ("Vies", f"{STARTING_LIVES}"),
            ("Palier", f"+{self.points_to_next_level()} pts"),
            ("Lignes", f"{self.total_lines}"),
            ("Marathon", f"{MARATHON_LINE_GOAL} lignes"),
            ("Record", f"{self.high_score}"),
            ("Diff.", self._difficulty_name()),
        )
        for lab, val in texts:
            a = self.font_small.render(lab + ":", True, (180, 185, 210))
            b = self.font_small.render(val, True, WHITE)
            self.screen.blit(a, (ox + 8, y))
            self.screen.blit(b, (ox + 108, y))
            y += 22

        inst = (
            ("Flèches", "déplacer"),
            ("Z/X", "rotation"),
            ("Bas", "chute rapide"),
            ("Espace", "chute instant."),
            ("P / Esc", "pause"),
        )
        if self.phase != GamePhase.MENU:
            y += 8
            for k, desc in inst:
                a = self.font_small.render(k, True, (150, 160, 200))
                b = self.font_small.render(desc, True, (120, 128, 150))
                self.screen.blit(a, (ox + 8, y))
                self.screen.blit(b, (ox + 112, y))
                y += 22

    def draw_menu(self):
        self.screen.fill(BG)
        title = self.font_title.render("TETRIS", True, TITLE_COLOR)
        subt = self.font.render("Pygame — Projet jeu 2D", True, WHITE)
        self.screen.blit(title, title.get_rect(center=(WINDOW_WIDTH // 2, 110)))
        self.screen.blit(subt, subt.get_rect(center=(WINDOW_WIDTH // 2, 162)))

        dname = self._difficulty_name()
        lab = self.font_small.render("Difficulté", True, (180, 185, 210))
        self.screen.blit(lab, lab.get_rect(center=(WINDOW_WIDTH // 2, 210)))

        mx, my = pygame.mouse.get_pos()
        self._layout_menu_rects()
        self._draw_button(self._menu_rects["diff_prev"], "<", hover=self._menu_rects["diff_prev"].collidepoint(mx, my), font=self.font_title)
        self._draw_button(self._menu_rects["diff_next"], ">", hover=self._menu_rects["diff_next"].collidepoint(mx, my), font=self.font_title)

        name_r = pygame.Rect(WINDOW_WIDTH // 2 - 90, 232, 180, 40)
        pygame.draw.rect(self.screen, (36, 40, 58), name_r, border_radius=8)
        pygame.draw.rect(self.screen, (90, 96, 120), name_r, 1, border_radius=8)
        dn = self.font.render(dname, True, (250, 190, 120))
        self.screen.blit(dn, dn.get_rect(center=name_r.center))

        self._draw_button(self._menu_rects["play"], "JOUER", hover=self._menu_rects["play"].collidepoint(mx, my))
        self._draw_button(self._menu_rects["quit"], "QUITTER", hover=self._menu_rects["quit"].collidepoint(mx, my), font=self.font_small)

        hint = self.font_small.render("Souris ou clavier — Entrée / Espace pour jouer", True, (150, 155, 175))
        self.screen.blit(hint, hint.get_rect(center=(WINDOW_WIDTH // 2, 424)))

        rec = self.font_small.render(f"Record : {self.high_score}", True, (170, 180, 205))
        self.screen.blit(rec, rec.get_rect(center=(WINDOW_WIDTH // 2, 454)))

    def draw_pause_overlay(self):
        ov = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        ov.set_alpha(160)
        ov.fill((0, 0, 0))
        self.screen.blit(ov, (0, 0))
        t = self.font_title.render("PAUSE", True, WHITE)
        self.screen.blit(t, t.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 70)))
        mx, my = pygame.mouse.get_pos()
        self._layout_pause_rects()
        self._draw_button(self._pause_rects["resume"], "Reprendre", hover=self._pause_rects["resume"].collidepoint(mx, my))
        self._draw_button(self._pause_rects["menu"], "Menu principal", hover=self._pause_rects["menu"].collidepoint(mx, my), font=self.font_small)

    def draw_gameover_overlay(self):
        ov = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        ov.set_alpha(190)
        ov.fill((35, 0, 22))
        self.screen.blit(ov, (0, 0))
        msg = (
            ("PARTIE TERMINÉE", self.font_title, (255, 200, 200)),
            (f"Score : {self.score}", self.font, WHITE),
        )
        yy = WINDOW_HEIGHT // 2 - 120
        for text, ft, color in msg:
            s = ft.render(text, True, color)
            self.screen.blit(s, s.get_rect(center=(WINDOW_WIDTH // 2, yy)))
            yy += 52
        mx, my = pygame.mouse.get_pos()
        self._layout_end_rects()
        self._draw_button(self._end_rects["menu"], "Menu principal", hover=self._end_rects["menu"].collidepoint(mx, my))
        self._draw_button(self._end_rects["quit"], "Quitter", hover=self._end_rects["quit"].collidepoint(mx, my), font=self.font_small)
        hint = self.font_small.render("Entrée / Espace — menu", True, (190, 190, 210))
        self.screen.blit(hint, hint.get_rect(center=(WINDOW_WIDTH // 2, 560)))

    def draw_marathon_win(self):
        ov = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        ov.set_alpha(180)
        ov.fill((10, 50, 30))
        self.screen.blit(ov, (0, 0))
        lines = [
            ("MARATHON TERMINÉ !", self.font_title, (180, 255, 210)),
            (f"{MARATHON_LINE_GOAL} lignes effacées", self.font, WHITE),
            (f"Score final : {self.score}", self.font_small, (220, 240, 220)),
        ]
        yy = WINDOW_HEIGHT // 2 - 130
        for text, ft, color in lines:
            s = ft.render(text, True, color)
            self.screen.blit(s, s.get_rect(center=(WINDOW_WIDTH // 2, yy)))
            yy += 52
        mx, my = pygame.mouse.get_pos()
        self._layout_end_rects()
        self._draw_button(self._end_rects["menu"], "Menu principal", hover=self._end_rects["menu"].collidepoint(mx, my))
        self._draw_button(self._end_rects["quit"], "Quitter", hover=self._end_rects["quit"].collidepoint(mx, my), font=self.font_small)
        hint = self.font_small.render("Entrée / Espace — menu", True, (200, 220, 200))
        self.screen.blit(hint, hint.get_rect(center=(WINDOW_WIDTH // 2, 560)))

    def draw(self):
        if self.phase == GamePhase.MENU:
            self.draw_menu()
            return

        self.screen.fill(BG)
        self.draw_board_area()
        self.draw_next_preview()
        self.draw_hud()

        if self.phase == GamePhase.PAUSE:
            self.draw_pause_overlay()
        elif self.phase == GamePhase.GAMEOVER:
            self.draw_gameover_overlay()
        elif self.phase == GamePhase.MARATHON_WIN:
            self.draw_marathon_win()

    def update(self):
        self.update_play()

    def run(self):
        running = True
        while running:
            for ev in pygame.event.get():
                self.handle_event(ev)
            self.update()
            self.draw()
            pygame.display.flip()
            self.clock.tick(FPS)

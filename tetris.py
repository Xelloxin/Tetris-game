#!/usr/bin/env python3
"""
Tetris - Pygame version
Install: pip install pygame
Run:     python tetris_pygame.py
"""

import pygame
import random
import sys

# ── Constants ─────────────────────────────────────────────────────────────────
CELL = 32
COLS, ROWS = 10, 20
SIDEBAR = 200

W = COLS * CELL + SIDEBAR
H = ROWS * CELL

FPS = 60

BLACK   = (0,   0,   0)
DARK    = (20,  20,  30)
GREY    = (40,  40,  55)
WHITE   = (255, 255, 255)
GHOST   = (80,  80, 100)

COLORS = {
    'I': (0,   220, 220),
    'O': (240, 220,   0),
    'T': (180,   0, 220),
    'S': (0,   200,  60),
    'Z': (220,  30,  30),
    'J': (30,   80, 220),
    'L': (220, 140,   0),
}

SHAPES = {
    'I': [[1,1,1,1]],
    'O': [[1,1],[1,1]],
    'T': [[0,1,0],[1,1,1]],
    'S': [[0,1,1],[1,1,0]],
    'Z': [[1,1,0],[0,1,1]],
    'J': [[1,0,0],[1,1,1]],
    'L': [[0,0,1],[1,1,1]],
}

LINE_SCORES = [0, 100, 300, 500, 800]

# ── Helpers ───────────────────────────────────────────────────────────────────

def rotate(shape):
    return [list(row) for row in zip(*shape[::-1])]

def new_piece():
    name = random.choice(list(SHAPES))
    shape = [row[:] for row in SHAPES[name]]
    return {'name': name, 'shape': shape,
            'x': COLS // 2 - len(shape[0]) // 2, 'y': 0}

def valid(board, piece, dx=0, dy=0, shape=None):
    s = shape or piece['shape']
    for r, row in enumerate(s):
        for c, cell in enumerate(row):
            if cell:
                nx = piece['x'] + c + dx
                ny = piece['y'] + r + dy
                if nx < 0 or nx >= COLS or ny >= ROWS:
                    return False
                if ny >= 0 and board[ny][nx]:
                    return False
    return True

def lock(board, piece):
    for r, row in enumerate(piece['shape']):
        for c, cell in enumerate(row):
            if cell:
                board[piece['y'] + r][piece['x'] + c] = piece['name']

def clear_lines(board):
    full = [r for r, row in enumerate(board) if all(row)]
    for r in full:
        del board[r]
        board.insert(0, [0] * COLS)
    return len(full)

def ghost_y(board, piece):
    gy = piece['y']
    while valid(board, {**piece, 'y': gy + 1}):
        gy += 1
    return gy

def level_interval(level):
    """Frames between automatic drops."""
    return max(2, 48 - (level - 1) * 4)

# ── Drawing ───────────────────────────────────────────────────────────────────

def draw_cell(surf, x, y, color, alpha=255):
    rect = pygame.Rect(x * CELL, y * CELL, CELL - 1, CELL - 1)
    if alpha < 255:
        s = pygame.Surface((CELL - 1, CELL - 1), pygame.SRCALPHA)
        s.fill((*color, alpha))
        surf.blit(s, rect.topleft)
    else:
        pygame.draw.rect(surf, color, rect, border_radius=3)
        highlight = tuple(min(255, v + 60) for v in color)
        pygame.draw.rect(surf, highlight, rect, width=2, border_radius=3)

def draw_board(surf, board):
    # Background grid
    for r in range(ROWS):
        for c in range(COLS):
            pygame.draw.rect(surf, GREY,
                             (c * CELL, r * CELL, CELL - 1, CELL - 1),
                             border_radius=2)
            cell = board[r][c]
            if cell:
                draw_cell(surf, c, r, COLORS[cell])

def draw_piece(surf, piece, color=None, gy=None):
    y_offset = gy if gy is not None else piece['y']
    col = color or COLORS[piece['name']]
    for r, row in enumerate(piece['shape']):
        for c, cell in enumerate(row):
            if cell:
                draw_cell(surf, piece['x'] + c, y_offset + r, col)

def draw_ghost(surf, board, piece):
    gy = ghost_y(board, piece)
    if gy == piece['y']:
        return
    for r, row in enumerate(piece['shape']):
        for c, cell in enumerate(row):
            if cell:
                rect = pygame.Rect((piece['x'] + c) * CELL,
                                   (gy + r) * CELL, CELL - 1, CELL - 1)
                pygame.draw.rect(surf, GHOST, rect, width=2, border_radius=3)

def draw_sidebar(surf, font, big_font, next_piece, score, level, lines, paused):
    ox = COLS * CELL
    # Background
    pygame.draw.rect(surf, DARK, (ox, 0, SIDEBAR, H))
    pygame.draw.line(surf, GREY, (ox, 0), (ox, H), 2)

    def text(s, x, y, f=font, color=WHITE):
        surf.blit(f.render(s, True, color), (ox + x, y))

    text('TETRIS', 20, 18, big_font, (0, 220, 220))

    text(f'SCORE', 20, 80)
    text(f'{score}', 20, 102, big_font, (240, 220, 0))

    text(f'LEVEL', 20, 150)
    text(f'{level}', 20, 172, big_font, (0, 200, 100))

    text(f'LINES', 20, 220)
    text(f'{lines}', 20, 242, big_font, (180, 100, 255))

    text('NEXT', 20, 295)
    # Draw next piece preview
    ns = next_piece['shape']
    pw = len(ns[0]) * CELL
    start_x = ox + (SIDEBAR - pw) // 2
    start_y = 325
    for r, row in enumerate(ns):
        for c, cell in enumerate(row):
            if cell:
                rect = pygame.Rect(start_x + c * CELL, start_y + r * CELL,
                                   CELL - 1, CELL - 1)
                color = COLORS[next_piece['name']]
                pygame.draw.rect(surf, color, rect, border_radius=3)
                highlight = tuple(min(255, v + 60) for v in color)
                pygame.draw.rect(surf, highlight, rect, width=2, border_radius=3)

    # Controls
    controls = [
        ('← →', 'Move'),
        ('↑',   'Rotate'),
        ('↓',   'Soft drop'),
        ('SPC', 'Hard drop'),
        ('P',   'Pause'),
        ('Q',   'Quit'),
    ]
    cy = H - 175
    small = pygame.font.SysFont('consolas', 14)
    for key, action in controls:
        k = small.render(key, True, (200, 200, 255))
        a = small.render(action, True, (160, 160, 160))
        surf.blit(k, (ox + 15, cy))
        surf.blit(a, (ox + 70, cy))
        cy += 22

    if paused:
        s = big_font.render('PAUSED', True, (255, 220, 0))
        surf.blit(s, (ox + SIDEBAR // 2 - s.get_width() // 2, H // 2 - 20))

# ── Main ──────────────────────────────────────────────────────────────────────

def show_screen(surf, font, big_font, title, subtitle, color):
    surf.fill(DARK)
    t = big_font.render(title, True, color)
    s = font.render(subtitle, True, WHITE)
    surf.blit(t, (W // 2 - t.get_width() // 2, H // 2 - 60))
    surf.blit(s, (W // 2 - s.get_width() // 2, H // 2 + 10))
    pygame.display.flip()

def main():
    pygame.init()
    surf = pygame.display.set_mode((W, H))
    pygame.display.set_caption('Tetris')
    clock = pygame.time.Clock()

    font     = pygame.font.SysFont('consolas', 20)
    big_font = pygame.font.SysFont('consolas', 28, bold=True)

    # ── Start screen ──
    show_screen(surf, font, big_font, 'TETRIS', 'Press any key to start', (0, 220, 220))
    waiting = True
    while waiting:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN:
                waiting = False

    while True:  # restart loop
        board = [[0] * COLS for _ in range(ROWS)]
        piece = new_piece()
        next_piece = new_piece()
        score, level, total_lines = 0, 1, 0
        fall_timer = 0
        paused = False
        game_over = False

        while not game_over:
            clock.tick(FPS)
            fall_timer += 1

            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_q:
                        pygame.quit(); sys.exit()
                    if e.key == pygame.K_p:
                        paused = not paused
                    if paused:
                        continue
                    if e.key == pygame.K_LEFT and valid(board, piece, dx=-1):
                        piece['x'] -= 1
                    if e.key == pygame.K_RIGHT and valid(board, piece, dx=1):
                        piece['x'] += 1
                    if e.key == pygame.K_UP:
                        rotated = rotate(piece['shape'])
                        if valid(board, piece, shape=rotated):
                            piece['shape'] = rotated
                    if e.key == pygame.K_DOWN:
                        if valid(board, piece, dy=1):
                            piece['y'] += 1
                            score += 1
                            fall_timer = 0
                    if e.key == pygame.K_SPACE:
                        while valid(board, piece, dy=1):
                            piece['y'] += 1
                            score += 2
                        fall_timer = level_interval(level) + 1  # force lock

            if paused:
                # Still draw while paused
                surf.fill(DARK)
                draw_board(surf, board)
                draw_ghost(surf, board, piece)
                draw_piece(surf, piece)
                draw_sidebar(surf, font, big_font, next_piece, score, level, total_lines, True)
                pygame.display.flip()
                continue

            # Gravity
            if fall_timer >= level_interval(level):
                fall_timer = 0
                if valid(board, piece, dy=1):
                    piece['y'] += 1
                else:
                    lock(board, piece)
                    cleared = clear_lines(board)
                    total_lines += cleared
                    score += LINE_SCORES[cleared] * level
                    level = total_lines // 10 + 1
                    piece = next_piece
                    next_piece = new_piece()
                    if not valid(board, piece):
                        game_over = True

            # Draw
            surf.fill(DARK)
            draw_board(surf, board)
            draw_ghost(surf, board, piece)
            draw_piece(surf, piece)
            draw_sidebar(surf, font, big_font, next_piece, score, level, total_lines, False)
            pygame.display.flip()

        # Game over
        show_screen(surf, font, big_font,
                    'GAME OVER', f'Score: {score}   Press any key to restart', (220, 50, 50))
        waiting = True
        while waiting:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if e.type == pygame.KEYDOWN:
                    waiting = False

if __name__ == '__main__':
    main()

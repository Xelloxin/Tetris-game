#!/usr/bin/env python3
"""
Terminal Tetris - Arrow keys to move/rotate, Q to quit, P to pause.
Requires: Python 3, curses (built-in on Linux/macOS).
Windows users: pip install windows-curses
"""

import curses
import random
import time

# ── Tetromino definitions ─────────────────────────────────────────────────────
SHAPES = {
    'I': [[1, 1, 1, 1]],
    'O': [[1, 1],
          [1, 1]],
    'T': [[0, 1, 0],
          [1, 1, 1]],
    'S': [[0, 1, 1],
          [1, 1, 0]],
    'Z': [[1, 1, 0],
          [0, 1, 1]],
    'J': [[1, 0, 0],
          [1, 1, 1]],
    'L': [[0, 0, 1],
          [1, 1, 1]],
}

COLORS = {
    'I': 1, 'O': 2, 'T': 3, 'S': 4, 'Z': 5, 'J': 6, 'L': 7,
}

BOARD_W, BOARD_H = 10, 20

# ── Helper functions ──────────────────────────────────────────────────────────

def rotate(shape):
    return [list(row) for row in zip(*shape[::-1])]

def new_piece():
    name = random.choice(list(SHAPES))
    return {'name': name, 'shape': [row[:] for row in SHAPES[name]],
            'x': BOARD_W // 2 - len(SHAPES[name][0]) // 2, 'y': 0}

def valid(board, piece, dx=0, dy=0, shape=None):
    s = shape if shape else piece['shape']
    for r, row in enumerate(s):
        for c, cell in enumerate(row):
            if cell:
                nx, ny = piece['x'] + c + dx, piece['y'] + r + dy
                if nx < 0 or nx >= BOARD_W or ny >= BOARD_H:
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
        board.insert(0, [0] * BOARD_W)
    return len(full)

def level_speed(level):
    return max(0.05, 0.5 - (level - 1) * 0.04)

# ── Drawing ───────────────────────────────────────────────────────────────────

def draw(stdscr, board, piece, next_piece, score, level, lines, paused):
    stdscr.clear()
    h, w = stdscr.getmaxyx()

    # Build display grid
    grid = [[board[r][c] for c in range(BOARD_W)] for r in range(BOARD_H)]

    # Ghost piece
    ghost = {'name': piece['name'], 'shape': piece['shape'],
              'x': piece['x'], 'y': piece['y']}
    while valid(board, ghost, dy=1):
        ghost['y'] += 1
    for r, row in enumerate(ghost['shape']):
        for c, cell in enumerate(row):
            gy, gx = ghost['y'] + r, ghost['x'] + c
            if cell and 0 <= gy < BOARD_H and not grid[gy][gx]:
                grid[gy][gx] = '.'

    # Active piece
    for r, row in enumerate(piece['shape']):
        for c, cell in enumerate(row):
            py, px = piece['y'] + r, piece['x'] + c
            if cell and 0 <= py < BOARD_H:
                grid[py][px] = piece['name']

    # Border + board
    offset_x = max(0, w // 2 - BOARD_W - 2)
    offset_y = max(0, (h - BOARD_H - 2) // 2)

    try:
        stdscr.addstr(offset_y, offset_x, '┌' + '──' * BOARD_W + '┐')
        for r in range(BOARD_H):
            stdscr.addstr(offset_y + 1 + r, offset_x, '│')
            for c in range(BOARD_W):
                cell = grid[r][c]
                if cell and cell != '.':
                    color = curses.color_pair(COLORS.get(cell, 0))
                    stdscr.addstr('██', color | curses.A_BOLD)
                elif cell == '.':
                    stdscr.addstr('░░', curses.color_pair(0))
                else:
                    stdscr.addstr('  ')
            stdscr.addstr('│')
        stdscr.addstr(offset_y + BOARD_H + 1, offset_x, '└' + '──' * BOARD_W + '┘')

        # Sidebar
        sx = offset_x + BOARD_W * 2 + 3
        sy = offset_y

        stdscr.addstr(sy,     sx, 'TETRIS', curses.A_BOLD)
        stdscr.addstr(sy + 2, sx, f'Score : {score}')
        stdscr.addstr(sy + 3, sx, f'Level : {level}')
        stdscr.addstr(sy + 4, sx, f'Lines : {lines}')

        stdscr.addstr(sy + 6, sx, 'NEXT:', curses.A_BOLD)
        ns = next_piece['shape']
        for r, row in enumerate(ns):
            line = ''
            for cell in row:
                line += '██' if cell else '  '
            color = curses.color_pair(COLORS.get(next_piece['name'], 0))
            stdscr.addstr(sy + 7 + r, sx, line, color | curses.A_BOLD)

        stdscr.addstr(sy + 13, sx, '← → : Move')
        stdscr.addstr(sy + 14, sx, '↑   : Rotate')
        stdscr.addstr(sy + 15, sx, '↓   : Soft drop')
        stdscr.addstr(sy + 16, sx, 'SPC : Hard drop')
        stdscr.addstr(sy + 17, sx, 'P   : Pause')
        stdscr.addstr(sy + 18, sx, 'Q   : Quit')

        if paused:
            msg = '  PAUSED  '
            stdscr.addstr(offset_y + BOARD_H // 2,
                          offset_x + BOARD_W - len(msg) // 2 + 1,
                          msg, curses.A_REVERSE | curses.A_BOLD)

    except curses.error:
        pass  # ignore drawing outside terminal bounds

    stdscr.refresh()

# ── Main game loop ────────────────────────────────────────────────────────────

def game(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(50)

    # Colors: I=cyan O=yellow T=magenta S=green Z=red J=blue L=white
    curses.start_color()
    curses.init_pair(1, curses.COLOR_CYAN,    curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_YELLOW,  curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_GREEN,   curses.COLOR_BLACK)
    curses.init_pair(5, curses.COLOR_RED,     curses.COLOR_BLACK)
    curses.init_pair(6, curses.COLOR_BLUE,    curses.COLOR_BLACK)
    curses.init_pair(7, curses.COLOR_WHITE,   curses.COLOR_BLACK)

    board = [[0] * BOARD_W for _ in range(BOARD_H)]
    piece = new_piece()
    next_piece = new_piece()
    score, level, total_lines = 0, 1, 0
    fall_time = time.time()
    paused = False
    line_scores = [0, 100, 300, 500, 800]

    while True:
        key = stdscr.getch()

        if key == ord('q') or key == ord('Q'):
            break
        if key == ord('p') or key == ord('P'):
            paused = not paused

        if not paused:
            if key == curses.KEY_LEFT and valid(board, piece, dx=-1):
                piece['x'] -= 1
            elif key == curses.KEY_RIGHT and valid(board, piece, dx=1):
                piece['x'] += 1
            elif key == curses.KEY_UP:
                rotated = rotate(piece['shape'])
                if valid(board, piece, shape=rotated):
                    piece['shape'] = rotated
            elif key == curses.KEY_DOWN:
                if valid(board, piece, dy=1):
                    piece['y'] += 1
                    score += 1
            elif key == ord(' '):
                while valid(board, piece, dy=1):
                    piece['y'] += 1
                    score += 2

            # Gravity
            now = time.time()
            if now - fall_time >= level_speed(level):
                fall_time = now
                if valid(board, piece, dy=1):
                    piece['y'] += 1
                else:
                    lock(board, piece)
                    cleared = clear_lines(board)
                    total_lines += cleared
                    score += line_scores[cleared] * level
                    level = total_lines // 10 + 1
                    piece = next_piece
                    next_piece = new_piece()
                    if not valid(board, piece):
                        break  # Game over

        draw(stdscr, board, piece, next_piece, score, level, total_lines, paused)

    # Game over screen
    stdscr.nodelay(False)
    h, w = stdscr.getmaxyx()
    msg = f' GAME OVER  Score: {score} '
    try:
        stdscr.addstr(h // 2, max(0, w // 2 - len(msg) // 2), msg,
                      curses.A_REVERSE | curses.A_BOLD)
        stdscr.addstr(h // 2 + 1, max(0, w // 2 - 10), ' Press any key to exit ',
                      curses.A_BOLD)
    except curses.error:
        pass
    stdscr.refresh()
    stdscr.getch()


def main():
    curses.wrapper(game)

if __name__ == '__main__':
    main()

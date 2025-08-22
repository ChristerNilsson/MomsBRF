#!/usr/bin/env python3
import curses, time
import numpy as np

ALIVE_CHAR = "█"     # Fungerar bra i Linux-terminaler; byt till "O" om din font strular
DENSITY = 0.25       # starttäthet

def init_colors():
    curses.start_color()
    curses.use_default_colors()
    # 5 åldersnivåer → olika färgpar
    curses.init_pair(1, curses.COLOR_GREEN,  -1)  # ny
    curses.init_pair(2, curses.COLOR_CYAN,   -1)  # ung
    curses.init_pair(3, curses.COLOR_YELLOW, -1)  # mogen
    curses.init_pair(4, curses.COLOR_MAGENTA,-1)  # gammal
    curses.init_pair(5, curses.COLOR_RED,    -1)  # mycket gammal
    return {1: curses.color_pair(1),
            2: curses.color_pair(2),
            3: curses.color_pair(3),
            4: curses.color_pair(4),
            5: curses.color_pair(5)}

def age_to_attr(age, pairs):
    if age <= 1:  return pairs[1]
    if age <= 3:  return pairs[2]
    if age <= 7:  return pairs[3]
    if age <= 15: return pairs[4]
    return pairs[5]

def random_board(h, w, density=DENSITY):
    return (np.random.random((h, w)) < density)

def life_step(board):
    # toroidal grannskaps-summering utan SciPy
    neighbors = sum(
        np.roll(np.roll(board, dy, axis=0), dx, axis=1)
        for dy in (-1, 0, 1) for dx in (-1, 0, 1)
        if not (dy == 0 and dx == 0)
    )
    return (neighbors == 3) | (board & (neighbors == 2))

def resize_arrays(board, ages, new_h, new_w):
    new_b = np.zeros((new_h, new_w), dtype=bool)
    new_a = np.zeros((new_h, new_w), dtype=np.uint16)
    h = min(new_h, board.shape[0])
    w = min(new_w, board.shape[1])
    new_b[:h, :w] = board[:h, :w]
    new_a[:h, :w] = ages[:h, :w]
    return new_b, new_a

def draw(stdscr, board, ages, color_pairs, gen, fps, paused):
    stdscr.erase()
    h, w = board.shape
    ys, xs = np.nonzero(board)
    # Rita bara levande celler (snabbt och enkelt)
    for y, x in zip(ys.tolist(), xs.tolist()):
        try:
            stdscr.addstr(y, x, ALIVE_CHAR, age_to_attr(int(ages[y, x]), color_pairs))
        except curses.error:
            pass
    status = f"Gen {gen} | {np.count_nonzero(board)} levande | {'paus' if paused else f'{fps:.1f} FPS'} | q=quit, space=paus, s=steg, r=slumpa, c=rensa, +/-=hastighet"
    try:
        stdscr.addstr(h, 0, status[:w-1])
    except curses.error:
        pass
    stdscr.refresh()

def main(stdscr):
    try: curses.curs_set(0)
    except: pass
    stdscr.nodelay(True)
    stdscr.keypad(True)

    colors = init_colors()
    fps = 20.0
    paused = False
    gen = 0

    H, W = stdscr.getmaxyx()
    H = max(1, H - 1)  # sista raden för status
    W = max(1, W)

    board = random_board(H, W)
    ages = np.zeros((H, W), dtype=np.uint16)

    last_frame = time.time()
    while True:
        ch = stdscr.getch()
        if ch != -1:
            if ch in (ord('q'), 27):  # q eller ESC
                return
            elif ch == ord(' '):
                paused = not paused
            elif ch == ord('s'):
                paused = True
                new_board = life_step(board)
                ages = (ages + 1) * new_board  # döda → 0, levande åldras
                board = new_board
                gen += 1
            elif ch == ord('r'):
                board = random_board(H, W); ages.fill(0); gen = 0
            elif ch == ord('c'):
                board[:] = False; ages.fill(0); gen = 0
            elif ch in (ord('+'), ord('=')):
                fps = min(120.0, fps * 1.25)
            elif ch in (ord('-'), ord('_')):
                fps = max(1.0, fps / 1.25)
            elif ch == curses.KEY_RESIZE:
                h2, w2 = stdscr.getmaxyx()
                h2 = max(1, h2 - 1); w2 = max(1, w2)
                if (h2, w2) != (H, W):
                    board, ages = resize_arrays(board, ages, h2, w2)
                    H, W = h2, w2

        if not paused:
            new_board = life_step(board)
            ages = (ages + 1) * new_board
            board = new_board
            gen += 1

        now = time.time()
        target = 1.0 / fps
        if (now - last_frame) >= target or paused:
            draw(stdscr, board, ages, colors, gen, fps, paused)
            last_frame = now
        else:
            time.sleep(max(0, target - (now - last_frame)))

if __name__ == "__main__":
    curses.wrapper(main)

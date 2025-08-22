import curses

ALIVE_CHAR = "█"	 # Fungerar bra i Linux-terminaler; byt till "O" om din font strular
N = 78

# testkommentar 
def println(win, text=""):
	"""Skriver text och flyttar sedan till nästa rad, kolumn 0"""
	y, x = win.getyx()		  # aktuell position
	win.addstr(text)			# skriv text
	y, x = win.getyx()		  # ny position efter texten
	win.move(y+1, 0)			# hoppa till början på nästa rad

def init_colors():
	curses.start_color()
	curses.use_default_colors()
	curses.init_pair(1, curses.COLOR_GREEN,  curses.COLOR_BLACK)
	curses.init_pair(2, curses.COLOR_BLACK,  curses.COLOR_YELLOW)
	# return {1: curses.color_pair(1)}

def draw(stdscr, y, x, text, colorindex):
	# stdscr.erase()
	stdscr.addstr(y ,x, text, curses.color_pair(colorindex))
	stdscr.refresh()

def main(stdscr):
	try: curses.curs_set(0)
	except: pass
	stdscr.nodelay(True)
	stdscr.keypad(True)
	init_colors()
	x=5
	y=5
	board = []
	for i in range(N):
		board.append([0] * N)
		draw(stdscr, i, 0, '0' * N, 1)
	draw(stdscr, y, x, str(board[y][x]), 2)
	while True:
		ch = stdscr.getch()
		if ch != -1:
			if ch == ord('q'): return
			draw(stdscr, y, x, str(board[y][x]), 1)
			if ch == ord(' '): board[y][x] = (board[y][x] + 1) % 10
			if ch == curses.KEY_LEFT: x += -1
			if ch == curses.KEY_DOWN: y += 1
			if ch == curses.KEY_RIGHT: x += 1
			if ch == curses.KEY_UP: y += -1
			if x==-1: x=N-1
			if y==N: y=0
			if x==N: x=0
			if y==-1: y=N-1
			draw(stdscr, y, x, str(board[y][x]), 2)

if __name__ == "__main__":
	curses.wrapper(main)

import curses

class Window:
    def __init__(self):
        self.scr = curses.initscr()

    def run(self)
        try:
            curses.noecho()
            curses.cbreak()
            self.init_color()
            self.scr.keypad(True) # Clears window
            while self.running:
                self.scr.addstr(0, 0, self.scr.getch())
        except KeyboardInterrupt: # Control+C
            self.close()
        except Exception: # Genuine Error
            self.close() # Gracefully close
            print(traceback.format_exc()) # Print the stack trace

    def close(self)
        curses.echo()
        curses.nocbreak()
        self.scr.keypad(False)
        curses.endwin() # Not sure if this is needed


if __name__ == "__main__":
    win = Window()
    win.run()
import curses
import traceback
import sys
import re

class Inputs:
    CTRL_I = 9
    CTRL_O = 15
    CTRL_A = 1
    CTRL_X = 24

class FileEditor:
    def __init__(self, file: str=""):
        self.scr = curses.initscr()
        self.running = False
        self.file_object = None
        self.current_file = file

    def handle_input(self):
        ...

    def run(self) -> None:
        try:
            self.running = True
            curses.noecho()
            curses.cbreak()
            self.scr.keypad(True)
            while self.running:
                self.handle_input()
        except KeyboardInterrupt:
            self.close()
        except Exception:
            self.close()
            print(traceback.format_exc())

    def close(self) -> None:
        """
            Sets terminal back to default settings
            and closes the file editor and any open file
        """
        self.running = False
        curses.echo()
        curses.nocbreak()
        self.scr.keypad(False)
        curses.endwin() # Not sure if this is needed
        if self.file_object:
            self.file_object.close()

if __name__ == "__main__":
    try:
        win = FileEditor(sys.argv[1])
    except IndexError:
        win = FileEditor()
    win.run()

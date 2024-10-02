"""
    Meda - A Python Command Line Text Editor
    @author: Luna
"""

import curses
import traceback
import sys
import re

class Inputs:
    CTRL_I = 9
    CTRL_O = 15
    CTRL_A = 1
    CTRL_X = 24
    OVERRIDES = [CTRL_I, CTRL_O, CTRL_A, CTRL_X]

class FileEditor:
    def __init__(self, file: str=""):
        self.scr = curses.initscr()
        self.running = False
        self.file_object = None
        self.current_file = file
        self.can_move_x, self.can_move_y = True, True
        self.rows, self.columns = 0, 0
        self.file_x, self.file_y = 0, 0
        self.cursor_x, self.cursor_y = 0, 1
        self.focus = "File"

    def init_color(self) -> None:
        """
            Initiates color pairs for syntax highlighting
            Assumes you have a colored terminal
        """
        curses.start_color()
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
        curses.init_pair(2, curses.COLOR_BLUE, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(5, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
        curses.init_pair(6, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(7, curses.COLOR_YELLOW, curses.COLOR_BLACK)

    def draw_box(self, title : str=None, writable : bool=False):
        for i in range(self.rows//3, self.rows//3+11):
            line = ""
            if i == self.rows//3:
                line += " "
                for _ in range(self.columns//2-2):
                    line += "_"
                line += " "
            elif i == self.rows//3+10:
                line += "|"
                for _ in range(self.columns//2-2):
                    line += "_"
                line += "|"
            else:
                line += "|"
                for _ in range(self.columns//2-2):
                    line += " "
                line += "|"
            self.scr.addstr(i, (self.columns//2//2), line)

    def handle_override(self, inp) -> None:
        if inp == Inputs.CTRL_O: # Open File
            self.draw_box()
        if inp == Inputs.CTRL_X: # Close App
            ...

    def handle_input(self) -> None:
        self.rows, self.columns = self.scr.getmaxyx()
        inp = self.scr.getch()
        if inp in Inputs.OVERRIDES:
            self.handle_override(inp)

    def run(self) -> None:
        """
            Sets the terminal to no echo, and process user input
            without waiting for return. Opens the FileEditor window
        """
        try:
            self.running = True
            curses.noecho()
            curses.cbreak()
            self.init_color()
            self.scr.keypad(True) # Clears window
            while self.running:
                self.handle_input()
        except KeyboardInterrupt: # Control+C
            self.close()
        except Exception: # Genuine Error
            self.close()
            print(traceback.format_exc()) # Print the stack trace

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

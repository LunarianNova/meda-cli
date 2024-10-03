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
        self.content = [""]
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

    def move_cursor(self, x: int=None, y: int=None) -> None:
        """
            Moves cursor to x and y position
            If no positions given, it moves to where it should currently be
            Useful for after you write a line, since curses will move cursor
        """
        x = self.cursor_x if not x else x
        y = self.cursor_y if not y else y
        self.scr.move(y, x)
        curses.setsyx(y, x)
        self.scr.refresh()

    def draw_box(self, title : str=None, writable : bool=False) -> None:
        """
            Draws a box on the screen in the middle
            Used for user inputs or confirmations
            TODO: Make it a standalone class?
        """
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
        """
            Overrides are things that can be executed at any time
            This is for things like saving or quitting
        """
        if inp == Inputs.CTRL_O: # Open File
            self.draw_box()
        if inp == Inputs.CTRL_X: # Close App
            ...

    def handle_input(self) -> None:
        self.rows, self.columns = self.scr.getmaxyx()
        inp = self.scr.getch()
        if inp in Inputs.OVERRIDES:
            self.handle_override(inp)

    def clear_screen(self) -> None:
        """
            Clear everything on the screen, excluding header/footer
        """
        for line in range(1, self.rows-1):
            self.scr.addstr(0, line, " "*self.columns)
        self.move_cursor() # Reset cursor

    def write_line(self, y : int, content : str, index : int=0, parse : bool=False) -> None:
        """
            Writes a line of content, from index on, at the line y
            Takes an optional parsed argument
        """
        try:
            line = content[index:index+self.columns-2]
        except:
            line = content[index:]
        line += " "*(self.rows-len(line))
        if parse:
            parsed = self.parse_line(line)
            for i in range(len(line)):
                self.scr.addch(y, i, line[i], parsed[i])
        else:
            self.scr.addstr(y, 0, line)

    def write_content(self, line: int=0, index: int=0) -> None:
        """
            Writes all the content in self.content from line to end of screen
            Optional index in case of horizontal scrolling
        """
        self.clear_screen()
        for y, text in enumerate(self.content[line:]):
            self.write_line(y+1, text, index)
            if y+2 >= self.rows:
                break
        self.move_cursor()

    def read_file(self, file : str) -> None:
        """
            Sets attributes to equal a new file, as indicated by a passed string
        """
        self.file_object = open(file)
        self.content = self.file_object.read().split("\n")
        self.write_content()

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
            if self.current_file: # Arg passed at creation
                self.rows, self.columns = self.scr.getmaxyx()
                self.read_file(self.current_file)
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

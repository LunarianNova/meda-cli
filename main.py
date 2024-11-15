"""
    Meda - A Python Command Line Text Editor
    @author: Luna
"""

import curses
import traceback
import sys
import re
import CursesBoxes


class Inputs:
    CTRL_O = 15
    CTRL_A = 1
    CTRL_X = 24
    ARROW_DOWN = 258
    ARROW_UP = 259
    ARROW_LEFT = 260
    ARROW_RIGHT = 261

    MOVEMENT = [ARROW_DOWN, ARROW_UP, ARROW_LEFT, ARROW_RIGHT]
    OVERRIDES = [CTRL_O, CTRL_A, CTRL_X]


class FileEditor:
    def __init__(self, file: str = "") -> None:
        self.scr = curses.initscr()
        self.running = False
        self.file_object = None
        self.current_file = file
        self.content = [""]
        self.original_content = [""]
        self.parsed_content = {}
        self.can_move_x, self.can_move_y = True, True
        self.rows, self.columns = 0, 0
        self.file_x, self.file_y = 0, 0
        self.cursor_x, self.cursor_y = 0, 1
        self.max_x = 0
        self.scrolled_x = 0
        self.focus_object = self
        self.focus = "File"

    def init_color(self) -> None:
        """
        Initiates color pairs for syntax highlighting
        Assumes you have a colored terminal
        """
        curses.start_color()
        # curses.init_pair(num, text_color, background_color)
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
        curses.init_pair(2, curses.COLOR_BLUE, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(5, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
        curses.init_pair(6, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(7, curses.COLOR_YELLOW, curses.COLOR_BLACK)

    def write_header(self) -> None:
        """
        Stickied header containing the filename for now
        """
        # Add * if file is modified
        filename = (
            self.current_file + "*"
            if self.content != self.original_content
            else self.current_file
        )
        header = filename.center(self.columns)
        self.scr.addstr(0, 0, header, curses.color_pair(1))
        self.move_cursor()

    def write_footer() -> None: ...

    def move_cursor(self, y: int = None, x: int = None) -> None:
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

    def adjust_x(self, old_line: int, new_line: int) -> None:
        """
        Make sure the cursor stays at the most optimal x value possible
        max_x should be moved when x is modified by user input, but not automatically
        """
        old_content = self.content[old_line]
        new_content = self.content[new_line]
        new_start = ""

        if self.scrolled_x:
            # Write the old line back at the first page
            self.write_line(self.cursor_y + (old_line - new_line), old_content)

        if len(new_content) <= self.max_x:
            # If the new line is shorter than current x position
            self.file_x = len(new_content)
            if len(new_content) < self.columns - 2:
                # If the new line is smaller than the screen
                self.cursor_x = self.file_x
            else:
                # If the new line is larger than the screen
                self.scrolled_x = (
                    (self.file_x - (self.columns - 2)) // (self.columns - 6)
                ) + 1
                self.scrolled_x = max(0, self.scrolled_x)
                new_start = (
                    (self.columns - 7) + ((self.columns - 6) * (self.scrolled_x - 1))
                    if self.scrolled_x != 0
                    else 0
                )
                self.cursor_x = len(new_content) - new_start - 1
                self.write_line(self.cursor_y, new_content, index=new_start)

        else:
            if self.scrolled_x:
                # If the new line is larger than the max position
                self.file_x = self.max_x
                self.scrolled_x = (
                    (self.max_x - (self.columns - 2)) // (self.columns - 6)
                ) + 1
                self.scrolled_x = max(0, self.scrolled_x)
                # 82, 165, 248 ((self.columns-7)+((self.columns-6)*(self.scrolled_x-1)))
                # self.columns = 89
                new_start = (
                    (self.columns - 7) + ((self.columns - 6) * (self.scrolled_x - 1))
                    if self.scrolled_x != 0
                    else 0
                )
                self.cursor_x = self.max_x - new_start - 1
                self.write_line(self.cursor_y, new_content, index=new_start)
            else:
                # If the new line and current line are both on the first screen
                self.file_x = self.max_x
                self.cursor_x = self.file_x

    def handle_movement(self, direction: int) -> bool:
        """
        given an ascii int, will process movement
        """

        match direction:
            case Inputs.ARROW_DOWN:  # Arrow Down
                if self.file_y + 1 < len(self.content):
                    # If there is a line under cursor
                    old_line = self.file_y
                    self.file_y += 1
                    new_line = self.file_y
                    if self.cursor_y + 1 < self.rows:
                        # If the cursor is not at the bottom of the screen
                        self.cursor_y += 1
                    else:
                        # If the cursor is at the bottom
                        self.write_content(self.file_y - self.rows + 2)

                    self.adjust_x(old_line, new_line)

            case Inputs.ARROW_UP:  # Arrow up
                if self.file_y - 1 >= 0:
                    # If there is a line before the current line
                    old_line = self.file_y
                    self.file_y -= 1
                    new_line = self.file_y
                    if self.cursor_y - 1 > 0:
                        # If the cursor is not at the start of the screen
                        self.cursor_y -= 1
                    else:
                        # If the cursor is at the top
                        self.write_content(self.file_y)

                    self.adjust_x(old_line, new_line)

            case Inputs.ARROW_LEFT:  # Arrow left
                if self.file_x - 1 >= 0:
                    # Cursor is not at the start of file
                    self.file_x -= 1

                    if self.cursor_x - 1 >= 0:
                        # Cursor is not at start of screen
                        self.cursor_x -= 1

                        if self.scrolled_x != 0 and self.cursor_x == 3:
                            # Screen is scrolled
                            new_start = max(
                                0, self.file_x - self.columns + 2
                            )  # 1->0 will be negative
                            self.scrolled_x -= 1
                            self.write_line(
                                y=self.cursor_y,
                                content=self.content[self.file_y],
                                index=new_start,
                            )
                            self.cursor_x = self.columns - 3

                    self.max_x = self.file_x

            case Inputs.ARROW_RIGHT:  # Arrow right
                if self.file_x + 1 <= len(self.content[self.file_y]):
                    self.file_x += 1
                    if self.cursor_x + 1 < self.columns - 2:
                        self.cursor_x += 1
                    else:
                        self.cursor_x = 4
                        self.write_line(
                            y=self.cursor_y,
                            content=self.content[self.file_y],
                            index=self.file_x - 5,
                        )
                        self.scrolled_x += 1

                    self.max_x = self.file_x

            case _:
                return False

        self.move_cursor()
        return True  # Was an arrow key

    def handle_override(self, inp) -> None:
        """
        Overrides are things that can be executed at any time
        This is for things like saving or quitting
        """
        match inp:
            case Inputs.CTRL_O:  # Open File
                if self.content != self.original_content:
                    box = CursesBoxes.SaveBox(height=10, width=self.columns // 2)
                    self.focus_object = box
                    self.focus = "SaveBox"
                    box.draw(scr=self.scr, y=self.rows // 3, x=self.columns // 2 // 2)
                    while not self.wait_for_response():
                        pass
                box = CursesBoxes.InputBox(
                    height=10, width=self.columns // 2, title="Enter File Name"
                )
                self.focus_object = box
                self.focus = "OpenFile"
                box.draw(scr=self.scr, y=self.rows // 3, x=self.columns // 2 // 2)

            case Inputs.CTRL_X:  # Close App
                if self.content != self.original_content:
                    box = CursesBoxes.SaveBox(height=10, width=self.columns // 2)
                    self.focus_object = box
                    self.focus = "SaveBox"
                    box.draw(scr=self.scr, y=self.rows // 3, x=self.columns // 2 // 2)
                    while not self.wait_for_response():
                        pass
                self.close()

            case Inputs.CTRL_A:
                if self.focus != "File":
                    self.focus_object = self
                    self.focus = "File"
                    self.write_content(self.file_y, self.file_x)

    def wait_for_response(self) -> None:
        """
        Call this in a while loop to suspend until
        Current overlay is closed
        """
        temp = self.focus_object
        self.handle_input()
        if temp != self.focus_object:
            return True
        return False

    def handle_input(self) -> None:
        """
        The ever-growing function which handles all input
        in the console
        """
        self.rows, self.columns = self.scr.getmaxyx()  # Update Dimensions
        inp = self.scr.getch()  # Wait for input
        if inp in Inputs.OVERRIDES:  # Handle overrides immediately
            self.handle_override(inp)
        elif type(self.focus_object) != type(
            self
        ):  # If user is focused on something other than editor
            res = self.focus_object.handle_input(
                inp
            )  # Send input to be handled by external object
            match self.focus:
                case "SaveBox":
                    if res == True:  # Y, or if user hits enter on "YES"
                        self.save_file()
                        # Fix focus
                        self.focus_object = self
                        self.focus = "File"
                    elif res == False:  # N, or if user hits enter on "NO"
                        self.focus_object = self
                        self.focus = "File"

                case "OpenFile":
                    if res:
                        self.read_file(res)  # Returns text entered on return input
                        # Fix focus
                        self.focus_object = self
                        self.focus = "File"

        else:
            move = self.handle_movement(inp)  # Attempt to interpret as movement
            if not move:  # If it isn't a movement key
                line = self.content[self.file_y]
                if inp == 8 or inp == 127:  # Backspace
                    if self.file_x - 1 >= 0:  # Can erase character
                        line = line[: self.file_x - 1] + line[self.file_x :]
                        self.content[self.file_y] = line
                        self.write_line(self.cursor_y, line)
                        self.handle_movement(
                            Inputs.ARROW_LEFT
                        )  # Backspace should move cursor left
                        if self.file_x > self.columns - 2:
                            self.adjust_x(self.file_y, self.file_y)
                    else:  # Erasing start of line
                        line_end = len(self.content[self.file_y - 1])
                        self.content[self.file_y - 1] += self.content[self.file_y]
                        self.content = (
                            self.content[: self.file_y]
                            + self.content[self.file_y + 1 :]
                        )
                        self.write_content()
                        self.file_y -= 1
                        self.cursor_y -= 1
                        self.file_x = line_end
                        self.cursor_x = line_end
                        self.adjust_x(self.file_y + 1, self.file_y)

                # Tab (or Ctrl+I)
                elif inp == 9:
                    self.content[self.file_y] = (" " * 4) + self.content[self.file_y]
                    for _ in range(4):
                        self.handle_movement(Inputs.ARROW_RIGHT)
                    self.write_line(self.cursor_y, self.content[self.file_y])
                    self.adjust_x(self.file_y, self.file_y)

                # Return
                elif inp == 10:
                    line = line[0 : self.file_x] + "\n" + line[self.file_x :]
                    self.content = (
                        self.content[: self.file_y]
                        + line.split("\n")
                        + self.content[self.file_y + 1 :]
                    )
                    self.write_content()
                    self.file_y += 1
                    self.cursor_y += 1
                    self.file_x = 0
                    self.cursor_x = 0
                    self.adjust_x(self.file_y - 1, self.file_y)

                # Real ASCII Letter Inputs
                elif inp >= 32 and inp <= 126:
                    try:
                        line = line[0 : self.file_x] + chr(inp) + line[self.file_x :]
                    except IndexError:
                        line += chr(inp)
                    self.content[self.file_y] = line
                    self.write_line(self.cursor_y, line)
                    self.handle_movement(Inputs.ARROW_RIGHT)
                    if self.file_x > self.columns - 2:
                        self.adjust_x(self.file_y, self.file_y)

                # Shift+Tab
                elif inp == 353:
                    if self.content[self.file_y].startswith(" " * 4):
                        self.content[self.file_y] = self.content[self.file_y][4:]
                        for _ in range(4):
                            self.handle_movement(Inputs.ARROW_LEFT)
                        self.write_line(self.cursor_y, self.content[self.file_y])
                        self.adjust_x(self.file_y, self.file_y)

                self.move_cursor()  # Adjust cursor
                self.write_header()  # In case file is now modified
                self.max_x = self.file_x  # Cursor is *always* manually moved here

    def clear_screen(self) -> None:
        """
        Clear everything on the screen, excluding header/footer
        """
        for line in range(1, self.rows - 1):
            self.scr.addstr(line, 0, " " * self.columns)
        self.scr.addstr(self.rows - 1, 0, " " * (self.columns - 1))
        self.move_cursor()  # Reset cursor

    def parse_line(self, line: str) -> list:
        """
        Basically, this returns a list where each character in line is assigned a color
        based on what it is (definition, declarative, comment, etc.)
        TODO: Multiline support (Needs a separate function)
        """
        parsed = []
        declaratives = r"(class|import|def|if|else|elif|while|for|try|except|or|and|match|case|return|is|in|not|with|as|assert|pass|break|continue)"

        # Default colors for alpha, numeric and non-alphanumeric
        for char in line:
            if char.isalnum():
                color = curses.color_pair(5) if char.isdigit() else curses.color_pair(0)
            else:
                color = curses.color_pair(2)
            parsed.append(color)

        # Declaratives
        for match in re.finditer(f"(\\(|^|\\s){declaratives}(:|\\s)", line):
            for i in range(match.start(), match.end()):
                parsed[i] = curses.color_pair(2)

        # Function/Class/Module names
        for word in ["def", "class", "import"]:
            if match := re.search(
                f"{word}\\s\\S*(\\(|:)", line
            ):  # Walrus operator my beloved
                for i in range(match.start() + len(word), match.end() - 1):
                    parsed[i] = curses.color_pair(7)

        # Dot notation
        for match in re.finditer(r"[^a-zA-Z]{1}[a-zA-Z]*\.", line):
            for i in range(match.start() + 1, match.end()):
                parsed[i] = curses.color_pair(3)

        # Comments and Quotes
        for case in [r"#.*", r'"[^"]*"', r"'[^']*'"]:
            for match in re.finditer(case, line):
                for i in range(match.start(), match.end()):
                    parsed[i] = curses.color_pair(4)

        # Definitions
        for case in [r"^\s*\S*\s*=", r"^\s*\S*\s*(\*=|\+=|-=)"]:
            if match := re.search(case, line):
                for i in range(match.start(), match.end() - 1):
                    parsed[i] = curses.color_pair(5)

        # Random Misc
        for match in re.finditer(r"(self|None|True|False)", line):
            for i in range(match.start(), match.end()):
                parsed[i] = curses.color_pair(6)

        return parsed

    def check_parsed_cache(self, line: str) -> list:
        """
        Checks self.parsed_content to see if a line is in it
        Can't directly check, because of how parsing is handled
        So it checks content first, and matches the content line to parsed line
        """
        try:
            line_index = self.content.index(line)
            if len(self.parsed_content[line_index]) == len(
                line
            ):  # Can't compare directly, so compare size
                return self.parsed_content[line_index]
            return None  # Not parsed

        except ValueError:  # Failed .index
            return None

    def write_line(
        self, y: int, content: str, index: int = 0, parse: bool = True
    ) -> None:
        """
        Writes a line of content, from index on, at the line y
        Takes an optional parse argument
        True to parse, False to not, or a parsed dict itself
        """
        line = content[index : index + self.columns]
        line += " " * (self.columns - len(line) + 1)  # Erase any text already there

        parsed = []

        if parse is True:
            # If it's not in cache, parse it
            parsed = (
                self.parse_line(line)
                if not self.check_parsed_cache(content)
                else self.check_parsed_cache(content)
            )
            parsed = parsed[index : index + self.columns]
        else:  # Throw default color
            parsed = [curses.color_pair(0) for i in range(self.columns - 2)]

        if (
            index > 0
        ):  # TODO: Fix the weird edge case (should be as easy as removing the 1s in correct_x)
            line = line[1:]
            parsed = parsed[1:]

        for i in range(min(self.columns - 1, len(line) - 1)):
            color = parsed[i] if i < len(parsed) else curses.color_pair(0)
            self.scr.addch(y, i, line[i], color)

        if index > 0:
            self.scr.addch(y, 0, "<", curses.color_pair(1))
        if len(content[index:]) >= self.columns - 2:
            self.scr.addch(y, self.columns - 2, ">", curses.color_pair(1))

    def write_content(self, line: int = 0, index: int = 0) -> None:
        """
        Writes all the content in self.content from line to end of screen
        Optional index in case of horizontal scrolling
        """
        for y, text in enumerate(self.content[line:]):
            parsed = self.parse_line(text)
            self.parsed_content[y] = parsed  # y = file line, not screen line
            self.write_line(y + 1, text, index)  # y+1 to account for header

            if y + 2 >= self.rows:
                break

        self.move_cursor()

    def read_file(self, file: str) -> None:
        """
        Sets attributes to equal a new file, as indicated by a passed string
        """
        # Move cursor to top left, both in file and window
        self.cursor_y = 1
        self.cursor_x, self.file_x, self.file_y = 0, 0, 0
        if self.file_object:  # Close any file that may be open
            self.file_object.close()
        try:
            # Update vars with new file
            self.file_object = open(file)
            self.content = self.file_object.read().split("\n")
            self.original_content = [x for x in self.content]
        except FileNotFoundError:
            # If no file is found, assume it will be created
            self.content = [""]
            self.original_content = [""]
        self.current_file = file
        for line in range(len(self.content)):
            # Pre-parse all the lines
            self.parsed_content[line] = self.parse_line(self.content[line])
        self.clear_screen()
        self.write_header()
        self.write_content()

    def save_file(self) -> None:
        self.file_object.close()  # Opened in read-only
        with open(self.current_file, "w") as f:
            f.write("\n".join(self.content))
        # In the case of just saving, without closing
        self.original_content = [x for x in self.content]
        self.file_object = open(self.current_file)

    def run(self) -> None:
        """
        Sets the terminal to no echo, and process user input
        without waiting for return. Opens the FileEditor window
        """
        try:
            self.running = True
            self.rows, self.columns = self.scr.getmaxyx()
            curses.noecho()
            curses.cbreak()
            self.init_color()
            self.scr.keypad(True)  # Clears window
            if self.current_file:  # Argument passed at creation
                self.read_file(self.current_file)
            while self.running:
                self.handle_input()
        except KeyboardInterrupt:  # Control+C
            self.close()
        except Exception:  # Genuine Error
            self.close()  # Gracefully close
            print(traceback.format_exc())  # Print the stack trace

    def close(self) -> None:
        """
        Sets terminal back to default settings
        and closes the file editor and any open file
        """
        self.running = False
        curses.echo()
        curses.nocbreak()
        self.scr.keypad(False)
        curses.endwin()  # Not sure if this is needed
        if self.file_object:
            self.file_object.close()  # Don't save


if __name__ == "__main__":
    try:
        win = FileEditor(sys.argv[1])
    except IndexError:
        win = FileEditor()
    win.run()

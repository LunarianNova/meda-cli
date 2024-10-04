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



class BaseBox:
    def __init__(self, height: int, width: int, title: str):
        self.height = height
        self.width = width
        self.title = title
        self.y, self.x, = 0, 0
        self.content = []
        self.active_screen = None
        self._instantiate_box()

    def _instantiate_box(self) -> None:
        """
            Sets the content to match arguments
        """
        self._draw_border()
        self._draw_title()

    def _draw_title(self) -> None:
        """
            Draws the title about 1/3 down the screen
        """
        self.content[self.height//3] = "|" + self.title.center(self.width-2) + "|"

    def _draw_border(self) -> None:
        """
            Draws the basic box border into self.content
        """
        self.content.append(" " + "_"*(self.width-2) + " ")
        for _ in range(self.height-2):
            self.content.append("|" + " "*(self.width-2) + "|")
        self.content.append("|" + "_"*(self.width-2) + "|")

    def draw(self, y: int=None, x: int=None, scr=None) -> None:
        """
            Draws the box on scr at y, x
        """
        scr = scr or self.active_screen
        self.x = x if x is not None else self.x
        self.y = y if y is not None else self.y
        self.active_screen = scr
        
        for i, line in enumerate(self.content):
            scr.addstr(y+i, x, line)
            
    def move_cursor(self, y: int, x: int, scr=None) -> None:
        """
            Moves cursor to y, x
            Useful for stickying cursor
        """
        scr = scr or self.active_screen
        scr.move(y, x)
        curses.setsyx(y, x)
        scr.refresh()



class SelectBox(BaseBox):
    def __init__(self, height: int, width: int, title: str, options: list):
        super().__init__(height, width, title)
        self.options = options
        self.active_option = 0

    def draw(self, y: int=None, x: int=None, scr=None) -> None:
        """
            Draws the SelectBox on given screen, or last used screen
        """
        scr = scr or self.active_screen
        self.x = x if x is not None else self.x
        self.y = y if y is not None else self.y
        self.active_screen = scr

        self._draw_options()
        super().draw(scr, y, x)

    def _draw_options(self) -> None:
        """
            Sets the line about 2/3 down in the box to the options
            Highlights active option
        """
        spacing = (self.width-2) // (len(self.options)+1)
        line = "|"

        for i, option in enumerate(self.options):
            if i == self.active_option:
                line += curses.color_pair(1) + option + curses.color_pair(0) # You can do coloring like this? I have to rewrite how I parse stuff if true
            else:
                line += option
            line += " "*(spacing-len(option))

        line += "|"
        self.content[(self.height//3)*2] = line



class SaveBox(SelectBox):
    def __init__(self, height: int, width: int):
        title = "Would you like to save?"
        options = ["YES", "NO"]
        super().__init__(height, width, title, options)



class FileEditor:
    def __init__(self, file: str=""):
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
        self.focus_object = self
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

    def write_header(self) -> None:
        """
            Stickied header containing the filename for now
        """
        file = self.current_file + "*" if self.content != self.original_content else self.current_file
        half_length = (self.columns-len(file))//2
        header = " "*half_length + file + " "*half_length
        self.scr.addstr(0, 0, header, curses.color_pair(1))
        self.move_cursor()

    def write_footer() -> None:
        ...

    def move_cursor(self, y: int=None, x: int=None) -> None:
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

    def handle_movement(self, direction : int) -> bool:
        """
            given an ascii int, will process movement
        """
        match direction:
            case 258: # Arrow Down
                if self.file_y+1 < len(self.content) and self.can_move_y: # If there is more content
                    if self.cursor_y+1 < self.rows: # If your cursor is not at the bottom
                        self.cursor_y += 1
                        self.file_y += 1
                    else: # Bottom of screen
                        self.write_content(line=self.file_y-self.rows+3)
                        self.file_y += 1 # Navigate through file, but not screen

            case 259: # Arrow up
                if self.file_y - 1 >= 0 and self.can_move_y: # Has content
                    if self.cursor_y != 1: # If its in middle of screen
                        self.cursor_y -= 1
                        self.file_y -= 1
                    else: # Top
                        self.file_y -= 1
                        self.write_content(line=self.file_y)

            case 260: # Arrow left
                if self.file_x - 1 >= 0 and self.can_move_x:
                    if self.cursor_x != 0:
                        self.cursor_x -= 1
                        self.file_x -= 1
                    else:
                        if self.file_x - 1 >= 0:
                            self.file_x -= 1
                            self.write_content(line=self.file_y-self.cursor_y+1, index=self.file_x)
                    self.max_x -= 1

            case 261: # Arrow right
                if self.file_x < len(self.content[self.file_y]) and self.can_move_x:
                    if self.cursor_x+3 < self.columns:
                        self.cursor_x += 1
                        self.file_x += 1
                    else:
                        self.file_x += 1
                        self.write_content(line=self.file_y-self.cursor_y+1, index=self.file_x-self.cursor_x)
                    self.max_x += 1

            case _:
                return False
            
        # Set X value to the last character in the line
        end = len(self.content[self.file_y])
        if self.max_x > end:
            self.file_x = end
            self.cursor_x = end

        self.move_cursor()
        return True # Was an arrow key

    def handle_override(self, inp) -> None:
        """
            Overrides are things that can be executed at any time
            This is for things like saving or quitting
        """
        match inp:
            case Inputs.CTRL_O: # Open File
                # box = Box(10, self.columns//2, title="File Name:", centered=True, options=["InputBox"])
                # self.focus_object = box
                # self.focus = "SaveBox"
                # box.draw(self.scr, self.rows//3, self.columns//2//2)
                self.move_cursor()
            case Inputs.CTRL_X: # Close App
                box = SaveBox()
                self.focus_object = box
                self.focus = "SaveBox"
                box.draw()
            case Inputs.CTRL_A:
                if self.focus != "File":
                    self.focus_object = self
                    self.focus = "File"
                    self.write_content(self.file_y, self.file_x)

    def handle_input(self) -> None:
        self.rows, self.columns = self.scr.getmaxyx()
        inp = self.scr.getch()
        if inp in Inputs.OVERRIDES:
            self.handle_override(inp)
        elif type(self.focus) != str:
            self.focus.handle_input(inp)
        else:
            res = self.handle_movement(inp)
            if self.focus == "SaveBox":
                if res == "Yes":
                    self.save_file()
                elif res == "No":
                    self.close()

    def clear_screen(self) -> None:
        """
            Clear everything on the screen, excluding header/footer
        """
        for line in range(1, self.rows-1):
            self.scr.addstr(line, 0, " "*self.columns)
        self.move_cursor() # Reset cursor

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
            if match := re.search(f"{word}\\s\\S*(\\(|:)", line): # Walrus operator my beloved
                for i in range(match.start()+len(word), match.end() - 1):
                    parsed[i] = curses.color_pair(7)

        # Dot notation
        for match in re.finditer(r"[^a-zA-Z]{1}[a-zA-Z]*\.", line):
            for i in range(match.start()+1, match.end()):
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
            if len(self.parsed_content[line_index]) == len(line): # Can't compare directly, so compare size
                return self.parsed_content[line_index]
            return None # Not parsed
        
        except ValueError: # Failed .index
            return None

    def write_line(self, y: int, content: str, index: int = 0, parse: bool | dict = False) -> None:
        """
            Writes a line of content, from index on, at the line y
            Takes an optional parse argument
            True to parse, False to not, or a parsed dict itself
        """
        line = content[index:index+self.columns-2] if index < len(content) else content[index:]
        line += " "*(self.columns-len(line)-1) # Erase any text already there
    
        if parse is True:
            parsed = self.parse_line(line) if not self.check_parsed_cache(content) else self.check_parsed_cache(content)
        elif parse:
            parsed = parse
        else:
            self.scr.addstr(y, 0, line) # TODO: Test if this is faster than adding each character
            return

        for i in range(len(line)):
            color = parsed[i] if i < len(parsed) else curses.color_pair(0)
            self.scr.addch(y, i, line[i], color)

    def write_content(self, line: int=0, index: int=0) -> None:
        """
            Writes all the content in self.content from line to end of screen
            Optional index in case of horizontal scrolling
        """
        for y, text in enumerate(self.content[line:]):
            parsed = self.parse_line(text)
            self.parsed_content[y] = parsed # y = file line, not screen line
            self.write_line(y+1, text, index, parse=True) # y+1 to account for header

            if y+2 >= self.rows:
                break

        self.move_cursor()

    def read_file(self, file : str) -> None:
        """
            Sets attributes to equal a new file, as indicated by a passed string
        """
        self.file_object = open(file)
        self.content = self.file_object.read().split("\n")
        self.original_content = self.content
        self.clear_screen()
        self.write_header()
        self.write_content()

    def save_file(self) -> None:
        self.file_object.close()
        with open(self.current_file, "w") as f:
            f.write("\n".join(self.content))            

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
            self.scr.keypad(True) # Clears window
            if self.current_file: # Argument passed at creation
                self.read_file(self.current_file)
            while self.running:
                self.handle_input()
        except KeyboardInterrupt: # Control+C
            self.close()
        except Exception: # Genuine Error
            self.close() # Gracefully close
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
            self.file_object.close() # Don't save

if __name__ == "__main__":
    try:
        win = FileEditor(sys.argv[1])
    except IndexError:
        win = FileEditor()
    win.run()

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
        self.parsed_content = {}
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

    def draw(self, scr=None, y: int=None, x: int=None) -> None:
        """
            Draws the box on scr at y, x
        """
        scr = scr or self.active_screen
        self.x = x if x is not None else self.x
        self.y = y if y is not None else self.y
        self.active_screen = scr
        
        for i, line in enumerate(self.content):
            try:
                parsed = self.parsed_content[i]
                for index, char in enumerate(line):
                    scr.addch(self.y+i, self.x+index, char, parsed[index])
            except:
                scr.addstr(self.y+i, self.x, line)
            
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

    def draw(self, scr=None, y: int=None, x: int=None) -> None:
        """
            Draws the SelectBox on given screen, or last used screen
        """
        scr = scr or self.active_screen
        cur_y, cur_x = scr.getyx()
        self.x = x if x is not None else self.x
        self.y = y if y is not None else self.y
        self.active_screen = scr

        self._draw_options()
        super().draw(scr=scr, y=y, x=x)
        super().move_cursor(cur_y, cur_x)

    def _draw_options(self) -> None:
        """
            Sets the line about 2/3 down in the box to the options
            Highlights active option
        """
        spacing = (self.width-2) // (len(self.options)+1)
        line = "|"
        parsed = []

        for option in self.options:
            line += " "*(spacing-len(option))
            line += option

        line += " "*(spacing-len(option)+2)
        line += "|"

        for _ in line: # Default Colors
            parsed.append(curses.color_pair(0))

        res = re.search(self.options[self.active_option], line)
        for i in range(res.start(), res.end()): # Active Option
            parsed[i] = curses.color_pair(1)

        self.parsed_content[(self.height//3)*2] = parsed
        self.content[(self.height//3)*2] = line

    def handle_input(self, inp: int) -> int:
        """
            Handles changing the active option as well as returning on enter
        """
        match inp:
            case 260: # Left
                self.active_option = self.active_option-1 if self.active_option-1 >= 0 else self.active_option
            case 261: # Right
                self.active_option = self.active_option+1 if self.active_option+1 < len(self.options) else self.active_option
            case 10: # Enter
                return self.active_option
        self._draw_options()
        self.draw()



class InputBox(BaseBox):
    def __init__(self, height: int, width: int, title: str):
        self.text = ""
        self.input_start = None
        self.active_position = 0
        super().__init__(height, width, title)

    def draw(self, scr=None, y: int=None, x: int=None) -> None:
        scr = scr or self.active_screen
        cur_y, cur_x = scr.getyx()
        self.x = x if x is not None else self.x
        self.y = y if y is not None else self.y
        self.active_screen = scr
        
        self._draw_inputbox()
        self.input_start = self._get_input_start()
        super().draw(scr=scr, y=y, x=x)
        super().move_cursor(self.y+((self.height//3)*2), self.x+self.input_start+self.active_position)

    def _get_input_start(self) -> int:
        for i, char in enumerate(self.content[(self.height//3)*2]):
            if char != "|" and char != " ":
                return i
        return -1

    def _draw_inputbox(self) -> None:
        if self.input_start is None: # First Run
            line = "|" + ("_"*(self.width//2)).center(self.width-2) + "|"
        elif self.input_start:
            line = "|"
            empty_count = (self.width//2)-len(self.text)
            line += (self.text+"_"*(empty_count)).center(self.width-2) + "|"

        self.content[(self.height//3)*2] = line

    def handle_input(self, inp: int) -> str:
        match inp:
            case 260: # Left
                self.active_position -= 1 if self.active_position-1 >= 0 else 0
            case 261: # Right
                self.active_position += 1 if self.active_position+1 <= len(self.text) else 0
            case 10: # Enter
                return self.text
            case 8:
                self.text = self.text[:self.active_position-1] + self.text[self.active_position:] if len(self.text) > 0 else ""
                self.active_position -= 1 if self.active_position-1 >= 0 else 0
            case 127:
                self.text = self.text[:self.active_position-1] + self.text[self.active_position:] if len(self.text) > 0 else ""
                self.active_position -= 1 if self.active_position-1 >= 0 else 0
            case _: # Anything else
                if inp >= 33 and inp <= 126:
                    self.text += chr(inp)
                    self.active_position += 1
        self._draw_inputbox()
        self.draw()



class SaveBox(SelectBox):
    def __init__(self, height: int, width: int):
        title = "Would you like to save?"
        options = ["YES", "NO"]
        super().__init__(height, width, title, options)

    def handle_input(self, inp: int) -> int:
        """
            If the returned option is 0, return True (Save)
            Else return False (Don't save)
        """
        res = super().handle_input(inp)
        if inp == 121:
            return True
        elif inp == 110:
            return False
        if res == 0:
            return True
        elif res == 1:
            return False
        return None



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
        self.scrolled_x = 0
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

    def adjust_x(self, old_line: int, new_line: int):
        old_content = self.content[old_line]
        new_content = self.content[new_line]
        new_start = ""

        if self.scrolled_x:
            self.write_line(self.cursor_y+(old_line-new_line), old_content)

        if len(new_content) <= self.max_x:
            # If the new line is shorter than current x position
            self.file_x = len(new_content)
            if len(new_content) < self.columns-2:
                # If the new line is smaller than the screen
                self.cursor_x = self.file_x
            else:
                # If the new line is larger than the screen
                self.scrolled_x = ((self.file_x-(self.columns-2)) // (self.columns-6)) + 1
                self.scrolled_x = max(0, self.scrolled_x)
                new_start = (self.columns-7)+((self.columns-6)*(self.scrolled_x-1)) if self.scrolled_x != 0 else 0
                self.cursor_x = len(new_content) - new_start - 1
                self.write_line(self.cursor_y, new_content, index=new_start)
        
        else:
            if self.scrolled_x:
                # If the new line is larger than the max position
                self.file_x = self.max_x
                self.scrolled_x = ((self.max_x-(self.columns-2)) // (self.columns-6)) + 1
                self.scrolled_x = max(0, self.scrolled_x)
                # 82, 165, 248 ((self.columns-7)+((self.columns-6)*(self.scrolled_x-1))) 
                # self.columns = 89
                new_start = (self.columns-7)+((self.columns-6)*(self.scrolled_x-1)) if self.scrolled_x != 0 else 0
                self.cursor_x = self.max_x-new_start-1
                self.write_line(self.cursor_y, new_content, index=new_start)
            else:
                self.file_x = self.max_x
                self.cursor_x = self.file_x

    def handle_movement(self, direction : int) -> bool:
        """
            given an ascii int, will process movement
        """

        match direction:
            case 258: # Arrow Down
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
                        self.write_content(self.file_y-self.rows+2)

                    self.adjust_x(old_line, new_line)

            case 259: # Arrow up
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

            case 260: # Arrow left
                if self.file_x - 1 >= 0:
                    # Cursor is not at the start of file
                    self.file_x -= 1

                    if self.cursor_x - 1 >= 0:
                        # Cursor is not at start of screen
                        self.cursor_x -= 1

                        if self.scrolled_x != 0 and self.cursor_x == 3:
                            # Screen is scrolled
                            new_start = max(0, self.file_x-self.columns+2) # 1->0 will be negative
                            self.scrolled_x -= 1
                            self.write_line(y=self.cursor_y, content=self.content[self.file_y], index=new_start)
                            self.cursor_x = self.columns-3

                    self.max_x = self.file_x

            case 261: # Arrow right
                if self.file_x + 1 <= len(self.content[self.file_y]):
                    self.file_x += 1
                    if self.cursor_x + 1 < self.columns-2:
                        self.cursor_x += 1
                    else:
                        self.cursor_x = 4
                        self.write_line(y=self.cursor_y, content=self.content[self.file_y], index=self.file_x-5)
                        self.scrolled_x += 1

                    self.max_x = self.file_x

            case _:
                return False
            

        self.move_cursor()
        return True # Was an arrow key

    def handle_override(self, inp) -> None:
        """
            Overrides are things that can be executed at any time
            This is for things like saving or quitting
        """
        match inp:
            case Inputs.CTRL_O: # Open File
                box = InputBox(height=10, width=self.columns//2, title="Enter File Name")
                self.focus_object = box
                self.focus = "OpenFile"
                box.draw(scr=self.scr, y=self.rows//3, x=self.columns//2//2)

            case Inputs.CTRL_X: # Close App
                box = SaveBox(height=10, width=self.columns//2)
                self.focus_object = box
                self.focus = "SaveBox"
                box.draw(scr=self.scr, y=self.rows//3, x=self.columns//2//2)

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
        elif type(self.focus_object) != type(self):
            res = self.focus_object.handle_input(inp)
            match self.focus:
                case "SaveBox":
                    if res == True:
                        self.save_file()
                        self.close()
                    elif res == False:
                        self.close()
                case "OpenFile":
                    if res:
                        self.read_file(res)
                        self.focus_object = self
                        self.focus = "File"
        else:
            move = self.handle_movement(inp)
            if not move:
                line = self.content[self.file_y]
                if inp == 8 or inp == 127: # Backspace
                    if self.file_x-1 >= 0: # Can erase character
                        line = line[:self.file_x-1] + line[self.file_x:]
                        self.content[self.file_y] = line
                        self.write_line(self.cursor_y, line)
                        self.handle_movement(260)
                        if self.file_x > self.columns - 2:
                            self.adjust_x(self.file_y, self.file_y)
                    else: # Erasing start of line
                        line_end = len(self.content[self.file_y-1])
                        self.content[self.file_y-1] += self.content[self.file_y]
                        self.content = self.content[:self.file_y] + self.content[self.file_y+1:]
                        self.write_content() 
                        self.file_y -= 1
                        self.cursor_y -= 1
                        self.file_x = line_end
                        self.cursor_x = line_end
                        self.adjust_x(self.file_y+1, self.file_y)

                elif inp == 10:
                    line = line[0:self.file_x] + "\n" + line[self.file_x:]
                    self.content = self.content[:self.file_y] + line.split("\n") + self.content[self.file_y+1:]
                    self.write_content()
                    self.file_y += 1
                    self.cursor_y += 1
                    self.file_x = 0
                    self.cursor_x = 0
                    self.adjust_x(self.file_y-1, self.file_y)

                elif (inp >= 33 and inp <= 126) or inp == 32:
                    try:
                        line = line[0:self.file_x] + chr(inp) + line[self.file_x:]
                    except IndexError:
                        line += chr(inp)
                    self.content[self.file_y] = line
                    self.write_line(self.cursor_y, line)
                    self.handle_movement(261)
                    if self.file_x > self.columns - 2:
                        self.adjust_x(self.file_y, self.file_y)
                
                self.move_cursor()
                self.max_x = self.file_x
                

    def clear_screen(self) -> None:
        """
            Clear everything on the screen, excluding header/footer
        """
        for line in range(1, self.rows-1):
            self.scr.addstr(line, 0, " "*self.columns)
        self.scr.addstr(self.rows-1, 0, " "*(self.columns-1))
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

    def write_line(self, y: int, content: str, index: int = 0, parse: bool = True) -> None:
        """
            Writes a line of content, from index on, at the line y
            Takes an optional parse argument
            True to parse, False to not, or a parsed dict itself
        """
        line = content[index:index+self.columns]
        line += " "*(self.columns-len(line)+1) # Erase any text already there

        parsed = []
            
        if parse is True:
            parsed = self.parse_line(line) if not self.check_parsed_cache(content) else self.check_parsed_cache(content)
            parsed = parsed[index:index+self.columns]
        else:
            parsed = [curses.color_pair(0) for i in range(self.columns-2)]
        
        if index > 0: # TODO: Fix the weird edge case (should be as easy as removing the 1s in correct_x)
            line = line[1:]
            parsed = parsed[1:]

        for i in range(min(self.columns-1, len(line)-1)):
            color = parsed[i] if i < len(parsed) else curses.color_pair(0)
            self.scr.addch(y, i, line[i], color)

        if index > 0:
            self.scr.addch(y, 0, "<", curses.color_pair(1))
        if len(content[index:]) >= self.columns-2:
            self.scr.addch(y, self.columns-2, ">", curses.color_pair(1))


    def write_content(self, line: int=0, index: int=0) -> None:
        """
            Writes all the content in self.content from line to end of screen
            Optional index in case of horizontal scrolling
        """
        for y, text in enumerate(self.content[line:]):
            parsed = self.parse_line(text)
            self.parsed_content[y] = parsed # y = file line, not screen line
            self.write_line(y+1, text, index) # y+1 to account for header

            if y+2 >= self.rows:
                break

        self.move_cursor()

    def read_file(self, file : str) -> None:
        """
            Sets attributes to equal a new file, as indicated by a passed string
        """
        self.cursor_y = 1
        self.cursor_x, self.file_x, self.file_y = 0, 0, 0
        if self.file_object:
            self.file_object.close()
        try:
            self.file_object = open(file)
            self.content = self.file_object.read().split("\n")
        except FileNotFoundError:
            self.content = [""]
        self.current_file = file
        self.original_content = self.content
        for line in range(len(self.content)):
            self.parsed_content[line] = self.parse_line(self.content[line])
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

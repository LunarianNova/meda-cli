import curses
import re


class BaseBox:
    """
    A base class for all boxes, extends to input and select
    Meant to be built off of, not used by itself
    """

    def __init__(self, height: int, width: int, title: str) -> None:
        self.height = height
        self.width = width
        self.title = title
        (
            self.y,
            self.x,
        ) = (
            0,
            0,
        )
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
        self.content[self.height // 3] = "|" + self.title.center(self.width - 2) + "|"

    def _draw_border(self) -> None:
        """
        Draws the basic box border into self.content
        """
        self.content.append(" " + "_" * (self.width - 2) + " ")
        for _ in range(self.height - 2):
            self.content.append("|" + " " * (self.width - 2) + "|")
        self.content.append("|" + "_" * (self.width - 2) + "|")

    def draw(self, scr=None, y: int = None, x: int = None) -> None:
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
                    scr.addch(self.y + i, self.x + index, char, parsed[index])
            except:
                scr.addstr(self.y + i, self.x, line)

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
    """
    A box with values that the user can select
    Meant to be extended, not used directly (see SaveBox)
    """

    def __init__(self, height: int, width: int, title: str, options: list) -> None:
        super().__init__(height, width, title)
        self.options = options
        self.active_option = 0

    def draw(self, scr=None, y: int = None, x: int = None) -> None:
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
        spacing = (self.width - 2) // (len(self.options) + 1)
        line = "|"
        parsed = []

        for option in self.options:
            line += " " * (spacing - len(option))
            line += option

        line += " " * (spacing - len(option) + 2)
        line += "|"

        for _ in line:  # Default Colors
            parsed.append(curses.color_pair(0))

        res = re.search(self.options[self.active_option], line)
        for i in range(res.start(), res.end()):  # Active Option
            parsed[i] = curses.color_pair(1)

        self.parsed_content[(self.height // 3) * 2] = parsed
        self.content[(self.height // 3) * 2] = line

    def handle_input(self, inp: int) -> int:
        """
        Handles changing the active option as well as returning on enter
        """
        match inp:
            case 260:  # Left
                self.active_option = (
                    self.active_option - 1
                    if self.active_option - 1 >= 0
                    else self.active_option
                )
            case 261:  # Right
                self.active_option = (
                    self.active_option + 1
                    if self.active_option + 1 < len(self.options)
                    else self.active_option
                )
            case 10:  # Enter
                return self.active_option
        self._draw_options()
        self.draw()


class InputBox(BaseBox):
    """
    A box that takes user text input
    Meant to be used by itself, with an extra title argument passed
    """

    def __init__(self, height: int, width: int, title: str) -> None:
        self.text = ""
        self.input_start = None
        self.active_position = 0
        self.cursor_position = 0
        super().__init__(height, width, title)

    def draw(self, scr=None, y: int = None, x: int = None) -> None:
        scr = scr or self.active_screen
        cur_y, cur_x = scr.getyx()
        self.x = x if x is not None else self.x
        self.y = y if y is not None else self.y
        self.active_screen = scr

        self._draw_inputbox()
        self.input_start = self._get_input_start()
        super().draw(scr=scr, y=y, x=x)
        super().move_cursor(
            self.y + ((self.height // 3) * 2),
            self.x + self.input_start + self.cursor_position,
        )

    def _get_input_start(self) -> int:
        for i, char in enumerate(self.content[(self.height // 3) * 2]):
            if char != "|" and char != " ":
                return i
        return -1

    def _draw_inputbox(self) -> None:
        if self.input_start is None:  # First Run
            line = "|" + ("_" * (self.width // 2)).center(self.width - 2) + "|"
        elif self.input_start:
            line = "|"
            empty_count = (self.width // 2) - len(self.text)
            if len(self.text) <= self.width // 2:
                line += (self.text + "_" * (empty_count)).center(self.width - 2) + "|"
            else:
                line += (
                    self.text[
                        max(0, self.active_position - (self.width // 2)) : max(
                            self.width // 2, self.active_position
                        )
                    ].center(self.width - 2)
                    + "|"
                )

        self.content[(self.height // 3) * 2] = line

    def handle_input(self, inp: int) -> str:
        match inp:
            case 260:  # Left
                self.active_position -= 1 if self.active_position - 1 >= 0 else 0
                if self.cursor_position == self.active_position + 1:
                    self.cursor_position -= 1 if self.cursor_position - 1 >= 0 else 0
            case 261:  # Right
                self.active_position += (
                    1 if self.active_position + 1 <= len(self.text) else 0
                )
                self.cursor_position += (
                    1 if self.cursor_position + 1 <= len(self.text) else 0
                )
            case 10:  # Enter
                return self.text
            case 8:
                self.text = (
                    self.text[: self.active_position - 1]
                    + self.text[self.active_position :]
                    if len(self.text) > 0
                    else ""
                )
                self.active_position -= 1 if self.active_position - 1 >= 0 else 0
                if self.cursor_position == self.active_position + 1:
                    self.cursor_position -= 1 if self.cursor_position - 1 >= 0 else 0
            case 127:
                self.text = (
                    self.text[: self.active_position - 1]
                    + self.text[self.active_position :]
                    if len(self.text) > 0
                    else ""
                )
                self.active_position -= 1 if self.active_position - 1 >= 0 else 0
                if self.cursor_position == self.active_position + 1:
                    self.cursor_position -= 1 if self.cursor_position - 1 >= 0 else 0
            case _:  # Anything else
                if inp >= 33 and inp <= 126:
                    self.text = (
                        self.text[: self.active_position]
                        + chr(inp)
                        + self.text[self.active_position :]
                    )
                    self.active_position += 1
                    self.cursor_position += 1
        if self.cursor_position > self.width // 2:
            self.cursor_position = self.width // 2
        self._draw_inputbox()
        self.draw()


class SaveBox(SelectBox):
    """
    A box for specifically when asking the user to save
    Extends SelectBox, adding its own input handling
    """

    def __init__(self, height: int, width: int) -> None:
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

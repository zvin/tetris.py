# Rules are from https://tetris.fandom.com/wiki/SRS

# [0, 0] is the bottom left

from asyncio import (
    StreamReader,
    StreamReaderProtocol,
    create_task,
    get_event_loop,
    run,
    sleep,
)
from contextlib import contextmanager
from copy import deepcopy
from random import choice
from sys import stdin, stdout
from termios import ECHO, ICANON, TCSADRAIN, tcgetattr, tcsetattr
from textwrap import dedent
from time import time

tetrominoes = {
    "i": [
        [
            [0, 0, 0, 0],
            [1, 1, 1, 1],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
        ],
        [
            [0, 0, 1, 0],
            [0, 0, 1, 0],
            [0, 0, 1, 0],
            [0, 0, 1, 0],
        ],
        [
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [1, 1, 1, 1],
            [0, 0, 0, 0],
        ],
        [
            [0, 1, 0, 0],
            [0, 1, 0, 0],
            [0, 1, 0, 0],
            [0, 1, 0, 0],
        ],
    ],
    "j": [
        [
            [1, 0, 0],
            [1, 1, 1],
            [0, 0, 0],
        ],
        [
            [0, 1, 1],
            [0, 1, 0],
            [0, 1, 0],
        ],
        [
            [0, 0, 0],
            [1, 1, 1],
            [0, 0, 1],
        ],
        [
            [0, 1, 0],
            [0, 1, 0],
            [1, 1, 0],
        ],
    ],
    "l": [
        [
            [0, 0, 1],
            [1, 1, 1],
            [0, 0, 0],
        ],
        [
            [0, 1, 0],
            [0, 1, 0],
            [0, 1, 1],
        ],
        [
            [0, 0, 0],
            [1, 1, 1],
            [1, 0, 0],
        ],
        [
            [1, 1, 0],
            [0, 1, 0],
            [0, 1, 0],
        ],
    ],
    "o": [
        [
            [0, 1, 1, 0],
            [0, 1, 1, 0],
            [0, 0, 0, 0],
        ],
        [
            [0, 1, 1, 0],
            [0, 1, 1, 0],
            [0, 0, 0, 0],
        ],
        [
            [0, 1, 1, 0],
            [0, 1, 1, 0],
            [0, 0, 0, 0],
        ],
        [
            [0, 1, 1, 0],
            [0, 1, 1, 0],
            [0, 0, 0, 0],
        ],
    ],
    "s": [
        [
            [0, 1, 1],
            [1, 1, 0],
            [0, 0, 0],
        ],
        [
            [0, 1, 0],
            [0, 1, 1],
            [0, 0, 1],
        ],
        [
            [0, 0, 0],
            [0, 1, 1],
            [1, 1, 0],
        ],
        [
            [1, 0, 0],
            [1, 1, 0],
            [0, 1, 0],
        ],
    ],
    "t": [
        [
            [0, 1, 0],
            [1, 1, 1],
            [0, 0, 0],
        ],
        [
            [0, 1, 0],
            [0, 1, 1],
            [0, 1, 0],
        ],
        [
            [0, 0, 0],
            [1, 1, 1],
            [0, 1, 0],
        ],
        [
            [0, 1, 0],
            [1, 1, 0],
            [0, 1, 0],
        ],
    ],
    "z": [
        [
            [1, 1, 0],
            [0, 1, 1],
            [0, 0, 0],
        ],
        [
            [0, 0, 1],
            [0, 1, 1],
            [0, 1, 0],
        ],
        [
            [0, 0, 0],
            [1, 1, 0],
            [0, 1, 1],
        ],
        [
            [0, 1, 0],
            [1, 1, 0],
            [1, 0, 0],
        ],
    ],
}

jlstz_wall_kicks = {
    0: {
        1: [
            [0, 0],
            [-1, 0],
            [-1, 1],
            [0, -2],
            [-1, -2],
        ],
        3: [
            [0, 0],
            [1, 0],
            [1, 1],
            [0, -2],
            [1, -2],
        ],
    },
    1: {
        0: [
            [0, 0],
            [1, 0],
            [1, -1],
            [0, 2],
            [1, 2],
        ],
        2: [
            [0, 0],
            [1, 0],
            [1, -1],
            [0, 2],
            [1, 2],
        ],
    },
    2: {
        1: [
            [0, 0],
            [-1, 0],
            [-1, 1],
            [0, -2],
            [-1, -2],
        ],
        3: [
            [0, 0],
            [1, 0],
            [1, 1],
            [0, -2],
            [1, -2],
        ],
    },
    3: {
        0: [
            [0, 0],
            [-1, 0],
            [-1, -1],
            [0, 2],
            [-1, 2],
        ],
        2: [
            [0, 0],
            [-1, 0],
            [-1, -1],
            [0, 2],
            [-1, 2],
        ],
    },
}

i_wall_kicks = {
    0: {
        1: [
            [0, 0],
            [-2, 0],
            [1, 0],
            [-2, -1],
            [1, 2],
        ],
        3: [
            [0, 0],
            [-1, 0],
            [2, 0],
            [-1, -2],
            [2, -1],
        ],
    },
    1: {
        0: [
            [0, 0],
            [2, 0],
            [-0, 0],
            [2, 1],
            [-1, -2],
        ],
        2: [
            [0, 0],
            [-1, 0],
            [2, 0],
            [-1, 2],
            [2, -1],
        ],
    },
    2: {
        1: [
            [0, 0],
            [1, 0],
            [-2, 0],
            [1, -2],
            [-2, 1],
        ],
        3: [
            [0, 0],
            [2, 0],
            [-1, 0],
            [2, 1],
            [-1, -2],
        ],
    },
    3: {
        0: [
            [0, 0],
            [1, 0],
            [-2, 0],
            [1, -2],
            [-2, 1],
        ],
        2: [
            [0, 0],
            [-2, 0],
            [1, 0],
            [-2, -1],
            [1, 2],
        ],
    },
}

wall_kicks = {
    "j": jlstz_wall_kicks,
    "l": jlstz_wall_kicks,
    "s": jlstz_wall_kicks,
    "t": jlstz_wall_kicks,
    "z": jlstz_wall_kicks,
    "i": i_wall_kicks,
}

shapes = list(tetrominoes.keys())

blue = [0, 0, 255]
orange = [252, 171, 0]
yellow = [255, 255, 0]
green = [0, 255, 0]
purple = [154, 0, 254]
red = [255, 0, 0]
cyan = [0, 255, 255]

tetromino_colors = {
    "j": blue,
    "l": orange,
    "o": yellow,
    "s": green,
    "t": purple,
    "z": red,
    "i": cyan,
}

mini_t_spin_points = {
    0: 100,
    1: 200,
    2: 400,
}
t_spin_points = {
    0: 400,
    1: 800,
    2: 1200,
    3: 1600,
}
points = {
    1: 100,
    2: 300,
    3: 500,
    4: 800,
}


render_width_multiplier = 2


class Game:
    test = False
    debug_lines = []
    width = 10
    visible_height = 20
    height = visible_height * 2
    level = 1
    score = 0
    paused = False
    last_movement = None
    wall_kicked = False
    game_over = False
    bag = []
    current_shape = None
    current_row = None
    current_column = None
    current_rotation = None

    def __init__(self, grid=None):
        if grid is None:
            self.grid = [[None] * self.width for i in range(self.height)]
        else:
            self.grid = grid
            self.height = len(self.grid)
            self.visible_height = self.height // 2
            self.width = len(self.grid[0])
        self.next_shape = self.random_shape()

    def move(self, delta):
        if self.paused:
            return
        next_column = self.current_column + delta
        if self.tetromino_fits(
            self.current_shape, next_column, self.current_row, self.current_rotation
        ):
            self.current_column = next_column
            self.last_movement = "move"
            self.render()

    def rotate(self, direction):
        if self.paused:
            return
        if self.current_shape == "o":
            return
        next_rotation = (self.current_rotation + direction) % 4
        for i, wall_kick in enumerate(
            wall_kicks[self.current_shape][self.current_rotation][next_rotation]
        ):
            next_column = self.current_column + wall_kick[0]
            next_row = self.current_row + wall_kick[1]
            if self.tetromino_fits(
                self.current_shape, next_column, next_row, next_rotation
            ):
                self.current_rotation = next_rotation
                self.current_row = next_row
                self.current_column = next_column
                self.last_movement = "rotate"
                self.render()
                break
        self.wall_kicked = i != 0

    def random_shape(self):
        if len(self.bag) == 0:
            self.bag = shapes[:]
        shape = choice(self.bag)
        self.bag.remove(shape)
        return shape

    def new_tetromino(self):
        self.current_shape = self.next_shape
        self.next_shape = self.random_shape()
        [current_column, current_row] = self.spawn_position(self.current_shape)
        self.current_column = current_column
        self.current_row = current_row
        self.current_rotation = 0

    def pause(self):
        self.paused = not self.paused
        self.render()

    def t_corner_count(self, row, column):
        count = 0
        for i in [0, 2]:
            for j in [0, 2]:
                r = row + i
                c = column + j
                if (
                    not self.in_bounds(r, c)
                    or self.grid[row + i][column + j] is not None
                ):
                    count += 1
        return count

    def update_score(self, lines_removed, t_spin, mini_t_spin):
        p = points
        if t_spin:
            p = t_spin_points
        elif mini_t_spin:
            p = mini_t_spin_points
        self.score += p.get(lines_removed, 0) * self.level
        if self.score >= level_goal(self.level):
            self.level += 1

    def move_down(self, soft_drop=False, hard_drop=False):
        if self.paused:
            return
        if self.tetromino_touches_ground(
            self.current_shape,
            self.current_column,
            self.current_row,
            self.current_rotation,
        ):
            t_spin = False
            mini_t_spin = False
            if self.last_movement == "rotate":
                if self.t_corner_count(self.current_row, self.current_column) >= 3:
                    if self.wall_kicked:
                        mini_t_spin = True
                    else:
                        t_spin = True
            put_tetromino(
                self.grid,
                self.current_shape,
                self.current_column,
                self.current_row,
                self.current_rotation,
            )
            self.remove_complete_lines(t_spin, mini_t_spin)
            if self.tetromino_touches_ceiling(
                self.current_shape,
                self.current_column,
                self.current_row,
                self.current_rotation,
            ):
                self.game_over = True
            self.new_tetromino()
            return True
        self.current_row -= 1
        self.last_movement = "down"
        if soft_drop:
            self.score += 1
        if hard_drop:
            self.score += 2
        else:
            self.render()

    def remove_complete_lines(self, t_spin, mini_t_spin):
        self.grid[:] = [row for row in self.grid if not all(row)]
        lines_removed = self.height - len(self.grid)
        self.update_score(lines_removed, t_spin, mini_t_spin)
        while len(self.grid) < self.height:
            self.grid.append([None] * self.width)

    def hard_drop(self):
        if self.paused:
            return
        while not self.move_down(hard_drop=True):
            pass
        self.render()

    def spawn_position(self, shape):
        row = self.visible_height
        column = (self.width - tetromino_width(shape)) // 2
        return [column, row]

    def in_bounds(self, row, column):
        return row >= 0 and column >= 0 and column < self.width

    def tetromino_fits(self, shape, column, row, rotation):
        return all(
            self.in_bounds(row + i, column + j)
            and self.grid[row + i][column + j] is None
            for [i, j] in grid_iterator(shape, column, row, rotation)
        )

    def tetromino_touches_ground(self, shape, column, row, rotation):
        return not self.tetromino_fits(shape, column, row - 1, rotation)

    def tetromino_touches_ceiling(self, shape, column, row, rotation):
        return any(
            row + i == self.visible_height
            for [i, j] in grid_iterator(shape, column, row, rotation)
        )

    def get_ghost_row(self):
        ghost_row = self.current_row
        while not self.tetromino_touches_ground(
            self.current_shape, self.current_column, ghost_row, self.current_rotation
        ):
            ghost_row -= 1
        return ghost_row

    def render_grid(self):
        visible_grid = deepcopy(self.grid)
        put_tetromino(
            visible_grid,
            self.current_shape,
            self.current_column,
            self.get_ghost_row(),
            self.current_rotation,
            "🮙",
        )
        put_tetromino(
            visible_grid,
            self.current_shape,
            self.current_column,
            self.current_row,
            self.current_rotation,
        )
        lines = [
            "".join(
                (
                    " " * render_width_multiplier
                    if cell is None
                    else color_string(cell[0] * render_width_multiplier, cell[1])
                    for cell in line
                )
            )
            for line in list(reversed(visible_grid))[self.visible_height :]
        ]
        return frame(lines, "", self.width * render_width_multiplier)

    def render_preview(self):
        next_tetromino = tetrominoes[self.next_shape][0]
        padding = " " if tetromino_width(self.next_shape) == 3 else ""
        block = " " * render_width_multiplier
        return [
            "".join(
                (
                    padding,
                    *(
                        block
                        if cell == 0
                        else color_string(block, tetromino_colors[self.next_shape])
                        for cell in tetromino_line
                    ),
                    padding,
                )
            )
            for tetromino_line in next_tetromino[:2]
        ]

    def render(self, clr=True):
        lines = self.render_grid()
        render_side(lines, 0, "next", self.render_preview(), 8)
        render_side(lines, 4, "score", ["{:>8}".format(self.score)])
        render_side(lines, 7, "level", ["{:>8}".format(self.level)])
        render_side(lines, 10, "controls", controls)
        if self.paused:
            lines[20] += " PAUSED"
        if not self.test:
            clear()
        lines += self.debug_lines
        print("\n".join(lines))
        if not self.test:
            hide_cursor()

    def interval(self):
        return (0.8 - ((self.level - 1) * 0.007)) ** (self.level - 1)

    def debug(self, *args):
        self.debug_lines.append(" ".join(map(str, args)))
        self.debug_lines = self.debug_lines[-5:]

    async def timer(self):
        target_time = time()
        while not self.game_over:
            target_time += self.interval()
            await sleep(target_time - time())
            if self.game_over:
                break
            yield

    async def game_loop(self):
        # TODO: move out of Game
        self.new_tetromino()
        create_task(self.handle_input())
        try:
            async for tick in self.timer():
                self.move_down()
            print("game over, score:", self.score)
        finally:
            show_cursor()

    async def handle_input(self):
        # TODO: move out of Game
        q = []
        with raw_mode(stdin):
            reader = StreamReader()
            loop = get_event_loop()
            await loop.connect_read_pipe(lambda: StreamReaderProtocol(reader), stdin)
            while not reader.at_eof():
                ch = await reader.read(1)
                # '' means EOF, chr(4) means EOT (sent by CTRL+D on UNIX terminals)
                if not ch or ord(ch) <= 4:
                    break
                elif ch == b"q":
                    self.game_over = True
                elif ch == b"p":
                    self.pause()
                elif ch == b"x":
                    self.rotate(-1)
                elif ch == b" ":
                    self.hard_drop()
                elif ch == b"\x1b":
                    q.append(ch)
                elif q == [b"\x1b"] and ch == b"[":
                    q.append(ch)
                elif q == [b"\x1b", b"["]:
                    if ch == b"D":
                        # left
                        self.move(-1)
                    elif ch == b"C":
                        # right
                        self.move(1)
                    elif ch == b"A":
                        # up
                        self.rotate(1)
                    elif ch == b"B":
                        # down
                        self.move_down(soft_drop=True)
                    q.clear()


def color_string(text, color):
    return "\x1b[48;2;{};{};{}m{}\x1b[0m".format(*color, text)


def tetromino_width(shape):
    return len(tetrominoes[shape][0][0])


def grid_iterator(shape, column, row, rotation):
    for i, line in enumerate(reversed(tetrominoes[shape][rotation])):
        for j, cell in enumerate(line):
            if cell:
                yield [i, j]


def put_tetromino(grid, shape, column, row, rotation, character=" "):
    for [i, j] in grid_iterator(shape, column, row, rotation):
        grid[row + i][column + j] = (character, tetromino_colors[shape])


def clear():
    print("\x1bc")


def hide_cursor():
    stdout.write("\033[?25l")
    stdout.flush()


def show_cursor():
    stdout.write("\033[?25h")
    stdout.flush()


def frame(lines, title, width=None):
    if width is None:
        width = max(len(line) for line in lines)
    padding_left = (width - len(title)) // 2
    padding_right = width - len(title) - padding_left
    return [
        "┏" + "━" * padding_left + title + "━" * padding_right + "┓",
        *("┃" + line + " " * (width - len(line)) + "┃" for line in lines),
        "┗" + "━" * width + "┛",
    ]


def render_side(lines, n, title, data, width=None):
    # lines are lines rendered by render_grid()
    data = frame(data, title, width)
    for i, line in enumerate(data):
        lines[n + i] += " " + line


controls = (
    dedent(
        """
            🠅: rotate cw
            🠄: left
            🠆: right
            🠇: soft drop
            x rotate ccw
            ␣: hard drop
            p: pause
            q: quit
        """
    )
    .strip()
    .split("\n")
)


@contextmanager
def raw_mode(file):
    old_attrs = tcgetattr(file.fileno())
    new_attrs = old_attrs[:]
    new_attrs[3] = new_attrs[3] & ~(ECHO | ICANON)
    try:
        tcsetattr(file.fileno(), TCSADRAIN, new_attrs)
        yield
    finally:
        tcsetattr(file.fileno(), TCSADRAIN, old_attrs)


def level_goal(level):
    return sum(range(level + 1)) * 500


if __name__ == "__main__":
    game = Game()
    run(game.game_loop())

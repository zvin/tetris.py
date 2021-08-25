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

width = 10
visible_height = 20
height = visible_height * 2
render_width_multiplier = 2
level = 1
score = 0
paused = False

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


grid = [[None] * width for i in range(height)]
game_over = False
bag = []


def color_string(text, color):
    return "\x1b[48;2;{};{};{}m{}\x1b[0m".format(*color, text)


def tetromino_width(shape):
    return len(tetrominoes[shape][0][0])


def spawn_position(shape):
    row = visible_height
    column = (width - tetromino_width(shape)) // 2
    return [column, row]


def grid_iterator(shape, column, row, rotation):
    for i, line in enumerate(reversed(tetrominoes[shape][rotation])):
        for j, cell in enumerate(line):
            if cell:
                yield [i, j]


def put_tetromino(grid, shape, column, row, rotation, character=" "):
    for [i, j] in grid_iterator(shape, column, row, rotation):
        grid[row + i][column + j] = (character, tetromino_colors[shape])


def in_bounds(row, column):
    return row >= 0 and column >= 0 and column < width


def tetromino_fits(shape, column, row, rotation):
    return all(
        in_bounds(row + i, column + j) and grid[row + i][column + j] is None
        for [i, j] in grid_iterator(shape, column, row, rotation)
    )


def tetromino_touches_ground(shape, column, row, rotation):
    return not tetromino_fits(shape, column, row - 1, rotation)


def tetromino_touches_ceiling(shape, column, row, rotation):
    return any(
        row + i == visible_height
        for [i, j] in grid_iterator(shape, column, row, rotation)
    )


def move(delta):
    if paused:
        return
    global current_column
    next_column = current_column + delta
    if tetromino_fits(current_shape, next_column, current_row, current_rotation):
        current_column = next_column
        render()


def rotate(direction):
    global current_rotation, current_column, current_row
    if paused:
        return
    if current_shape == "o":
        return
    next_rotation = (current_rotation + direction) % 4
    for wall_kick in wall_kicks[current_shape][current_rotation][next_rotation]:
        next_column = current_column + wall_kick[0]
        next_row = current_row + wall_kick[1]
        if tetromino_fits(current_shape, next_column, next_row, next_rotation):
            current_rotation = next_rotation
            current_row = next_row
            current_column = next_column
            render()
            break


def random_shape():
    global bag
    if len(bag) == 0:
        bag = shapes[:]
    shape = choice(bag)
    bag.remove(shape)
    return shape


def clear():
    print("\x1bc")


def hide_cursor():
    stdout.write("\033[?25l")
    stdout.flush()


def show_cursor():
    stdout.write("\033[?25h")
    stdout.flush()


def get_ghost_row():
    ghost_row = current_row
    while not tetromino_touches_ground(
        current_shape, current_column, ghost_row, current_rotation
    ):
        ghost_row -= 1
    return ghost_row


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


def render_grid():
    visible_grid = deepcopy(grid)
    put_tetromino(
        visible_grid,
        current_shape,
        current_column,
        get_ghost_row(),
        current_rotation,
        "🮙",
    )
    put_tetromino(
        visible_grid, current_shape, current_column, current_row, current_rotation
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
        for line in list(reversed(visible_grid))[visible_height:]
    ]
    return frame(lines, "", width * render_width_multiplier)


def render_side(lines, n, title, data, width=None):
    # lines are lines rendered by render_grid()
    data = frame(data, title, width)
    for i, line in enumerate(data):
        lines[n + i] += " " + line


def render_preview():
    next_tetromino = tetrominoes[next_shape][0]
    padding = " " if tetromino_width(next_shape) == 3 else ""
    block = " " * render_width_multiplier
    return [
        "".join(
            (
                padding,
                *(
                    block
                    if cell == 0
                    else color_string(block, tetromino_colors[next_shape])
                    for cell in tetromino_line
                ),
                padding,
            )
        )
        for tetromino_line in next_tetromino[:2]
    ]


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


def render():
    lines = render_grid()
    render_side(lines, 0, "next", render_preview(), 8)
    render_side(lines, 4, "score", ["{:>8}".format(score)])
    render_side(lines, 7, "level", ["{:>8}".format(level)])
    render_side(lines, 10, "controls", controls)
    if paused:
        lines[19] += " PAUSED"
    clear()
    print("\n".join(lines))
    hide_cursor()


def new_tetromino():
    global current_shape, current_column, current_row, current_rotation, next_shape
    current_shape = next_shape
    next_shape = random_shape()
    [current_column, current_row] = spawn_position(current_shape)
    current_rotation = 0


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


def pause():
    global paused
    paused = not paused
    render()


async def handle_input():
    global game_over
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
                game_over = True
            elif ch == b"p":
                pause()
            elif ch == b"x":
                rotate(-1)
            elif ch == b" ":
                hard_drop()
            elif ch == b"\x1b":
                q.append(ch)
            elif q == [b"\x1b"] and ch == b"[":
                q.append(ch)
            elif q == [b"\x1b", b"["]:
                if ch == b"D":
                    # left
                    move(-1)
                elif ch == b"C":
                    # right
                    move(1)
                elif ch == b"A":
                    # up
                    rotate(1)
                elif ch == b"B":
                    # down
                    move_down(soft_drop=True)
                q.clear()


def update_score(lines_removed):
    global score, level
    points = {
        1: 100,
        2: 300,
        3: 500,
        4: 800,
    }
    score += points.get(lines_removed, 0) * level
    if score >= level_goal(level):
        level += 1


def level_goal(level):
    return sum(range(level + 1)) * 500


def remove_complete_lines():
    grid[:] = [row for row in grid if not all(row)]
    lines_removed = height - len(grid)
    update_score(lines_removed)
    while len(grid) < height:
        grid.append([None] * width)


def hard_drop():
    if paused:
        return
    while not move_down(hard_drop=True):
        pass
    render()


def move_down(soft_drop=False, hard_drop=False):
    global current_row, game_over, score
    if paused:
        return
    if tetromino_touches_ground(
        current_shape, current_column, current_row, current_rotation
    ):
        put_tetromino(
            grid, current_shape, current_column, current_row, current_rotation
        )
        remove_complete_lines()
        if tetromino_touches_ceiling(
            current_shape, current_column, current_row, current_rotation
        ):
            game_over = True
        new_tetromino()
        return True
    current_row -= 1
    if soft_drop:
        score += 1
    if hard_drop:
        score += 2
    else:
        render()


def interval():
    return (0.8 - ((level - 1) * 0.007)) ** (level - 1)


next_shape = random_shape()


async def game_loop():
    new_tetromino()
    create_task(handle_input())
    try:
        while not game_over:
            move_down()
            if game_over:
                break
            await sleep(interval())
        print("game over, score:", score)
    finally:
        show_cursor()


run(game_loop())

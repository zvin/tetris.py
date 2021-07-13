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
from math import floor
from random import choice
from sys import stdin, stdout
from termios import ECHO, ICANON, TCSADRAIN, tcgetattr, tcsetattr

width = 10
height = 20
frequency = 2

render_width_multiplier = 2

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


def color_string(text, color):
    return "\x1b[48;2;{};{};{}m{}\x1b[0m".format(*color, text)


grid = [[None] * width for i in range(height)]


def tetromino_width(shape):
    return len(tetrominoes[shape][0][0])


def tetromino_height(shape):
    return len(tetrominoes[shape][0])


def spawn_position(shape):
    row = height
    column = floor((width - tetromino_width(shape)) / 2)
    return [column, row]


def put_tetromino(grid, shape, column, row, rotation):
    for i, line in enumerate(reversed(tetrominoes[shape][rotation])):
        for j, cell in enumerate(line):
            if cell:
                try:
                    # TODO: check bounds instead
                    grid[row + i][column + j] = tetromino_colors[shape]
                except:
                    pass


def tetromino_fits(shape, column, row, rotation):
    for i, line in enumerate(reversed(tetrominoes[shape][rotation])):
        for j, cell in enumerate(line):
            if cell and grid[row + i][column + j] is not None:
                return False
    return True


def tetromino_touches_ground(shape, column, row, rotation):
    for i, line in enumerate(reversed(tetrominoes[shape][rotation])):
        for j, cell in enumerate(line):
            try:
                # TODO: check bounds instead
                if cell and (row + i == 0 or grid[row + i - 1][column + j] is not None):
                    return True
            except:
                pass
    return False


def tetromino_touches_ceiling(shape, column, row, rotation):
    # TODO: only check the highest row
    for i, line in enumerate(reversed(tetrominoes[shape][rotation])):
        for j, cell in enumerate(line):
            try:
                # TODO: check bounds instead
                if cell and row + i == height + 1:
                    return True
            except:
                pass
    return False


def tetromino_touches_left(shape, column, row, rotation):
    # TODO: only check the leftmost blocks
    for i, line in enumerate(reversed(tetrominoes[shape][rotation])):
        for j, cell in enumerate(line):
            try:
                # TODO: check bounds instead
                if cell and (
                    column + j == 0 or grid[row + i][column + j - 1] is not None
                ):
                    return True
            except:
                pass
    return False


def tetromino_touches_right(shape, column, row, rotation):
    # TODO: only check the rightmost blocks
    for i, line in enumerate(reversed(tetrominoes[shape][rotation])):
        for j, cell in enumerate(line):
            try:
                # TODO: check bounds instead
                if cell and (
                    column + j == width - 1 or grid[row + i][column + j + 1] is not None
                ):
                    return True
            except:
                pass
    return False


def move_left():
    global current_column
    if not tetromino_touches_left(
        current_shape, current_column, current_row, current_rotation
    ):
        current_column -= 1
        render()


def move_right():
    global current_column
    if not tetromino_touches_right(
        current_shape, current_column, current_row, current_rotation
    ):
        current_column += 1
        render()


def rotate():
    global current_rotation, current_column, current_row
    if current_shape == "o":
        return
    next_rotation = (current_rotation + 1) % 4
    for wall_kick in wall_kicks[current_shape][current_rotation][next_rotation]:
        next_column = current_column + wall_kick[0]
        next_row = current_row + wall_kick[1]
        if not (
            tetromino_touches_left(current_shape, next_column, next_row, next_rotation)
            or tetromino_touches_right(
                current_shape, next_column, next_row, next_rotation
            )
            or tetromino_touches_ground(
                current_shape, next_column, next_row, next_rotation
            )
        ):
            current_rotation = next_rotation
            current_row = next_row
            current_column = next_column
            render()
            break


bag = []


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


def render():
    clear()
    visible_grid = deepcopy(grid)
    put_tetromino(
        visible_grid, current_shape, current_column, current_row, current_rotation
    )
    print("┏" + "━" * width * render_width_multiplier + "┓")
    for line in reversed(visible_grid):
        print("┃", end="")
        for cell in line:
            cell_repr = (
                " " * render_width_multiplier
                if cell is None
                else color_string(" " * render_width_multiplier, cell)
            )
            print(cell_repr, end="")
        print("┃")
    print("┗" + "━" * width * render_width_multiplier + "┛")
    hide_cursor()


def new_tetromino():
    global current_shape, current_column, current_row, current_rotation
    current_shape = random_shape()
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


async def handle_input():
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
            elif ch == b"\x1b":
                q.append(ch)
                continue
            elif q == [b"\x1b"] and ch == b"[":
                q.append(ch)
                continue
            elif q == [b"\x1b", b"["]:
                if ch == b"D":
                    # left
                    move_left()
                elif ch == b"C":
                    # right
                    move_right()
                elif ch == b"A":
                    # up
                    rotate()
                elif ch == b"B":
                    # down
                    move_down()
                q.clear()
                continue


def remove_complete_lines():
    grid[:] = [row for row in grid if not all(row)]
    while len(grid) < height:
        grid.append([None] * width)


def move_down():
    global current_row, game_over
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
            return
        new_tetromino()
    current_row -= 1
    render()


game_over = False


async def game_loop():
    create_task(handle_input())
    new_tetromino()
    while not game_over:
        move_down()
        if game_over:
            break
        await sleep(1 / frequency)
    print("game over")


run(game_loop())

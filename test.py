from textwrap import dedent
import unittest

from tetris import Game


pink = [255, 192, 203]


def game_with_grid(
    matrix=None, shape=None, rotation=None, row=None, column=None, width=10, height=20
):
    if matrix is None:
        grid = None
    else:
        lines = list(reversed(dedent(matrix).strip("\n").split("\n")))
        # Add missing top lines
        lines += ["0" * width for i in range(height - len(lines))]
        # Double the rows count
        lines += ["0" * width for i in range(len(lines))]
        grid = [
            [None if char in ("0", "░") else (" ", pink) for char in line]
            for line in lines
        ]
    game = Game(grid)
    game.test = True
    if shape is not None:
        game.current_shape = shape
    if rotation is not None:
        game.current_rotation = rotation
    if row is not None:
        game.current_row = row
    if column is not None:
        game.current_column = column
    return game


class TestTetris(unittest.TestCase):
    def test_initial_score_and_level(self):
        game = Game()
        self.assertEqual(game.score, 0)
        self.assertEqual(game.level, 1)

    def test_wall_kick_i_left(self):
        game = game_with_grid(None, "i", 3, 10, -1)
        game.rotate(1)
        self.assertEqual(game.current_column, 0)
        self.assertEqual(game.current_rotation, 0)
        self.assertEqual(game.current_row, 10)
        self.assertEqual(game.last_movement, "rotate")
        self.assertEqual(game.wall_kicked, True)

    def test_wall_kick_i_left_2(self):
        game = game_with_grid(None, "i", 1, 10, -2)
        game.rotate(1)
        self.assertEqual(game.current_column, 0)
        self.assertEqual(game.current_rotation, 2)
        self.assertEqual(game.current_row, 10)
        self.assertEqual(game.last_movement, "rotate")
        self.assertEqual(game.wall_kicked, True)

    def test_t_spin_simple(self):
        matrix = """
            ██░░░░░░░░
            █░░░░░░░░░
            ██░███████
        """
        game = game_with_grid(matrix, "t", 0, 0, 1)
        game.rotate(-1)
        game.move_down()
        self.assertEqual(game.last_movement, "rotate")
        self.assertEqual(game.wall_kicked, False)
        self.assertEqual(game.score, 800)

    def test_t_spin_double(self):
        matrix = """
            ░░░░░░██░░
            ████░░░███
            █████░████
        """
        game = game_with_grid(matrix, "t", 3, 0, 4)
        game.rotate(-1)
        game.move_down()
        self.assertEqual(game.last_movement, "rotate")
        self.assertEqual(game.wall_kicked, False)
        self.assertEqual(game.score, 1200)

    def test_mini_t_spin_double(self):
        matrix = """
            ░░██░░██░░
            ████░░░███
            █████░████
        """
        game = game_with_grid(matrix, "t", 1, 1, 3)
        game.rotate(1)
        game.move_down()
        self.assertEqual(game.last_movement, "rotate")
        self.assertEqual(game.wall_kicked, True)
        self.assertEqual(game.score, 400)

    def test_mini_t_spin_simple_floor(self):
        matrix = """
            ░░░░░░████
            ████░░████
            ███░░░████
        """
        game = game_with_grid(matrix, "t", 3, 0, 4)
        game.rotate(1)
        game.move_down()
        self.assertEqual(game.last_movement, "rotate")
        self.assertEqual(game.wall_kicked, True)
        self.assertEqual(game.score, 200)


if __name__ == "__main__":
    unittest.main()

# -*- coding: utf-8 -*-
"""
Copyright (C) 2024  walker li <walker8088@gmail.com>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

from .common import RED, BLACK, opposite_color, fench_to_species


# pylint: disable=invalid-name,too-few-public-methods


def abs_diff(pos1, pos2):
    """计算两个位置坐标的绝对差值 (dx, dy)。"""
    return (abs(pos1[0] - pos2[0]), abs(pos1[1] - pos2[1]))


_advisor_pos = (
    (),
    ((3, 7), (5, 7), (4, 8), (3, 9), (5, 9)),  # RED (bottom)
    ((3, 0), (5, 0), (4, 1), (3, 2), (5, 2)),  # BLACK (top)
)

_bishop_pos = (
    (),
    ((2, 5), (6, 5), (0, 7), (4, 7), (8, 7), (2, 9), (6, 9)),  # RED (bottom)
    ((2, 0), (6, 0), (0, 2), (4, 2), (8, 2), (2, 4), (6, 4)),  # BLACK (top)
)


# -----------------------------------------------------#
class Piece:
    """棋子基类，定义棋子的基本属性和通用合法性检查。"""

    def __init__(self, board, fench, pos):
        """初始化棋子。

        参数:
            board (ChessBoard): 所属棋盘对象。
            fench (str): 棋子的 FEN 字符。
            pos (tuple): 棋子的当前坐标 (x, y)。
        """
        self.board = board
        self.fench = fench
        self.x, self.y = pos
        self.species, self.color = fench_to_species(fench)

    @staticmethod
    def create(board, fench, pos):
        """静态工厂方法：根据 FEN 字符创建具体的棋子子类实例。"""
        species, _ = fench_to_species(fench)
        if species == "k":
            return King(board, fench, pos)
        if species == "a":
            return Advisor(board, fench, pos)
        if species == "b":
            return Bishop(board, fench, pos)
        if species == "n":
            return Knight(board, fench, pos)
        if species == "r":
            return Rook(board, fench, pos)
        if species == "c":
            return Cannon(board, fench, pos)
        if species == "p":
            return Pawn(board, fench, pos)
        return None

    def is_valid_pos(self, pos):
        """判断坐标是否在 9x10 棋盘范围内。"""
        return (0 <= pos[0] <= 8) and (0 <= pos[1] <= 9)

    def is_valid_move(self, pos_to):
        """判断移动到目标位置是否合法（子类需覆盖）。"""
        return self.is_valid_pos(pos_to)


# -----------------------------------------------------#
# 将/帅
class King(Piece):
    """将/帅棋子，只能在九宫格内走动，且有白脸将规则。"""

    def is_valid_pos(self, pos):
        """判断位置是否在己方九宫格内。"""
        if not super().is_valid_pos(pos):
            return False

        if pos[0] < 3 or pos[0] > 5:
            return False

        if (self.color == RED) and (pos[1] < 7): # Corrected: RED is at bottom
            return False

        if (self.color == BLACK) and (pos[1] > 2): # Corrected: BLACK is at top
            return False

        return True

    def is_valid_move(self, pos_to):
        """判断将/帅移动到目标位置是否合法（含白脸将规则）。"""
        k2 = self.board.get_king(opposite_color(self.color))
        # 白脸将 (Flying General)
        if (
            k2 and (self.x == k2.x)
            and (pos_to[0] == k2.x) # Target must stay on same column for flying
            and (self.board.get_fench(pos_to) == k2.fench)
            and (self.board.count_y_line_in(self.x, self.y, k2.y) == 0)
        ):
            return True

        if not self.is_valid_pos(pos_to):
            return False

        diff = abs_diff(pos_to, (self.x, self.y))

        return (diff[0] + diff[1]) == 1

    def create_moves(self):
        """生成将/帅所有可能的合法走子。"""
        poss = [
            (self.x + 1, self.y),
            (self.x - 1, self.y),
            (self.x, self.y + 1),
            (self.x, self.y - 1),
        ]

        k2 = self.board.get_king(opposite_color(self.color))
        if k2: poss.append((k2.x, k2.y))

        curr_pos = (self.x, self.y)
        moves = [(curr_pos, to_pos) for to_pos in poss]
        return filter(self.board.is_valid_move_t, moves)


# -----------------------------------------------------#
# 士
class Advisor(Piece):
    """士/仕棋子，只能在九宫格内斜走。"""

    def is_valid_pos(self, pos):
        """判断位置是否在己方九宫格内的士位上。"""
        if not super().is_valid_pos(pos):
            return False
        return pos in _advisor_pos[self.color]

    def is_valid_move(self, pos_to):
        """判断士/仕斜走一步到目标位置是否合法。"""
        if not self.is_valid_pos(pos_to):
            return False

        if abs_diff((self.x, self.y), pos_to) == (1, 1):
            return True

        return False

    def create_moves(self):
        """生成士/仕所有可能的合法走子。"""
        poss = [
            (self.x + 1, self.y + 1),
            (self.x + 1, self.y - 1),
            (self.x - 1, self.y + 1),
            (self.x - 1, self.y - 1),
        ]
        curr_pos = (self.x, self.y)
        moves = [(curr_pos, to_pos) for to_pos in poss]
        return filter(self.board.is_valid_move_t, moves)


# -----------------------------------------------------#
# 象
class Bishop(Piece):
    """象/相棋子，走田字，不能过河。"""

    def is_valid_pos(self, pos):
        """判断位置是否在己方半场内的象位上。"""
        if not super().is_valid_pos(pos):
            return False

        return pos in _bishop_pos[self.color]

    def is_valid_move(self, pos_to):
        """判断象/相走田字到目标位置是否合法（含塞象眼和过河检查）。"""
        if abs_diff((self.x, self.y), (pos_to)) != (2, 2):
            return False

        if not self.is_valid_pos(pos_to):
            return False

        # 检查塞象眼
        eye_pos = ((self.x + pos_to[0]) // 2, (self.y + pos_to[1]) // 2)
        if self.board.get_fench(eye_pos) is not None:
            return False

        return True

    def create_moves(self):
        """生成象/相所有可能的合法走子。"""
        poss = [
            (self.x + 2, self.y + 2),
            (self.x + 2, self.y - 2),
            (self.x - 2, self.y + 2),
            (self.x - 2, self.y - 2),
        ]
        curr_pos = (self.x, self.y)
        moves = [(curr_pos, to_pos) for to_pos in poss]
        return filter(self.board.is_valid_move_t, moves)


# -----------------------------------------------------#
# 马
class Knight(Piece):
    """马棋子，走日字，含蹩马腿规则。"""

    def is_valid_move(self, pos_to):
        """判断马走日字到目标位置是否合法（含蹩马腿检查）。"""
        if not self.is_valid_pos(pos_to):
            return False

        diff = abs_diff((self.x, self.y), pos_to)
        if diff not in ((1, 2), (2, 1)):
            return False

        # 检查蹩马腿
        if diff[0] == 1:
            leg_pos = (self.x, (self.y + pos_to[1]) // 2)
        else:
            leg_pos = ((self.x + pos_to[0]) // 2, self.y)

        if self.board.get_fench(leg_pos) is not None:
            return False

        return True

    def create_moves(self):
        """生成马所有可能的合法走子。"""
        poss = [
            (self.x + 1, self.y + 2),
            (self.x + 1, self.y - 2),
            (self.x - 1, self.y + 2),
            (self.x - 1, self.y - 2),
            (self.x + 2, self.y + 1),
            (self.x + 2, self.y - 1),
            (self.x - 2, self.y + 1),
            (self.x - 2, self.y - 1),
        ]
        curr_pos = (self.x, self.y)
        moves = [(curr_pos, to_pos) for to_pos in poss]
        return filter(self.board.is_valid_move_t, moves)


# -----------------------------------------------------#
# 车
class Rook(Piece):
    """车棋子，沿直线移动，中间不能有阻碍。"""

    def is_valid_move(self, pos_to):
        """判断车移动到目标位置是否合法。"""
        if not self.is_valid_pos(pos_to):
            return False

        if (self.x != pos_to[0]) and (self.y != pos_to[1]):
            return False

        if self.x == pos_to[0]:
            count = self.board.count_y_line_in(self.x, self.y, pos_to[1])
        else:
            count = self.board.count_x_line_in(self.y, self.x, pos_to[0])

        return count == 0

    def create_moves(self):
        """生成车所有可能的合法走子。"""
        moves = []
        curr_pos = (self.x, self.y)
        for x in range(9):
            for y in range(10):
                if self.x == x and self.y == y:
                    continue
                moves.append((curr_pos, (x, y)))
        return filter(self.board.is_valid_move_t, moves)


# -----------------------------------------------------#
# 炮
class Cannon(Piece):
    """炮棋子，移动如车，吃子需翻山。"""

    def is_valid_move(self, pos_to):
        """判断炮移动或吃子到目标位置是否合法（含翻山规则）。"""
        if not self.is_valid_pos(pos_to):
            return False

        if self.x == pos_to[0]:
            if self.y == pos_to[1]:
                return False

            count = self.board.count_y_line_in(self.x, self.y, pos_to[1])
            if (count == 0) and (self.board.get_fench(pos_to) is None):
                return True
            if (count == 1) and (self.board.get_fench(pos_to) is not None):
                return True
        else:
            if self.y != pos_to[1]:
                return False

            count = self.board.count_x_line_in(self.y, self.x, pos_to[0])
            if (count == 0) and (self.board.get_fench(pos_to) is None):
                return True
            if (count == 1) and (self.board.get_fench(pos_to) is not None):
                return True

        return False

    def create_moves(self):
        """生成炮所有可能的合法走子。"""
        moves = []
        curr_pos = (self.x, self.y)
        for x in range(9):
            for y in range(10):
                if self.x == x and self.y == y:
                    continue
                moves.append((curr_pos, (x, y)))
        return filter(self.board.is_valid_move_t, moves)


# -----------------------------------------------------#
# 兵/卒
class Pawn(Piece):
    """兵/卒棋子，未过河前只能前进，过河后可左右移动。"""

    def is_valid_pos(self, pos):
        """判断位置是否在兵的合法活动范围内（不能后退）。"""
        if not super().is_valid_pos(pos):
            return False
        return True

    def is_valid_move(self, pos_to):
        """判断兵/卒移动到目标位置是否合法（含过河前后规则）。"""
        # For RED (at bottom): forward is (0, -1)
        # For BLACK (at top): forward is (0, 1)
        not_crossed_river_step = ((), (0, -1), (0, 1))
        crossed_river_step = ((), ((-1, 0), (1, 0), (0, -1)), ((-1, 0), (1, 0), (0, 1)))

        step = (pos_to[0] - self.x, pos_to[1] - self.y)

        crossed_river = self.is_crossed_river()

        if (not crossed_river) and (step == not_crossed_river_step[self.color]):
            return True

        if crossed_river and (step in crossed_river_step[self.color]):
            return True

        return False

    def is_crossed_river(self):
        """判断兵/卒是否已经过河。"""
        if (self.color == RED) and (self.y <= 4): # Corrected: RED crossed if y <= 4
            return True

        if (self.color == BLACK) and (self.y >= 5): # Corrected: BLACK crossed if y >= 5
            return True

        return False

    def create_moves(self):
        """生成兵/卒所有可能的合法走子。"""
        moves = []
        curr_pos = (self.x, self.y)
        for x in range(9):
            for y in range(10):
                if self.x == x and self.y == y:
                    continue
                moves.append((curr_pos, (x, y)))
        return filter(self.board.is_valid_move_t, moves)

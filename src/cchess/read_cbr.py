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

import struct

from .common import RED, BLACK, fench_to_species
from .board import ChessPlayer, ChessBoard
from .game import Game
from .exception import CChessException


# pylint: disable=too-many-locals,too-many-branches,fixme

CODING_PAGE_CBR = "utf-16-le"

# -----------------------------------------------------#
piece_dict = {
    # 红方
    0x11: "R",  # 车
    0x12: "N",  # 马
    0x13: "B",  # 相
    0x14: "A",  # 仕
    0x15: "K",  # 帅
    0x16: "C",  # 炮
    0x17: "P",  # 兵
    # 黑方
    0x21: "r",  # 车
    0x22: "n",  # 马
    0x23: "b",  # 相
    0x24: "a",  # 仕
    0x25: "k",  # 帅
    0x26: "c",  # 炮
    0x27: "p",  # 卒
}

result_dict = {0: "*", 1: "1-0", 2: "0-1", 3: "1/2-1/2", 4: "1/2-1/2"}


# -----------------------------------------------------#
def _decode_pos(p):
    return (p % 9, p // 9)


def cut_bytes_to_str(buff):
    """将字节缓冲区截断到首个空字节并解码为字符串。"""
    end_index = buff.find(b"\x00\x00")
    if end_index >= 0:
        annote = buff[:end_index].decode(CODING_PAGE_CBR, errors="ignore")
    else:
        annote = buff.decode(CODING_PAGE_CBR, errors="ignore")
    return annote


# -----------------------------------------------------#
class CbrBuffDecoder:
    """对 CBR 文件缓冲区提供顺序读取辅助。"""

    def __init__(self, buffer, coding):
        self.buffer = buffer
        self.index = 0
        self.length = len(buffer)
        self.coding = coding

    def __read(self, size):
        start = self.index
        stop = min(self.index + size, self.length)

        self.index = stop
        return self.buffer[start:stop]

    def is_end(self):
        """判断是否已读取缓冲区末尾。"""
        return (self.length - self.index) < 4

    def read_str(self, size):
        """读取指定字节并解码为字符串（去除末尾空字节）。"""
        buff = self.__read(size)
        return cut_bytes_to_str(buff)

    def read_bytes(self, size):
        """读取指定字节并返回 bytearray。"""
        return bytearray(self.__read(size))

    def read_int(self):
        """读取 4 字节并按小端序返回有符号整数。"""
        data = self.read_bytes(4)
        return struct.unpack("<i", data)[0]


# -----------------------------------------------------#
def __read_init_info(buff_decoder):
    """读取并返回走子前的初始化注释信息。"""
    if buff_decoder.is_end():
        return ""
    a_len = buff_decoder.read_int()
    if a_len == 0:
        return ""
    annote_len = buff_decoder.read_int()
    return buff_decoder.read_str(annote_len)


# -----------------------------------------------------#
def __read_steps(buff_decoder, game, parent_move, board):
    """递归读取走子数据块并将走子构造为 `Game` 中的 `Move` 链。"""
    if buff_decoder.is_end():
        return

    step_info = buff_decoder.read_bytes(4)

    if len(step_info) < 4:
        return

    if step_info == b"\x00\x00\x00\x00":
        return

    step_mark, _step_none, step_from, step_to = step_info

    has_next_move = not (step_mark & 0x01)
    has_var_step = bool(step_mark & 0x02)

    if step_mark & 0x04:
        annote_len = buff_decoder.read_int()
        annote = buff_decoder.read_str(annote_len) if annote_len > 0 else None
    else:
        annote = None

    board_bak = board.copy()
    
    move_from = _decode_pos(step_from)
    move_to = _decode_pos(step_to)

    curr_move = None
    try:
        if not board.is_valid_move(move_from, move_to):
            board.move_player = board.move_player.opposite()
            
        curr_move = board.move(move_from, move_to)
        if curr_move:
            board.next_turn()
            curr_move.annote = annote
            if parent_move:
                parent_move.append_next_move(curr_move)
            else:
                game.append_first_move(curr_move)
    except:
        pass

    if curr_move and has_next_move:
        __read_steps(buff_decoder, game, curr_move, board)
    
    if has_var_step:
        __read_steps(buff_decoder, game, parent_move, board_bak)


# -----------------------------------------------------#
def read_from_cbr_buffer(contents):
    """从 CBR 文件的字节内容解析并返回 `Game` 对象。"""
    if len(contents) < 2218:
        return None
        
    (
        magic,
        _is1,
        title,
        _is2,
        event,
        _is3,
        red,
        _is_red,
        black,
        _is_black,
        game_result,
        _is4,
        _steps,
        _is5,
        move_side,
        _is6,
        boards,
        _is7,
    ) = struct.unpack(
        "<16s164s128s384s64s320s64s160s64s712sB35sB3sH2s90si", contents[:2214]
    )

    if magic != b"CCBridge Record\x00":
        return None

    game_info = {}
    game_info["source"] = "CBR"
    game_info["title"] = cut_bytes_to_str(title)
    game_info["event"] = cut_bytes_to_str(event)
    game_info["red"] = cut_bytes_to_str(red)
    game_info["black"] = cut_bytes_to_str(black)
    game_info["result"] = result_dict[game_result]
    
    board = ChessBoard()
    board.move_player = ChessPlayer(RED) if move_side in [0, 1] else ChessPlayer(BLACK)

    for i in range(90):
        v = boards[i]
        if v in piece_dict:
            board.put_fench(piece_dict[v], (i % 9, i // 9))

    buff_decoder = CbrBuffDecoder(contents[2214:], CODING_PAGE_CBR)
    game_annote = __read_init_info(buff_decoder)
    game = Game(board, game_annote)
    game.info = game_info

    if not buff_decoder.is_end():
        __read_steps(buff_decoder, game, None, board)

    return game


# -----------------------------------------------------#
def read_from_cbr(file_name):
    """从 `.cbr` 文件读取并解析为 `Game` 对象。"""
    with open(file_name, "rb") as f:
        contents = f.read()

    return read_from_cbr_buffer(contents)


# -----------------------------------------------------#
def read_from_cbl(file_name, verify=True):  # pylint: disable=unused-argument
    """从 `.cbl` 棋谱库文件读取并返回包含多个 `Game` 的字典。"""
    with open(file_name, "rb") as f:
        contents = f.read()

    magic, _i1, _book_count, lib_name = struct.unpack("<16s44si512s", contents[:576])

    if magic != b"CCBridgeLibrary\x00":
        return None

    lib_info = {}
    lib_info["name"] = cut_bytes_to_str(lib_name)
    lib_info["games"] = []

    idx = contents.find(b"CCBridge Record")
    if idx < 0:
        return lib_info

    while idx >= 0:
        game = read_from_cbr_buffer(contents[idx:])
        if game:
            lib_info["games"].append(game)
        idx = contents.find(b"CCBridge Record", idx + 16)

    return lib_info


def read_from_cbl_progressing(file_name):
    """从 `.cbl` 棋谱库文件逐步读取并 yield 中间结果（用于进度显示）。"""
    res = read_from_cbl(file_name)
    if res:
        yield res

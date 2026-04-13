# -*- coding: utf-8 -*-
"""
ElephantBridge (CBR/CBL) format writer.
Strictly calibrated with CCBridge binary offsets and metadata.
"""

import struct
import os
from .common import RED, BLACK

class CbrWriter:
    """写入符合象棋桥规范的 CBR 记录。"""
    
    def __init__(self, game):
        self.game = game
        self.data = bytearray(b"\x00" * 4096)
        
    def _set_str(self, offset, text, length):
        """设置 UTF-16LE 字符串。"""
        if not text: return
        encoded = text.encode("utf-16-le")
        to_write = encoded[:length-2]
        for i, b in enumerate(to_write):
            self.data[offset + i] = b

    def _encode_pos(self, pos):
        """(x, y) -> 象棋桥 0-89 坐标。
        象棋桥坐标系：0 在左上 (a9)，89 在右下 (i0)。
        """
        return (9 - pos[1]) * 9 + pos[0]

    def save(self, file_name):
        # 1. Magic
        self.data[0:16] = b"CCBridge Record\x00"
        # Offset 19: 文件标识 (02 表示棋谱)
        self.data[19] = 0x02
        
        info = self.game.info
        # 2. Metadata Offsets
        self._set_str(180, info.get("title", ""), 128)
        self._set_str(692, info.get("event", ""), 64)
        self._set_str(1076, info.get("red", ""), 64)
        self._set_str(1300, info.get("black", ""), 64)
        
        # 3. Game Type & Result
        self.data[2040] = 0x00 # 全局
        res_map = {"*": 0, "1-0": 1, "0-1": 2, "1/2-1/2": 3}
        self.data[2076] = res_map.get(info.get("result", "*"), 0)
        
        # 4. Starting Side (Offset 2112) & Start Round (Offset 2116)
        side_val = 1 if self.game.init_board.get_move_color() == RED else 2
        self.data[2112] = side_val
        struct.pack_into("<H", self.data, 2116, 1) # 第 1 回合
        
        # 5. Board (90 bytes at Offset 2120)
        rev_piece = {
            "R": 0x11, "N": 0x12, "B": 0x13, "A": 0x14, "K": 0x15, "C": 0x16, "P": 0x17,
            "r": 0x21, "n": 0x22, "b": 0x23, "a": 0x24, "k": 0x25, "c": 0x26, "p": 0x27
        }
        board = self.game.init_board
        for y in range(10):
            for x in range(9):
                p = board._board[y][x]
                if p in rev_piece:
                    pos_idx = self._encode_pos((x, y))
                    self.data[2120 + pos_idx] = rev_piece[p]
        
        # 6. Status (Offset 2210)
        self.data[2210:2214] = b"\xFF\xFF\xFF\xFF"
        
        # 7. Steps (Starts at 2214)
        # 前 4 字节是 a_len (初始化注释), 设为 0
        struct.pack_into("<i", self.data, 2214, 0)
        
        curr_offset = 2218
        move_lines = self.game.dump_moves()
        if move_lines:
            main_line = move_lines[0]['moves']
            for i, move in enumerate(main_line):
                if curr_offset + 4 >= 4096: break
                
                # mark: 0x01 表示结束
                mark = 0x01 if i == len(main_line) - 1 else 0x00
                p_from = self._encode_pos(move.p_from)
                p_to = self._encode_pos(move.p_to)
                
                self.data[curr_offset] = mark
                self.data[curr_offset + 1] = 0x00
                self.data[curr_offset + 2] = p_from
                self.data[curr_offset + 3] = p_to
                curr_offset += 4
        
        with open(file_name, "wb") as f:
            f.write(self.data)
        return True

class CblWriter:
    """写入兼容象棋桥的库文件。"""
    def __init__(self, games):
        self.games = games
        
    def save(self, file_name):
        # 象棋桥库文件第一局起始位置 101952
        header = bytearray(b"\x00" * 101952)
        header[0:16] = b"CCBridgeLibrary\x00"
        
        # 写入数量 (Offset 60)
        struct.pack_into("<i", header, 60, len(self.games))
        
        with open(file_name, "wb") as f:
            f.write(header)
            for g in self.games:
                writer = CbrWriter(g)
                writer.save("tmp.cbr")
                with open("tmp.cbr", "rb") as tmp:
                    f.write(tmp.read())
        if os.path.exists("tmp.cbr"): os.remove("tmp.cbr")
        return True

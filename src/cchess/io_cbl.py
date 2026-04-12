# -*- coding: utf-8 -*-
"""
ElephantBridge (CBR/CBL) format writer.
Reverse engineered from read_cbr.py.
"""

import struct
import os
from .common import RED, fench_to_species
from .board import ChessBoard

class CbrWriter:
    """写入单个象棋桥 CBR 记录。"""
    
    def __init__(self, game):
        self.game = game
        # CBR 固定头部和元数据区
        self.data = bytearray(b"\x00" * 4096)
        
    def _set_str(self, offset, text, length):
        """设置 UTF-16LE 字符串。"""
        if not text: return
        encoded = text.encode("utf-16-le")
        # 截断或填充
        to_write = encoded[:length-2]
        for i, b in enumerate(to_write):
            self.data[offset + i] = b

    def save(self, file_name):
        # 1. Magic
        self.data[0:16] = b"CCBridge Record\x00"
        
        # 2. Metadata (参考 read_cbr.py 的 unpack 格式)
        # title(128), event(64), red(64), black(64) 等
        info = self.game.info
        self._set_str(180, info.get("title", ""), 128)
        self._set_str(692, info.get("event", ""), 64)
        self._set_str(1076, info.get("red", ""), 64)
        self._set_str(1300, info.get("black", ""), 64)
        
        # 3. Result
        res_map = {"*": 0, "1-0": 1, "0-1": 2, "1/2-1/2": 3}
        self.data[1524] = res_map.get(info.get("result", "*"), 0)
        
        # 4. Board (90 bytes)
        # piece_dict 反向映射
        rev_piece = {
            "R": 0x11, "N": 0x12, "B": 0x13, "A": 0x14, "K": 0x15, "C": 0x16, "P": 0x17,
            "r": 0x21, "n": 0x22, "b": 0x23, "a": 0x24, "k": 0x25, "c": 0x26, "p": 0x27
        }
        
        board = self.game.init_board
        for x in range(9):
            for y in range(10):
                p = board._board[y][x]
                if p in rev_piece:
                    # offset 2122 (approx, based on read_cbr.py)
                    self.data[2122 + (9-y)*9 + x] = rev_piece[p]
        
        # 5. Moves (这里简化处理，暂不支持复杂变着)
        # TODO: 实现完整变着编码
        
        with open(file_name, "wb") as f:
            f.write(self.data)
        return True

class CblWriter:
    """写入象棋桥库 CBL 文件。"""
    def __init__(self, games):
        self.games = games
        
    def save(self, file_name):
        header = bytearray(b"\x00" * 101952)
        header[0:16] = b"CCBridgeLibrary\x00"
        # 写入数量 (offset 60 approx)
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

# -*- coding: utf-8 -*-
"""
ElephantBridge (CBR/CBL) format writer.
Final precise calibration based on misk samples and binary diff.
"""

import struct
import os
import uuid
from .common import RED, BLACK

class CbrWriter:
    """写入符合象棋桥规范的 CBR 记录。"""
    
    def __init__(self, game):
        self.game = game
        self.data = bytearray(b"\x00" * 4096)
        self.used_size = 2218
        self.game_uuid = uuid.uuid4()
        
    def _set_str(self, offset, text, length):
        if not text: return
        try:
            encoded = text.encode("utf-16-le")
            to_write = encoded[:length-2]
            for i, b in enumerate(to_write):
                self.data[offset + i] = b
        except: pass

    def _encode_pos(self, pos):
        return (9 - pos[1]) * 9 + pos[0]

    def save(self, file_name=None):
        # 1. Magic
        self.data[0:16] = b"CCBridge Record\x00"
        # [16] 00 00 00 02
        self.data[19] = 0x02
        
        # [20] UUID (Binary LE format)
        self.data[20:36] = self.game_uuid.bytes_le
        
        info = self.game.info
        # 2. Metadata Offsets
        self._set_str(180, info.get("title", ""), 128)
        self._set_str(692, info.get("event", ""), 64)
        self._set_str(1076, info.get("red", ""), 64)
        self._set_str(1300, info.get("black", ""), 64)
        
        # 3. Game Type & Result
        self.data[2040] = 0x00
        res_map = {"*": 0, "1-0": 1, "0-1": 2, "1/2-1/2": 3}
        self.data[2076] = res_map.get(info.get("result", "*"), 0)
        
        # 4. Starting Side
        side_val = 1 if self.game.init_board.get_move_color() == RED else 2
        self.data[2112] = side_val
        struct.pack_into("<H", self.data, 2116, 1)
        
        # 5. Board
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
        
        # 6. Status
        self.data[2210:2214] = b"\xFF\xFF\xFF\xFF"
        
        # 7. Steps
        struct.pack_into("<i", self.data, 2214, 0)
        
        curr_offset = 2218
        move_lines = self.game.dump_moves()
        if move_lines:
            main_line = move_lines[0]['moves']
            for i, move in enumerate(main_line):
                if curr_offset + 4 >= 4096: break
                mark = 0x01 if i == len(main_line) - 1 else 0x00
                p_from = self._encode_pos(move.p_from)
                p_to = self._encode_pos(move.p_to)
                self.data[curr_offset] = mark
                self.data[curr_offset + 1] = 0x00
                self.data[curr_offset + 2] = p_from
                self.data[curr_offset + 3] = p_to
                curr_offset += 4
        
        self.used_size = curr_offset
        
        if file_name:
            with open(file_name, "wb") as f:
                f.write(self.data)
        return self.data

class CblWriter:
    """写入兼容 PC 原生象棋桥的库文件。"""
    def __init__(self, games):
        self.games = games
        self.lib_uuid = uuid.uuid4()
        
    def save(self, file_name):
        count = len(self.games)
        
        if count <= 128: header_size = 101952
        elif count <= 256: header_size = 137280
        elif count <= 384: header_size = 151080
        elif count <= 512: header_size = 207936
        else: header_size = 349248
            
        header = bytearray(b"\x00" * header_size)
        header[0:16] = b"CCBridgeLibrary\x00"
        
        # [16] Version
        struct.pack_into("<i", header, 16, 0x03)
        # [20] Lib UUID (LE)
        header[20:36] = self.lib_uuid.bytes_le
        
        # [52] Flag
        header[52:56] = b"\xFF\xFF\xFF\x7F"
        # [60] Capacity Tier
        struct.pack_into("<i", header, 60, 128 if count <= 128 else 256)
        
        # [1052] Fixed value matching sample
        header[1052] = 0x37
        
        cbr_blocks = []
        for g in self.games:
            writer = CbrWriter(g)
            cbr_blocks.append((writer.save(), writer.used_size, writer.game_uuid))
            
        for i in range(count):
            summary_offset = 66624 + (i * 276)
            if summary_offset + 276 > header_size: break
            
            # [0] 07
            struct.pack_into("<i", header, summary_offset, 0x07)
            # [4] Index
            struct.pack_into("<i", header, summary_offset + 4, i)
            # [8] Active
            struct.pack_into("<i", header, summary_offset + 8, 0x01)
            # [12] Used Size
            struct.pack_into("<i", header, summary_offset + 12, cbr_blocks[i][1])
            
            # [24] UUID String
            game_uuid_str = f"{{{str(cbr_blocks[i][2]).upper()}}}".encode("utf-16-le")
            header[summary_offset+24:summary_offset+24+len(game_uuid_str)] = game_uuid_str
            
            # [100] Title
            title = self.games[i].info.get("title") or f"Game {i+1}"
            try:
                encoded_title = title.encode("utf-16-le")[:128]
                header[summary_offset+100:summary_offset+100+len(encoded_title)] = encoded_title
            except: pass
        
        with open(file_name, "wb") as f:
            f.write(header)
            for block, _, _ in cbr_blocks:
                f.write(block)
        return True

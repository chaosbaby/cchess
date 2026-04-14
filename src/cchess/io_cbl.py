# -*- coding: utf-8 -*-
import struct
import uuid
from .common import RED, BLACK

class CbrWriter:
    def __init__(self, game):
        self.game = game
        self.data = bytearray(b"\x00" * 4096)
        self.used_size = 2218
        self.game_uuid = uuid.uuid4()
        self.offset = 2218

    def _get_info(self, *keys):
        info = self.game.info
        for k in keys:
            if k in info and info[k]:
                return info[k]
        return ""

    def _set_str(self, offset, text, length):
        if not text: return
        try:
            encoded = text.encode("utf-16-le")
            to_write = encoded[:length-2]
            for i, b in enumerate(to_write):
                if offset + i < len(self.data):
                    self.data[offset + i] = b
        except: pass

    def _encode_pos(self, pos):
        # Standard CCBridge move coordinate: y * 9 + x
        return pos[1] * 9 + pos[0]

    def _write_node(self, move):
        if self.offset + 1024 >= len(self.data):
            self.data.extend(b"\x00" * 4096)
            
        idx, count = move.get_variation_index()
        has_more = (idx < count - 1)
        
        mark = 0x00
        if not move.next_move: mark |= 0x01
        if has_more: mark |= 0x02
        if move.annote: mark |= 0x04
        
        start_off = self.offset
        # Structure: AA BB CC DD
        self.data[start_off] = mark
        self.data[start_off+1] = 0x00
        self.data[start_off+2] = self._encode_pos(move.p_from)
        self.data[start_off+3] = self._encode_pos(move.p_to)
        self.offset += 4
        
        if move.annote:
            annote_bytes = move.annote.encode("utf-16-le")
            a_len = len(annote_bytes)
            struct.pack_into("<I", self.data, self.offset, a_len)
            self.offset += 4
            self.data[self.offset : self.offset + a_len] = annote_bytes
            self.offset += a_len
            
        if move.next_move:
            self._write_node(move.next_move)
            
        if has_more:
            self._write_node(move.variations_all[idx + 1])

    def save(self, file_name=None):
        if len(self.data) < 2218:
            self.data.extend(b"\x00" * (2218 - len(self.data)))
            
        self.data[0:16] = b"CCBridge Record\x00"
        self.data[19] = 0x02
        self.data[20:36] = self.game_uuid.bytes_le
        
        self._set_str(180, self._get_info("title"), 128)
        self._set_str(692, self._get_info("event", "match"), 64)
        self._set_str(882, self._get_info("date"), 64)
        self._set_str(948, self._get_info("place", "location", "addr"), 64)
        self._set_str(1074, self._get_info("red", "red_player"), 64)
        self._set_str(1300, self._get_info("black", "black_player"), 64)
        
        res_map = {"*": 0, "1-0": 1, "0-1": 2, "1/2-1/2": 3, "未知": 0, "红胜": 1, "黑胜": 2, "平局": 3}
        self.data[2076] = res_map.get(self._get_info("result"), 0)
        self.data[2112] = 0 if self.game.init_board.move_player.color == RED else 1
        
        board = self.game.init_board
        rev_piece = {
            "R":0x11, "N":0x12, "B":0x13, "A":0x14, "K":0x15, "C":0x16, "P":0x17,
            "r":0x21, "n":0x22, "b":0x23, "a":0x24, "k":0x25, "c":0x26, "p":0x27
        }
        for y in range(10):
            for x in range(9):
                p = board.get_fench((x, y))
                if p in rev_piece:
                    self.data[2120 + (y * 9 + x)] = rev_piece[p]
        
        self.data[2210:2214] = b"\xFF\xFF\xFF\xFF"
        self.data[2214:2218] = b"\x00\x00\x00\x00"
        
        self.offset = 2218
        if self.game.first_move:
            self._write_node(self.game.first_move)
            
        self.used_size = self.offset
        if file_name:
            with open(file_name, "wb") as f:
                f.write(self.data[:self.used_size])
        return self.data[:self.used_size]

class CblWriter:
    def __init__(self, games):
        self.games = games
        self.lib_uuid = uuid.uuid4()
        
    def save(self, file_name):
        count = len(self.games)
        if count <= 128: h_size = 101952
        else: h_size = 207936
        
        header = bytearray(b"\x00" * h_size)
        header[0:16] = b"CCBridgeLibrary\x00"
        struct.pack_into("<i", header, 16, 0x03)
        header[20:36] = self.lib_uuid.bytes_le
        header[52:56] = b"\xFF\xFF\xFF\x7F"
        struct.pack_into("<i", header, 60, 128 if count <= 128 else 256)
        
        blocks = []
        for g in self.games:
            w = CbrWriter(g)
            blocks.append((w.save(), w.used_size, w.game_uuid))
            
        for i in range(len(blocks)):
            off = 66624 + (i * 276)
            if off + 276 > h_size: break
            struct.pack_into("<i", header, off, 0x07)
            struct.pack_into("<i", header, off+4, i)
            struct.pack_into("<i", header, off+8, 0x01)
            struct.pack_into("<i", header, off+12, len(blocks[i][0]))
            u_str = f"{{{str(blocks[i][2]).upper()}}}".encode("utf-16-le")
            header[off+24:off+24+len(u_str)] = u_str
            info = self.games[i].info
            t = self._get_title(info) or f"Game {i+1}"
            try:
                et = t.encode("utf-16-le")[:128]
                header[off+100:off+100+len(et)] = et
            except: pass
            
        with open(file_name, "wb") as f:
            f.write(header)
            for b, _, _ in blocks:
                f.write(b)
        return True

    def _get_title(self, info):
        for k in ["title", "name"]:
            if k in info and info[k]: return info[k]
        return ""

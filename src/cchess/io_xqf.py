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
from typing import Tuple

from .common import RED, fench_to_species
from .board import ChessPlayer, ChessBoard
from .game import Game

result_dict = {0: "*", 1: "1-0", 2: "0-1", 3: "1/2-1/2", 4: "1/2-1/2"}

def _decode_pos(p_val):
    return (int(p_val // 10), 9 - (p_val % 10))

class XQFBuffDecoder:
    def __init__(self, buffer):
        self.buffer = buffer
        self.index = 0
        self.length = len(buffer)

    def read_str(self, size, coding="GB18030"):
        start = self.index
        stop = min(self.index + size, self.length)
        self.index = stop
        buff = self.buffer[start:stop]
        try: return buff.decode(coding)
        except: return None

    def read_bytes(self, size):
        start = self.index
        stop = min(self.index + size, self.length)
        self.index = stop
        return bytearray(self.buffer[start:stop])

    def read_int(self):
        data = self.read_bytes(4)
        if len(data) < 4: return 0
        return int.from_bytes(data, "little")

def calculate_keys(data):
    if len(data) < 16: return None
    v, m = data[2], data[3]
    oa, ob, oc, od = data[8], data[9], data[10], data[11]
    s, xy, xyf, xyt = data[12], data[13], data[14], data[15]
    b = ((s&m)|oa, (xy&m)|ob, (xyf&m)|oc, (xyt&m)|od)
    
    char_list = "[(C) Copyright Mr. Dong Shiwei.]"
    f32 = bytearray(32)
    for i in range(32): f32[i] = ord(char_list[i]) & b[i % 4]
        
    def calc_k(bk, seed):
        return (((((bk * bk) * 3 + 9) * 3 + 8) * 2 + 1) * 3 + 8) * seed
            
    if v <= 10:
        return {'version': v, 'f32_keys': f32, 's_key_xy': 0, 's_key_xyf': 0, 's_key_xyt': 0, 's_key_rmk_size': 0}
    
    s_xy = calc_k(xy, xy) % 256
    s_xyf = calc_k(xyf, s_xy) % 256
    s_xyt = calc_k(xyt, s_xyf) % 256
    s_rmk = ((s * 256) + xy) % 32000 + 767
    
    return {'version': v, 'f32_keys': f32, 's_key_xy': s_xy, 's_key_xyf': s_xyf, 's_key_xyt': s_xyt, 's_key_rmk_size': s_rmk}

def __read_steps(decoder, keys, game, parent_move, board):
    if decoder.index + 4 > decoder.length: return
    
    b = decoder.read_bytes(4)
    tag = b[2]
    
    rmk_size = 0
    if keys['version'] <= 10:
        rmk_size = decoder.read_int()
    else:
        if (tag & 0x20) != 0:
            rmk_size = decoder.read_int() - keys['s_key_rmk_size']
        tag = tag & 0xE0 # Clean flags for logic

    if keys['version'] <= 10:
        f_xqf, t_xqf = (b[0]-0x18)%256, (b[1]-0x20)%256
    else:
        f_xqf = (b[0]-0x18-keys['s_key_xyf'])%256
        t_xqf = (b[1]-0x20-keys['s_key_xyt'])%256

    move_from, move_to = _decode_pos(f_xqf), _decode_pos(t_xqf)
    annote = decoder.read_str(rmk_size) if rmk_size > 0 else None

    curr_move = None
    board_bak = board.copy()
    
    fench = board.get_fench(move_from)
    if fench:
        _, side = fench_to_species(fench)
        if board.move_player.color != side: board.move_player = ChessPlayer(side)
        if board.is_valid_move(move_from, move_to):
            curr_move = board.move(move_from, move_to)
            board.next_turn()
            curr_move.annote = annote
            if parent_move: parent_move.append_next_move(curr_move)
            else: game.append_first_move(curr_move)

    has_next = (tag & 0x80) != 0 if keys['version'] > 10 else (tag & 0xF0) != 0
    has_var = (tag & 0x40) != 0 if keys['version'] > 10 else (tag & 0x0F) != 0

    if has_next:
        __read_steps(decoder, keys, game, curr_move or parent_move, board)
    if has_var:
        __read_steps(decoder, keys, game, parent_move, board_bak)

def read_from_xqf(file_name, read_annotation=True):
    with open(file_name, "rb") as f: data = f.read()
    if data[:2] != b"XQ": return None
    
    keys = calculate_keys(data)
    if not keys: return None
    
    # Initial board
    qizi_raw = data[16:48]
    rearranged = [0] * 32
    for i in range(32):
        if keys['version'] >= 12:
            target = (i + 1 + keys['s_key_xy']) % 32
            rearranged[target] = qizi_raw[i]
        else:
            rearranged[i] = qizi_raw[i]
            
    final_qizi = []
    for val in rearranged:
        dec = (val - keys['s_key_xy']) % 256
        final_qizi.append(dec if dec <= 89 else 0xFF)
        
    board = ChessBoard()
    kinds = ("R","N","B","A","K","A","B","N","R","C","C","P","P","P","P","P")
    for side in range(2):
        for i in range(16):
            m_pos = final_qizi[side*16+i]
            if m_pos <= 89: board.put_fench(chr(ord(kinds[i])+side*32), _decode_pos(m_pos))

    ptree_pos = int.from_bytes(data[56:60], "little") or 1024
    steps_raw = data[ptree_pos:]
    steps_dec = bytearray(steps_raw)
    for i in range(len(steps_raw)):
        steps_dec[i] = (steps_raw[i] - keys['f32_keys'][(ptree_pos + i)%32]) % 256
    
    decoder = XQFBuffDecoder(bytes(steps_dec))
    
    # XQF pseudo-first record
    if decoder.index + 4 > decoder.length:
        return Game(board)
        
    b = decoder.read_bytes(4)
    tag = b[2]
    init_rmk_size = 0
    if keys['version'] <= 10:
        init_rmk_size = decoder.read_int()
    else:
        if (tag & 0x20) != 0:
            init_rmk_size = decoder.read_int() - keys['s_key_rmk_size']
            
    init_annote = decoder.read_str(init_rmk_size) if init_rmk_size > 0 else None
    game = Game(board, init_annote)
    
    # Metadata
    def ext_s(off, l):
        chunk = data[off:off+l]
        try: return chunk.split(b'\x00')[0].decode('gbk').strip()
        except: return ""

    game.info.update({
        'title': ext_s(80, 64),
        'event': ext_s(208, 64),
        'date': ext_s(272, 16),
        'red_player': ext_s(304, 16),
        'black_player': ext_s(320, 16)
    })

    has_next = (tag & 0x80) != 0 if keys['version'] > 10 else (tag & 0xF0) != 0
    has_var = (tag & 0x40) != 0 if keys['version'] > 10 else (tag & 0x0F) != 0
    
    if has_next:
        __read_steps(decoder, keys, game, None, board)
    if has_var:
        __read_steps(decoder, keys, game, None, board.copy())
        
    if game.first_move: game.init_board.move_player = game.first_move.board.move_player
    return game

class XQFWriter:
    def __init__(self, game):
        self.game = game
    def save(self, file_name):
        pass

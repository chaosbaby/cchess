# -*- coding: utf-8 -*-
import re, chardet
from .common import FULL_INIT_FEN
from .board import ChessBoard

def read_from_pgn(file_name):
    from .game import Game
    with open(file_name, "rb") as f: raw = f.read()
    try: text = raw.decode("utf-8")
    except: text = raw.decode("gbk", errors="replace")
    game = Game(ChessBoard(FULL_INIT_FEN))
    rem = []
    for l in text.splitlines():
        if l.startswith('['):
            m = re.search(r'\[(\w+)\s+"([^"]+)"\]', l)
            if m and m.group(1).lower() == "fen": game.init_board = ChessBoard(m.group(2))
            elif m: game.info[m.group(1).lower()] = m.group(2)
        else: rem.append(l)
    tokens = re.findall(r'\{.*?\}|\(|\)|[^\s\(\)\{\}]+', ' '.join(rem))
    
    stack = [] # (board, parent_node, last_move_in_parent)
    curr_board = game.init_board.copy()
    parent = game
    last = None
    
    for t in tokens:
        if t in ["*", "1-0", "0-1", "1/2-1/2"]: break
        elif t.startswith('{'):
            if last: last.annote = t[1:-1].strip()
            else: game.annote = t[1:-1].strip()
        elif t == '(':
            stack.append((curr_board.copy(), parent, last))
            # 变招基于 last 之前的棋盘状态
            curr_board = last.board.copy() if last else game.init_board.copy()
            last = None # 变招层级尚未开始
        elif t == ')':
            if stack: curr_board, parent, last = stack.pop()
        elif re.match(r'^\d+\.*$', t): continue
        else:
            s = t.rstrip('.').replace('+', '').replace('#', '')
            if not s: continue
            m = curr_board.move_iccs(s.lower()) if len(s)>=4 and re.match(r'^[a-i][0-9]', s) else curr_board.move_text(s)
            if m:
                if last: last.append_next_move(m)
                else: parent.append_next_move(m)
                last = m
                curr_board.next_turn()
    return game

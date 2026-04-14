# -*- coding: utf-8 -*-
import re
from .exception import CChessException
from .common import fench_to_species, FULL_INIT_FEN
from .board import ChessBoard

def decode_txt_pos(pos): return (int(pos[0]), 9 - int(pos[1]))

def read_from_txt(moves_txt, pos_txt=None):
    from .game import Game
    board = ChessBoard(FULL_INIT_FEN if not pos_txt else None)
    if pos_txt:
        kinds = 'RNBAKABNRCCPPPPP'
        for s in range(2):
            for i in range(16):
                p_idx = (s*16+i)*2; m_p = pos_txt[p_idx:p_idx+2]
                if m_p != '99': board.put_fench(chr(ord(kinds[i])+s*32), decode_txt_pos(m_p))
    game = Game(board)
    if not moves_txt: return game
    curr = game; b = board.copy()
    for i in range(0, len(moves_txt), 4):
        m = b.move(decode_txt_pos(moves_txt[i:i+2]), decode_txt_pos(moves_txt[i+2:i+4]))
        if m: curr.append_next_move(m); curr = m; b.next_turn()
    return game

def ubb_to_dict(ubb):
    content = ubb
    m = re.search(r'\[DhtmlXQHTML\](.*?)\[/DhtmlXQHTML\]', ubb, re.S)
    if m: content = m.group(1)
    return {k: v.strip() for k, v in re.findall(r'\[DhtmlXQ_([^]]+)\](.*?)\[/DhtmlXQ_\1\]', content, re.S)}

def txt_to_board(pos):
    board = ChessBoard(FULL_INIT_FEN if not pos else None)
    if pos:
        kinds = 'RNBAKABNRCCPPPPP'
        for s in range(2):
            for i in range(16):
                p_idx = (s*16+i)*2; m_p = pos[p_idx:p_idx+2]
                if m_p != '99': board.put_fench(chr(ord(kinds[i])+s*32), decode_txt_pos(m_p))
    return board

def read_from_ubb_dhtml(ubb):
    from .game import Game
    info = ubb_to_dict(ubb)
    if not info: return None
    board = txt_to_board(info.get('binit'))
    game = Game(board); game.info = info
    
    comments = {}
    for k, v in info.items():
        if k.startswith('comment'):
            tag = k[7:]; parts = tag.split('_')
            v_id, step = (int(parts[0]), int(parts[1])) if '_' in tag else (0, int(tag))
            comments[(v_id, step)] = v

    branches = {}
    for k, v in info.items():
        if k.startswith('move_'):
            p_var, step, n_var = map(int, k.split('_')[1:4])
            branches.setdefault((p_var, step), []).append((n_var, v))

    def build(var_id, start_step, parent_node, current_board):
        seq = info.get('movelist') if var_id == 0 else None
        if var_id > 0:
            for (p, s), blist in branches.items():
                for nv, s_seq in blist:
                    if nv == var_id: seq = s_seq; break
                if seq: break
        if not seq: return

        b = current_board.copy()
        curr = parent_node
        
        for i in range(0, len(seq), 4):
            step_idx = start_step + (i // 4)
            m_str = seq[i:i+4]
            b_pre = b.copy()
            m = b.move(decode_txt_pos(m_str[0:2]), decode_txt_pos(m_str[2:4]))
            if not m: break
            
            m.annote = comments.get((var_id, step_idx))
            if var_id > 0 and i == 0:
                # First move of variation: must be sibling of parent_node
                # Actually, the logic should be: parent_node was the main move at this step
                parent_node.add_variation(m)
            else:
                if var_id == 0 and i == 0: game.append_first_move(m)
                else: curr.append_next_move(m)
            
            for nv, n_seq in branches.get((var_id, step_idx), []):
                build(nv, step_idx, m, b_pre.copy())
            
            b.next_turn(); curr = m

    build(0, 1, game, board)
    return game

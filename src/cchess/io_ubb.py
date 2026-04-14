# -*- coding: utf-8 -*-
"""
UBB (DhtmlXQ) format writer for CChess.
Follows standard DhtmlXQ format with separate tags for moves, variations and comments.
Uses GB18030 encoding for CCBridge compatibility.
"""

class UBBWriter:
    def __init__(self, game):
        self.game = game
        self.variation_counter = 0
        self.tags = []
        self.moves_tags = []
        self.comment_tags = []

    def _get_info(self, *keys):
        info = self.game.info
        for k in keys:
            if k in info and info[k]:
                return info[k]
        return ""

    def _pos_to_ubb(self, pos):
        if pos is None: return "99"
        return f"{pos[0]}{9 - pos[1]}"

    def _move_to_ubb(self, m):
        return self._pos_to_ubb(m.p_from) + self._pos_to_ubb(m.p_to)

    def _get_binit(self):
        board = self.game.init_board
        # Coordinates order for binit
        red_order = ['R','N','B','A','K','A','B','N','R','C','C','P','P','P','P','P']
        black_order = ['r','n','b','a','k','a','b','n','r','c','c','p','p','p','p','p']
        
        pos_map = {}
        counts = {}
        for y in range(10):
            for x in range(9):
                ch = board.get_fench((x, y))
                if ch:
                    idx = counts.get(ch, 0)
                    pos_map[(ch, idx)] = (x, y)
                    counts[ch] = idx + 1
        
        res = []
        for ch_list in [red_order, black_order]:
            cur_counts = {}
            for ch in ch_list:
                idx = cur_counts.get(ch, 0)
                pos = pos_map.get((ch, idx), None)
                res.append(self._pos_to_ubb(pos))
                cur_counts[ch] = idx + 1
        return "".join(res)

    def _collect_data(self, move, var_id, start_step):
        if move is None:
            return ""
        
        move_seq = []
        curr = move
        step = start_step
        
        while curr:
            move_seq.append(self._move_to_ubb(curr))
            
            # Collect comment
            if curr.annote:
                tag_name = f"DhtmlXQ_comment{var_id}_{step}" if var_id > 0 else f"DhtmlXQ_comment{step}"
                self.comment_tags.append((tag_name, curr.annote))
            
            # Handle variations (only from the first variation to avoid recursion)
            idx, count = curr.get_variation_index()
            if count > 1 and idx == 0:
                for v_idx, v in enumerate(curr.get_variations()):
                    self.variation_counter += 1
                    new_var_id = self.variation_counter
                    v_seq = self._collect_data(v, new_var_id, step)
                    self.moves_tags.append((f"DhtmlXQ_move_{var_id}_{step}_{new_var_id}", v_seq))
            
            curr = curr.next_move
            step += 1
            
        return "".join(move_seq)

    def generate_ubb(self):
        self.variation_counter = 0
        self.moves_tags = []
        self.comment_tags = []
        
        main_line = self._collect_data(self.game.first_move, 0, 1)
        
        res = ["[DhtmlXQ]"]
        res.append("[DhtmlXQ_ver]www_dpxq_com[/DhtmlXQ_ver]")
        res.append("[DhtmlXQ_init]500,350[/DhtmlXQ_init]")
        
        # Metadata mapping with fallback keys
        mapping = {
            'title': ['title'],
            'event': ['event', 'match'],
            'date': ['date'],
            'place': ['place', 'location', 'addr'],
            'red': ['red', 'red_player'],
            'black': ['black', 'black_player'],
            'result': ['result'],
            'author': ['author'],
            'remark': ['remark', 'annote'],
            'open': ['open']
        }
        
        for tag_name, keys in mapping.items():
            val = self._get_info(*keys)
            res.append(f"[DhtmlXQ_{tag_name}]{val}[/DhtmlXQ_{tag_name}]")
            
        res.append(f"[DhtmlXQ_binit]{self._get_binit()}[/DhtmlXQ_binit]")
        res.append(f"[DhtmlXQ_movelist]{main_line}[/DhtmlXQ_movelist]")
        
        for tag, val in self.moves_tags:
            res.append(f"[{tag}]{val}[/{tag}]")
            
        for tag, val in self.comment_tags:
            res.append(f"[{tag}]{val}[/{tag}]")
            
        res.append("[DhtmlXQ_generator]cchess converter[/DhtmlXQ_generator]")
        res.append("[/DhtmlXQ]")
        return "\n".join(res)

    def save(self, file_path):
        # Use GB18030 for CCBridge compatibility
        with open(file_path, "w", encoding="gb18030", errors="replace") as f:
            f.write(self.generate_ubb())
        return True

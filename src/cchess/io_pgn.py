# -*- coding: utf-8 -*-
"""
PGN format writer for CChess.
Strict adherence to PGN standard for round-trip compatibility.
Only exports main line as per user requirement for software compatibility.
"""

from .common import FULL_INIT_FEN

class PGNWriter:
    def __init__(self, game):
        self.game = game

    def write_headers(self):
        lines = ['[Game "Chinese Chess"]']
        # Map various possible keys to standard PGN headers
        header_mapping = {
            'Event': ['event', 'Event', 'match'],
            'Date': ['date', 'Date'],
            'Round': ['round', 'Round'],
            'Site': ['site', 'Site', 'place', 'location', 'addr'],
            'Red': ['red', 'Red', 'red_player'],
            'Black': ['black', 'Black', 'black_player'],
            'Result': ['result', 'Result']
        }
        
        info = self.game.info
        for pgn_key, possible_keys in header_mapping.items():
            value = ""
            for k in possible_keys:
                if k in info and info[k]:
                    value = info[k]
                    break
            lines.append(f'[{pgn_key} "{value or ""}"]')

        init_fen = self.game.init_board.to_fen()
        if init_fen != FULL_INIT_FEN:
            lines.append(f'[FEN "{self.game.init_board.to_full_fen()}"]')
            lines.append('[SetUp "1"]')

        if self.game.annote:
            lines.append(f'{{{self.game.annote}}}')
        return '\n'.join(lines)

    def _write_main_line(self, move):
        """仅写入主线招法节点。"""
        if move is None: return ""
        
        parts = []
        # 1. Numbering
        if move.step_index % 2 == 0:
            parts.append(f"{move.step_index//2+1}.")
        
        # 2. Move text
        parts.append(move.to_text())
        if move.annote:
            parts.append(f"{{{move.annote}}}")
            
        # 3. Next move (Main line only)
        if move.next_move:
            # If main line continues and it's black's turn, may need numbering ...
            if move.next_move.step_index % 2 != 0:
                # parts.append(f"{move.next_move.step_index//2+1}...") # Some PGN readers prefer this
                pass
            parts.append(self._write_main_line(move.next_move).strip())
            
        return " ".join(parts)

    def write_lines(self):
        headers = self.write_headers()
        moves_text = self._write_main_line(self.game.first_move)
        res = headers + "\n\n" + moves_text
        result = ""
        for k in ['result', 'Result']:
            if k in self.game.info and self.game.info[k]:
                result = self.game.info[k]
                break
        if result:
            res += f"  {result}"
        return res

    def save(self, file_name):
        with open(file_name, 'w', encoding='utf-8') as f:
            f.write(self.write_lines())
        return True

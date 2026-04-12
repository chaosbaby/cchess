# -*- coding: utf-8 -*-
"""
Core conversion logic for CChess files.
Supports recursive file scanning and batch processing.
"""

import os
import sqlite3
from pathlib import Path
from typing import Generator, Dict, Optional

from .game import Game
from .uim import init_db, save_node, save_edge, save_game

SUPPORTED_EXTS = {'.xqf', '.pgn', '.cbl', '.cbf', '.ubb'}

def walk_files(path: Path, recursive: bool = False, max_level: int = 999) -> Generator[Path, None, None]:
    """
    扫描目录下的棋谱文件。
    """
    if not path.exists():
        return
    
    if path.is_file():
        if path.suffix.lower() in SUPPORTED_EXTS:
            yield path
        return

    base_level = len(path.parts)
    
    for root, dirs, files in os.walk(str(path)):
        current_path = Path(root)
        current_level = len(current_path.parts) - base_level
        
        if current_level > max_level:
            dirs[:] = []
            continue
            
        for f in files:
            f_path = Path(root) / f
            if f_path.suffix.lower() in SUPPORTED_EXTS:
                yield f_path
        
        if not recursive:
            break

def convert_file(input_path: Path, target_format: str, output_path: Path, uim_conn=None):
    """
    执行单个文件的转换。
    :param uim_conn: 可选的现有 SQLite 连接，用于批量入库提速。
    """
    target_format = target_format.lower()
    game = Game.read_from(str(input_path))
    
    if target_format == "uim":
        conn = uim_conn if uim_conn else init_db(str(output_path))
        
        red = game.info.get('red', 'Unknown')
        black = game.info.get('black', 'Unknown')
        date = game.info.get('date', 'Unknown')
        result = game.info.get('result', '*')
        event = game.info.get('event', '')
        
        game_id = save_game(conn, red, black, date, result, event)
        
        move_lines = game.dump_moves()
        if not move_lines:
            save_node(conn, game.init_board)
        else:
            main_line = move_lines[0]['moves']
            board = game.init_board.copy()
            prev_hash = save_node(conn, board)
            
            for move in main_line:
                board.move_iccs(move.to_iccs())
                curr_hash = save_node(conn, board)
                save_edge(conn, prev_hash, curr_hash, move.to_iccs(), game_id)
                prev_hash = curr_hash
        
        if not uim_conn:
            conn.commit()
            conn.close()
    else:
        if output_path.is_dir():
            output_file = output_path / (input_path.stem + "." + target_format)
        else:
            output_file = output_path
            
        game.save_to(str(output_file))

# -*- coding: utf-8 -*-
"""
Core conversion logic for CChess files.
Supports recursive file scanning and batch processing.
"""

import os
import sqlite3
from pathlib import Path
from typing import Generator, Dict, Optional, List

from .game import Game
from .uim import init_db, save_node, save_edge, save_game
from .io_cbl import CblWriter

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
    """
    target_format = target_format.lower()

    # 格式到后缀的映射
    ext_mapping = {
        'ubb': 'txt',
        'cbl': 'cbr' # 单个文件转cbl实际上是存为cbr块
    }
    target_ext = ext_mapping.get(target_format, target_format)

    # 特殊处理：如果是从 CBL 转出，可能包含多局
    if input_path.suffix.lower() == ".cbl":
        lib_data = Game.read_from_lib(str(input_path))
        games = lib_data.get("games", [])
        for i, g in enumerate(games):
            # 导出到目录
            if target_format == "uim":
                _save_game_to_uim(g, uim_conn)
            else:
                out_f = output_path / f"{input_path.stem}_{i}.{target_ext}"
                g.save_to(str(out_f))
        return

    game = Game.read_from(str(input_path))

    if target_format == "uim":
        _save_game_to_uim(game, uim_conn if uim_conn else init_db(str(output_path)))
    else:
        if output_path.is_dir():
            output_file = output_path / (input_path.stem + "." + target_ext)
        else:
            output_file = output_path
        game.save_to(str(output_file))

def _save_game_to_uim(game, conn):
    """内部函数：将整棵 Game 走子树存入 UIM 数据库。"""
    red = game.info.get('red', 'Unknown')
    black = game.info.get('black', 'Unknown')
    date = game.info.get('date', 'Unknown')
    result = game.info.get('result', '*')
    event = game.info.get('event', '')
    
    game_id = save_game(conn, red, black, date, result, event)
    
    # 保存初始节点
    board = game.init_board.copy()
    start_hash = save_node(conn, board)
    
    if not game.first_move:
        return

    # 递归遍历走子树
    def save_tree(move, prev_hash):
        # 保存当前走子产生的边
        curr_hash = save_node(conn, move.board_done)
        save_edge(conn, prev_hash, curr_hash, move.to_iccs(), game_id)
        
        # 递归处理下一步及其变招
        if move.next_move:
            # 遍历该位置的所有子节点（主线+变招）
            for child in move.next_move.variations_all:
                save_tree(child, curr_hash)

    # 从第一步的所有变招开始
    for m in game.first_move.variations_all:
        save_tree(m, start_hash)

def batch_convert_to_cbl(input_files: List[Path], output_file: Path):
    """
    将多个文件批量转换并合并为一个 CBL 库文件。
    """
    all_games = []
    for f in input_files:
        try:
            if f.suffix.lower() == ".cbl":
                lib_data = Game.read_from_lib(str(f))
                all_games.extend(lib_data.get("games", []))
            else:
                game = Game.read_from(str(f))
                all_games.append(game)
        except Exception as e:
            print(f"Error loading {f} for CBL: {e}")
            
    writer = CblWriter(all_games)
    writer.save(str(output_file))

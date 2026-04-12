# -*- coding: utf-8 -*-
"""
Unified Intermediate Model (UIM) for CChess.
Provides Zobrist DAG and PieceMask encoding for high-speed indexing.
"""

import sqlite3
from typing import List, Dict
from .board import ChessBoard
from .zhash_data import Z_HASH_TABLE, Z_RED_KEY, z_pieces

def _to_signed64(n: int) -> int:
    """将无符号 64 位整数转换为 SQLite 支持的有符号 64 位整数。"""
    n = n & 0xFFFFFFFFFFFFFFFF
    return n - 0x10000000000000000 if n >= 0x8000000000000000 else n

def encode_counts_to_mask(counts: Dict[str, int]) -> int:
    """将兵种计数字典编码为 PieceMask。"""
    mask = 0
    order = ['K', 'A', 'B', 'N', 'R', 'C', 'P', 'k', 'a', 'b', 'n', 'r', 'c', 'p']
    for i, p_char in enumerate(order):
        count = counts.get(p_char, 0) & 0xF
        mask |= (count << (i * 4))
    return _to_signed64(mask)

def encode_piecemask(board: ChessBoard) -> int:
    """
    将棋盘棋子分布编码为 64 位整数。
    每 4 位代表一种棋子的数量。
    """
    counts = {
        'K': 0, 'A': 0, 'B': 0, 'N': 0, 'R': 0, 'C': 0, 'P': 0,
        'k': 0, 'a': 0, 'b': 0, 'n': 0, 'r': 0, 'c': 0, 'p': 0
    }
    
    for y in range(10):
        for x in range(9):
            p = board._board[y][x]
            if p in counts:
                counts[p] += 1
                
    return encode_counts_to_mask(counts)

def get_zhash(board: ChessBoard) -> int:
    """
    计算棋盘的 Zobrist 哈希值。返回有符号 64 位整数。
    """
    zhash = 0
    for y in range(10):
        for x in range(9):
            p = board._board[y][x]
            if p:
                piece_idx = z_pieces.get(p)
                if piece_idx is not None:
                    pos_idx = y * 9 + x
                    zhash ^= Z_HASH_TABLE[pos_idx * 14 + piece_idx]
    
    if board.get_move_color() == 1:
        zhash ^= Z_RED_KEY
        
    return _to_signed64(zhash)

def init_db(db_path: str):
    """
    初始化 UIM SQLite 数据库架构。
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS nodes (
        zhash INTEGER PRIMARY KEY,
        piece_mask INTEGER,
        fen TEXT
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS edges (
        from_hash INTEGER,
        to_hash INTEGER,
        move_uci TEXT,
        game_id INTEGER
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS games (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        red TEXT,
        black TEXT,
        date TEXT,
        result TEXT,
        event TEXT
    )
    """)
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_piece_mask ON nodes(piece_mask)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_edge_from ON edges(from_hash)")
    
    conn.commit()
    return conn

def save_node(conn, board: ChessBoard) -> int:
    """
    保存局面到 nodes 表，如果已存在则忽略。返回有符号 zhash。
    """
    zhash = get_zhash(board)
    piece_mask = encode_piecemask(board)
    fen = board.to_fen()
    
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO nodes (zhash, piece_mask, fen) VALUES (?, ?, ?)",
                   (zhash, piece_mask, fen))
    conn.commit()
    return zhash

def save_edge(conn, from_hash, to_hash, move_uci, game_id):
    """
    保存变着关系。
    """
    cursor = conn.cursor()
    cursor.execute("INSERT INTO edges (from_hash, to_hash, move_uci, game_id) VALUES (?, ?, ?, ?)",
                   (from_hash, to_hash, move_uci, game_id))
    conn.commit()

def save_game(conn, red, black, date, result, event="") -> int:
    """
    保存棋谱元数据，返回自动生成的 game_id。
    """
    cursor = conn.cursor()
    cursor.execute("INSERT INTO games (red, black, date, result, event) VALUES (?, ?, ?, ?, ?)",
                   (red, black, date, result, event))
    conn.commit()
    return cursor.lastrowid

def search_by_piecemask(conn, target_counts: Dict[str, int]) -> List[str]:
    """
    根据给定的兵种计数字典检索符合条件的局面 FEN 列表。
    """
    mask = encode_counts_to_mask(target_counts)
    cursor = conn.cursor()
    cursor.execute("SELECT fen FROM nodes WHERE piece_mask = ?", (mask,))
    return [row[0] for row in cursor.fetchall()]

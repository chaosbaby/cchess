import unittest
import os
import time
import sqlite3
from pathlib import Path
from cchess.board import ChessBoard
from cchess.game import Game
from cchess.uim import init_db, save_node, save_game, save_edge, search_by_piecemask
from cchess.common import get_fen_pieces

class PerformanceReport(unittest.TestCase):
    def setUp(self):
        self.db_path = "uim_perf.db"
        self.conn = init_db(self.db_path)
        self.test_data_dir = Path("data")
        self.xqf_files = list(self.test_data_dir.glob("*.xqf"))

    def test_performance_vs_naive(self):
        print(f"\n[Performance Report]")
        print(f"Loading {len(self.xqf_files)} XQF files into UIM...")
        
        start_load = time.time()
        for xqf_path in self.xqf_files:
            try:
                game = Game.read_from(str(xqf_path))
                game_id = save_game(self.conn, game.red, game.black, game.date, game.result)
                
                # UIM DAG: 遍历所有走子并保存节点
                board = game.init_board.copy()
                prev_hash = save_node(self.conn, board)
                
                for move in game.moves:
                    board.move(move)
                    curr_hash = save_node(self.conn, board)
                    save_edge(self.conn, prev_hash, curr_hash, move.iccs, game_id)
                    prev_hash = curr_hash
            except Exception as e:
                # print(f"Error loading {xqf_path}: {e}")
                continue
        
        load_duration = time.time() - start_load
        print(f"Total load time: {load_duration:.2f}s")
        
        # 3. 执行检索测试
        target_counts = {'K': 1, 'k': 1} # 仅剩将帅
        
        print("\nSearching for 'King vs King' boards...")
        
        # UIM 检索
        start_uim = time.time()
        uim_results = search_by_piecemask(self.conn, target_counts)
        uim_duration = time.time() - start_uim
        print(f"UIM Search Time: {uim_duration*1000:.4f}ms (Count: {len(uim_results)})")
        
        # Naive 检索
        print("Simulating Naive Search (Re-parsing all files)...")
        start_naive = time.time()
        naive_count = 0
        for xqf_path in self.xqf_files:
            try:
                game = Game.read_from(str(xqf_path))
                board = game.init_board.copy()
                if get_fen_pieces(board.to_fen()) == target_counts:
                    naive_count += 1
                for move in game.moves:
                    board.move(move)
                    if get_fen_pieces(board.to_fen()) == target_counts:
                        naive_count += 1
            except: pass
        naive_duration = time.time() - start_naive
        print(f"Naive Search Time: {naive_duration*1000:.4f}ms (Count: {naive_count})")
        
        speedup = naive_duration / uim_duration if uim_duration > 0 else 0
        print(f"\nSpeedup: {speedup:.1f}x")
        
        self.assertGreater(speedup, 1.0)

    def tearDown(self):
        self.conn.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

if __name__ == '__main__':
    unittest.main()

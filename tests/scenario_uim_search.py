import unittest
import os
import time
from cchess.board import ChessBoard
from cchess.uim import init_db, save_node, save_game, save_edge, encode_piecemask

class ScenarioUIMSearch(unittest.TestCase):
    def setUp(self):
        self.db_path = "uim_scenario.db"
        self.conn = init_db(self.db_path)

    def test_search_horse_cannon_endgame(self):
        """
        场景: 
        1. 模拟存入一个马炮局面。
        2. 模拟存入一个初始局面。
        3. 仅通过 PieceMask 搜索马炮局面。
        """
        # 1. 马炮局面 FEN (红方 1马 1炮 1兵, 黑方 1马 1炮)
        # piece_mask 编码规则: R(K,A,B,N,R,C,P), B(k,a,b,n,r,c,p)
        # 红: K1, N1, C1, P1 | 黑: k1, n1, c1
        # 对应位: K(0), N(3), C(5), P(6) | k(7), n(10), c(12)
        fen_hc = "3akab2/9/4n4/2P1p4/9/9/9/4C1N2/9/4K4 w"
        board_hc = ChessBoard(fen_hc)
        save_node(self.conn, board_hc)
        
        # 调试: 打印实际统计到的棋子
        mask_hc = encode_piecemask(board_hc)
        print(f"\nDebug: board_hc mask = {mask_hc}")
        
        # 初始局面
        from cchess.common import FULL_INIT_FEN
        board_init = ChessBoard(FULL_INIT_FEN)
        save_node(self.conn, board_init)
        
        # 2. 构造查询用的 Mask
        from cchess.uim import search_by_piecemask
        from cchess.common import get_fen_pieces

        # 动态获取 board_hc 的棋子分布以进行精确匹配
        target_counts = get_fen_pieces(fen_hc)

        results = search_by_piecemask(self.conn, target_counts)

        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], board_hc.to_fen())

    def tearDown(self):
        self.conn.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

if __name__ == '__main__':
    unittest.main()

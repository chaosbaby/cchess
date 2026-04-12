import unittest
from cchess.board import ChessBoard
# Under test: cchess.uim (does not exist yet)

class TestPieceMask(unittest.TestCase):
    def test_encode_initial_board(self):
        """
        验证初始棋盘的 PieceMask 是否正确。
        红方: K1, A2, B2, N2, R2, C2, P5 = 1, 2, 2, 2, 2, 2, 5
        """
        from cchess.uim import encode_piecemask
        from cchess.common import FULL_INIT_FEN
        board = ChessBoard(FULL_INIT_FEN) # Explicitly load start
        mask = encode_piecemask(board)
        
        # 验证红方兵(P)的数量是否在对应位
        # 假设 P 是红方第 7 个 4-bit 块
        p_count = (mask >> (6 * 4)) & 0xF
        self.assertEqual(p_count, 5)

if __name__ == '__main__':
    unittest.main()

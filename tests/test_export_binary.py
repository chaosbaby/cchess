import unittest
import os
from pathlib import Path
from cchess.game import Game

class TestExportBinary(unittest.TestCase):
    def setUp(self):
        self.input_pgn = Path("data/test.pgn")
        self.output_xqf = Path("test_out.xqf")
        if self.output_xqf.exists(): os.remove(self.output_xqf)

    def test_export_xqf(self):
        """测试 PGN 到 XQF 的转换。"""
        game = Game.read_from(str(self.input_pgn))
        # 确保 save_to 能正常工作
        game.save_to(str(self.output_xqf))
        self.assertTrue(self.output_xqf.exists())
        
        # 再次读入验证
        game2 = Game.read_from(str(self.output_xqf))
        self.assertEqual(len(game2.dump_moves()), len(game.dump_moves()))

if __name__ == '__main__':
    unittest.main()

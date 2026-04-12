import unittest
import os
import sqlite3
from pathlib import Path
from cchess.game import Game
from cchess.uim import init_db
from cchess.converter import convert_file

class TestConversionEngine(unittest.TestCase):
    def setUp(self):
        self.input_xqf = Path("data/game_test.xqf")
        self.output_pgn = Path("test_out.pgn")
        self.output_db = Path("test_out.db")
        if self.output_pgn.exists(): os.remove(self.output_pgn)
        if self.output_db.exists(): os.remove(self.output_db)

    def test_convert_to_pgn(self):
        # 使用 converter 模块进行转换
        convert_file(self.input_xqf, "pgn", self.output_pgn)
        self.assertTrue(self.output_pgn.exists())
        with open(self.output_pgn, 'r') as f:
            content = f.read()
            self.assertIn("[Game", content)

    def test_convert_to_uim(self):
        # 转换到 UIM 数据库
        convert_file(self.input_xqf, "uim", self.output_db)
        self.assertTrue(self.output_db.exists())
        
        # 验证数据库内容
        conn = sqlite3.connect(self.output_db)
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) FROM nodes")
        self.assertGreater(cursor.fetchone()[0], 0)
        conn.close()

    def tearDown(self):
        if self.output_pgn.exists(): os.remove(self.output_pgn)
        if self.output_db.exists(): os.remove(self.output_db)

if __name__ == '__main__':
    unittest.main()

import unittest
import os
import shutil
import sqlite3
from pathlib import Path
from cchess.__main__ import main
from unittest.mock import patch

class ScenarioBatchConvert(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path("scenario_batch")
        self.test_dir.mkdir(exist_ok=True)
        (self.test_dir / "sub1").mkdir(exist_ok=True)
        
        # 拷贝真实的 XQF 文件到测试目录
        self.src_xqf = Path("data/game_test.xqf")
        shutil.copy(self.src_xqf, self.test_dir / "game1.xqf")
        shutil.copy(self.src_xqf, self.test_dir / "sub1" / "game2.xqf")
        
        self.output_db = "batch_test.db"
        if os.path.exists(self.output_db): os.remove(self.output_db)

    def test_recursive_directory_to_uim(self):
        """测试递归转换文件夹到 UIM。"""
        # 模拟命令行输入: cc convert scenario_batch --to uim -o batch_test.db -r
        with patch('sys.argv', ["cchess", "convert", str(self.test_dir), "--to", "uim", "-o", self.output_db, "-r"]):
            main()
            
        self.assertTrue(os.path.exists(self.output_db))
        
        # 验证数据库中是否包含两个棋谱 (game1, game2)
        conn = sqlite3.connect(self.output_db)
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) FROM games")
        game_count = cursor.fetchone()[0]
        conn.close()
        
        # 应该有两个棋谱被存入
        self.assertEqual(game_count, 2)

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        if os.path.exists(self.output_db):
            os.remove(self.output_db)

if __name__ == '__main__':
    unittest.main()

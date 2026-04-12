import unittest
import sqlite3
import os
from cchess.board import ChessBoard
from cchess.uim import init_db, save_node, get_zhash

class TestUIMConverter(unittest.TestCase):
    def setUp(self):
        self.db_path = "uim_conv_test.db"
        self.conn = init_db(self.db_path)

    def test_save_node_new_and_exists(self):
        from cchess.common import FULL_INIT_FEN
        board = ChessBoard(FULL_INIT_FEN)
        zhash = get_zhash(board)
        
        # 第一次保存
        returned_hash = save_node(self.conn, board)
        self.assertEqual(returned_hash, zhash)
        
        # 验证数据库中有一行
        cursor = self.conn.cursor()
        cursor.execute("SELECT count(*) FROM nodes WHERE zhash=?", (zhash,))
        self.assertEqual(cursor.fetchone()[0], 1)
        
        # 第二次保存相同局面
        save_node(self.conn, board)
        cursor.execute("SELECT count(*) FROM nodes WHERE zhash=?", (zhash,))
        self.assertEqual(cursor.fetchone()[0], 1) # 仍应为 1

    def tearDown(self):
        self.conn.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

if __name__ == '__main__':
    unittest.main()

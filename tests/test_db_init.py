import unittest
import os
import sqlite3

class TestDBInit(unittest.TestCase):
    def setUp(self):
        self.db_name = "uim_test.db"
        if os.path.exists(self.db_name):
            os.remove(self.db_name)

    def test_init_schema(self):
        from cchess.uim import init_db
        conn = init_db(self.db_name)
        
        cursor = conn.cursor()
        # 验证表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        
        self.assertIn("nodes", tables)
        self.assertIn("edges", tables)
        self.assertIn("games", tables)
        
        conn.close()

    def tearDown(self):
        if os.path.exists(self.db_name):
            os.remove(self.db_name)

if __name__ == '__main__':
    unittest.main()

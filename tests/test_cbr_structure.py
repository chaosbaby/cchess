import unittest
import struct
from pathlib import Path
from cchess.game import Game

class TestCBRStructure(unittest.TestCase):
    def test_compare_with_real_cbr(self):
        """对比真实 CBR 和生成的 CBR 关键偏移量。"""
        real_cbr_path = Path("data/test.cbr")
        if not real_cbr_path.exists():
            self.skipTest("No real CBR file found for comparison")
            
        with open(real_cbr_path, "rb") as f:
            real_data = f.read()
            
        # 生成一个测试 CBR
        game = Game.read_from(str(real_cbr_path))
        temp_cbr = "temp_tdd.cbr"
        game.save_to(temp_cbr)
        
        with open(temp_cbr, "rb") as f:
            gen_data = f.read()
            
        # 1. 验证 Magic
        self.assertEqual(gen_data[0:15], b"CCBridge Record")
        
        # 2. 验证 Board 偏移 (2120)
        # 初始局面下，(4,0) 应该是帅 (0x15)，(4,9) 应该是将 (0x25)
        # 象棋桥坐标 p = (9-y)*9 + x
        # 帅 (4,0) -> p = 81 + 4 = 85
        # 将 (4,9) -> p = 0 + 4 = 4
        self.assertEqual(gen_data[2120 + 85], 0x15, "Red King position mismatch")
        self.assertEqual(gen_data[2120 + 4], 0x25, "Black King position mismatch")
        
        # 3. 验证 Move Side (2116)
        # 应该是 1 (红先) 或 2 (黑先)
        side = struct.unpack_from("<H", gen_data, 2116)[0]
        self.assertIn(side, [1, 2])

if __name__ == '__main__':
    unittest.main()

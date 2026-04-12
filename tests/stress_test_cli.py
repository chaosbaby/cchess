import unittest
import os
import time
from pathlib import Path
from cchess.__main__ import main
from unittest.mock import patch

class StressTestCLI(unittest.TestCase):
    def test_mass_conversion_uim(self):
        """测试大规模转换到 UIM 的压力和速度。"""
        input_dir = "data"
        output_db = "stress_test.db"
        if os.path.exists(output_db): os.remove(output_db)
        
        print(f"\n[Stress Test] Converting all files in {input_dir} to UIM...")
        start = time.time()
        with patch('sys.argv', ["cchess", "convert", input_dir, "--to", "uim", "-o", output_db]):
            main()
        duration = time.time() - start
        
        print(f"Stress Test Duration: {duration:.2f}s")
        self.assertTrue(os.path.exists(output_db))
        # 针对 29 个文件的复杂解析，15s 是合理的基准
        self.assertLess(duration, 15.0)

    def test_mass_conversion_pgn(self):
        """测试大规模转换到 PGN。"""
        input_dir = "data"
        output_dir = "stress_pgn_out"
        if os.path.exists(output_dir): 
            import shutil
            shutil.rmtree(output_dir)
        
        print(f"\n[Stress Test] Converting all files in {input_dir} to PGN...")
        start = time.time()
        with patch('sys.argv', ["cchess", "convert", input_dir, "--to", "pgn", "-o", output_dir]):
            main()
        duration = time.time() - start
        
        print(f"PGN Mass Conversion Duration: {duration:.2f}s")
        pgn_files = list(Path(output_dir).glob("*.pgn"))
        print(f"Generated {len(pgn_files)} PGN files.")
        self.assertGreater(len(pgn_files), 10)

if __name__ == '__main__':
    unittest.main()

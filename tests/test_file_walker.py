import unittest
import os
import shutil
from pathlib import Path

# Under test: cchess.converter (to be created)

class TestFileWalker(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path("tmp_test_walker")
        self.test_dir.mkdir(exist_ok=True)
        # Create structure:
        # tmp_test_walker/1.xqf
        # tmp_test_walker/sub/2.pgn
        # tmp_test_walker/sub/sub2/3.cbl
        (self.test_dir / "1.xqf").touch()
        sub = self.test_dir / "sub"
        sub.mkdir(exist_ok=True)
        (sub / "2.pgn").touch()
        sub2 = sub / "sub2"
        sub2.mkdir(exist_ok=True)
        (sub2 / "3.cbl").touch()

    def test_recursive_scan(self):
        from cchess.converter import walk_files
        files = list(walk_files(self.test_dir, recursive=True))
        self.assertEqual(len(files), 3)

    def test_level_limit(self):
        from cchess.converter import walk_files
        # Level 0: Only current dir
        files_l0 = list(walk_files(self.test_dir, recursive=True, max_level=0))
        self.assertEqual(len(files_l0), 1)
        
        # Level 1: current + sub
        files_l1 = list(walk_files(self.test_dir, recursive=True, max_level=1))
        self.assertEqual(len(files_l1), 2)

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

if __name__ == '__main__':
    unittest.main()

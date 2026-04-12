import unittest
import sys
import os
from unittest.mock import patch

# Under test: src/cchess/__main__.py (CLI Entry point)

class TestCLIArgs(unittest.TestCase):
    def test_missing_required_args(self):
        """测试缺少必填参数（--to）时是否报错。"""
        from cchess.__main__ import parse_args
        with self.assertRaises(SystemExit):
            parse_args(["convert", "data/"])

    def test_valid_args(self):
        """测试合法的参数解析。"""
        from cchess.__main__ import parse_args
        args = parse_args(["convert", "data/", "--to", "uim", "-r", "--level", "2", "-o", "test.db"])
        self.assertEqual(args.input, "data/")
        self.assertEqual(args.to, "uim")
        self.assertTrue(args.recursive)
        self.assertEqual(args.level, 2)
        self.assertEqual(args.output, "test.db")

    def test_invalid_input_path(self):
        """测试不存在的输入路径是否在逻辑层抛出异常。"""
        from cchess.__main__ import main
        with patch('sys.argv', ["cc", "convert", "non_existent_path", "--to", "pgn"]):
            # 应该捕获到路径不存在的错误
            with self.assertRaises(FileNotFoundError):
                main()

if __name__ == '__main__':
    unittest.main()

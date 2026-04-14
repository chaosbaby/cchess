# -*- coding: utf-8 -*-
import unittest
import os
from pathlib import Path
from src.cchess.game import Game
from src.cchess.read_pgn import read_from_pgn
from src.cchess.read_cbr import read_from_cbr
from src.cchess.read_txt import read_from_ubb_dhtml

class TestRoundTrip(unittest.TestCase):
    def setUp(self):
        self.xqf_file = "data/test_5_variations.xqf"
        self.output_dir = Path("test_roundtrip_output")
        self.output_dir.mkdir(exist_ok=True)
        self.original_game = Game.read_from(self.xqf_file)
        print(f"\nOriginal XQF paths: {len(self.original_game.dump_iccs_moves())}")

    def _compare_games(self, game1, game2):
        # 1. 比较所有路径的招法 (ICCS)
        moves1 = game1.dump_iccs_moves()
        moves2 = game2.dump_iccs_moves()
        
        self.assertEqual(len(moves1), len(moves2), f"路径数量不一致: {len(moves1)} vs {len(moves2)}")
        for i in range(len(moves1)):
            self.assertEqual(moves1[i], moves2[i], f"路径 {i} 的招法不一致")

        # 2. 比较关键元数据
        keys = ["red", "black", "event", "result"]
        for k in keys:
            v1 = str(game1.info.get(k, "") or "")
            v2 = str(game2.info.get(k, "") or "")
            # PGN 可能会有默认值，如果原件没有值，这里允许差异，或者只比较有的值
            if v1:
                self.assertEqual(v1, v2, f"元数据 {k} 不一致")

    def test_pgn_roundtrip(self):
        """XQF -> PGN -> Game (read_from_pgn) -> Compare"""
        pgn_file = self.output_dir / "roundtrip.pgn"
        self.original_game.save_to(str(pgn_file))

        # 使用原有的 read_from_pgn 读取
        new_game = read_from_pgn(str(pgn_file))
        # PGN 仅导出主线，故比较第一条路径
        moves1 = self.original_game.dump_iccs_moves()[0]
        moves2 = new_game.dump_iccs_moves()[0]
        self.assertEqual(moves1, moves2, "PGN 主线招法不一致")

    def test_cbr_roundtrip(self):
        """XQF -> CBR -> Game (read_from_cbr) -> Compare"""
        cbr_file = self.output_dir / "roundtrip.cbr"
        self.original_game.save_to(str(cbr_file))
        
        # 使用原有的 read_from_cbr 读取
        new_game = read_from_cbr(str(cbr_file))
        self._compare_games(self.original_game, new_game)

    def test_ubb_roundtrip(self):
        """XQF -> UBB -> Game (read_from_ubb_dhtml) -> Compare"""
        ubb_file = self.output_dir / "roundtrip.ubb"
        self.original_game.save_to(str(ubb_file))
        
        # 使用完善后的 read_from_ubb_dhtml 读取
        with open(ubb_file, "r", encoding="utf-8") as f:
            content = f.read()
        new_game = read_from_ubb_dhtml(content)
        self._compare_games(self.original_game, new_game)

if __name__ == "__main__":
    unittest.main()

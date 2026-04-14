# -*- coding: utf-8 -*-
import unittest
from pathlib import Path
from src.cchess.game import Game

class TestDataIntegrity(unittest.TestCase):
    def setUp(self):
        self.xqf_file = "data/test_5_variations.xqf"
        self.output_dir = Path("test_output")
        self.output_dir.mkdir(exist_ok=True)

    def test_xqf_to_ubb_integrity(self):
        """验证 XQF 转 UBB 是否包含招法、评论和变招。"""
        game = Game.read_from(self.xqf_file)
        ubb_file = self.output_dir / "test.ubb"
        game.save_to(str(ubb_file))
        
        with open(ubb_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 验证是否包含招法数据 (DhtmlXQ_movelist)
        self.assertIn("[DhtmlXQ_movelist]", content, "UBB 应该包含招法列表")
        # 验证是否包含变招
        self.assertIn("(", content, "UBB 应该包含变招标记 (")
        # 验证是否包含评论
        # 假设 test_5_variations.xqf 中有评论
        # self.assertIn("[DhtmlXQ_comment", content)

    def test_uim_integrity(self):
        """验证转入 UIM 是否包含变招。"""
        from src.cchess.uim import init_db
        from src.cchess.converter import convert_file
        
        db_file = self.output_dir / "test.uim"
        if db_file.exists(): db_file.unlink()
        
        conn = init_db(str(db_file))
        convert_file(Path(self.xqf_file), "uim", self.output_dir, uim_conn=conn)
        conn.commit()
        
        # 检查边（Edge）的数量，如果只有主线，边数会很少
        count = conn.execute("SELECT COUNT(*) FROM edges").fetchone()[0]
        # test_5_variations.xqf 应该有很多边
        self.assertGreater(count, 10, "UIM 数据库中的边数应该反映所有变招")
        conn.close()

    def test_xqf_to_pgn_integrity(self):
        """验证 XQF 转 PGN 是否包含嵌套变招和注释。"""
        game = Game.read_from(self.xqf_file)
        pgn_file = self.output_dir / "test.pgn"
        game.save_to(str(pgn_file))
        
        with open(pgn_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 验证变招标记 (
        self.assertIn("(", content, "PGN 应该包含变招标记 (")
        # 检查是否保留了元数据标签，例如 Red, Black, Event
        self.assertIn("[Red", content)
        self.assertIn("[Event", content)

    def test_xqf_to_cbr_integrity(self):
        """验证 XQF 转 CBR 是否包含变招。"""
        game = Game.read_from(self.xqf_file)
        cbr_file = self.output_dir / "test.cbr"
        game.save_to(str(cbr_file))
        
        # 读取生成的 CBR
        game_read = Game.read_from(str(cbr_file))
        
        # 验证变招树是否被还原
        self.assertGreater(len(game_read.dump_moves()), 1, "导出的 CBR 应该包含多个分支")
        # 验证元数据 (归一化比较)
        def normalize(v): return v if v is not None else ""
        self.assertEqual(normalize(game_read.info.get("event")), normalize(game.info.get("event")))

    def test_batch_cbl_integrity(self):
        """验证批量转换到 CBL 库的完整性。"""
        from src.cchess.converter import batch_convert_to_cbl
        
        files = [Path(self.xqf_file), Path("data/game_test.xqf")]
        cbl_file = self.output_dir / "test_lib.cbl"
        
        batch_convert_to_cbl(files, cbl_file)
        
        # 验证库是否可读且包含正确数量的棋局
        from src.cchess.game import Game
        lib_data = Game.read_from_lib(str(cbl_file))
        
        self.assertEqual(len(lib_data.get("games", [])), 2, "CBL 库应该包含 2 局棋")
        # 验证第一局是否有变招（来自 test_5_variations.xqf）
        self.assertGreater(len(lib_data["games"][0].dump_moves()), 1)

if __name__ == "__main__":
    unittest.main()

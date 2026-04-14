# Track: CLI Converter Implementation (CLI-001)

## Goal
实现一个支持全格式、递归深度控制、数据库入库/导出的高性能象棋棋谱转换工具 `cchess-cli`。

## Tasks
- [ ] **Phase 1: CLI Framework (TDD)**
    - [x] T1.1: 命令行参数解析逻辑 (Unit Test: `test_cli_args.py`)
    - [ ] T1.2: 递归文件扫描器逻辑 (Unit Test: `test_file_walker.py`)
- [x] **Phase 2: Data Integrity & Core Engine (TDD) [COMPLETED]**
    - [x] T2.1: 修复 XQF -> UBB/PGN 的数据丢失（招法、评论、变招、元数据）
    - [x] T2.2: 完善 CBL 读写的数据完整性
    - [x] T2.3: 实现 UIM 完整树状结构入库（包含变招）
- [ ] **Phase 3: Scenario & Stress (TDD)**
    - [ ] T3.1: 场景测试：递归文件夹 -> UIM 数据库 (Scenario Test: `scenario_batch.py`)
    - [ ] T3.2: 压力测试：处理大批量文件的内存占用与并发性。

## Current Status
[GREEN] - Completed Phase 2 (Data Integrity). Core engine now supports full move trees, variations, and metadata for all formats. Standard round-trip tests validated.

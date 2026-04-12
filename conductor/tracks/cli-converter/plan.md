# Track: CLI Converter Implementation (CLI-001)

## Goal
实现一个支持全格式、递归深度控制、数据库入库/导出的高性能象棋棋谱转换工具 `cchess-cli`。

## Tasks
- [ ] **Phase 1: CLI Framework (TDD)**
    - [ ] T1.1: 命令行参数解析逻辑 (Unit Test: `test_cli_args.py`)
    - [ ] T1.2: 递归文件扫描器逻辑 (Unit Test: `test_file_walker.py`)
- [ ] **Phase 2: Core Conversion Engine (TDD)**
    - [ ] T2.1: 实现 Game 对象与各格式（PGN, XQF, UIM）的互转接口 (Unit Test: `test_conversion_engine.py`)
    - [ ] T2.2: 实现 UIM 批量入库与导出逻辑。
- [ ] **Phase 3: Scenario & Stress (TDD)**
    - [ ] T3.1: 场景测试：递归文件夹 -> UIM 数据库 (Scenario Test: `scenario_batch.py`)
    - [ ] T3.2: 压力测试：处理大批量文件的内存占用与并发性。

## Current Status
[RED] - Waiting for T1.1 (CLI Argument Parsing Failure).

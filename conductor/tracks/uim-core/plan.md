# Track: UIM Core Implementation (UIM-001)

## Goal
实现基于 Zobrist DAG 的高效棋谱检索系统 (UIM)，并证明其比传统 PGN 解析快 100 倍以上。

## Tasks
- [ ] **Phase 1: Database & Schema (TDD)**
    - [ ] T1.1: 实现 PieceMask 编码器 (Unit Test: `test_piecemask.py`)
    - [ ] T1.2: 建立 SQLite 初始化脚本 (Unit Test: `test_db_init.py`)
- [ ] **Phase 2: Converter & DAG (TDD)**
    - [ ] T2.1: 实现 `Board` 到 `Node` 的映射逻辑 (Unit Test: `test_uim_converter.py`)
    - [ ] T2.2: 实现批量棋谱导入逻辑。
- [ ] **Phase 3: Scenario & Efficiency (TDD)**
    - [ ] T3.1: 场景测试：搜索“特定杀法” (Scenario Test: `scenario_uim_search.py`)
    - [ ] T3.2: 效率测试报告。

## Current Status
[RED] - Waiting for T1.1 Failure.

#!/bin/bash
# 梯度样本生成脚本

export PYTHONPATH=$PYTHONPATH:$(pwd)/src
OUT_DIR="manual_verify_out"
mkdir -p $OUT_DIR

INPUT_SAMPLE="data/game_test.xqf"

echo "Generating graduated CBL samples..."

# 1. 只有 1 局
python3 -m cchess convert $INPUT_SAMPLE --to cbl -o $OUT_DIR/verify_1.cbl

# 2. 只有 5 局
# 临时构造 5 个文件的目录
mkdir -p tmp_5
for i in {1..5}; do cp $INPUT_SAMPLE tmp_5/game_$i.xqf; done
python3 -m cchess convert tmp_5 --to cbl -o $OUT_DIR/verify_5.cbl
rm -rf tmp_5

# 3. 只有 10 局
mkdir -p tmp_10
for i in {1..10}; do cp $INPUT_SAMPLE tmp_10/game_$i.xqf; done
python3 -m cchess convert tmp_10 --to cbl -o $OUT_DIR/verify_10.cbl
rm -rf tmp_10

# 4. 全部 (158局)
python3 -m cchess convert data --to cbl -o $OUT_DIR/verify_all.cbl

# 5. 同时生成其他格式作为对比
python3 -m cchess convert $INPUT_SAMPLE --to xqf -o $OUT_DIR/verify.xqf
python3 -m cchess convert $INPUT_SAMPLE --to cbr -o $OUT_DIR/verify.cbr
python3 -m cchess convert $INPUT_SAMPLE --to pgn -o $OUT_DIR/verify.pgn

echo "Done. Please check $OUT_DIR."
ls -lh $OUT_DIR/verify_*.cbl

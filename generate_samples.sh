#!/bin/bash
# 全格式生成脚本，用于手动核查

export PYTHONPATH=$PYTHONPATH:$(pwd)/src
OUT_DIR="manual_verify_out"
mkdir -p $OUT_DIR

INPUT="data/game_test.xqf"

echo "Generating verification samples in $OUT_DIR..."

# 1. PGN
python3 -m cchess convert $INPUT --to pgn -o $OUT_DIR/verify.pgn
# 2. FEN
python3 -m cchess convert $INPUT --to fen -o $OUT_DIR/verify.fen
# 3. TXT
python3 -m cchess convert $INPUT --to txt -o $OUT_DIR/verify.txt
# 4. UBB
python3 -m cchess convert $INPUT --to ubb -o $OUT_DIR/verify.ubb
# 5. XQF
python3 -m cchess convert $INPUT --to xqf -o $OUT_DIR/verify.xqf
# 6. CBR (象棋桥单局)
python3 -m cchess convert $INPUT --to cbr -o $OUT_DIR/verify.cbr
# 7. CBL (象棋桥库 - 包含多个)
python3 -m cchess convert data --to cbl -o $OUT_DIR/verify_full_lib.cbl

echo "Done. Please check $OUT_DIR directory."
ls -lh $OUT_DIR

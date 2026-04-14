#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Batch generation script for CChess.
Converts XQF files in a folder to multiple formats and creates a combined CBL library.
"""

import os
import sys
from pathlib import Path

# Ensure we can import from src
sys.path.insert(0, str(Path(__file__).parent / "src"))

from cchess.game import Game
from cchess.io_cbl import CblWriter

def batch_process(input_dir, output_dir):
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True, parents=True)
    
    xqf_files = sorted(list(input_path.glob("*.xqf")))
    if not xqf_files:
        print(f"No XQF files found in {input_dir}")
        return
    
    all_games = []
    print(f"Processing {len(xqf_files)} files...")
    
    for xqf in xqf_files:
        try:
            game = Game.read_from(str(xqf))
            if not game:
                print(f"Failed to read {xqf.name}")
                continue
            
            all_games.append(game)
            base_name = xqf.stem
            
            # 1. Save as .txt (UBB/DhtmlXQ) - Now using GB18030
            game.save_to(str(output_path / f"{base_name}.txt"))
            
            # 2. Save as .cbr (CCBridge Record)
            game.save_to(str(output_path / f"{base_name}.cbr"))
            
            # 3. Save as .pgn (Main line)
            game.save_to(str(output_path / f"{base_name}.pgn"))
            
            print(f"  Converted {xqf.name} to TXT, CBR, PGN")
        except Exception as e:
            print(f"  Error processing {xqf.name}: {e}")
            
    # 4. Save combined .cbl
    if all_games:
        cbl_file = output_path / "combined_library.cbl"
        writer = CblWriter(all_games)
        writer.save(str(cbl_file))
        print(f"\nCreated combined library: {cbl_file.name} with {len(all_games)} games.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Batch convert XQF files")
    parser.add_argument("input", help="Input directory containing XQF files")
    parser.add_argument("-o", "--output", default="batch_output", help="Output directory")
    
    args = parser.parse_args()
    batch_process(args.input, args.output)

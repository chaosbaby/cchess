# -*- coding: utf-8 -*-
"""
Main entry point for CChess CLI.
Supports conversion between various formats including UIM, XQF, and CBL.
"""

import argparse
import sys
import os
from pathlib import Path
from .converter import walk_files, convert_file, batch_convert_to_cbl
from .uim import init_db

def parse_args(args=None):
    parser = argparse.ArgumentParser(prog="cchess")
    subparsers = parser.add_subparsers(dest="command", help="Sub-commands")

    # Convert command
    conv_parser = subparsers.add_parser("convert", help="Convert chess move formats")
    conv_parser.add_argument("input", help="Input file or directory")
    conv_parser.add_argument("--to", required=True, choices=["uim", "pgn", "fen", "txt", "ubb", "xqf", "cbl", "cbr"], 
                             help="Target format")
    conv_parser.add_argument("--from-ext", dest="from_ext", choices=["xqf", "pgn", "cbl", "cbf", "ubb", "uim"],
                             help="Force input format (optional)")
    conv_parser.add_argument("-o", "--output", help="Output directory or database file")
    conv_parser.add_argument("-r", "--recursive", action="store_true", help="Recursive scan")
    conv_parser.add_argument("--level", type=int, default=999, help="Max recursion level")
    
    return parser.parse_args(args)

def main():
    args = parse_args(sys.argv[1:])
    
    if args.command == "convert":
        input_path = Path(args.input)
        if not input_path.exists():
            raise FileNotFoundError(f"Input path not found: {args.input}")
            
        target_format = args.to.lower()
        
        if args.output:
            output_path = Path(args.output)
        else:
            output_path = Path("output")
            
        is_batch = input_path.is_dir()
        
        # 智能创建目录
        if target_format not in ["uim", "cbl"]:
            if is_batch or output_path.suffix == "":
                output_path.mkdir(parents=True, exist_ok=True)
            else:
                output_path.parent.mkdir(parents=True, exist_ok=True)

        print(f"Scanning files in {input_path}...")
        files = list(walk_files(input_path, recursive=args.recursive, max_level=args.level))
        print(f"Found {len(files)} files. Starting conversion...")
        
        # 修正: 如果目标是 CBL，无论输入多少文件，都视为“库操作”
        if target_format == "cbl":
            print(f"Creating CBL library {output_path}...")
            batch_convert_to_cbl(files, output_path)
        else:
            # 常规逐个处理
            uim_conn = None
            if target_format == "uim":
                uim_conn = init_db(str(output_path))
                uim_conn.execute("PRAGMA journal_mode = OFF")
                uim_conn.execute("PRAGMA synchronous = OFF")
                uim_conn.execute("BEGIN")

            for f in files:
                try:
                    print(f"Processing {f.name}...")
                    convert_file(f, target_format, output_path, uim_conn=uim_conn)
                except Exception as e:
                    print(f"Error converting {f}: {e}")
            
            if uim_conn:
                uim_conn.commit()
                uim_conn.close()
                
        print("Done.")
    else:
        print("Use 'cchess --help' for usage.")

if __name__ == "__main__":
    main()

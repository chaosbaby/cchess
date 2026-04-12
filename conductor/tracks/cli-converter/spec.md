# CLI Converter Specification (v1.0)

## 1. Command Syntax
`cchess convert <input_path> --to <target_format> [options]`

## 2. Supported Formats
- **Input**: xqf, pgn, cbl, cbf, ubb, uim (SQLite)
- **Output**: pgn, uim, fen, txt, ubb

## 3. Recursive Logic
- `-r, --recursive`: Boolean, default False.
- `--level <int>`: Integer, depth of recursion. 0 means current dir, 1 means sub-dirs, etc.

## 4. Mode
- **Batch Mode**: If input is a directory, all compatible files are processed.
- **Merge Mode**: If target is `uim`, data is appended/merged into the SQLite database.

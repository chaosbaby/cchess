# UIM Specification (v1.0)

## 1. Zobrist Hashing
Inherit constants from `src/cchess/zhash_data.py`.
Standard 64-bit Zobrist key for board representation.

## 2. PieceMask (64-bit)
Structure (bits 0-63):
- [Red] K: 4 bits | A: 4 bits | B: 4 bits | N: 4 bits | R: 4 bits | C: 4 bits | P: 4 bits
- [Black] k: 4 bits | a: 4 bits | b: 4 bits | n: 4 bits | r: 4 bits | c: 4 bits | p: 4 bits
- Remaining bits: Reserved.

## 3. SQLite Schema
- **nodes**: (zhash INT64 PK, piece_mask INT64, fen TEXT)
- **edges**: (from_hash INT64, to_hash INT64, move_uci TEXT, game_id INT)
- **games**: (id INTEGER PK, red TEXT, black TEXT, date TEXT, result TEXT)

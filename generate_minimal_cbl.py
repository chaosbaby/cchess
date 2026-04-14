import unittest
from pathlib import Path
from cchess.game import Game
from cchess.board import ChessBoard
from cchess.io_cbl import CblWriter

def generate_minimal():
    from cchess.common import FULL_INIT_FEN
    # 1. Create a game with 1 move
    board = ChessBoard(FULL_INIT_FEN) # Initial
    game = Game(board)
    # Right Cannon to center: 70 -> 67
    # In my board.py, we use algebraic or ICCS.
    # Cannon at (7, 2) to (4, 2)
    move = board.move_iccs("h2e2") # Right cannon center
    game.append_first_move(move)
    
    # 2. Save to CBL
    writer = CblWriter([game])
    writer.save("manual_verify_out/verify_minimal_1.cbl")
    print("Generated verify_minimal_1.cbl")

if __name__ == "__main__":
    generate_minimal()

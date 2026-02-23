import ChessEngine

gs = ChessEngine.GameState()

# clear the board
for r in range(8):
    for c in range(8):
        gs.board[r][c] = "--"

# just kings and one knight
gs.board[7][4] = "wK"
gs.board[0][4] = "bK"
gs.white_king_location = (7, 4)
gs.black_king_location = (0, 4)

# knight on f3
gs.board[5][5] = "wN"
print("Knight on f3:", ChessEngine.evaluate_board(gs))

# move knight to h3
gs.board[5][5] = "--"
gs.board[5][7] = "wN"
print("Knight on h3:", ChessEngine.evaluate_board(gs))
# will handle all the game logic


class Move:
    # converts rows and columns to chess notation
    ranks_to_rows = {"1": 7, "2": 6, "3": 5, "4": 4, "5": 3, "6": 2, "7": 1, "8": 0}
    rows_to_ranks = {v: k for k, v in ranks_to_rows.items()}
    files_to_cols = {"a": 0, "b": 1, "c": 2, "d": 3, "e": 4, "f": 5, "g": 6, "h": 7}
    cols_to_files = {v: k for k, v in files_to_cols.items()}

    def __init__(self, start_sq, end_sq, board, is_castle=False, promotion_choice="Q"):
        self.start_row = start_sq[0]
        self.start_col = start_sq[1]
        self.end_row = end_sq[0]
        self.end_col = end_sq[1]

        self.piece_moved = board[self.start_row][self.start_col]
        self.piece_captured = board[self.end_row][self.end_col]

        self.is_castle = is_castle
        self.promotion_choice = promotion_choice

        # check if pawn is to be promoted
        self.is_pawn_promotion = False
        if self.piece_moved[1] == "P":
            if self.piece_moved[0] == "w" and self.end_row == 0:
                self.is_pawn_promotion = True
            if self.piece_moved[0] == "b" and self.end_row == 7:
                self.is_pawn_promotion = True

        # give each move a unique id so comparison made easy
        self.move_id = self.start_row * 1000 + self.start_col * 100 + self.end_row * 10 + self.end_col

    def __eq__(self, other):
        if not isinstance(other, Move):
            return False
        return self.move_id == other.move_id and self.piece_moved == other.piece_moved

    def getChessNotation(self):
        return self.getRankFile(self.start_row, self.start_col) + self.getRankFile(self.end_row, self.end_col)

    def getRankFile(self, r, c):
        return self.cols_to_files[c] + self.rows_to_ranks[r]


class CastleRights:
    def __init__(self, wks, bks, wqs, bqs):
        self.wks = wks  # white king side
        self.bks = bks  # black king side
        self.wqs = wqs  # white queen side
        self.bqs = bqs  # black queen side


class GameState:
    def __init__(self):
        # board is 8x8, first character is color white or black, second is piece type
        # -- means empty square
        self.board = [
            ["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"],
            ["bP", "bP", "bP", "bP", "bP", "bP", "bP", "bP"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["wP", "wP", "wP", "wP", "wP", "wP", "wP", "wP"],
            ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"]
        ]

        self.white_to_move = True
        self.move_log = []

        self.white_king_location = (7, 4)
        self.black_king_location = (0, 4)

        self.checkmate = False
        self.stalemate = False
        self.in_check = False

        self.pins = []
        self.checks = []


        self.current_castling_rights = CastleRights(True, True, True, True)
        self.castle_rights_log = [CastleRights(True, True, True, True)]

    def makeMove(self, move):
        self.board[move.start_row][move.start_col] = "--"
        self.board[move.end_row][move.end_col] = move.piece_moved

        # handle pawn promotion just auto queen for now
        if move.is_pawn_promotion:
            self.board[move.end_row][move.end_col] = move.piece_moved[0] + move.promotion_choice

        # move the rook too when castling
        if move.is_castle:
            if move.end_col - move.start_col == 2:  # king side
                self.board[move.end_row][move.end_col - 1] = self.board[move.end_row][move.end_col + 1]
                self.board[move.end_row][move.end_col + 1] = "--"
            else:  # queen side
                self.board[move.end_row][move.end_col + 1] = self.board[move.end_row][move.end_col - 2]
                self.board[move.end_row][move.end_col - 2] = "--"

        self.move_log.append(move)

        # keep track of where kings are
        if move.piece_moved == "wK":
            self.white_king_location = (move.end_row, move.end_col)
        elif move.piece_moved == "bK":
            self.black_king_location = (move.end_row, move.end_col)

        self.updateCastleRights(move)
        self.castle_rights_log.append(CastleRights(
            self.current_castling_rights.wks,
            self.current_castling_rights.bks,
            self.current_castling_rights.wqs,
            self.current_castling_rights.bqs
        ))

        self.white_to_move = not self.white_to_move

    def undoMove(self):
        if len(self.move_log) == 0:
            return

        move = self.move_log.pop()
        self.white_to_move = not self.white_to_move

        self.board[move.start_row][move.start_col] = move.piece_moved
        self.board[move.end_row][move.end_col] = move.piece_captured

        # undo the rook move for castling
        if move.is_castle:
            if move.end_col - move.start_col == 2:  # king side
                self.board[move.end_row][move.end_col + 1] = self.board[move.end_row][move.end_col - 1]
                self.board[move.end_row][move.end_col - 1] = "--"
            else:  # queen side
                self.board[move.end_row][move.end_col - 2] = self.board[move.end_row][move.end_col + 1]
                self.board[move.end_row][move.end_col + 1] = "--"

        if move.piece_moved == "wK":
            self.white_king_location = (move.start_row, move.start_col)
        elif move.piece_moved == "bK":
            self.black_king_location = (move.start_row, move.start_col)

        # restore old castling rights
        self.castle_rights_log.pop()
        prev_rights = self.castle_rights_log[-1]
        self.current_castling_rights = CastleRights(prev_rights.wks, prev_rights.bks, prev_rights.wqs, prev_rights.bqs)

        self.checkmate = False
        self.stalemate = False

    def updateCastleRights(self, move):
        # king moved = lose both castling rights for that side
        if move.piece_moved == "wK":
            self.current_castling_rights.wks = False
            self.current_castling_rights.wqs = False
        elif move.piece_moved == "bK":
            self.current_castling_rights.bks = False
            self.current_castling_rights.bqs = False

        # rook moved from start square
        if move.piece_moved == "wR":
            if move.start_row == 7 and move.start_col == 0:
                self.current_castling_rights.wqs = False
            elif move.start_row == 7 and move.start_col == 7:
                self.current_castling_rights.wks = False
        elif move.piece_moved == "bR":
            if move.start_row == 0 and move.start_col == 0:
                self.current_castling_rights.bqs = False
            elif move.start_row == 0 and move.start_col == 7:
                self.current_castling_rights.bks = False

        # rook captured on starting square
        if move.piece_captured == "wR":
            if move.end_row == 7 and move.end_col == 0:
                self.current_castling_rights.wqs = False
            elif move.end_row == 7 and move.end_col == 7:
                self.current_castling_rights.wks = False
        elif move.piece_captured == "bR":
            if move.end_row == 0 and move.end_col == 0:
                self.current_castling_rights.bqs = False
            elif move.end_row == 0 and move.end_col == 7:
                self.current_castling_rights.bks = False

    def getValidMoves(self):
        self.checkmate = False
        self.stalemate = False

        self.in_check, self.pins, self.checks = self.checkForPinsAndChecks()

        moves = []
        if self.white_to_move:
            king_row, king_col = self.white_king_location
        else:
            king_row, king_col = self.black_king_location

        if self.in_check:
            if len(self.checks) == 1:
                moves = self.getAllPossibleMoves()

                check = self.checks[0]
                check_row = check[0]
                check_col = check[1]
                check_dir_r = check[2]
                check_dir_c = check[3]

                # squares piece can move to in order to block the check
                valid_squares = [(check_row, check_col)]

                checking_piece = self.board[check_row][check_col]
                if checking_piece[1] != "N":  # knight checks cant be blocked
                    for i in range(1, 8):
                        r = king_row + check_dir_r * i
                        c = king_col + check_dir_c * i
                        valid_squares.append((r, c))
                        if r == check_row and c == check_col:
                            break

                # only keep moves that deal with the check
                filtered = []
                for m in moves:
                    if m.piece_moved[1] == "K":
                        filtered.append(m)
                    elif (m.end_row, m.end_col) in valid_squares:
                        filtered.append(m)
                moves = filtered
            else:
                # double check so king has to move
                self.getKingMoves(king_row, king_col, moves)
        else:
            moves = self.getAllPossibleMoves()
            self.getCastleMoves(king_row, king_col, moves)

        # cant capture the king (prevents some weird edge cases)
        moves = [m for m in moves if not m.piece_captured.endswith("K")]

        if len(moves) == 0:
            if self.in_check:
                self.checkmate = True
            else:
                self.stalemate = True

        return moves

    def getAllPossibleMoves(self):
        moves = []
        for r in range(8):
            for c in range(8):
                piece = self.board[r][c]
                if piece == "--":
                    continue
                color = piece[0]
                if (color == "w" and self.white_to_move) or (color == "b" and not self.white_to_move):
                    p = piece[1]
                    if p == "P":
                        self.getPawnMoves(r, c, moves)
                    elif p == "R":
                        self.getRookMoves(r, c, moves)
                    elif p == "N":
                        self.getKnightMoves(r, c, moves)
                    elif p == "B":
                        self.getBishopMoves(r, c, moves)
                    elif p == "Q":
                        self.getQueenMoves(r, c, moves)
                    elif p == "K":
                        self.getKingMoves(r, c, moves)
        return moves
     

    def _pinned_info(self, r, c):
        # returns whether piece at r,c is pinned and in what direction
        for pin in self.pins:
            if pin[0] == r and pin[1] == c:
                return True, pin[2], pin[3]
        return False, 0, 0

    def checkForPinsAndChecks(self):
        pins = []
        checks = []
        in_check = False

        if self.white_to_move:
            enemy = "b"
            ally = "w"
            start_row, start_col = self.white_king_location
        else:
            enemy = "w"
            ally = "b"
            start_row, start_col = self.black_king_location

        # check all 8 directions from the king
        directions = [
            (-1, 0), (0, -1), (1, 0), (0, 1),    # up left down right
            (-1, -1), (-1, 1), (1, -1), (1, 1)    # diagonals
        ]

        for j in range(len(directions)):
            dr = directions[j][0]
            dc = directions[j][1]
            possible_pin = None

            for i in range(1, 8):
                end_r = start_row + dr * i
                end_c = start_col + dc * i
                if not (0 <= end_r < 8 and 0 <= end_c < 8):
                    break

                end_piece = self.board[end_r][end_c]
                if end_piece[0] == ally and end_piece[1] != "K":
                    if possible_pin is None:
                        possible_pin = (end_r, end_c, dr, dc)
                    else:
                        break  # second ally piece so no pin possible
                elif end_piece[0] == enemy:
                    ptype = end_piece[1]

                    # rook or queen attacking straight
                    if 0 <= j <= 3 and ptype in ("R", "Q"):
                        if possible_pin is None:
                            in_check = True
                            checks.append((end_r, end_c, dr, dc))
                        else:
                            pins.append(possible_pin)
                        break

                    # bishop or queen attacking diagonal
                    if 4 <= j <= 7 and ptype in ("B", "Q"):
                        if possible_pin is None:
                            in_check = True
                            checks.append((end_r, end_c, dr, dc))
                        else:
                            pins.append(possible_pin)
                        break

                    # pawn attacking
                    if i == 1 and ptype == "P":
                        if enemy == "w":
                            if dr == -1 and dc in (-1, 1):
                                in_check = True
                                checks.append((end_r, end_c, dr, dc))
                                break
                        else:
                            if dr == 1 and dc in (-1, 1):
                                in_check = True
                                checks.append((end_r, end_c, dr, dc))
                                break

                    if i == 1 and ptype == "K":
                        in_check = True
                        checks.append((end_r, end_c, dr, dc))
                        break

                    break  # any other enemy piece doesnt attack this way

        # check for knight attacks separately since they jump over pieces
        knight_jumps = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]
        for dr, dc in knight_jumps:
            end_r = start_row + dr
            end_c = start_col + dc
            if 0 <= end_r < 8 and 0 <= end_c < 8:
                end_piece = self.board[end_r][end_c]
                if end_piece[0] == enemy and end_piece[1] == "N":
                    in_check = True
                    checks.append((end_r, end_c, dr, dc))

        return in_check, pins, checks

    def squareUnderAttack(self, r, c):
        # flip turn to see what the opponent could do
        self.white_to_move = not self.white_to_move
        opp_moves = self.getAllPossibleMoves()
        self.white_to_move = not self.white_to_move
        for mv in opp_moves:
            if mv.end_row == r and mv.end_col == c:
                return True
        return False

    def getCastleMoves(self, r, c, moves):
        if self.squareUnderAttack(r, c):
            return  # cant castle when in check

        if self.white_to_move:
            if self.current_castling_rights.wks:
                self.getKingsideCastleMoves(r, c, moves)
            if self.current_castling_rights.wqs:
                self.getQueensideCastleMoves(r, c, moves)
        else:
            if self.current_castling_rights.bks:
                self.getKingsideCastleMoves(r, c, moves)
            if self.current_castling_rights.bqs:
                self.getQueensideCastleMoves(r, c, moves)

    def getKingsideCastleMoves(self, r, c, moves):
        if self.board[r][c + 1] == "--" and self.board[r][c + 2] == "--":
            if not self.squareUnderAttack(r, c + 1) and not self.squareUnderAttack(r, c + 2):
                moves.append(Move((r, c), (r, c + 2), self.board, is_castle=True))

    def getQueensideCastleMoves(self, r, c, moves):
        if self.board[r][c - 1] == "--" and self.board[r][c - 2] == "--" and self.board[r][c - 3] == "--":
            if not self.squareUnderAttack(r, c - 1) and not self.squareUnderAttack(r, c - 2):
                moves.append(Move((r, c), (r, c - 2), self.board, is_castle=True))

    def getPawnMoves(self, r, c, moves):
        pinned, pin_dr, pin_dc = self._pinned_info(r, c)

        if self.white_to_move:
            move_amount = -1
            start_row = 6
            enemy = "b"
        else:
            move_amount = 1
            start_row = 1
            enemy = "w"

        # move forward 1 square
        if 0 <= r + move_amount < 8 and self.board[r + move_amount][c] == "--":
            can_move = (not pinned) or (pin_dr == move_amount and pin_dc == 0) or (pin_dr == -move_amount and pin_dc == 0)
            if can_move:
                moves.append(Move((r, c), (r + move_amount, c), self.board))
                # move forward 2 from starting row
                if r == start_row and self.board[r + 2 * move_amount][c] == "--":
                    moves.append(Move((r, c), (r + 2 * move_amount, c), self.board))

        # diagonal captures
        for dc in (-1, 1):
            end_r = r + move_amount
            end_c = c + dc
            if 0 <= end_r < 8 and 0 <= end_c < 8:
                if self.board[end_r][end_c] != "--" and self.board[end_r][end_c][0] == enemy:
                    can_capture = (not pinned) or (pin_dr == move_amount and pin_dc == dc) or (pin_dr == -move_amount and pin_dc == -dc)
                    if can_capture:
                        moves.append(Move((r, c), (end_r, end_c), self.board))

    def getRookMoves(self, r, c, moves):
        self._getSlidingMoves(r, c, moves, [(1, 0), (-1, 0), (0, 1), (0, -1)])

    def getBishopMoves(self, r, c, moves):
        self._getSlidingMoves(r, c, moves, [(1, 1), (1, -1), (-1, 1), (-1, -1)])

    def getQueenMoves(self, r, c, moves):
        # queen is just rook + bishop combined
        self._getSlidingMoves(r, c, moves, [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)])

    def _getSlidingMoves(self, r, c, moves, directions):
        pinned, pin_dr, pin_dc = self._pinned_info(r, c)
        ally = "w" if self.white_to_move else "b"
        enemy = "b" if self.white_to_move else "w"

        for dr, dc in directions:
            # if pinned can only move along the pin direction
            if pinned and (dr, dc) != (pin_dr, pin_dc) and (dr, dc) != (-pin_dr, -pin_dc):
                continue

            for i in range(1, 8):
                end_r = r + dr * i
                end_c = c + dc * i
                if not (0 <= end_r < 8 and 0 <= end_c < 8):
                    break

                end_piece = self.board[end_r][end_c]
                if end_piece == "--":
                    moves.append(Move((r, c), (end_r, end_c), self.board))
                elif end_piece[0] == enemy:
                    moves.append(Move((r, c), (end_r, end_c), self.board))
                    break  # cant go further after capture
                else:
                    break  # blocked by own piece

    def getKnightMoves(self, r, c, moves):
        pinned, _, _ = self._pinned_info(r, c)
        if pinned:
            return  # pinned knight literally cant move

        ally = "w" if self.white_to_move else "b"
        jumps = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]

        for dr, dc in jumps:
            end_r = r + dr
            end_c = c + dc
            if 0 <= end_r < 8 and 0 <= end_c < 8:
                end_piece = self.board[end_r][end_c]
                if end_piece == "--" or end_piece[0] != ally:
                    moves.append(Move((r, c), (end_r, end_c), self.board))

    def getKingMoves(self, r, c, moves):
        ally = "w" if self.white_to_move else "b"

        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                end_r = r + dr
                end_c = c + dc
                if 0 <= end_r < 8 and 0 <= end_c < 8:
                    end_piece = self.board[end_r][end_c]
                    if end_piece == "--" or end_piece[0] != ally:
                        # temporarily move king to check if square is safe
                        if ally == "w":
                            original = self.white_king_location
                            self.white_king_location = (end_r, end_c)
                        else:
                            original = self.black_king_location
                            self.black_king_location = (end_r, end_c)

                        in_check, _, _ = self.checkForPinsAndChecks()
                        if not in_check:
                            moves.append(Move((r, c), (end_r, end_c), self.board))

                        # king back where he was
                        if ally == "w":
                            self.white_king_location = original
                        else:
                            self.black_king_location = original


# piece values
PIECE_VALUE = {"K": 0, "Q": 900, "R": 500, "B": 330, "N": 320, "P": 100}
PAWN_TABLE = [
    [0,0,0,0,0,0,0,0],
    [50,50,50,50,50,50,50,50],
    [10,10,20,30,30,20,10,10],
    [5,5,10,25,25,10,5,5],
    [0,0,0,0,0,0,0,0],
    [5,-5,-10,0,0,-10,-5,5],
    [5,10,10,-20,-20,10,10,5],
    [0,0,0,0,0,0,0,0]
]
KNIGHT_TABLE = [
    [-50,-40,-30,-30,-30,-30,-40,-50],
    [-40,-20,0,0,0,0,-20,-40],
    [-30,0,10,15,15,10,0,-30],
    [-30,5,15,20,20,15,5,-30],
    [-30,0,15,20,20,15,0,-30],
    [-30,5,10,15,15,10,5,-30],
    [-40,-20,0,5,5,0,-20,-40],
    [-50,-40,-30,-30,-30,-30,-40,-50]
]
BISHOP_TABLE = [
    [-20,-10,-10,-10,-10,-10,-10,-20],
    [-10,0,0,0,0,0,0,-10],
    [-10,0, 5,10,10,5,0,-10],
    [-10,5,5,10,10,5,5,-10],
    [-10,0,10,10,10,10,0,-10],
    [-10,10,10,10,10,10,10,-10],
    [-10,5,0,0,0,0,5,-10],
    [-20,-10,-10,-10,-10,-10,-10,-20]
]

nodes_evaluated = 0

def evaluate_board(gs):
    if gs.checkmate:
        # lose game
        if gs.white_to_move:
            return -999999
        else:
            return 999999
    if gs.stalemate:
        return 0

    score = 0
    for r in range(8):
        for c in range(8):
            piece = gs.board[r][c]
            if piece == "--":
                continue

            color = piece[0]
            ptype = piece[1]
            val = PIECE_VALUE[ptype]
#adding the piece table's eval to the material eval
            if color== "w":
                score += val
            if ptype == "P":
                score+= PAWN_TABLE[r][c]
            elif ptype == "N":
                score+= KNIGHT_TABLE[r][c]
            elif ptype == "B":
                score+= BISHOP_TABLE[r][c]
            
            else:
                score -=val
                if ptype == "P":
                    score -= PAWN_TABLE[7-r][c]
                elif ptype == "N":
                    score -= KNIGHT_TABLE[7-r][c]
                elif ptype == "B":
                    score -= BISHOP_TABLE[7-r][c]

    return score




# minimax and alpha-beta
# alpha is best score white can guarantee, beta is best score black can guarantee
# if beta smaller than alpha we can stop searching that branch
def minimax(gs, depth, alpha, beta, maximizing):
    # hit the depth limit or game ended
    global nodes_evaluated 
    nodes_evaluated += 1 
    if depth == 0 or gs.checkmate or gs.stalemate:
        return evaluate_board(gs)

    moves = gs.getValidMoves()

    if maximizing:
        best = -999999
        for move in moves:
            gs.makeMove(move)
            score = minimax(gs, depth - 1, alpha, beta, False)
            gs.undoMove()

            if score > best:
                best = score
            if best > alpha:
                alpha = best
            if beta <= alpha:
                break  # prune black has a better move already
        return best

    else:
        best = 999999
        for move in moves:
            gs.makeMove(move)
            score = minimax(gs, depth - 1, alpha, beta, True)
            gs.undoMove()

            if score < best:
                best = score
            if best < beta:
                beta = best
            if beta <= alpha:
                break  # prune as white has a better move already
        return best


def choose_best_move(gs, depth):

    moves = gs.getValidMoves()
    if not moves:
        return None

    best_move = None

    if gs.white_to_move:
        best_score = -999999
        for move in moves:
            gs.makeMove(move)
            # start with worst possibility alpha/beta so nothing gets pruned at the root
            score = minimax(gs, depth - 1, -999999, 999999, False)
            gs.undoMove()
            if score > best_score:
                best_score = score
                best_move = move
    else:
        best_score = 999999
        for move in moves:
            gs.makeMove(move)
            score = minimax(gs, depth - 1, -999999, 999999, True)
            gs.undoMove()
            if score < best_score:
                best_score = score
                best_move = move

    return best_move
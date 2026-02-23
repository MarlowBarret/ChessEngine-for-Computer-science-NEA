# Will run the game window and handle inputs
# Z to undo moves, A to make AI moves

import pygame as pg
import ChessEngine

WINDOW = 512
DIM = 8
SQ = WINDOW // DIM
FPS = 60

LIGHT = pg.Color("antiquewhite")
DARK = pg.Color("tan")
HIGHLIGHT = pg.Color(120, 160, 220, 120)


def load_images():
    pieces = ["wP", "wR", "wN", "wB", "wQ", "wK", "bP", "bR", "bN", "bB", "bQ", "bK"]
    images = {}
    for piece in pieces:
        img = pg.image.load("Images/{}.png".format(piece)).convert_alpha()
        images[piece] = pg.transform.smoothscale(img, (SQ, SQ))
    return images


def get_square_from_mouse(pos):
    x = pos[0]
    y = pos[1]
    col = x // SQ
    row = y // SQ
    return (row, col)


def draw_board(screen):
    for r in range(DIM):
        for c in range(DIM):
            if (r + c) % 2 == 0:
                color = LIGHT
            else:
                color = DARK
            pg.draw.rect(screen, color, pg.Rect(c * SQ, r * SQ, SQ, SQ))


def draw_highlight(screen, selected):
    if selected == None:
        return
    r, c = selected
    # highlights the box selected
    surf = pg.Surface((SQ, SQ), pg.SRCALPHA)
    surf.fill(HIGHLIGHT)
    screen.blit(surf, (c * SQ, r * SQ))


def draw_pieces(screen, board, images):
    for r in range(DIM):
        for c in range(DIM):
            piece = board[r][c]
            if piece != "--":
                screen.blit(images[piece], (c * SQ, r * SQ))


def draw_everything(screen, gs, images, selected):
    draw_board(screen)
    draw_highlight(screen, selected)
    draw_pieces(screen, gs.board, images)


def main():
    pg.init()
    screen = pg.display.set_mode((WINDOW, WINDOW))
    pg.display.set_caption("Chess")
    clock = pg.time.Clock()

    images = load_images()
    gs = ChessEngine.GameState()
    legal_moves = gs.getValidMoves()

    selected = None  # the square the player clicked first
    clicks = []      # stores the two clicks for a move
    move_made = False

    running = True
    while running:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False

            elif event.type == pg.MOUSEBUTTONDOWN:
                sq = get_square_from_mouse(pg.mouse.get_pos())

                if selected == sq:
                    # clicked same square twice then deselect
                    selected = None
                    clicks = []
                else:
                    selected = sq
                    clicks.append(sq)

                if len(clicks) == 2:
                    mv = ChessEngine.Move(clicks[0], clicks[1], gs.board)
                    if mv in legal_moves:
                        gs.makeMove(mv)
                        move_made = True
                    # reset either way
                    selected = None
                    clicks = []

            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_z:
                    gs.undoMove()
                    move_made = True

                # press A to make an AI move
                if event.key == pg.K_a:
                    best = ChessEngine.choose_best_move(gs, depth=3)
                    if best is not None:
                        gs.makeMove(best)
                        move_made = True

        if move_made:
            legal_moves = gs.getValidMoves()
            move_made = False

            score = ChessEngine.evaluate_board(gs)
            print("eval:", score, "| in check:", gs.in_check, "| moves:", len(legal_moves))

            if gs.checkmate:
                pg.display.set_caption("Chess - CHECKMATE")
            elif gs.stalemate:
                pg.display.set_caption("Chess - STALEMATE")
            elif gs.in_check:
                pg.display.set_caption("Chess - CHECK")
            else:
                pg.display.set_caption("Chess")

        draw_everything(screen, gs, images, selected)
        pg.display.flip()
        clock.tick(FPS)

    pg.quit()


if __name__ == "__main__":
    main()
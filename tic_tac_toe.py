import pygame
import sys
from math import inf

# ── Colours & Layout ──────────────────────────────────────────────────────────
BG          = (15,  15,  20)   # near-black background
GRID_COLOR  = (50,  50,  65)   # muted grid lines
X_COLOR     = (94,  198, 255)  # icy blue  – AI
O_COLOR     = (255, 111, 105)  # coral red – human
WIN_COLOR   = (255, 220,  80)  # gold highlight for winning line
TEXT_COLOR  = (220, 220, 230)
DIM_COLOR   = (100, 100, 120)

WIDTH, HEIGHT = 540, 640       # extra 100px at bottom for status bar
GRID_SIZE     = 540
CELL          = GRID_SIZE // 3
LINE_W        = 4
PIECE_W       = 8
PIECE_PAD     = 45             # padding inside each cell

# ── Minimax (unchanged logic) ─────────────────────────────────────────────────
def check_winner(board):
    wins = [(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]
    for a,b,c in wins:
        if board[a] == board[b] == board[c] != ' ':
            return board[a], (a, b, c)
    return None, None

def is_full(board):
    return ' ' not in board

def available_moves(board):
    return [i for i, v in enumerate(board) if v == ' ']

def evaluate(board):
    w, _ = check_winner(board)
    if w == 'X': return 10
    if w == 'O': return -10
    return 0

def minimax(board, is_max, depth=0, alpha=-inf, beta=inf):
    w, _ = check_winner(board)
    if w is not None or is_full(board):
        return evaluate(board)
    if is_max:
        best = -inf
        for move in available_moves(board):
            board[move] = 'X'
            best = max(best, minimax(board, False, depth+1, alpha, beta))
            board[move] = ' '
            alpha = max(alpha, best)
            if beta <= alpha:
                break
        return best
    else:
        best = inf
        for move in available_moves(board):
            board[move] = 'O'
            best = min(best, minimax(board, True, depth+1, alpha, beta))
            board[move] = ' '
            beta = min(beta, best)
            if beta <= alpha:
                break
        return best

def find_best_move(board):
    best_score, best_move = -inf, None
    for move in available_moves(board):
        board[move] = 'X'
        score = minimax(board, False)
        board[move] = ' '
        if score > best_score:
            best_score, best_move = score, move
    return best_move

# ── Drawing helpers ───────────────────────────────────────────────────────────
def draw_grid(surface):
    for i in range(1, 3):
        # vertical
        pygame.draw.line(surface, GRID_COLOR,
                         (i * CELL, 0), (i * CELL, GRID_SIZE), LINE_W)
        # horizontal
        pygame.draw.line(surface, GRID_COLOR,
                         (0, i * CELL), (GRID_SIZE, i * CELL), LINE_W)

def cell_rect(idx):
    row, col = divmod(idx, 3)
    return pygame.Rect(col * CELL, row * CELL, CELL, CELL)

def draw_x(surface, idx, alpha=255):
    r = cell_rect(idx).inflate(-PIECE_PAD*2, -PIECE_PAD*2)
    color = (*X_COLOR, alpha) if alpha < 255 else X_COLOR
    # draw on a temp surface for alpha support
    tmp = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
    p = PIECE_PAD
    pygame.draw.line(tmp, color, (p, p), (CELL-p, CELL-p), PIECE_W)
    pygame.draw.line(tmp, color, (CELL-p, p), (p, CELL-p), PIECE_W)
    row, col = divmod(idx, 3)
    surface.blit(tmp, (col*CELL, row*CELL))

def draw_o(surface, idx, alpha=255):
    cx = cell_rect(idx).centerx
    cy = cell_rect(idx).centery
    radius = CELL // 2 - PIECE_PAD
    color = (*O_COLOR, alpha) if alpha < 255 else O_COLOR
    tmp = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
    pygame.draw.circle(tmp, color, (CELL//2, CELL//2), radius, PIECE_W)
    row, col = divmod(idx, 3)
    surface.blit(tmp, (col*CELL, row*CELL))

def draw_winning_line(surface, combo):
    """Draw a gold line through the three winning cells."""
    a, c = combo[0], combo[2]
    x1 = cell_rect(a).centerx
    y1 = cell_rect(a).centery
    x2 = cell_rect(c).centerx
    y2 = cell_rect(c).centery
    pygame.draw.line(surface, WIN_COLOR, (x1, y1), (x2, y2), 6)

def draw_board(surface, board, winning_combo=None):
    surface.fill(BG)
    draw_grid(surface)
    for i, val in enumerate(board):
        if val == 'X':
            draw_x(surface, i)
        elif val == 'O':
            draw_o(surface, i)
    if winning_combo:
        draw_winning_line(surface, winning_combo)

def draw_status(surface, msg, sub=None):
    """Render status text in the bottom bar."""
    bar_y = GRID_SIZE
    pygame.draw.rect(surface, (22, 22, 30), (0, bar_y, WIDTH, HEIGHT - GRID_SIZE))
    font_big  = pygame.font.SysFont("segoeui", 26, bold=True)
    font_small = pygame.font.SysFont("segoeui", 18)
    txt = font_big.render(msg, True, TEXT_COLOR)
    surface.blit(txt, (WIDTH//2 - txt.get_width()//2, bar_y + 18))
    if sub:
        stxt = font_small.render(sub, True, DIM_COLOR)
        surface.blit(stxt, (WIDTH//2 - stxt.get_width()//2, bar_y + 54))

def draw_hover(surface, idx):
    """Subtle highlight on hovered empty cell."""
    r = cell_rect(idx)
    tmp = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
    tmp.fill((255, 255, 255, 12))
    surface.blit(tmp, r.topleft)

# ── Main game loop ────────────────────────────────────────────────────────────
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Tic-Tac-Toe  ·  You (O)  vs  AI (X)")
    clock = pygame.time.Clock()

    board = [' '] * 9
    game_over = False
    winning_combo = None
    status_msg  = "Your turn"
    status_sub  = "You are O  ·  AI is X  ·  Click a square"
    hover_cell  = None

    while True:
        mx, my = pygame.mouse.get_pos()

        # Determine hovered cell
        if my < GRID_SIZE and not game_over:
            col = mx // CELL
            row = my // CELL
            idx = row * 3 + col
            hover_cell = idx if board[idx] == ' ' else None
        else:
            hover_cell = None

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:          # R to restart
                    board = [' '] * 9
                    game_over = False
                    winning_combo = None
                    status_msg = "Your turn"
                    status_sub = "You are O  ·  AI is X  ·  Click a square"

            if event.type == pygame.MOUSEBUTTONDOWN and not game_over:
                if my < GRID_SIZE:
                    if board[idx] == ' ':
                        # Human plays O
                        board[idx] = 'O'
                        winner, winning_combo = check_winner(board)
                        if winner:
                            status_msg = "You won! 🎉"
                            status_sub = "Press R to play again"
                            game_over = True
                        elif is_full(board):
                            status_msg = "It's a Draw!"
                            status_sub = "Press R to play again"
                            game_over = True
                        else:
                            # AI plays X
                            status_msg = "AI is thinking…"
                            draw_board(screen, board, winning_combo)
                            draw_status(screen, status_msg, status_sub)
                            pygame.display.flip()
                            pygame.time.delay(200)        # tiny dramatic pause

                            ai_move = find_best_move(board)
                            board[ai_move] = 'X'
                            winner, winning_combo = check_winner(board)
                            if winner:
                                status_msg = "AI won!"
                                status_sub = "Press R to play again"
                                game_over = True
                            elif is_full(board):
                                status_msg = "It's a Draw!"
                                status_sub = "Press R to play again"
                                game_over = True
                            else:
                                status_msg = "Your turn"
                                status_sub = "You are O  ·  Click a square"

        # ── Render ────────────────────────────────────────────────────────────
        draw_board(screen, board, winning_combo)
        if hover_cell is not None:
            draw_hover(screen, hover_cell)
        draw_status(screen, status_msg, status_sub)
        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()

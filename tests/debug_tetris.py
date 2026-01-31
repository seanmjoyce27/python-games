
# Mocks for browser environment
import sys
import types

# Create mock module 'js'
mock_js = types.ModuleType('js')
mock_js.clear_screen = lambda: None
mock_js.draw_rect = lambda x, y, w, h, c: None
mock_js.draw_text = lambda t, x, y, c, f: None
mock_js.draw_circle = lambda x, y, r, c: None
mock_js.document = None

# Mock keys
keys_pressed = set()
def is_key_pressed(key):
    return key in keys_pressed
mock_js.is_key_pressed = is_key_pressed

sys.modules['js'] = mock_js

# --- TETRIS CODE START ---
import random

# Game settings
BLOCK_SIZE = 28
BOARD_WIDTH = 10
BOARD_HEIGHT = 20
CANVAS_WIDTH = 600
CANVAS_HEIGHT = 600

class Piece:
    def __init__(self, shape, color):
        self.shape = [row[:] for row in shape]  # Copy shape
        self.color = color
        self.x = BOARD_WIDTH // 2 - len(shape[0]) // 2
        self.y = 0

    def rotate(self):
        """Rotate piece clockwise"""
        self.shape = [[self.shape[y][x]
                      for y in range(len(self.shape)-1, -1, -1)]
                      for x in range(len(self.shape[0]))]

    def move_down(self):
        self.y += 1

    def move_left(self):
        self.x -= 1

    def move_right(self):
        self.x += 1

    def move_up(self):
        self.y -= 1

class Board:
    def __init__(self):
        self.width = BOARD_WIDTH
        self.height = BOARD_HEIGHT
        self.grid = [[0 for _ in range(self.width)]
                     for _ in range(self.height)]
        self.colors = [["#000000" for _ in range(self.width)]
                      for _ in range(self.height)]
        self.score = 0
        self.lines_cleared = 0

    def check_collision(self, piece):
        """Check if piece collides with board or other pieces"""
        for y, row in enumerate(piece.shape):
            for x, cell in enumerate(row):
                if cell:
                    new_x = piece.x + x
                    new_y = piece.y + y

                    # Check horizontal bounds
                    if new_x < 0 or new_x >= self.width:
                        return True

                    # Check vertical bounds
                    if new_y >= self.height:
                        return True  # Below the board

                    # Only check grid collision if within visible board area
                    if new_y >= 0 and self.grid[new_y][new_x]:
                        return True
        return False

    def lock_piece(self, piece):
        """Lock piece into board"""
        for y, row in enumerate(piece.shape):
            for x, cell in enumerate(row):
                if cell and piece.y + y >= 0:
                    actual_y = piece.y + y
                    self.grid[actual_y][piece.x + x] = 1
                    self.colors[actual_y][piece.x + x] = piece.color

    def clear_full_lines(self):
        """Remove completed lines and award points"""
        lines_to_clear = []
        for y in range(self.height):
            if all(self.grid[y]):
                lines_to_clear.append(y)

        for y in lines_to_clear:
            del self.grid[y]
            del self.colors[y]
            self.grid.insert(0, [0] * self.width)
            self.colors.insert(0, ["#000000"] * self.width)

        cleared = len(lines_to_clear)
        self.lines_cleared += cleared
        scores = [0, 100, 300, 500, 800]
        self.score += scores[min(cleared, 4)]
        return cleared

# Tetris shapes and colors
SHAPES = [
    ([[1, 1, 1, 1]], "#00f0f0"),  # I - cyan
    ([[1, 1], [1, 1]], "#f0f000"),  # O - yellow
    ([[0, 1, 0], [1, 1, 1]], "#a000f0"),  # T - purple
    ([[1, 1, 0], [0, 1, 1]], "#00f000"),  # S - green
    ([[0, 1, 1], [1, 1, 0]], "#f00000"),  # Z - red
    ([[1, 1, 1], [1, 0, 0]], "#f0a000"),  # L - orange
    ([[1, 1, 1], [0, 0, 1]], "#0000f0"),  # J - blue
]

def create_new_piece():
    """Create a random piece"""
    shape, color = random.choice(SHAPES)
    return Piece(shape, color)

board = Board()
current_piece = create_new_piece()
next_piece = create_new_piece()

# Game state
game_over = False
game_started = False
drop_counter = 0
drop_speed = 30
fast_drop = False
move_delay = 0
last_key = None
lock_timer = 30

def update():
    """Update game logic"""
    global current_piece, next_piece, game_over, game_started, drop_counter, fast_drop, move_delay, last_key, lock_timer

    # Simulating key presses
    # In test script we can control keys_pressed manually

    if game_over:
        return

    # Check if piece is on ground (predictive check)
    current_piece.move_down()
    on_ground = board.check_collision(current_piece)
    current_piece.move_up()

    if on_ground:
        lock_timer -= 1
        if lock_timer <= 0:
            # Lock the piece at current position
            board.lock_piece(current_piece)
            board.clear_full_lines()

            # Create new piece
            current_piece = next_piece
            next_piece = create_new_piece()
            lock_timer = 30  # Reset for next piece

            # Check game over
            if board.check_collision(current_piece):
                game_over = True
            return
    else:
        lock_timer = 30

    # Auto drop
    if not on_ground:
        drop_counter += 1
        current_drop_speed = 3 if fast_drop else drop_speed

        if drop_counter >= current_drop_speed:
            drop_counter = 0
            current_piece.move_down()

# --- TEST HARNESS ---
def print_board():
    for y, row in enumerate(board.grid):
        line = f"{y:2d} "
        for x, cell in enumerate(row):
            # Check if current piece occupies this cell
            is_piece = False
            if current_piece:
                py = y - current_piece.y
                px = x - current_piece.x
                if 0 <= py < len(current_piece.shape) and 0 <= px < len(current_piece.shape[0]):
                    if current_piece.shape[py][px]:
                        is_piece = True
            
            if is_piece:
                line += "[]"
            elif cell:
                line += "##"
            else:
                line += ".."
        print(line)
    print(f"Piece Y: {current_piece.y}, Lock Timer: {lock_timer}")

def run_test():
    global game_started, current_piece, board
    game_started = True
    
    # Initialize board with a "floor" at row 18 (index 18)
    # Piece should land on row 17.
    # Board height is 20 (0-19).
    board = Board()
    print("Creating floor at Row 18...")
    for x in range(BOARD_WIDTH):
        board.grid[18][x] = 1
        board.colors[18][x] = "#888888"

    # Spawn I-piece
    print("Spawning I-piece...")
    current_piece = Piece([[1, 1, 1, 1]], "#00f0f0") # Horizontal I
    current_piece.x = 3
    current_piece.y = 15 # Start close to bottom
    
    print(f"Start Y: {current_piece.y}")

    # Run loop
    print("\n--- STARTING SIMULATION ---")
    print(f"Initial State: Y={current_piece.y}")
    
    previous_y = current_piece.y
    
    for i in range(50):
        # Capture state before update
        y_before = current_piece.y
        
        # Run update
        update()
        
        # Capture state after update
        y_after = current_piece.y
        
        status = "FALLING"
        if y_after == y_before:
            status = f"LANDED/LOCKED? (Timer: {lock_timer})"
        elif y_after < y_before:
            status = "BOUNCED UP! <<<<<< WARNING"
        
        print(f"Frame {i:02d}: {y_before} -> {y_after} | {status}")
        
        if lock_timer < 30 and lock_timer % 10 == 0:
             print(f"       (Lock Timer: {lock_timer})")

        # Check if spawned new piece (reset to top)
        if current_piece.y < 5 and i > 5:
             print(">> PIECE LOCKED AND RESPAWNED (Success)")
             break
        
    print_board()

if __name__ == "__main__":
    run_test()

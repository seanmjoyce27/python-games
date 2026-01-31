import sys
import os

# Add parent directory to path to import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db, Game, CodeVersion

def update_tetris():
    with app.app_context():
        tetris = Game.query.filter_by(name='tetris').first()
        if not tetris:
            print("Tetris game not found!")
            return

        print(f"Updating Tetris (ID: {tetris.id})...")
        
        # New code with Lock Delay
        new_code = '''# Tetris
# Arrow keys: Left/Right to move, Up to rotate, Down to drop faster
# Clear lines to score points!

from js import clear_screen, draw_rect, draw_text, document
import random

# Game settings
BLOCK_SIZE = 28
BOARD_WIDTH = 10
BOARD_HEIGHT = 20
CANVAS_WIDTH = 600
CANVAS_HEIGHT = 700

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

        # Score based on number of lines cleared at once
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

# Create board and first piece
board = Board()
current_piece = create_new_piece()
next_piece = create_new_piece()

# Game state
game_over = False
game_started = False
drop_counter = 0
drop_speed = 30  # Frames between automatic drops
fast_drop = False
move_delay = 0
last_key = None
lock_timer = 30

def update():
    """Update game logic"""
    global current_piece, next_piece, game_over, game_started, drop_counter, fast_drop, move_delay, last_key, lock_timer

    # Check for SPACE to start game
    from js import is_key_pressed
    if not game_started and not game_over:
        if is_key_pressed(' '):
            game_started = True
        return

    if game_over:
        return

    # Handle keyboard input with delay

    # Left movement
    if is_key_pressed('ArrowLeft'):
        if last_key != 'ArrowLeft' or move_delay <= 0:
            current_piece.move_left()
            if board.check_collision(current_piece):
                current_piece.move_right()
            else:
                # Reset lock timer if we moved successfully
                if lock_timer < 30:
                    lock_timer = 30
            move_delay = 5
            last_key = 'ArrowLeft'
    # Right movement
    elif is_key_pressed('ArrowRight'):
        if last_key != 'ArrowRight' or move_delay <= 0:
            current_piece.move_right()
            if board.check_collision(current_piece):
                current_piece.move_left()
            else:
                # Reset lock timer if we moved successfully
                if lock_timer < 30:
                    lock_timer = 30
            move_delay = 5
            last_key = 'ArrowRight'
    # Rotation
    elif is_key_pressed('ArrowUp'):
        if last_key != 'ArrowUp' or move_delay <= 0:
            current_piece.rotate()
            if board.check_collision(current_piece):
                # Rotate back if collision
                for _ in range(3):
                    current_piece.rotate()
            else:
                # Reset lock timer if we rotated successfully
                if lock_timer < 30:
                    lock_timer = 30
            move_delay = 10
            last_key = 'ArrowUp'
    # Fast drop
    elif is_key_pressed('ArrowDown'):
        fast_drop = True
        last_key = 'ArrowDown'
    else:
        fast_drop = False
        last_key = None

    if move_delay > 0:
        move_delay -= 1

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

def draw():
    """Draw everything"""
    # Clear screen
    clear_screen()

    # Draw background
    draw_rect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT, "#1a1a1a")

    # Show start screen if game hasn't started
    if not game_started and not game_over:
        draw_text("TETRIS", 220, 250, "#ffffff", "72px Arial")
        draw_text("Press SPACE to Start", 180, 320, "#ffffff", "28px Arial")
        draw_text("← → : Move  ↑ : Rotate  ↓ : Drop", 120, 370, "#888888", "18px Arial")
        return

    # Board offset to center it
    offset_x = 100
    offset_y = 50

    # Draw board border
    draw_rect(offset_x - 5, offset_y - 5, BOARD_WIDTH * BLOCK_SIZE + 10, BOARD_HEIGHT * BLOCK_SIZE + 10, "#444444")
    draw_rect(offset_x, offset_y, BOARD_WIDTH * BLOCK_SIZE, BOARD_HEIGHT * BLOCK_SIZE, "#000000")

    # Draw locked pieces
    for y in range(BOARD_HEIGHT):
        for x in range(BOARD_WIDTH):
            if board.grid[y][x]:
                draw_rect(
                    offset_x + x * BLOCK_SIZE + 1,
                    offset_y + y * BLOCK_SIZE + 1,
                    BLOCK_SIZE - 2,
                    BLOCK_SIZE - 2,
                    board.colors[y][x]
                )

    # Draw current piece
    if not game_over:
        for y, row in enumerate(current_piece.shape):
            for x, cell in enumerate(row):
                if cell and current_piece.y + y >= 0:
                    draw_rect(
                        offset_x + (current_piece.x + x) * BLOCK_SIZE + 1,
                        offset_y + (current_piece.y + y) * BLOCK_SIZE + 1,
                        BLOCK_SIZE - 2,
                        BLOCK_SIZE - 2,
                        current_piece.color
                    )

    # Draw next piece preview
    draw_text("NEXT:", offset_x + BOARD_WIDTH * BLOCK_SIZE + 30, offset_y + 30, "#ffffff", "20px Arial")
    for y, row in enumerate(next_piece.shape):
        for x, cell in enumerate(row):
            if cell:
                draw_rect(
                    offset_x + BOARD_WIDTH * BLOCK_SIZE + 30 + x * 20,
                    offset_y + 50 + y * 20,
                    18,
                    18,
                    next_piece.color
                )

    # Draw score
    draw_text(f"Score: {board.score}", offset_x + BOARD_WIDTH * BLOCK_SIZE + 30, offset_y + 150, "#ffffff", "18px Arial")
    draw_text(f"Lines: {board.lines_cleared}", offset_x + BOARD_WIDTH * BLOCK_SIZE + 30, offset_y + 180, "#ffffff", "18px Arial")

    # Controls help
    draw_text("← → : Move", 10, CANVAS_HEIGHT - 60, "#888888", "14px Arial")
    draw_text("↑ : Rotate", 10, CANVAS_HEIGHT - 40, "#888888", "14px Arial")
    draw_text("↓ : Drop Fast", 10, CANVAS_HEIGHT - 20, "#888888", "14px Arial")

    # Draw game over
    if game_over:
        draw_rect(offset_x, offset_y + BOARD_HEIGHT * BLOCK_SIZE // 2 - 40, BOARD_WIDTH * BLOCK_SIZE, 80, "#000000")
        draw_text("GAME OVER", offset_x + 30, offset_y + BOARD_HEIGHT * BLOCK_SIZE // 2, "#ff4444", "32px Arial")
        draw_text(f"Score: {board.score}", offset_x + 45, offset_y + BOARD_HEIGHT * BLOCK_SIZE // 2 + 35, "#ffffff", "20px Arial")

# TODO: Make game faster as score increases (reduce drop_speed)
# TODO: Add sound effects for line clears
# TODO: Track and display high score
'''
        
        tetris.template_code = new_code
        
        # ALSO update all user code versions to fix the height issue
        # This is a critical fix for existing saves
        print("Patching user saves...")
        versions = CodeVersion.query.filter_by(game_id=tetris.id).all()
        count = 0
        for v in versions:
            if 'CANVAS_HEIGHT = 600' in v.code:
                v.code = v.code.replace('CANVAS_HEIGHT = 600', 'CANVAS_HEIGHT = 700')
                count += 1
        
        db.session.commit()
        print(f"Updated Tetris code successfully! (Patched {count} user saves)")

if __name__ == "__main__":
    update_tetris()

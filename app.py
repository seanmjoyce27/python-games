from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
import difflib
import os

app = Flask(__name__)

# Replit-optimized configuration
# Use absolute path for SQLite database
basedir = os.path.abspath(os.path.dirname(__file__))
instance_path = os.path.join(basedir, 'instance')
os.makedirs(instance_path, exist_ok=True)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL',
    f'sqlite:///{os.path.join(instance_path, "python_games.db")}'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

db = SQLAlchemy(app)
CORS(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    code_versions = db.relationship('CodeVersion', backref='user', lazy=True, cascade='all, delete-orphan')

class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    display_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    template_code = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class CodeVersion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'), nullable=False)
    code = db.Column(db.Text, nullable=False)
    message = db.Column(db.String(200))  # Optional commit message
    is_checkpoint = db.Column(db.Boolean, default=False)  # Manual saves
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    game = db.relationship('Game', backref='versions')

# Routes
@app.route('/')
def index():
    """Game selection page"""
    games = Game.query.all()
    users = User.query.all()
    return render_template('index.html', games=games, users=users)

@app.route('/game/<int:game_id>')
def game_page(game_id):
    """Code editor and game canvas page"""
    game = Game.query.get_or_404(game_id)
    users = User.query.all()
    return render_template('game.html', game=game, users=users)

# API Endpoints
@app.route('/api/users', methods=['GET', 'POST'])
def manage_users():
    """Get all users or create a new user"""
    if request.method == 'POST':
        data = request.json
        username = data.get('username')

        if not username or len(username) < 2:
            return jsonify({'error': 'Username must be at least 2 characters'}), 400

        if User.query.filter_by(username=username).first():
            return jsonify({'error': 'Username already exists'}), 400

        user = User(username=username)
        db.session.add(user)
        db.session.commit()

        return jsonify({'id': user.id, 'username': user.username}), 201

    users = User.query.all()
    return jsonify([{'id': u.id, 'username': u.username} for u in users])

@app.route('/api/games', methods=['GET'])
def get_games():
    """Get all available games"""
    games = Game.query.all()
    return jsonify([{
        'id': g.id,
        'name': g.name,
        'display_name': g.display_name,
        'description': g.description
    } for g in games])

@app.route('/api/code/load', methods=['POST'])
def load_code():
    """Load the latest code for a user and game"""
    data = request.json
    user_id = data.get('user_id')
    game_id = data.get('game_id')

    if not user_id or not game_id:
        return jsonify({'error': 'user_id and game_id required'}), 400

    # Get the latest version
    latest = CodeVersion.query.filter_by(
        user_id=user_id,
        game_id=game_id
    ).order_by(CodeVersion.created_at.desc()).first()

    if latest:
        return jsonify({
            'code': latest.code,
            'version_id': latest.id,
            'created_at': latest.created_at.isoformat()
        })

    # If no saved code, return template
    game = Game.query.get(game_id)
    return jsonify({
        'code': game.template_code,
        'version_id': None,
        'created_at': None
    })

@app.route('/api/code/save', methods=['POST'])
def save_code():
    """Save a new version of code"""
    data = request.json
    user_id = data.get('user_id')
    game_id = data.get('game_id')
    code = data.get('code')
    message = data.get('message', '')
    is_checkpoint = data.get('is_checkpoint', False)

    if not all([user_id, game_id, code is not None]):
        return jsonify({'error': 'user_id, game_id, and code required'}), 400

    # Check if code has actually changed
    latest = CodeVersion.query.filter_by(
        user_id=user_id,
        game_id=game_id
    ).order_by(CodeVersion.created_at.desc()).first()

    if latest and latest.code == code:
        return jsonify({
            'message': 'No changes detected',
            'version_id': latest.id
        })

    # Create new version
    version = CodeVersion(
        user_id=user_id,
        game_id=game_id,
        code=code,
        message=message,
        is_checkpoint=is_checkpoint
    )
    db.session.add(version)
    db.session.commit()

    return jsonify({
        'message': 'Code saved successfully',
        'version_id': version.id,
        'created_at': version.created_at.isoformat()
    }), 201

@app.route('/api/code/history', methods=['POST'])
def get_history():
    """Get version history for a user and game (unlimited saves)"""
    data = request.json
    user_id = data.get('user_id')
    game_id = data.get('game_id')
    limit = data.get('limit', 100)  # Default to showing last 100
    offset = data.get('offset', 0)

    if not user_id or not game_id:
        return jsonify({'error': 'user_id and game_id required'}), 400

    # Get total count for pagination
    total_count = CodeVersion.query.filter_by(
        user_id=user_id,
        game_id=game_id
    ).count()

    # Get paginated versions
    versions = CodeVersion.query.filter_by(
        user_id=user_id,
        game_id=game_id
    ).order_by(CodeVersion.created_at.desc()).limit(limit).offset(offset).all()

    return jsonify({
        'versions': [{
            'id': v.id,
            'message': v.message,
            'is_checkpoint': v.is_checkpoint,
            'created_at': v.created_at.isoformat(),
            'preview': v.code[:100] + '...' if len(v.code) > 100 else v.code
        } for v in versions],
        'total': total_count,
        'limit': limit,
        'offset': offset,
        'has_more': (offset + limit) < total_count
    })

@app.route('/api/code/version/<int:version_id>', methods=['GET'])
def get_version(version_id):
    """Get a specific version of code"""
    version = CodeVersion.query.get_or_404(version_id)
    return jsonify({
        'id': version.id,
        'code': version.code,
        'message': version.message,
        'is_checkpoint': version.is_checkpoint,
        'created_at': version.created_at.isoformat()
    })

@app.route('/api/code/diff', methods=['POST'])
def get_diff():
    """Get diff between two versions"""
    data = request.json
    version1_id = data.get('version1_id')
    version2_id = data.get('version2_id')

    if not version1_id or not version2_id:
        return jsonify({'error': 'version1_id and version2_id required'}), 400

    v1 = CodeVersion.query.get_or_404(version1_id)
    v2 = CodeVersion.query.get_or_404(version2_id)

    # Generate unified diff
    diff = difflib.unified_diff(
        v1.code.splitlines(keepends=True),
        v2.code.splitlines(keepends=True),
        fromfile=f'Version {v1.id}',
        tofile=f'Version {v2.id}',
        lineterm=''
    )

    return jsonify({
        'diff': list(diff),
        'from_version': v1.id,
        'to_version': v2.id
    })

@app.route('/api/code/restore/<int:version_id>', methods=['POST'])
def restore_version(version_id):
    """Restore code from a previous version (creates a new version)"""
    data = request.json
    user_id = data.get('user_id')

    if not user_id:
        return jsonify({'error': 'user_id required'}), 400

    old_version = CodeVersion.query.get_or_404(version_id)

    # Create new version with the old code
    new_version = CodeVersion(
        user_id=user_id,
        game_id=old_version.game_id,
        code=old_version.code,
        message=f'Restored from version {version_id}',
        is_checkpoint=True
    )
    db.session.add(new_version)
    db.session.commit()

    return jsonify({
        'message': 'Version restored successfully',
        'version_id': new_version.id,
        'code': new_version.code
    }), 201

def init_db():
    """Initialize database with sample games"""
    with app.app_context():
        db.create_all()

        # Check if games already exist
        if Game.query.count() > 0:
            return

        # 1. Snake Game
        snake_template = '''# Snake Game
# Use arrow keys to move the snake
# Eat the red food to grow!

class Snake:
    def __init__(self):
        self.x = 10
        self.y = 10
        self.segments = [(10, 10)]
        self.direction = "right"
        self.speed = 5  # Try changing this!

    def move(self):
        """Move the snake in the current direction"""
        if self.direction == "right":
            self.x += 1
        elif self.direction == "left":
            self.x -= 1
        elif self.direction == "up":
            self.y -= 1
        elif self.direction == "down":
            self.y += 1

        # Add new head position
        self.segments.insert(0, (self.x, self.y))
        self.segments.pop()  # Remove tail

    def grow(self):
        """Make the snake longer"""
        tail = self.segments[-1]
        self.segments.append(tail)

# Create the snake
snake = Snake()

# TODO: Try changing the speed!
# TODO: Try changing the starting position!
# TODO: Can you make the snake start longer?
'''

        snake = Game(
            name='snake',
            display_name='Snake Game',
            description='Classic snake game - eat food and grow!',
            template_code=snake_template
        )
        db.session.add(snake)

        # 2. Pong Game (2-player)
        pong_template = '''# Pong Game - Two Player!
# Player 1: W/S keys | Player 2: Up/Down arrows
# First to 5 points wins!

class Paddle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 10
        self.height = 60
        self.speed = 8  # Try changing paddle speed!
        self.score = 0

    def move_up(self):
        """Move paddle up"""
        self.y -= self.speed
        # Keep on screen
        if self.y < 0:
            self.y = 0

    def move_down(self):
        """Move paddle down"""
        self.y += self.speed
        # Keep on screen (assuming 400 height)
        if self.y > 340:
            self.y = 340

class Ball:
    def __init__(self):
        self.x = 300  # Center of 600px canvas
        self.y = 200  # Center of 400px canvas
        self.size = 10
        self.speed_x = 5  # Try changing ball speed!
        self.speed_y = 5

    def move(self):
        """Move the ball"""
        self.x += self.speed_x
        self.y += self.speed_y

    def bounce_y(self):
        """Bounce ball vertically (hit top/bottom)"""
        self.speed_y = -self.speed_y

    def bounce_x(self):
        """Bounce ball horizontally (hit paddle)"""
        self.speed_x = -self.speed_x
        # Speed up slightly each hit!
        self.speed_x *= 1.05
        self.speed_y *= 1.05

    def reset(self):
        """Reset ball to center"""
        self.x = 300
        self.y = 200
        self.speed_x = 5 if self.speed_x > 0 else -5
        self.speed_y = 5

# Create players and ball
player1 = Paddle(20, 170)   # Left paddle
player2 = Paddle(570, 170)  # Right paddle
ball = Ball()

# TODO: Make paddles bigger or smaller
# TODO: Make the ball faster
# TODO: Change winning score to 10
# TODO: Add a power-up that speeds up your paddle!
'''

        pong = Game(
            name='pong',
            display_name='Pong (2-Player)',
            description='Classic 2-player Pong! First to 5 points wins.',
            template_code=pong_template
        )
        db.session.add(pong)

        # 3. Space Invaders
        space_invaders_template = '''# Space Invaders
# Arrow keys to move, SPACE to shoot!
# Destroy all aliens before they reach the bottom!

class Player:
    def __init__(self):
        self.x = 300  # Center of screen
        self.y = 550  # Near bottom
        self.width = 40
        self.height = 30
        self.speed = 7  # Try changing this!
        self.lives = 3

    def move_left(self):
        self.x -= self.speed
        if self.x < 0:
            self.x = 0

    def move_right(self):
        self.x += self.speed
        if self.x > 560:  # Keep on 600px screen
            self.x = 560

class Bullet:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 4
        self.height = 10
        self.speed = 10  # Try making bullets faster!
        self.active = True

    def move(self):
        self.y -= self.speed
        # Remove if off screen
        if self.y < 0:
            self.active = False

class Alien:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 30
        self.height = 30
        self.speed = 2  # Alien movement speed
        self.alive = True
        self.points = 10  # Try different point values!

    def move_down(self):
        """Aliens move down when hitting edge"""
        self.y += 20

# Create player
player = Player()

# Create grid of aliens (5 rows x 8 columns)
aliens = []
for row in range(5):
    for col in range(8):
        x = 50 + col * 60  # Space them out
        y = 50 + row * 50
        aliens.append(Alien(x, y))

# List to hold bullets
bullets = []

# Game state
score = 0
game_over = False

# TODO: Add more alien rows
# TODO: Make aliens move faster
# TODO: Add different alien types worth more points
# TODO: Give player more lives
# TODO: Add a special weapon that shoots 3 bullets!
'''

        space_invaders = Game(
            name='space_invaders',
            display_name='Space Invaders',
            description='Shoot the aliens before they reach Earth!',
            template_code=space_invaders_template
        )
        db.session.add(space_invaders)

        # 4. Maze Game
        maze_template = '''# Maze Game
# Arrow keys to move
# Find the exit without hitting walls!

class Player:
    def __init__(self):
        self.x = 1  # Grid position
        self.y = 1
        self.size = 30  # Size in pixels
        self.moves = 0  # Count moves to exit

    def move(self, dx, dy, maze):
        """Try to move in direction, check for walls"""
        new_x = self.x + dx
        new_y = self.y + dy

        # Check if move is valid (not a wall)
        if maze[new_y][new_x] != 1:
            self.x = new_x
            self.y = new_y
            self.moves += 1
            return True
        return False

class Maze:
    def __init__(self):
        # 0 = path, 1 = wall, 2 = exit
        # Try creating your own maze!
        self.grid = [
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            [1, 0, 0, 0, 1, 0, 0, 0, 0, 1],
            [1, 0, 1, 0, 1, 0, 1, 1, 0, 1],
            [1, 0, 1, 0, 0, 0, 0, 1, 0, 1],
            [1, 0, 1, 1, 1, 1, 0, 1, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 1, 0, 1],
            [1, 1, 1, 1, 1, 1, 0, 1, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 1, 1, 1, 1, 1, 1, 2, 1],
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        ]
        self.cell_size = 40  # Size of each cell

    def check_win(self, player):
        """Check if player reached the exit"""
        return self.grid[player.y][player.x] == 2

# Create game objects
player = Player()
maze = Maze()

# Game state
won = False
best_moves = None  # Track fastest solution

# TODO: Create a bigger maze (15x15)
# TODO: Add treasures to collect (value 3)
# TODO: Add moving enemies to avoid
# TODO: Make multiple levels
# TODO: Add a timer - can you solve it in 30 seconds?
'''

        maze = Game(
            name='maze',
            display_name='Maze Adventure',
            description='Navigate the maze and find the exit!',
            template_code=maze_template
        )
        db.session.add(maze)

        # 5. Tetris
        tetris_template = '''# Tetris
# Arrow keys: Left/Right to move, Up to rotate, Down to drop faster
# Clear lines to score points!

class Piece:
    def __init__(self, shape):
        self.shape = shape  # 2D array of blocks
        self.x = 3  # Start in middle-ish
        self.y = 0
        self.rotation = 0

    def rotate(self):
        """Rotate piece clockwise"""
        # This rotates a 2D array 90 degrees
        self.shape = [[self.shape[y][x]
                      for y in range(len(self.shape)-1, -1, -1)]
                      for x in range(len(self.shape[0]))]

    def move_left(self):
        self.x -= 1

    def move_right(self):
        self.x += 1

    def move_down(self):
        self.y += 1

class Board:
    def __init__(self):
        self.width = 10
        self.height = 20
        # 0 = empty, 1 = filled
        self.grid = [[0 for _ in range(self.width)]
                     for _ in range(self.height)]
        self.score = 0

    def check_collision(self, piece):
        """Check if piece collides with board or other pieces"""
        for y, row in enumerate(piece.shape):
            for x, cell in enumerate(row):
                if cell:  # If this part of piece exists
                    new_x = piece.x + x
                    new_y = piece.y + y

                    # Check boundaries
                    if new_x < 0 or new_x >= self.width:
                        return True
                    if new_y >= self.height:
                        return True
                    if new_y >= 0 and self.grid[new_y][new_x]:
                        return True
        return False

    def lock_piece(self, piece):
        """Lock piece into board"""
        for y, row in enumerate(piece.shape):
            for x, cell in enumerate(row):
                if cell:
                    self.grid[piece.y + y][piece.x + x] = 1

    def clear_lines(self):
        """Remove completed lines and award points"""
        lines_cleared = 0
        y = self.height - 1

        while y >= 0:
            if all(self.grid[y]):  # Line is full
                del self.grid[y]
                self.grid.insert(0, [0] * self.width)
                lines_cleared += 1
            else:
                y -= 1

        # Score: 100, 300, 500, 800 for 1,2,3,4 lines
        scores = [0, 100, 300, 500, 800]
        self.score += scores[min(lines_cleared, 4)]

        return lines_cleared

# Tetris piece shapes (the famous tetrominoes!)
SHAPES = [
    [[1, 1, 1, 1]],  # I piece
    [[1, 1], [1, 1]],  # O piece (square)
    [[0, 1, 0], [1, 1, 1]],  # T piece
    [[1, 1, 0], [0, 1, 1]],  # S piece
    [[0, 1, 1], [1, 1, 0]],  # Z piece
    [[1, 1, 1], [1, 0, 0]],  # L piece
    [[1, 1, 1], [0, 0, 1]],  # J piece
]

# Create board
board = Board()

# Game state
game_over = False
drop_speed = 500  # milliseconds between automatic drops

# TODO: Add a "next piece" preview
# TODO: Make game faster as score increases
# TODO: Add different colors for each piece type
# TODO: Track high score
# TODO: Add a "hold piece" feature
# TODO: Show ghost piece (where it will land)
'''

        tetris = Game(
            name='tetris',
            display_name='Tetris',
            description='Stack blocks and clear lines! Classic puzzle game.',
            template_code=tetris_template
        )
        db.session.add(tetris)

        # Commit all games
        db.session.commit()

        print("Database initialized with 5 games: Snake, Pong, Space Invaders, Maze, Tetris!")

if __name__ == '__main__':
    init_db()
    # Replit optimized: bind to 0.0.0.0 for external access
    port = int(os.environ.get('PORT', 8443))
    app.run(host='0.0.0.0', port=port, debug=os.environ.get('FLASK_ENV') != 'production')

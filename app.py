from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from dotenv import load_dotenv
from datetime import datetime, timezone
import difflib
import os
import signal
import sys
import atexit
import warnings

app = Flask(__name__)

# Replit-optimized configuration
# Use absolute path for SQLite database
basedir = os.path.abspath(os.path.dirname(__file__))
instance_path = os.path.join(basedir, 'instance')
os.makedirs(instance_path, exist_ok=True)

db_path = os.path.join(instance_path, "python_games.db")

# Always use SQLite - ignore Replit's DATABASE_URL if it's PostgreSQL
database_url = os.environ.get('DATABASE_URL', '')
if database_url.startswith('postgres'):
    # Replit provides PostgreSQL by default, but we want SQLite for this app
    database_url = f'sqlite:///{db_path}'
elif not database_url:
    database_url = f'sqlite:///{db_path}'

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

db = SQLAlchemy(app)
CORS(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    code_versions = db.relationship('CodeVersion', backref='user', lazy=True, cascade='all, delete-orphan')

class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    display_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    template_code = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class CodeVersion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'), nullable=False)
    code = db.Column(db.Text, nullable=False)
    message = db.Column(db.String(200))  # Optional commit message
    is_checkpoint = db.Column(db.Boolean, default=False)  # Manual saves
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    game = db.relationship('Game', backref='versions')

class Mission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    order = db.Column(db.Integer, nullable=False)  # Mission sequence number
    difficulty = db.Column(db.String(20))  # beginner, intermediate, advanced, expert
    validation_type = db.Column(db.String(50), nullable=False)  # code_contains, code_matches, variable_changed, etc.
    validation_data = db.Column(db.Text)  # JSON string with validation criteria
    hints = db.Column(db.Text)  # JSON array of hints
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    game = db.relationship('Game', backref='missions')

class UserMissionProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    mission_id = db.Column(db.Integer, db.ForeignKey('mission.id'), nullable=False)
    status = db.Column(db.String(20), default='not_started')  # not_started, in_progress, completed, failed
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    attempts = db.Column(db.Integer, default=0)
    validation_result = db.Column(db.Text)  # JSON with validation details

    user = db.relationship('User', backref='mission_progress')
    mission = db.relationship('Mission', backref='user_progress')

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
    game = db.session.get(Game, game_id)
    if game is None:
        return "Game not found", 404
    users = User.query.all()
    return render_template('game.html', game=game, users=users)

@app.route('/healthz')
def health_check():
    """Simple health check for deployment"""
    return jsonify({'status': 'ok'}), 200

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
    game = db.session.get(Game, game_id)
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
    version = db.session.get(CodeVersion, version_id)
    if version is None:
        return jsonify({'error': 'Version not found'}), 404
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

    v1 = db.session.get(CodeVersion, version1_id)
    v2 = db.session.get(CodeVersion, version2_id)

    if v1 is None or v2 is None:
        return jsonify({'error': 'Version not found'}), 404

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

    old_version = db.session.get(CodeVersion, version_id)
    if old_version is None:
        return jsonify({'error': 'Version not found'}), 404

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

# Mission API Endpoints
@app.route('/api/missions/<int:game_id>', methods=['GET'])
def get_missions(game_id):
    """Get all missions for a specific game, ordered by sequence"""
    missions = Mission.query.filter_by(game_id=game_id).order_by(Mission.order).all()
    return jsonify([{
        'id': m.id,
        'title': m.title,
        'description': m.description,
        'order': m.order,
        'difficulty': m.difficulty,
        'hints': m.hints
    } for m in missions])

@app.route('/api/missions/<int:mission_id>/progress', methods=['GET', 'POST'])
def mission_progress(mission_id):
    """Get or update progress for a mission"""
    if request.method == 'GET':
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({'error': 'user_id required'}), 400

        progress = UserMissionProgress.query.filter_by(
            user_id=user_id,
            mission_id=mission_id
        ).first()

        if not progress:
            return jsonify({
                'status': 'not_started',
                'attempts': 0
            })

        return jsonify({
            'id': progress.id,
            'status': progress.status,
            'started_at': progress.started_at.isoformat() if progress.started_at else None,
            'completed_at': progress.completed_at.isoformat() if progress.completed_at else None,
            'attempts': progress.attempts,
            'validation_result': progress.validation_result
        })

    # POST - Start or update mission
    data = request.json
    user_id = data.get('user_id')
    action = data.get('action')  # 'start', 'validate', 'complete'

    if not user_id:
        return jsonify({'error': 'user_id required'}), 400

    progress = UserMissionProgress.query.filter_by(
        user_id=user_id,
        mission_id=mission_id
    ).first()

    if action == 'start':
        if not progress:
            progress = UserMissionProgress(
                user_id=user_id,
                mission_id=mission_id,
                status='in_progress',
                started_at=datetime.now(timezone.utc)
            )
            db.session.add(progress)
        else:
            progress.status = 'in_progress'
            if not progress.started_at:
                progress.started_at = datetime.now(timezone.utc)

        db.session.commit()
        return jsonify({'message': 'Mission started', 'status': progress.status})

    return jsonify({'error': 'Invalid action'}), 400

@app.route('/api/missions/<int:mission_id>/validate', methods=['POST'])
def validate_mission(mission_id):
    """Validate user's code against mission criteria"""
    import json
    import re

    data = request.json
    user_id = data.get('user_id')
    code = data.get('code')

    if not user_id or code is None:
        return jsonify({'error': 'user_id and code required'}), 400

    mission = db.session.get(Mission, mission_id)
    if not mission:
        return jsonify({'error': 'Mission not found'}), 404

    # Get or create progress
    progress = UserMissionProgress.query.filter_by(
        user_id=user_id,
        mission_id=mission_id
    ).first()

    if not progress:
        progress = UserMissionProgress(
            user_id=user_id,
            mission_id=mission_id,
            status='in_progress',
            started_at=datetime.now(timezone.utc)
        )
        db.session.add(progress)

    progress.attempts += 1

    # Parse validation data
    validation_criteria = json.loads(mission.validation_data) if mission.validation_data else {}
    validation_type = mission.validation_type

    success = False
    feedback = ""

    # Validation logic based on type
    if validation_type == 'code_contains':
        required_text = validation_criteria.get('text', '')
        if required_text in code:
            success = True
            feedback = validation_criteria.get('success_message', 'Great job! You added the required code.')
        else:
            feedback = validation_criteria.get('failure_message', f'Missing required code: {required_text}')

    elif validation_type == 'variable_changed':
        var_name = validation_criteria.get('variable')
        old_value = str(validation_criteria.get('old_value'))
        new_value_pattern = validation_criteria.get('new_value_pattern', '.*')

        # Find variable assignment
        pattern = rf'{var_name}\s*=\s*([^\n]+)'
        matches = re.findall(pattern, code)

        if matches:
            current_value = matches[0].strip()
            if current_value != old_value and re.match(new_value_pattern, current_value):
                success = True
                feedback = validation_criteria.get('success_message', f'Excellent! You changed {var_name}.')
            else:
                feedback = validation_criteria.get('failure_message', f'Try changing {var_name} to a different value.')
        else:
            feedback = f'Could not find {var_name} in your code.'

    elif validation_type == 'code_pattern':
        pattern = validation_criteria.get('pattern')
        if re.search(pattern, code, re.MULTILINE):
            success = True
            feedback = validation_criteria.get('success_message', 'Perfect! Your code matches the pattern.')
        else:
            feedback = validation_criteria.get('failure_message', 'Your code doesn\'t match the expected pattern yet.')

    elif validation_type == 'line_count_increased':
        original_code = db.session.get(Game, mission.game_id).template_code
        original_lines = len([line for line in original_code.split('\n') if line.strip()])
        current_lines = len([line for line in code.split('\n') if line.strip()])
        min_increase = validation_criteria.get('min_increase', 1)

        if current_lines >= original_lines + min_increase:
            success = True
            feedback = validation_criteria.get('success_message', f'Awesome! You added {current_lines - original_lines} new lines of code.')
        else:
            feedback = validation_criteria.get('failure_message', f'Try adding at least {min_increase} more lines of code.')

    # Update progress
    if success:
        progress.status = 'completed'
        progress.completed_at = datetime.now(timezone.utc)

    progress.validation_result = json.dumps({'success': success, 'feedback': feedback})
    db.session.commit()

    return jsonify({
        'success': success,
        'feedback': feedback,
        'attempts': progress.attempts,
        'status': progress.status
    })

def init_db():
    """Initialize database with sample games"""
    # Ensure instance directory exists (important for Flask reloader)
    os.makedirs(instance_path, exist_ok=True)

    with app.app_context():
        db.create_all()

        # Check if games already exist
        if Game.query.count() > 0:
            return

        # 1. Snake Game
        snake_template = '''# Snake Game
# Use arrow keys to move the snake
# Eat the red food to grow!

from js import clear_screen, draw_rect, draw_circle, draw_text, document
import random

# Game settings
GRID_SIZE = 20
CANVAS_WIDTH = 600
CANVAS_HEIGHT = 600

class Snake:
    def __init__(self):
        self.x = 15
        self.y = 15
        self.segments = [(15, 15)]
        self.direction = "right"
        self.next_direction = "right"

    def change_direction(self, new_direction):
        """Change direction, but prevent 180-degree turns"""
        if new_direction == "right" and self.direction != "left":
            self.next_direction = "right"
        elif new_direction == "left" and self.direction != "right":
            self.next_direction = "left"
        elif new_direction == "up" and self.direction != "down":
            self.next_direction = "up"
        elif new_direction == "down" and self.direction != "up":
            self.next_direction = "down"

    def move(self):
        """Move the snake in the current direction"""
        self.direction = self.next_direction

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

    def check_collision(self):
        """Check if snake hit wall or itself"""
        # Wall collision
        if self.x < 0 or self.x >= CANVAS_WIDTH // GRID_SIZE:
            return True
        if self.y < 0 or self.y >= CANVAS_HEIGHT // GRID_SIZE:
            return True

        # Self collision
        if (self.x, self.y) in self.segments[1:]:
            return True

        return False

class Food:
    def __init__(self):
        self.x = random.randint(0, (CANVAS_WIDTH // GRID_SIZE) - 1)
        self.y = random.randint(0, (CANVAS_HEIGHT // GRID_SIZE) - 1)

    def respawn(self, snake_segments):
        """Place food at random position not on snake"""
        while True:
            self.x = random.randint(0, (CANVAS_WIDTH // GRID_SIZE) - 1)
            self.y = random.randint(0, (CANVAS_HEIGHT // GRID_SIZE) - 1)
            if (self.x, self.y) not in snake_segments:
                break

# Game state
snake = Snake()
food = Food()
score = 0
frame_count = 0
game_over = False
game_started = False

def update():
    """Update game logic (called every frame)"""
    global frame_count, score, game_over, game_started

    # Check for SPACE to start game
    from js import is_key_pressed
    if not game_started and not game_over:
        if is_key_pressed(' '):
            game_started = True
        return

    if game_over:
        return

    # Move snake every 6 frames (adjust for speed)
    frame_count += 1
    if frame_count % 6 != 0:
        return

    # Handle keyboard input
    from js import is_key_pressed
    if is_key_pressed("ArrowRight"):
        snake.change_direction("right")
    elif is_key_pressed("ArrowLeft"):
        snake.change_direction("left")
    elif is_key_pressed("ArrowUp"):
        snake.change_direction("up")
    elif is_key_pressed("ArrowDown"):
        snake.change_direction("down")

    # Move snake
    snake.move()

    # Check collision
    if snake.check_collision():
        game_over = True
        return

    # Check if snake ate food
    if snake.x == food.x and snake.y == food.y:
        snake.grow()
        food.respawn(snake.segments)
        score += 10

def draw():
    """Draw everything (called every frame)"""
    # Clear screen
    clear_screen()

    # Draw background
    draw_rect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT, "#1a1a1a")

    # Show start screen if game hasn't started
    if not game_started and not game_over:
        draw_text("SNAKE GAME", 180, 250, "#44ff44", "52px Arial")
        draw_text("Press SPACE to Start", 180, 320, "#ffffff", "28px Arial")
        draw_text("Use Arrow Keys to Move", 160, 360, "#888888", "20px Arial")
        return

    # Draw grid (optional, for visual reference)
    for i in range(0, CANVAS_WIDTH, GRID_SIZE):
        draw_rect(i, 0, 1, CANVAS_HEIGHT, "#2a2a2a")
    for i in range(0, CANVAS_HEIGHT, GRID_SIZE):
        draw_rect(0, i, CANVAS_WIDTH, 1, "#2a2a2a")

    # Draw food
    draw_rect(
        food.x * GRID_SIZE + 2,
        food.y * GRID_SIZE + 2,
        GRID_SIZE - 4,
        GRID_SIZE - 4,
        "#ff4444"
    )

    # Draw snake
    for i, (seg_x, seg_y) in enumerate(snake.segments):
        color = "#44ff44" if i == 0 else "#33cc33"  # Head is brighter
        draw_rect(
            seg_x * GRID_SIZE + 1,
            seg_y * GRID_SIZE + 1,
            GRID_SIZE - 2,
            GRID_SIZE - 2,
            color
        )

    # Draw score
    draw_text(f"Score: {score}", 10, 30, "#ffffff", "24px Arial")

    # Draw game over message
    if game_over:
        draw_text("GAME OVER!", 200, 300, "#ff4444", "48px Arial")
        draw_text(f"Final Score: {score}", 220, 350, "#ffffff", "24px Arial")

# TODO: Try changing the speed (change the % 6 in update function)
# TODO: Try changing the colors of the snake or food
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

from js import clear_screen, draw_rect, draw_circle, draw_text, document

# Game settings
CANVAS_WIDTH = 600
CANVAS_HEIGHT = 600
WINNING_SCORE = 5

class Paddle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 15
        self.height = 80
        self.speed = 8  # Try changing paddle speed!
        self.score = 0

    def move_up(self):
        """Move paddle up"""
        self.y -= self.speed
        if self.y < 0:
            self.y = 0

    def move_down(self):
        """Move paddle down"""
        self.y += self.speed
        if self.y > CANVAS_HEIGHT - self.height:
            self.y = CANVAS_HEIGHT - self.height

class Ball:
    def __init__(self):
        self.reset()

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
        if abs(self.speed_x) < 15:  # Max speed cap
            self.speed_x *= 1.1
            self.speed_y *= 1.1

    def reset(self):
        """Reset ball to center"""
        self.x = CANVAS_WIDTH // 2
        self.y = CANVAS_HEIGHT // 2
        self.radius = 8
        import random
        self.speed_x = 5 if random.random() > 0.5 else -5
        self.speed_y = random.uniform(-4, 4)

# Create players and ball
player1 = Paddle(30, CANVAS_HEIGHT // 2 - 40)    # Left paddle
player2 = Paddle(CANVAS_WIDTH - 45, CANVAS_HEIGHT // 2 - 40)  # Right paddle
ball = Ball()
game_over = False
game_started = False
countdown_active = False
countdown_timer = 0
countdown_value = 3
winner = ""

def update():
    """Update game logic (called every frame)"""
    global game_over, game_started, countdown_active, countdown_timer, countdown_value, winner

    # Check for SPACE to start game
    from js import is_key_pressed
    if not game_started and not game_over:
        if is_key_pressed(' '):
            game_started = True
            countdown_active = True
            countdown_timer = 0
            countdown_value = 3
        return

    # Handle countdown
    if countdown_active:
        countdown_timer += 1
        # Each number shows for about 30 frames (half a second at 60fps)
        if countdown_timer >= 30:
            countdown_timer = 0
            countdown_value -= 1
            if countdown_value <= 0:
                countdown_active = False
        return

    if game_over:
        return

    # Handle player 1 controls (W/S)
    if is_key_pressed('w') or is_key_pressed('W'):
        player1.move_up()
    elif is_key_pressed('s') or is_key_pressed('S'):
        player1.move_down()

    # Handle player 2 controls (Arrow keys)
    if is_key_pressed('ArrowUp'):
        player2.move_up()
    elif is_key_pressed('ArrowDown'):
        player2.move_down()

    # Move ball
    ball.move()

    # Ball collision with top/bottom
    if ball.y - ball.radius <= 0 or ball.y + ball.radius >= CANVAS_HEIGHT:
        ball.bounce_y()

    # Ball collision with paddles
    # Left paddle (player 1)
    if (ball.x - ball.radius <= player1.x + player1.width and
        player1.y <= ball.y <= player1.y + player1.height and
        ball.speed_x < 0):
        ball.bounce_x()

    # Right paddle (player 2)
    if (ball.x + ball.radius >= player2.x and
        player2.y <= ball.y <= player2.y + player2.height and
        ball.speed_x > 0):
        ball.bounce_x()

    # Ball out of bounds (scoring)
    if ball.x < 0:
        player2.score += 1
        ball.reset()
        countdown_active = True
        countdown_timer = 0
        countdown_value = 3
    elif ball.x > CANVAS_WIDTH:
        player1.score += 1
        ball.reset()
        countdown_active = True
        countdown_timer = 0
        countdown_value = 3

    # Check for winner
    if player1.score >= WINNING_SCORE:
        game_over = True
        winner = "Player 1"
    elif player2.score >= WINNING_SCORE:
        game_over = True
        winner = "Player 2"

def draw():
    """Draw everything (called every frame)"""
    # Clear screen
    clear_screen()

    # Draw background
    draw_rect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT, "#1a1a1a")

    # Show start screen if game hasn't started
    if not game_started and not game_over:
        draw_text("PONG", 240, 220, "#ffffff", "72px Arial")
        draw_text("Press SPACE to Start", 180, 300, "#ffffff", "28px Arial")
        draw_text("Player 1: W/S", 210, 350, "#4444ff", "20px Arial")
        draw_text("Player 2: ↑/↓", 210, 380, "#ff4444", "20px Arial")
        return

    # Draw center line
    for i in range(0, CANVAS_HEIGHT, 20):
        draw_rect(CANVAS_WIDTH // 2 - 2, i, 4, 10, "#444444")

    # Show countdown if active
    if countdown_active and countdown_value > 0:
        draw_text(str(countdown_value), CANVAS_WIDTH // 2 - 30, CANVAS_HEIGHT // 2, "#ffff44", "96px Arial")

    # Draw paddles
    draw_rect(player1.x, player1.y, player1.width, player1.height, "#4444ff")
    draw_rect(player2.x, player2.y, player2.width, player2.height, "#ff4444")

    # Draw ball
    draw_circle(ball.x, ball.y, ball.radius, "#ffffff")

    # Draw scores
    draw_text(str(player1.score), CANVAS_WIDTH // 2 - 50, 50, "#ffffff", "48px Arial")
    draw_text(str(player2.score), CANVAS_WIDTH // 2 + 30, 50, "#ffffff", "48px Arial")

    # Draw player labels
    draw_text("P1 (W/S)", 10, CANVAS_HEIGHT - 20, "#4444ff", "16px Arial")
    draw_text("P2 (↑/↓)", CANVAS_WIDTH - 100, CANVAS_HEIGHT - 20, "#ff4444", "16px Arial")

    # Draw game over message
    if game_over:
        draw_text(f"{winner} WINS!", 180, CANVAS_HEIGHT // 2, "#44ff44", "48px Arial")
        draw_text(f"Score: {player1.score} - {player2.score}", 200, CANVAS_HEIGHT // 2 + 50, "#ffffff", "24px Arial")

# TODO: Make paddles bigger or smaller (change height/width)
# TODO: Make the ball faster (change initial speed_x/speed_y)
# TODO: Change winning score to 10 (change WINNING_SCORE)
# TODO: Add sound effects when ball hits paddle!
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

from js import clear_screen, draw_rect, draw_text, document

# Game settings
CANVAS_WIDTH = 600
CANVAS_HEIGHT = 600

class Player:
    def __init__(self):
        self.x = CANVAS_WIDTH // 2 - 20
        self.y = CANVAS_HEIGHT - 80
        self.width = 40
        self.height = 30
        self.speed = 7  # Try changing this!
        self.lives = 3
        self.can_shoot = True
        self.shoot_cooldown = 0

    def move_left(self):
        self.x -= self.speed
        if self.x < 0:
            self.x = 0

    def move_right(self):
        self.x += self.speed
        if self.x > CANVAS_WIDTH - self.width:
            self.x = CANVAS_WIDTH - self.width

class Bullet:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 4
        self.height = 12
        self.speed = 8
        self.active = True

    def move(self):
        self.y -= self.speed
        if self.y < 0:
            self.active = False

class Alien:
    def __init__(self, x, y, row):
        self.x = x
        self.y = y
        self.width = 30
        self.height = 25
        self.alive = True
        # Different point values for different rows
        self.points = 30 - (row * 5)

# Create player
player = Player()

# Create grid of aliens (5 rows x 10 columns)
aliens = []
for row in range(5):
    for col in range(10):
        x = 40 + col * 50
        y = 50 + row * 40
        aliens.append(Alien(x, y, row))

# List to hold bullets
bullets = []

# Alien movement
alien_direction = 1  # 1 = right, -1 = left
alien_speed = 1
frame_count = 0

# Game state
score = 0
game_over = False
game_won = False
game_started = False

def check_collision(bullet, alien):
    """Check if bullet hits alien"""
    return (bullet.x < alien.x + alien.width and
            bullet.x + bullet.width > alien.x and
            bullet.y < alien.y + alien.height and
            bullet.y + bullet.height > alien.y)

def update():
    """Update game logic"""
    global alien_direction, frame_count, score, game_over, game_won, game_started

    if not game_started and not game_over:
        from js import is_key_pressed
        if is_key_pressed(' '):
            game_started = True
        return

    if game_over or game_won:
        return

    frame_count += 1

    # Handle player movement
    from js import is_key_pressed
    if is_key_pressed('ArrowLeft'):
        player.move_left()
    elif is_key_pressed('ArrowRight'):
        player.move_right()

    if is_key_pressed(' ') and player.can_shoot:
        # Shoot bullet
        bullets.append(Bullet(player.x + player.width // 2 - 2, player.y))
        player.can_shoot = False
        player.shoot_cooldown = 15

    # Handle shoot cooldown
    if player.shoot_cooldown > 0:
        player.shoot_cooldown -= 1
    else:
        player.can_shoot = True

    # Move bullets
    for bullet in bullets:
        bullet.move()

    # Remove inactive bullets
    bullets[:] = [b for b in bullets if b.active]

    # Move aliens (every 3 frames)
    if frame_count % 3 == 0:
        # Check if any alien hit edge
        hit_edge = False
        for alien in aliens:
            if alien.alive:
                if (alien.x <= 0 and alien_direction == -1) or \
                   (alien.x >= CANVAS_WIDTH - alien.width and alien_direction == 1):
                    hit_edge = True
                    break

        if hit_edge:
            # Change direction and move down
            alien_direction *= -1
            for alien in aliens:
                alien.y += 20
        else:
            # Move sideways
            for alien in aliens:
                alien.x += alien_direction * alien_speed

    # Check bullet-alien collisions
    for bullet in bullets[:]:
        for alien in aliens:
            if alien.alive and bullet.active and check_collision(bullet, alien):
                alien.alive = False
                bullet.active = False
                score += alien.points
                break

    # Check if aliens reached player
    for alien in aliens:
        if alien.alive and alien.y + alien.height >= player.y:
            game_over = True
            return

    # Check win condition
    if all(not alien.alive for alien in aliens):
        game_won = True

def draw():
    """Draw everything"""
    # Clear screen
    clear_screen()

    # Draw background
    draw_rect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT, "#0a0a2e")

    # Draw player
    draw_rect(player.x, player.y, player.width, player.height, "#44ff44")

    # Draw aliens
    for alien in aliens:
        if alien.alive:
            # Different colors for different rows
            colors = ["#ff4444", "#ff8844", "#ffcc44", "#88ff44", "#4488ff"]
            row = int((alien.y - 50) / 40)
            color = colors[min(row, 4)]
            draw_rect(alien.x, alien.y, alien.width, alien.height, color)

    # Draw bullets
    for bullet in bullets:
        if bullet.active:
            draw_rect(bullet.x, bullet.y, bullet.width, bullet.height, "#ffffff")

    # Show start screen if game hasn't started
    if not game_started and not game_over:
        draw_text("SPACE INVADERS", 140, 250, "#ffffff", "52px Arial")
        draw_text("Press SPACE to Start", 200, 320, "#ffffff", "28px Arial")
        draw_text("Arrow keys to move", 210, 370, "#888888", "20px Arial")
        draw_text("SPACE to shoot", 230, 400, "#888888", "20px Arial")
        return

    # Draw score and lives
    draw_text(f"Score: {score}", 10, 25, "#ffffff", "20px Arial")
    draw_text(f"Lives: {player.lives}", CANVAS_WIDTH - 100, 25, "#ffffff", "20px Arial")

    # Draw game over message
    if game_over:
        draw_text("GAME OVER!", 180, CANVAS_HEIGHT // 2, "#ff4444", "52px Arial")
        draw_text("Aliens reached Earth!", 180, CANVAS_HEIGHT // 2 + 60, "#ffffff", "24px Arial")

    # Draw win message
    if game_won:
        draw_text("YOU WIN!", 200, CANVAS_HEIGHT // 2, "#44ff44", "52px Arial")
        draw_text(f"Final Score: {score}", 200, CANVAS_HEIGHT // 2 + 60, "#ffffff", "28px Arial")

# TODO: Add more alien rows (change range(5) to range(7))
# TODO: Make aliens move faster (change alien_speed)
# TODO: Add power-ups that drop from defeated aliens
# TODO: Add shields for the player to hide behind
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

from js import clear_screen, draw_rect, draw_text, document

# Game settings
CELL_SIZE = 50
CANVAS_WIDTH = 600
CANVAS_HEIGHT = 600

class Player:
    def __init__(self):
        self.x = 1  # Grid position
        self.y = 1
        self.moves = 0
        self.last_move = 0  # Prevent too-fast movement

    def can_move(self, dx, dy, maze_grid):
        """Check if move is valid"""
        new_x = self.x + dx
        new_y = self.y + dy

        # Check bounds
        if new_y < 0 or new_y >= len(maze_grid):
            return False
        if new_x < 0 or new_x >= len(maze_grid[0]):
            return False

        # Check if not a wall
        return maze_grid[new_y][new_x] != 1

    def move(self, dx, dy, maze_grid):
        """Move if valid"""
        if self.can_move(dx, dy, maze_grid):
            self.x += dx
            self.y += dy
            self.moves += 1
            return True
        return False

class Maze:
    def __init__(self):
        # 0 = path, 1 = wall, 2 = exit, 3 = treasure
        self.grid = [
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            [1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 0, 1],
            [1, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 1],
            [1, 0, 1, 1, 1, 1, 1, 1, 0, 1, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1],
            [1, 1, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1],
            [1, 3, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1],
            [1, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1],
            [1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1],
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        ]

# Create game objects
player = Player()
maze = Maze()

# Game state
won = False
treasures_collected = 0
total_treasures = sum(row.count(3) for row in maze.grid)
frame_count = 0
game_started = False

def update():
    """Update game logic"""
    global won, treasures_collected, frame_count, game_started

    if not game_started and not won:
        from js import is_key_pressed
        if is_key_pressed(' '):
            game_started = True
        return

    if won:
        return

    frame_count += 1

    # Handle movement with delay to prevent too-fast movement
    if frame_count % 8 != 0:  # Only check input every 8 frames
        return

    from js import is_key_pressed
    moved = False

    if is_key_pressed('ArrowUp'):
        moved = player.move(0, -1, maze.grid)
    elif is_key_pressed('ArrowDown'):
        moved = player.move(0, 1, maze.grid)
    elif is_key_pressed('ArrowLeft'):
        moved = player.move(-1, 0, maze.grid)
    elif is_key_pressed('ArrowRight'):
        moved = player.move(1, 0, maze.grid)

    if moved:
        # Check for treasure
        if maze.grid[player.y][player.x] == 3:
            treasures_collected += 1
            maze.grid[player.y][player.x] = 0  # Remove treasure

        # Check for exit
        if maze.grid[player.y][player.x] == 2:
            won = True

def draw():
    """Draw everything"""
    # Clear screen
    clear_screen()

    # Draw background
    draw_rect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT, "#1a1a1a")

    # Show start screen if game hasn't started
    if not game_started and not won:
        draw_text("MAZE ADVENTURE", 160, 250, "#ffffff", "48px Arial")
        draw_text("Press SPACE to Start", 180, 320, "#ffffff", "28px Arial")
        draw_text("Arrow keys to move", 200, 370, "#888888", "20px Arial")
        draw_text("Collect treasures and find the exit!", 130, 400, "#ffd700", "18px Arial")
        return

    # Draw maze
    for y in range(len(maze.grid)):
        for x in range(len(maze.grid[y])):
            cell_x = x * CELL_SIZE
            cell_y = y * CELL_SIZE

            cell_type = maze.grid[y][x]

            if cell_type == 1:  # Wall
                draw_rect(cell_x, cell_y, CELL_SIZE, CELL_SIZE, "#4a4a4a")
            elif cell_type == 0:  # Path
                draw_rect(cell_x, cell_y, CELL_SIZE, CELL_SIZE, "#2a2a2a")
            elif cell_type == 2:  # Exit
                draw_rect(cell_x, cell_y, CELL_SIZE, CELL_SIZE, "#44ff44")
                draw_text("EXIT", cell_x + 5, cell_y + 30, "#000000", "16px Arial")
            elif cell_type == 3:  # Treasure
                draw_rect(cell_x, cell_y, CELL_SIZE, CELL_SIZE, "#2a2a2a")
                draw_rect(cell_x + 10, cell_y + 10, CELL_SIZE - 20, CELL_SIZE - 20, "#ffd700")

    # Draw player
    player_x = player.x * CELL_SIZE
    player_y = player.y * CELL_SIZE
    draw_rect(player_x + 8, player_y + 8, CELL_SIZE - 16, CELL_SIZE - 16, "#4444ff")

    # Draw stats
    draw_text(f"Moves: {player.moves}", 10, CANVAS_HEIGHT - 20, "#ffffff", "20px Arial")
    draw_text(f"Treasures: {treasures_collected}/{total_treasures}", 200, CANVAS_HEIGHT - 20, "#ffd700", "20px Arial")

    # Draw win message
    if won:
        draw_rect(100, 250, 400, 100, "#000000")
        draw_text("YOU WIN!", 180, 300, "#44ff44", "48px Arial")
        draw_text(f"Moves: {player.moves}", 220, 330, "#ffffff", "24px Arial")

# TODO: Create a bigger maze (add more rows/columns)
# TODO: Add more treasures to collect
# TODO: Try making a harder maze pattern
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

        tetris = Game(
            name='tetris',
            display_name='Tetris',
            description='Stack blocks and clear lines! Classic puzzle game.',
            template_code=tetris_template
        )
        db.session.add(tetris)

        # Commit games first to get IDs
        db.session.commit()

        # Add missions for Snake game
        import json

        # Snake Mission 1: Change speed
        mission1 = Mission(
            game_id=snake.id,
            title="Change the Snake's Speed",
            description="Find the `speed` variable (around line 8) and change it to a different number. Try 3 for slow, 10 for fast, or 20 for super fast! What feels best to you?",
            order=1,
            difficulty="beginner",
            validation_type="variable_changed",
            validation_data=json.dumps({
                'variable': 'speed',
                'old_value': '5',
                'new_value_pattern': r'\d+',
                'success_message': 'Awesome! You changed the speed. Try running the game to see how it feels!',
                'failure_message': 'Find the speed variable and change it to a different number.'
            }),
            hints=json.dumps([
                "Look for a line that says 'speed = 5'",
                "Try changing 5 to 10 to make the snake faster",
                "Numbers like 3, 8, 15, or 20 all work - pick what's fun!"
            ])
        )
        db.session.add(mission1)

        # Snake Mission 2: Change grid size
        mission2 = Mission(
            game_id=snake.id,
            title="Make the Game Board Bigger or Smaller",
            description="Find `GRID_SIZE = 20` (around line 10) and change it. Try 15 for a smaller board or 25 for a bigger board!",
            order=2,
            difficulty="beginner",
            validation_type="variable_changed",
            validation_data=json.dumps({
                'variable': 'GRID_SIZE',
                'old_value': '20',
                'new_value_pattern': r'\d+',
                'success_message': 'Perfect! You resized the game board. The snake has more (or less) room to move now!',
                'failure_message': 'Look for GRID_SIZE and change it from 20 to another number.'
            }),
            hints=json.dumps([
                "GRID_SIZE controls how big the game board is",
                "Smaller numbers = smaller board, bigger numbers = bigger board",
                "Try 15, 25, or 30 and see what you like!"
            ])
        )
        db.session.add(mission2)

        # Snake Mission 3: Make snake longer at start
        mission3 = Mission(
            game_id=snake.id,
            title="Start with a Longer Snake",
            description="Find where the snake's segments list is created and add more segments. Make your snake start with 5 segments instead of 3!",
            order=3,
            difficulty="intermediate",
            validation_type="code_pattern",
            validation_data=json.dumps({
                'pattern': r'self\.segments\s*=\s*\[[^\]]*,\s*[^\]]*,\s*[^\]]*,\s*[^\]]*,',
                'success_message': 'Excellent! Your snake now starts longer. That makes the game harder!',
                'failure_message': 'Add more coordinate tuples to the segments list. Each one is like (x, y).'
            }),
            hints=json.dumps([
                "Look for self.segments = [(10,10), (9,10), (8,10)]",
                "Add more tuples like (7,10), (6,10) to make it longer",
                "Each tuple represents one segment of the snake"
            ])
        )
        db.session.add(mission3)

        # Snake Mission 4: Add score tracking
        mission4 = Mission(
            game_id=snake.id,
            title="Add a Score Variable",
            description="Add a new variable called 'score' to track points. Initialize it to 0 in the __init__ method, then increase it by 10 each time the snake eats food!",
            order=4,
            difficulty="intermediate",
            validation_type="code_contains",
            validation_data=json.dumps({
                'text': 'self.score',
                'success_message': 'Great job! You added score tracking. Now players can see their progress!',
                'failure_message': 'Add "self.score = 0" in the Snake __init__ method.'
            }),
            hints=json.dumps([
                "In the __init__ method, add: self.score = 0",
                "In the grow() method, add: self.score += 10",
                "You can display the score using draw_text in the draw() function"
            ])
        )
        db.session.add(mission4)

        # Snake Mission 5: Add new features
        mission5 = Mission(
            game_id=snake.id,
            title="Add Your Own Creative Feature",
            description="Now it's your turn to be creative! Add at least 5 new lines of code that do something interesting. Ideas: change colors, add obstacles, make the snake rainbow, or anything you can imagine!",
            order=5,
            difficulty="advanced",
            validation_type="line_count_increased",
            validation_data=json.dumps({
                'min_increase': 5,
                'success_message': 'Amazing! You added your own creative code. You\'re becoming a real game developer!',
                'failure_message': 'Add at least 5 more lines of code to create something new and interesting.'
            }),
            hints=json.dumps([
                "Try changing the snake color in the draw() function",
                "Add obstacles that the snake must avoid",
                "Make the food change colors or size",
                "Add a timer or level system",
                "Be creative - there's no wrong answer!"
            ])
        )
        db.session.add(mission5)

        # Commit missions
        db.session.commit()

        print("Database initialized with 5 games and missions for Snake!")

def signal_handler(sig, frame):
    """Handle SIGINT (Ctrl+C) and SIGTERM gracefully"""
    print('\n🛑 Shutting down gracefully...')
    sys.exit(0)


if __name__ == '__main__':
    # Suppress resource tracker warnings from Werkzeug reloader
    # These are harmless and occur because Flask's dev server uses multiprocessing
    warnings.filterwarnings('ignore', category=UserWarning, module='multiprocessing.resource_tracker')

    # Register signal handlers for clean shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Initialize database before starting server
    # Only run in the parent process (when WERKZEUG_RUN_MAIN is not set)
    # The reloader child process will inherit the already-created database
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        init_db()

    # Replit optimized: bind to 0.0.0.0 for external access
    port = int(os.environ.get('PORT', 8443))
    is_debug = os.environ.get('FLASK_ENV') != 'production'

    try:
        app.run(
            host='0.0.0.0',
            port=port,
            debug=is_debug,
            use_reloader=is_debug,  # Only use reloader in debug mode
            threaded=True  # Enable threaded mode for better port cleanup
        )
    except KeyboardInterrupt:
        print('\n🛑 Server stopped by user')
    except Exception as e:
        print(f'\n❌ Server error: {e}')
        sys.exit(1)

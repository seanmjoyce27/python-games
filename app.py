from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
import difflib
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///python_games.db'
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

    # Keep only the last 25 versions per user per game
    old_versions = CodeVersion.query.filter_by(
        user_id=user_id,
        game_id=game_id
    ).order_by(CodeVersion.created_at.desc()).offset(25).all()

    for old in old_versions:
        db.session.delete(old)

    db.session.commit()

    return jsonify({
        'message': 'Code saved successfully',
        'version_id': version.id,
        'created_at': version.created_at.isoformat()
    }), 201

@app.route('/api/code/history', methods=['POST'])
def get_history():
    """Get version history for a user and game"""
    data = request.json
    user_id = data.get('user_id')
    game_id = data.get('game_id')

    if not user_id or not game_id:
        return jsonify({'error': 'user_id and game_id required'}), 400

    versions = CodeVersion.query.filter_by(
        user_id=user_id,
        game_id=game_id
    ).order_by(CodeVersion.created_at.desc()).limit(25).all()

    return jsonify([{
        'id': v.id,
        'message': v.message,
        'is_checkpoint': v.is_checkpoint,
        'created_at': v.created_at.isoformat(),
        'preview': v.code[:100] + '...' if len(v.code) > 100 else v.code
    } for v in versions])

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

        # Add Snake game
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
        db.session.commit()

        print("Database initialized with Snake game!")

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)

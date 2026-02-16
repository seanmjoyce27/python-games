from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, upgrade
from flask_cors import CORS
from dotenv import load_dotenv
from datetime import datetime, timezone
from sqlalchemy.exc import OperationalError
import difflib
import os
import signal
import sys
import atexit
import json
import warnings

# Load environment variables from .env file
load_dotenv()

# Fix macOS fork-safety crash: prevents SIGSEGV in Kerberos/CoreFoundation
# when Flask's dev reloader forks the process (multi-threaded process forked).
import platform
if platform.system() == 'Darwin':
    os.environ.setdefault('OBJC_DISABLE_INITIALIZE_FORK_SAFETY', 'YES')

app = Flask(__name__)

# Predefined kid-friendly coding avatars with sci-fi names
AVATAR_OPTIONS = [
    {"id": 1, "name": "Coremind Architect", "emoji": "🤖", "color": "#4A90E2"},
    {"id": 2, "name": "Astral Compiler", "emoji": "🚀", "color": "#E94B3C"},
    {"id": 3, "name": "Event Horizon Pathfinder", "emoji": "👾", "color": "#9B59B6"},
    {"id": 4, "name": "Neon Grid Pathfinder", "emoji": "🛸", "color": "#2ECC71"},
    {"id": 5, "name": "Hexblade Sentinel", "emoji": "⚔️", "color": "#F39C12"},
    {"id": 6, "name": "Chronoloop Warden", "emoji": "🔁", "color": "#1ABC9C"},
    {"id": 7, "name": "Glitch Reaper", "emoji": "🐛", "color": "#E74C3C"},
    {"id": 8, "name": "Logic Sharpshooter", "emoji": "🎯", "color": "#3498DB"},
    {"id": 9, "name": "Lambda Trickster", "emoji": "🦊", "color": "#E67E22"},
    {"id": 10, "name": "Dynamic Coil", "emoji": "🐍", "color": "#27AE60"},
    {"id": 11, "name": "Paradox Engineer", "emoji": "⚡", "color": "#9B59B6"},
    {"id": 12, "name": "Glyphweaver", "emoji": "⭐", "color": "#F1C40F"},
    {"id": 13, "name": "Twinbit Automaton", "emoji": "🎮", "color": "#34495E"},
    {"id": 14, "name": "Faultline Mechanic", "emoji": "🔧", "color": "#16A085"},
    {"id": 15, "name": "Terminal Warlord", "emoji": "🎖️", "color": "#C0392B"}
]

# Database Configuration
database_url = os.environ.get('DATABASE_URL')

if not database_url:
    # Default to local Postgres for development
    database_url = 'postgresql://localhost/python_games'
    print("⚠️  DATABASE_URL not set. Defaulting to local: postgresql://localhost/python_games")

if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

# Disable GSS/Kerberos authentication to prevent segfaults when forking on macOS.
# The crash occurs in libgssapi_krb5 when psycopg2/libpq checks for Kerberos creds
# in a forked child process (Flask reloader). Adding gssencmode=disable avoids this.
if '?' in database_url:
    if 'gssencmode' not in database_url:
        database_url += '&gssencmode=disable'
else:
    database_url += '?gssencmode=disable'

print(f"🐘 Connecting to PostgreSQL database...")

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

db = SQLAlchemy(app)
migrate = Migrate(app, db)
CORS(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    avatar_id = db.Column(db.Integer, nullable=False, default=1)  # References AVATAR_OPTIONS
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    code_versions = db.relationship('CodeVersion', backref='user', lazy=True, cascade='all, delete-orphan')

    def get_avatar(self):
        """Get avatar data for this user"""
        return next((a for a in AVATAR_OPTIONS if a['id'] == self.avatar_id), AVATAR_OPTIONS[0])

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
    try:
        games = Game.query.all()
        users = User.query.all()
        return render_template('index.html', games=games, users=users)
    except OperationalError:
        # DB/tables not ready yet (common on fresh deploy)
        return "Starting up…", 200
    except Exception as e:
        print(f"Error in index: {e}")
        return "Internal Server Error", 500

# Admin Routes
@app.route('/admin', methods=['GET', 'POST'])
def admin_panel():
    """Admin dashboard with password protection"""
    admin_password = os.environ.get('ADMIN_PASSWORD', 'python123')

    if request.method == 'POST' and not session.get('admin_authenticated'):
        entered_password = request.form.get('password', '')
        if entered_password == admin_password:
            session['admin_authenticated'] = True
            return redirect(url_for('admin_panel'))
        else:
            # Debug info (remove in production)
            print(f"Admin login failed. Expected: '{admin_password}', Got: '{entered_password}'")
            return render_template('admin.html', authenticated=False, error="Incorrect password")

    if not session.get('admin_authenticated'):
        return render_template('admin.html', authenticated=False)

    users = User.query.all()
    games = Game.query.all()
    total_saves = CodeVersion.query.count()
    total_missions = Mission.query.count()

    return render_template('admin.html', 
                         authenticated=True, 
                         users=users, 
                         games=games, 
                         total_saves=total_saves,
                         total_missions=total_missions)

@app.route('/admin/db/upgrade', methods=['POST'])
def admin_db_upgrade():
    """Run database migrations from the admin panel"""
    if not session.get('admin_authenticated'):
        return redirect(url_for('admin_panel'))
    
    try:
        upgrade()
        return redirect(url_for('admin_panel', message="Database upgraded successfully!"))
    except Exception as e:
        print(f"Migration failed: {e}")
        return redirect(url_for('admin_panel', error=f"Migration failed: {e}"))

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_authenticated', None)
    return redirect(url_for('admin_panel'))

@app.route('/admin/users/create', methods=['POST'])
def admin_create_user():
    if not session.get('admin_authenticated'):
        return redirect(url_for('admin_panel'))
    
    username = request.form.get('username')
    if username:
        if not User.query.filter_by(username=username).first():
            user = User(username=username)
            db.session.add(user)
            db.session.commit()
    
    return redirect(url_for('admin_panel'))

@app.route('/admin/users/delete/<username>', methods=['POST'])
def admin_delete_user(username):
    if not session.get('admin_authenticated'):
        return redirect(url_for('admin_panel'))
    
    user = User.query.filter_by(username=username).first()
    if user:
        db.session.delete(user)
        db.session.commit()
    
    return redirect(url_for('admin_panel'))

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
@app.route('/api/avatars', methods=['GET'])
def get_avatars():
    """Get all available avatars"""
    # Get list of already used avatar IDs
    used_avatar_ids = [u.avatar_id for u in User.query.all()]

    # Mark avatars as available or taken
    avatars_with_status = []
    for avatar in AVATAR_OPTIONS:
        avatars_with_status.append({
            **avatar,
            'available': avatar['id'] not in used_avatar_ids
        })

    return jsonify(avatars_with_status)

@app.route('/api/leaderboard', methods=['GET'])
def get_leaderboard():
    """Get leaderboard with mission completion counts"""
    users = User.query.all()
    leaderboard = []

    for user in users:
        # Count completed missions for this user
        completed_count = db.session.query(db.func.count(UserMissionProgress.id)).filter_by(
            user_id=user.id,
            status='completed'
        ).scalar() or 0

        leaderboard.append({
            'user_id': user.id,
            'avatar': user.get_avatar(),
            'completed_missions': completed_count
        })

    # Sort by completed missions (descending)
    leaderboard.sort(key=lambda x: x['completed_missions'], reverse=True)

    return jsonify(leaderboard)

@app.route('/api/users', methods=['GET', 'POST'])
def manage_users():
    """Get all users or create a new user"""
    if request.method == 'POST':
        data = request.json
        avatar_id = data.get('avatar_id')

        if not avatar_id or avatar_id < 1 or avatar_id > 15:
            return jsonify({'error': 'Invalid avatar selection'}), 400

        # Check if avatar is already taken
        if User.query.filter_by(avatar_id=avatar_id).first():
            return jsonify({'error': 'This avatar is already in use'}), 400

        # Get avatar data
        avatar = next((a for a in AVATAR_OPTIONS if a['id'] == avatar_id), None)
        if not avatar:
            return jsonify({'error': 'Avatar not found'}), 400

        user = User(username=avatar['name'], avatar_id=avatar_id)
        db.session.add(user)
        db.session.commit()

        return jsonify({
            'id': user.id,
            'username': user.username,
            'avatar_id': user.avatar_id,
            'avatar': avatar
        }), 201

    users = User.query.all()
    return jsonify([{
        'id': u.id,
        'username': u.username,
        'avatar_id': u.avatar_id,
        'avatar': u.get_avatar()
    } for u in users])

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
    with app.app_context():
        # Check if we should reinitialize the database from scratch
        if os.environ.get('REINIT_DB') == 'true':
            print("⚠️ REINIT_DB is true - dropping all tables and recreating...")
            db.drop_all()
            
        db.create_all()

        # Individual game seeding for robustness
        def get_or_create_game(name, display_name, description, template_code):
            game = Game.query.filter_by(name=name).first()
            if not game:
                game = Game(
                    name=name,
                    display_name=display_name,
                    description=description,
                    template_code=template_code
                )
                db.session.add(game)
                db.session.commit()
                print(f"✅ Seeded game: {display_name}")
            else:
                # Update template if it has changed in app.py
                if game.template_code != template_code:
                    game.template_code = template_code
                    game.display_name = display_name
                    game.description = description
                    db.session.commit()
                    print(f"🔄 Updated template for: {display_name}")
            return game

        # Helper to add mission if missing
        def get_or_create_mission(game_id, title, order, data):
            mission = Mission.query.filter_by(game_id=game_id, title=title).first()
            if not mission:
                mission = Mission(game_id=game_id, title=title, order=order, **data)
                db.session.add(mission)
                db.session.commit()
                print(f"✅ Seeded mission: {title}")
            return mission

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
        self.x = 10
        self.y = 10
        self.segments = [(10, 10), (9, 10), (8, 10)]
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

    # Move snake based on its speed
    frame_count += 1
    # Higher speed = fewer frames between moves
    move_delay = max(1, 10 - snake.speed) 
    if frame_count % move_delay != 0:
        return

    # Handle keyboard input
    if is_key_pressed("ArrowRight") and snake.direction != "left":
        snake.direction = "right"
    elif is_key_pressed("ArrowLeft") and snake.direction != "right":
        snake.direction = "left"
    elif is_key_pressed("ArrowUp") and snake.direction != "down":
        snake.direction = "up"
    elif is_key_pressed("ArrowDown") and snake.direction != "up":
        snake.direction = "down"

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

# TODO: Try changing the speed variable in the Snake class
# TODO: Try changing the colors of the snake or food
# TODO: Can you make the snake start even longer?
'''

        snake = get_or_create_game(
            name='snake',
            display_name='Snake Game',
            description='Classic snake game - eat food and grow!',
            template_code=snake_template
        )

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

        pong = get_or_create_game(
            name='pong',
            display_name='Pong (2-Player)',
            description='Classic 2-player Pong! First to 5 points wins.',
            template_code=pong_template
        )

        # 3. Space Invaders
        space_invaders_template = '''# Space Invaders
# Arrow keys to move, SPACE to shoot!
# Destroy all aliens before they reach the bottom!
# Watch out for alien bombs!

from js import clear_screen, draw_rect, draw_text, document
import random

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
        self.invincible = 0  # Brief invincibility after being hit

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

class AlienBomb:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 6
        self.height = 10
        self.speed = 4
        self.active = True

    def move(self):
        self.y += self.speed
        if self.y > CANVAS_HEIGHT:
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

# List to hold bullets and alien bombs
bullets = []
alien_bombs = []

# Alien movement
alien_direction = 1  # 1 = right, -1 = left
alien_speed = 1
frame_count = 0

# Bomb drop settings
bomb_drop_chance = 0.001  # Chance per alive alien per frame

# Game state
score = 0
game_over = False
game_won = False
game_started = False

def check_collision(a, b):
    """Check if two rectangles overlap"""
    return (a.x < b.x + b.width and
            a.x + a.width > b.x and
            a.y < b.y + b.height and
            a.y + a.height > b.y)

def check_bomb_hit_player(bomb, p):
    """Check if a bomb hits the player"""
    return (bomb.x < p.x + p.width and
            bomb.x + bomb.width > p.x and
            bomb.y < p.y + p.height and
            bomb.y + bomb.height > p.y)

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

    # Handle invincibility timer
    if player.invincible > 0:
        player.invincible -= 1

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

    # Move alien bombs
    for bomb in alien_bombs:
        bomb.move()

    # Remove inactive bombs
    alien_bombs[:] = [b for b in alien_bombs if b.active]

    # Aliens randomly drop bombs
    alive_aliens = [a for a in aliens if a.alive]
    for alien in alive_aliens:
        if random.random() < bomb_drop_chance:
            alien_bombs.append(AlienBomb(alien.x + alien.width // 2 - 3, alien.y + alien.height))

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

    # Check alien bombs hitting player
    if player.invincible == 0:
        for bomb in alien_bombs:
            if bomb.active and check_bomb_hit_player(bomb, player):
                bomb.active = False
                player.lives -= 1
                player.invincible = 60  # ~1 second of invincibility
                if player.lives <= 0:
                    game_over = True
                    return

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

    # Draw player ship (blink when invincible)
    if player.invincible == 0 or frame_count % 4 < 2:
        px, py = player.x, player.y
        # Ship body
        draw_rect(px + 4, py + 10, 32, 20, "#44ff44")
        # Ship nose/cannon
        draw_rect(px + 16, py, 8, 14, "#66ff66")
        # Ship wings
        draw_rect(px, py + 18, 8, 12, "#33cc33")
        draw_rect(px + 32, py + 18, 8, 12, "#33cc33")
        # Cockpit
        draw_rect(px + 16, py + 14, 8, 6, "#aaffaa")
        # Engine glow
        draw_rect(px + 12, py + 28, 4, 4, "#ffaa00")
        draw_rect(px + 24, py + 28, 4, 4, "#ffaa00")

    # Draw aliens as pixel-art sprites
    for alien in aliens:
        if alien.alive:
            colors = ["#ff4444", "#ff8844", "#ffcc44", "#88ff44", "#4488ff"]
            row = int((alien.y - 50) / 40)
            color = colors[min(row, 4)]
            ax, ay = alien.x, alien.y
            s = 5  # pixel size for sprite

            if row % 3 == 0:
                # Type A: Classic space invader (squid-like)
                draw_rect(ax + s*2, ay, s, s, color)
                draw_rect(ax + s*3, ay, s, s, color)
                draw_rect(ax + s, ay + s, s*4, s, color)
                draw_rect(ax, ay + s*2, s*6, s, color)
                draw_rect(ax, ay + s*3, s, s, color)
                draw_rect(ax + s*2, ay + s*3, s*2, s, color)
                draw_rect(ax + s*5, ay + s*3, s, s, color)
                draw_rect(ax + s, ay + s*4, s, s, color)
                draw_rect(ax + s*4, ay + s*4, s, s, color)
            elif row % 3 == 1:
                # Type B: Crab-like alien
                draw_rect(ax + s*2, ay, s*2, s, color)
                draw_rect(ax + s, ay + s, s*4, s, color)
                draw_rect(ax, ay + s*2, s*6, s, color)
                draw_rect(ax, ay + s*3, s*2, s, color)
                draw_rect(ax + s*4, ay + s*3, s*2, s, color)
                draw_rect(ax + s, ay + s*4, s, s, color)
                draw_rect(ax + s*4, ay + s*4, s, s, color)
            else:
                # Type C: Octopus-like alien
                draw_rect(ax + s, ay, s*4, s, color)
                draw_rect(ax, ay + s, s*6, s, color)
                draw_rect(ax, ay + s*2, s*6, s, color)
                draw_rect(ax + s, ay + s*3, s, s, color)
                draw_rect(ax + s*4, ay + s*3, s, s, color)
                draw_rect(ax, ay + s*4, s*2, s, color)
                draw_rect(ax + s*4, ay + s*4, s*2, s, color)

            # Eyes (dark pixels) for all types
            draw_rect(ax + s, ay + s*2, s, s, "#000000")
            draw_rect(ax + s*4, ay + s*2, s, s, "#000000")

    # Draw bullets
    for bullet in bullets:
        if bullet.active:
            draw_rect(bullet.x, bullet.y, bullet.width, bullet.height, "#ffffff")

    # Draw alien bombs (lightning bolt style)
    for bomb in alien_bombs:
        if bomb.active:
            bx, by = bomb.x, bomb.y
            draw_rect(bx + 2, by, 4, 3, "#ff3333")
            draw_rect(bx, by + 3, 4, 3, "#ff5555")
            draw_rect(bx + 2, by + 6, 4, 4, "#ff3333")

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
        if player.lives <= 0:
            draw_text("You were destroyed!", 190, CANVAS_HEIGHT // 2 + 60, "#ffffff", "24px Arial")
        else:
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

        space_invaders = get_or_create_game(
            name='space_invaders',
            display_name='Space Invaders',
            description='Shoot the aliens before they reach Earth!',
            template_code=space_invaders_template
        )

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

        maze = get_or_create_game(
            name='maze',
            display_name='Maze Adventure',
            description='Navigate the maze and find the exit!',
            template_code=maze_template
        )

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

        tetris = get_or_create_game(
            name='tetris',
            display_name='Tetris',
            description='Stack blocks and clear lines! Classic puzzle game.',
            template_code=tetris_template
        )

        # Snake Mission 1: Change speed
        get_or_create_mission(snake.id, "Change the Snake's Speed", 1, {
            'description': "Find the `speed` variable (around line 19) and change it to a different number. Try 3 for slow, 10 for fast, or 20 for super fast! What feels best to you?",
            'difficulty': "beginner",
            'validation_type': "variable_changed",
            'validation_data': json.dumps({
                'variable': 'speed',
                'old_value': '5',
                'new_value_pattern': r'\d+',
                'success_message': 'Awesome! You changed the speed. Try running the game to see how it feels!',
                'failure_message': 'Find the speed variable and change it to a different number.'
            }),
            'hints': json.dumps([
                "Look for a line that says 'speed = 5'",
                "Try changing 5 to 10 to make the snake faster",
                "Numbers like 3, 8, 15, or 20 all work - pick what's fun!"
            ])
        })

        # Snake Mission 2: Change grid size
        get_or_create_mission(snake.id, "Make the Grid Cells Bigger or Smaller", 2, {
            'description': "Find `GRID_SIZE = 20` (around line 9) and change it. Try 15 for bigger cells or 25 for smaller cells! The game board stays the same size, but the grid changes.",
            'difficulty': "beginner",
            'validation_type': "variable_changed",
            'validation_data': json.dumps({
                'variable': 'GRID_SIZE',
                'old_value': '20',
                'new_value_pattern': r'\d+',
                'success_message': 'Perfect! You changed the grid size. The cells are now bigger or smaller!',
                'failure_message': 'Look for GRID_SIZE and change it from 20 to another number.'
            }),
            'hints': json.dumps([
                "GRID_SIZE controls how many cells fit in the game board",
                "Smaller numbers = bigger cells (fewer cells fit), larger numbers = smaller cells (more cells fit)",
                "Try 15, 25, or 30 and see what you like!"
            ])
        })

        # Snake Mission 3: Make snake longer at start
        get_or_create_mission(snake.id, "Start with a Longer Snake", 3, {
            'description': "Find where the snake's segments list is created and add more segments. Make your snake start with 5 segments instead of 3!",
            'difficulty': "intermediate",
            'validation_type': "code_pattern",
            'validation_data': json.dumps({
                'pattern': r'self\.segments\s*=\s*\[[^\]]*,\s*[^\]]*,\s*[^\]]*,\s*[^\]]*,',
                'success_message': 'Excellent! Your snake now starts longer. That makes the game harder!',
                'failure_message': 'Add more coordinate tuples to the segments list. Each one is like (x, y).'
            }),
            'hints': json.dumps([
                "Look for self.segments = [(10,10), (9,10), (8,10)]",
                "Add more tuples like (7,10), (6,10) to make it longer",
                "Each tuple represents one segment of the snake"
            ])
        })

        # Snake Mission 4: Add score tracking
        get_or_create_mission(snake.id, "Add a Score Variable", 4, {
            'description': "Add a new variable called 'score' to track points. Initialize it to 0 in the __init__ method, then increase it by 10 each time the snake eats food!",
            'difficulty': "intermediate",
            'validation_type': "code_contains",
            'validation_data': json.dumps({
                'text': 'self.score',
                'success_message': 'Great job! You added score tracking. Now players can see their progress!',
                'failure_message': 'Add "self.score = 0" in the Snake __init__ method.'
            }),
            'hints': json.dumps([
                "In the __init__ method, add: self.score = 0",
                "In the grow() method, add: self.score += 10",
                "You can display the score using draw_text in the draw() function"
            ])
        })

        # Snake Mission 5: Add Your Own Creative Feature
        get_or_create_mission(snake.id, "Add Your Own Creative Feature", 5, {
            'description': "Now it's your turn to be creative! Add at least 5 new lines of code that do something interesting. Ideas: change colors, add obstacles, make the snake rainbow, or anything you can imagine!",
            'difficulty': "advanced",
            'validation_type': "line_count_increased",
            'validation_data': json.dumps({
                'min_increase': 5,
                'success_message': 'Amazing! You added your own creative code. You\'re becoming a real game developer!',
                'failure_message': 'Add at least 5 more lines of code to create something new and interesting.'
            }),
            'hints': json.dumps([
                "Change the snake color! In the draw() function, find '#44ff44' and '#33cc33' and try '#ff00ff' (purple) or '#00ffff' (cyan)",
                "Add a 'Game Over' restart! In the update() function where game_over is checked, add: if is_key_pressed('r'): then reset snake, food, score, and game_over",
                "Make a rainbow snake! In the draw loop, change the color line to: color = f'hsl({i * 30}, 100%, 50%)' so each segment is a different color",
                "Show a lives counter! Add self.lives = 3 in Snake __init__, then in check_collision() subtract a life instead of ending the game",
                "Add a speed boost! After the snake eats food, add: snake.speed = min(snake.speed + 1, 15) to get faster as your score goes up",
                "Make bigger food worth more! Add self.size = random.choice([1, 2]) to Food.__init__ and give 20 points for size 2 food",
                "Add a border! In draw(), add: draw_rect(0, 0, CANVAS_WIDTH, 2, '#ffff00') for each edge to show the walls"
            ])
        })

        # --- Pong Missions ---
        # Pong Mission 1: Change paddle speed
        get_or_create_mission(pong.id, "Change the Paddle Speed", 1, {
            'description': "Find the `speed` variable in the `Paddle` class (around line 19) and change it. Try 12 for faster paddles or 5 for a real challenge!",
            'difficulty': "beginner",
            'validation_type': "variable_changed",
            'validation_data': json.dumps({
                'variable': 'speed',
                'old_value': '8',
                'new_value_pattern': r'\d+',
                'success_message': 'Great! You changed the paddle speed. It should feel different now!',
                'failure_message': 'Find the speed variable in the Paddle class and change it to another number.'
            }),
            'hints': json.dumps([
                "Look for 'self.speed = 8' inside the Paddle __init__ method",
                "A higher number makes the paddle move faster",
                "Try a number like 12 or 15!"
            ])
        })

        # Pong Mission 2: Change winning score
        get_or_create_mission(pong.id, "Change the Winning Score", 2, {
            'description': "Find `WINNING_SCORE = 5` (around line 11) and change it to something else, like 10 or 3. How long do you want the game to last?",
            'difficulty': "beginner",
            'validation_type': "variable_changed",
            'validation_data': json.dumps({
                'variable': 'WINNING_SCORE',
                'old_value': '5',
                'new_value_pattern': r'\d+',
                'success_message': 'Excellent! You updated the rules of the game.',
                'failure_message': 'Look for WINNING_SCORE and change it to a different number.'
            }),
            'hints': json.dumps([
                "WINNING_SCORE is near the top of the file",
                "Change it to 10 for a longer game or 3 for a quick one!"
            ])
        })

        # Pong Mission 3: Make the ball bigger
        get_or_create_mission(pong.id, "Make the Ball Bigger", 3, {
            'description': "Find where the ball's `radius` is set in the `reset` method (around line 59) and change it. Try 15 or 20!",
            'difficulty': "beginner",
            'validation_type': "variable_changed",
            'validation_data': json.dumps({
                'variable': 'radius',
                'old_value': '8',
                'new_value_pattern': r'\d+',
                'success_message': 'Whoa! That\'s a big ball! Much easier to hit now.',
                'failure_message': 'Find "self.radius = 8" and change 8 to a larger number.'
            }),
            'hints': json.dumps([
                "Look for 'self.radius = 8' inside the Ball.reset() method",
                "A larger radius makes the ball look and act bigger"
            ])
        })

        # Pong Mission 4: Resize the paddles
        get_or_create_mission(pong.id, "Resize the Paddles", 4, {
            'description': "Find the `height` of the paddles (around line 18) and change it. Make them 120 pixels high to make it easier to block the ball!",
            'difficulty': "intermediate",
            'validation_type': "variable_changed",
            'validation_data': json.dumps({
                'variable': 'height',
                'old_value': '80',
                'new_value_pattern': r'\d+',
                'success_message': 'Paddles resized! They look like shields now.',
                'failure_message': 'Change "self.height = 80" to a different number in the Paddle class.'
            }),
            'hints': json.dumps([
                "Look for 'self.height = 80' in the Paddle __init__ method",
                "Try 120 for tall paddles or 40 for tiny paddles!"
            ])
        })

        # Pong Mission 5: Advanced Creative Feature
        get_or_create_mission(pong.id, "Add Your Own Creative Feature", 5, {
            'description': "Add your own creative touch to Pong! Add 5+ lines of code to make something new happened. Maybe change the colors when someone scores?",
            'difficulty': "advanced",
            'validation_type': "line_count_increased",
            'validation_data': json.dumps({
                'min_increase': 5,
                'success_message': 'Superb! You\'ve made Pong your own.',
                'failure_message': 'Add at least 5 more lines of code to create something unique.'
            }),
            'hints': json.dumps([
                "Try changing the background color in the draw() function",
                "Add a special effect when the ball hits a paddle",
                "Change the ball's color over time",
                "Add a third paddle in the middle!"
            ])
        })

        # --- Space Invaders Missions ---
        # Space Invaders Mission 1: Make the ship faster
        get_or_create_mission(space_invaders.id, "Make the Ship Faster", 1, {
            'description': "Find the `speed` variable in the `Player` class (around line 31) and increase it to 12. Zip across the screen!",
            'difficulty': "beginner",
            'validation_type': "variable_changed",
            'validation_data': json.dumps({
                'variable': 'speed',
                'old_value': '7',
                'new_value_pattern': r'\d+',
                'success_message': 'Speed boost activated! You can now outrun those aliens.',
                'failure_message': 'Find "self.speed = 7" in the Player class and change it.'
            }),
            'hints': json.dumps([
                "Look for 'self.speed = 7' inside Player.__init__",
                "A higher number makes the ship move faster"
            ])
        })

        # Space Invaders Mission 2: Make the aliens faster
        get_or_create_mission(space_invaders.id, "Make the Aliens Faster", 2, {
            'description': "Find `alien_speed = 1` (around line 86) and change it to 3. They're coming for Earth!",
            'difficulty': "beginner",
            'validation_type': "variable_changed",
            'validation_data': json.dumps({
                'variable': 'alien_speed',
                'old_value': '1',
                'new_value_pattern': r'\d+',
                'success_message': 'Oh no! The aliens have upgraded their engines!',
                'failure_message': 'Change alien_speed from 1 to another number.'
            }),
            'hints': json.dumps([
                "alien_speed is a global variable around line 86",
                "Try 2 or 3 for a real challenge!"
            ])
        })

        # Space Invaders Mission 3: Add more alien rows
        get_or_create_mission(space_invaders.id, "Add More Alien Rows", 3, {
            'description': "Find the loop that creates the aliens (around line 75) and change `range(5)` to `range(7)`. More aliens to defeat!",
            'difficulty': "intermediate",
            'validation_type': "code_contains",
            'validation_data': json.dumps({
                'text': 'range(7)',
                'success_message': 'An entire armada of aliens! Can you stop them all?',
                'failure_message': 'Change range(5) to range(7) in the alien creation loop.'
            }),
            'hints': json.dumps([
                "Look for 'for row in range(5):' near line 75",
                "Changing 5 to 7 adds two more rows of aliens"
            ])
        })

        # Space Invaders Mission 4: Increase starting lives
        get_or_create_mission(space_invaders.id, "Increase Starting Lives", 4, {
            'description': "Find where `self.lives` is set in the `Player` (around line 32) and change it to 5. Give yourself a little more breathing room!",
            'difficulty': "beginner",
            'validation_type': "variable_changed",
            'validation_data': json.dumps({
                'variable': 'lives',
                'old_value': '3',
                'new_value_pattern': r'\d+',
                'success_message': 'Extra lives! Use them wisely to save the planet.',
                'failure_message': 'Find "self.lives = 3" and change 3 to 5.'
            }),
            'hints': json.dumps([
                "Look for 'self.lives = 3' in the Player class",
                "More lives mean you can get hit more times before Game Over"
            ])
        })

        # Space Invaders Mission 5: Advanced Creative Feature
        get_or_create_mission(space_invaders.id, "Add Your Own Creative Feature", 5, {
            'description': "Add 5+ lines of code to create something unique. Maybe change the color of the bullets or make the player flash when they shoot!",
            'difficulty': "advanced",
            'validation_type': "line_count_increased",
            'validation_data': json.dumps({
                'min_increase': 5,
                'success_message': 'Incredible! Earth is safe thanks to your coding skills.',
                'failure_message': 'Add at least 5 more lines of code to create something interesting.'
            }),
            'hints': json.dumps([
                "Change the player color to something like '#ff00ff'",
                "Add a special effect when an alien is destroyed",
                "Make the aliens change color as they get lower",
                "Add a second type of bullet!"
            ])
        })

        # --- Maze Missions ---
        # Maze Mission 1: Change movement delay
        get_or_create_mission(maze.id, "Make the Player Move Faster", 1, {
            'description': "Find the line `if frame_count % 8 != 0:` (around line 81) and change 8 to 4. Your player will react much quicker!",
            'difficulty': "beginner",
            'validation_type': "code_contains",
            'validation_data': json.dumps({
                'text': '% 4 != 0',
                'success_message': 'Zoom! Your player is much more responsive now.',
                'failure_message': 'Change the number 8 to 4 in the movement delay line.'
            }),
            'hints': json.dumps([
                "The number after % controls how many frames to wait between moves",
                "A smaller number means less waiting and faster movement!"
            ])
        })

        # Maze Mission 2: Change the exit color
        get_or_create_mission(maze.id, "Change the Exit Color", 2, {
            'description': "Find where the exit is drawn in the `draw()` function (around line 135) and change the color from `\"#44ff44\"` to `\"#ff00ff\"` (magenta).",
            'difficulty': "beginner",
            'validation_type': "code_contains",
            'validation_data': json.dumps({
                'text': '"#ff00ff"',
                'success_message': 'The exit is now a bright magenta! Hard to miss!',
                'failure_message': 'Find the color "#44ff44" and change it to "#ff00ff".'
            }),
            'hints': json.dumps([
                "Look for draw_rect(cell_x, cell_y, CELL_SIZE, CELL_SIZE, \"#44ff44\")",
                "Changing the hex color code changes the color on screen"
            ])
        })

        # Maze Mission 3: Add a secret treasure
        get_or_create_mission(maze.id, "Add a Secret Treasure", 3, {
            'description': "Add another treasure to the maze! Find the `maze.grid` (around line 40) and change one of the `0`s to a `3`.",
            'difficulty': "intermediate",
            'validation_type': "code_pattern",
            'validation_data': json.dumps({
                'pattern': r'3.*3',
                'success_message': 'More gold for the adventurer! You\'ve hidden a new treasure.',
                'failure_message': 'Change one of the 0s in the grid to a 3 to add a treasure.'
            }),
            'hints': json.dumps([
                "Look for the maze.grid definition with lots of 0s and 1s",
                "0 is a path, 1 is a wall, and 3 is a treasure",
                "Put a 3 anywhere there is currently a 0!"
            ])
        })

        # Maze Mission 4: Change player color
        get_or_create_mission(maze.id, "Customize Your Player", 4, {
            'description': "Find where the player is drawn (around line 144) and change the color `\"#4444ff\"` to your favorite color!",
            'difficulty': "beginner",
            'validation_type': "variable_changed",
            'validation_data': json.dumps({
                'variable': 'color',
                'old_value': '"#4444ff"',
                'new_value_pattern': r'["\'#]\w+',
                'success_message': 'Looking sharp! Your player has a new style.',
                'failure_message': 'Find the color "#4444ff" and change it to something else.'
            }),
            'hints': json.dumps([
                "Look for the draw_rect line that uses \"#4444ff\"",
                "You can use color names like \"red\", \"green\", or hex codes like \"#f0f0f0\""
            ])
        })

        # Maze Mission 5: Advanced Creative Feature
        get_or_create_mission(maze.id, "Add Your Own Creative Feature", 5, {
            'description': "Add 5+ lines of code to the Maze game. Maybe add a timer, a move counter, or even a second floor!",
            'difficulty': "advanced",
            'validation_type': "line_count_increased",
            'validation_data': json.dumps({
                'min_increase': 5,
                'success_message': 'You solved the maze of coding! Well done.',
                'failure_message': 'Add at least 5 more lines of code to create something new.'
            }),
            'hints': json.dumps([
                "Add a 'level' variable that increases when you find the exit",
                "Create a new maze grid for level 2",
                "Add a penalty if the player hits a wall",
                "Display a 'Game Over' message if moves exceed a limit"
            ])
        })

        # --- Tetris Missions ---
        # Tetris Mission 1: Change the drop speed
        get_or_create_mission(tetris.id, "Make the Game Faster", 1, {
            'description': "Find `drop_speed = 30` (around line 125) and change it to 15. The blocks will fall twice as fast!",
            'difficulty': "beginner",
            'validation_type': "variable_changed",
            'validation_data': json.dumps({
                'variable': 'drop_speed',
                'old_value': '30',
                'new_value_pattern': r'\d+',
                'success_message': 'Lightning fast! Can you keep up?',
                'failure_message': 'Find drop_speed and change it to a smaller number.'
            }),
            'hints': json.dumps([
                "A smaller drop_speed means fewer frames between drops",
                "Try 20 or 15 for a good challenge"
            ])
        })

        # Tetris Mission 2: Change the block size
        get_or_create_mission(tetris.id, "Change the Block Size", 2, {
            'description': "Find `BLOCK_SIZE = 28` (around line 7) and change it to 20. The board will look very different!",
            'difficulty': "beginner",
            'validation_type': "variable_changed",
            'validation_data': json.dumps({
                'variable': 'BLOCK_SIZE',
                'old_value': '28',
                'new_value_pattern': r'\d+',
                'success_message': 'Mini-Tetris! Everything is smaller now.',
                'failure_message': 'Change BLOCK_SIZE to a different number.'
            }),
            'hints': json.dumps([
                "BLOCK_SIZE is near the top of the file",
                "If you make blocks smaller, everything will shrink to the top-left"
            ])
        })

        # Tetris Mission 3: Make it score more points
        get_or_create_mission(tetris.id, "Award More Points", 3, {
            'description': "Find the `scores` list in `clear_full_lines` (around line 97) and double all the values! Who doesn't love a high score?",
            'difficulty': "intermediate",
            'validation_type': "code_pattern",
            'validation_data': json.dumps({
                'pattern': r'\[0,\s*200,\s*600,\s*1000,\s*1600\]',
                'success_message': 'Double points! You\'re going to be a Tetris grandmaster in no time.',
                'failure_message': 'Update the scores list to double the points for line clears.'
            }),
            'hints': json.dumps([
                "Look for 'scores = [0, 100, 300, 500, 800]'",
                "Change them to [0, 200, 600, 1000, 1600]"
            ])
        })

        # Tetris Mission 4: Change the background color
        get_or_create_mission(tetris.id, "Style the Game Board", 4, {
            'description': "Find where the background is drawn (around line 236) and change `\"#1a1a1a\"` to `\"#000033\"` (dark blue).",
            'difficulty': "beginner",
            'validation_type': "code_contains",
            'validation_data': json.dumps({
                'text': '"#000033"',
                'success_message': 'A deep space blue background! Looks great.',
                'failure_message': 'Change the background color from "#1a1a1a" to "#000033".'
            }),
            'hints': json.dumps([
                "Look for draw_rect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT, \"#1a1a1a\")",
                "You can use any hex color you like!"
            ])
        })

        # Tetris Mission 5: Advanced Creative Feature
        get_or_create_mission(tetris.id, "Add Your Own Creative Feature", 5, {
            'description': "Add 5+ lines of code to Tetris. Maybe add a 'hold' feature, different colors for levels, or a combo system!",
            'difficulty': "advanced",
            'validation_type': "line_count_increased",
            'validation_data': json.dumps({
                'min_increase': 5,
                'success_message': 'A masterpiece! You\'ve truly mastered the game of Tetris.',
                'failure_message': 'Add at least 5 more lines of code to the game.'
            }),
            'hints': json.dumps([
                "Add a level variable that increases every 5 lines",
                "Change the color palette as levels increase",
                "Add a special effect when a Tetris (4 lines) is cleared",
                "Keep track of the time played"
            ])
        })

        # 6. Minecraft Game
        minecraft_template = '''# Minecraft 2D
# Use WASD to move, arrow keys to place/break blocks
# Arrow Up/Down/Left/Right aim the cursor, SPACE to place, E to break
# Number keys 1-4 to select block type

from js import clear_screen, draw_rect, draw_circle, draw_text, is_key_pressed
import random

# Game settings
CANVAS_WIDTH = 600
CANVAS_HEIGHT = 700
BLOCK_SIZE = 25
GRID_W = CANVAS_WIDTH // BLOCK_SIZE   # 24 columns
GRID_H = CANVAS_HEIGHT // BLOCK_SIZE  # 28 rows
GRAVITY_SPEED = 4  # Frames between gravity ticks

# Block types: id -> (name, color, breakable)
BLOCK_TYPES = {
    0: ("Air", "#87CEEB", False),       # Sky background
    1: ("Grass", "#4CAF50", True),
    2: ("Dirt", "#8B4513", True),
    3: ("Stone", "#808080", True),
    4: ("Wood", "#A0522D", True),
    5: ("Leaves", "#228B22", True),
    6: ("Sand", "#F4D03F", True),
    7: ("Water", "#2196F3", False),
    8: ("Bedrock", "#333333", False),
    9: ("Coal", "#1a1a1a", True),
    10: ("Gold", "#FFD700", True),
}

class Player:
    def __init__(self):
        self.x = GRID_W // 2
        self.y = 0
        self.width = 1
        self.height = 2  # Player is 2 blocks tall
        self.vy = 0
        self.on_ground = False
        self.color = "#FF6347"
        self.head_color = "#FFDAB9"
        self.speed = 1
        self.health = 10
        self.selected_block = 1  # Currently selected block type
        self.inventory = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 9: 0, 10: 0}
        # Cursor offset from player for placing/breaking
        self.cursor_dx = 1
        self.cursor_dy = 0

    def get_cursor_targets(self):
        """Get list of world positions the cursor targets for mining/placing.
        Returns a list of (x, y) tuples, ordered by priority."""
        targets = []
        if self.cursor_dy < 0:
            # Aiming up: block above head
            targets.append((self.x, self.y - 1))
        elif self.cursor_dy > 0:
            # Aiming down: block below feet
            targets.append((self.x, self.y + self.height))
        else:
            # Aiming sideways: head level then feet level
            nx = self.x + self.cursor_dx
            targets.append((nx, self.y))      # Head level
            targets.append((nx, self.y + 1))  # Feet level
        return targets

    def get_cursor_pos(self):
        """Get primary cursor position for display"""
        targets = self.get_cursor_targets()
        return targets[0] if targets else (self.x, self.y)

class World:
    def __init__(self):
        self.grid = [[0] * GRID_W for _ in range(GRID_H)]
        self.generate_terrain()

    def generate_terrain(self):
        """Create a procedural terrain with hills and caves"""
        # Generate height map with gentle hills
        heights = []
        h = GRID_H // 2
        for x in range(GRID_W):
            h += random.choice([-1, 0, 0, 0, 1])
            h = max(GRID_H // 3, min(GRID_H - 6, h))
            heights.append(h)

        # Fill terrain layers
        for x in range(GRID_W):
            surface = heights[x]
            for y in range(GRID_H):
                if y == GRID_H - 1:
                    self.grid[y][x] = 8  # Bedrock at bottom
                elif y == surface:
                    self.grid[y][x] = 1  # Grass on top
                elif y > surface and y < surface + 4:
                    self.grid[y][x] = 2  # Dirt layer
                elif y >= surface + 4:
                    self.grid[y][x] = 3  # Stone below
                else:
                    self.grid[y][x] = 0  # Air above

        # Scatter ores in stone
        for y in range(GRID_H):
            for x in range(GRID_W):
                if self.grid[y][x] == 3:
                    r = random.random()
                    if r < 0.03:
                        self.grid[y][x] = 10  # Gold (rare)
                    elif r < 0.08:
                        self.grid[y][x] = 9   # Coal

        # Add a few trees on the surface
        for x in range(2, GRID_W - 2, random.randint(4, 7)):
            surface = heights[x] if x < len(heights) else GRID_H // 2
            if self.grid[surface][x] == 1:  # Only on grass
                # Trunk (3 blocks tall)
                for ty in range(1, 4):
                    if surface - ty >= 0:
                        self.grid[surface - ty][x] = 4
                # Leaves (simple cross pattern)
                for lx in range(-1, 2):
                    for ly in range(-1, 2):
                        tx = x + lx
                        ty2 = surface - 4 + ly
                        if 0 <= tx < GRID_W and 0 <= ty2 < GRID_H:
                            if self.grid[ty2][tx] == 0:
                                self.grid[ty2][tx] = 5
                # Top leaf
                if surface - 5 >= 0 and self.grid[surface - 5][x] == 0:
                    self.grid[surface - 5][x] = 5

        # Add a small pond
        pond_x = random.randint(4, GRID_W - 6)
        pond_surface = heights[min(pond_x, len(heights) - 1)]
        for px in range(pond_x, min(pond_x + 4, GRID_W)):
            if 0 <= pond_surface < GRID_H:
                self.grid[pond_surface][px] = 7  # Water
                if pond_surface + 1 < GRID_H:
                    self.grid[pond_surface + 1][px] = 6  # Sand under water

    def get_block(self, x, y):
        if 0 <= x < GRID_W and 0 <= y < GRID_H:
            return self.grid[y][x]
        return 0

    def set_block(self, x, y, block_id):
        if 0 <= x < GRID_W and 0 <= y < GRID_H:
            self.grid[y][x] = block_id

    def is_solid(self, x, y):
        block = self.get_block(x, y)
        return block != 0 and block != 7  # Air and water are not solid

# Create world and player
world = World()
player = Player()

# Place player on top of terrain
for y in range(GRID_H):
    if world.is_solid(player.x, y):
        player.y = y - 2  # Stand on top
        break

# Game state
game_over = False
game_started = False
frame_count = 0
gravity_timer = 0
move_delay = 0
last_move_key = None
message = ""
message_timer = 0
score = 0

def show_message(msg, duration=90):
    global message, message_timer
    message = msg
    message_timer = duration

def update():
    """Update game logic"""
    global game_over, game_started, frame_count, gravity_timer
    global move_delay, last_move_key, message_timer, score

    frame_count += 1

    if not game_started:
        if is_key_pressed(' '):
            game_started = True
        return

    if game_over:
        if is_key_pressed(' '):
            # Restart
            game_over = False
            world.__init__()
            player.__init__()
            for y in range(GRID_H):
                if world.is_solid(player.x, y):
                    player.y = y - 2
                    break
            score = 0
            show_message("New world generated!", 60)
        return

    if message_timer > 0:
        message_timer -= 1

    # Movement with delay for responsiveness
    moved = False

    if is_key_pressed('a') or is_key_pressed('A'):
        if last_move_key != 'a' or move_delay <= 0:
            nx = player.x - 1
            # Check both blocks of the player (head and body)
            if not world.is_solid(nx, player.y) and not world.is_solid(nx, player.y + 1):
                player.x = nx
                moved = True
            move_delay = 4
            last_move_key = 'a'
    elif is_key_pressed('d') or is_key_pressed('D'):
        if last_move_key != 'd' or move_delay <= 0:
            nx = player.x + 1
            if not world.is_solid(nx, player.y) and not world.is_solid(nx, player.y + 1):
                player.x = nx
                moved = True
            move_delay = 4
            last_move_key = 'd'
    elif is_key_pressed('w') or is_key_pressed('W'):
        if last_move_key != 'w' or move_delay <= 0:
            # Jump: only if on ground
            if player.on_ground:
                player.vy = -2
                player.on_ground = False
            move_delay = 6
            last_move_key = 'w'
    else:
        last_move_key = None

    if move_delay > 0:
        move_delay -= 1

    # Cursor movement with arrow keys
    if is_key_pressed('ArrowLeft'):
        player.cursor_dx = -1
        player.cursor_dy = 0
    elif is_key_pressed('ArrowRight'):
        player.cursor_dx = 1
        player.cursor_dy = 0
    elif is_key_pressed('ArrowUp'):
        player.cursor_dx = 0
        player.cursor_dy = -1
    elif is_key_pressed('ArrowDown'):
        player.cursor_dx = 0
        player.cursor_dy = 1

    # Block selection with number keys
    if is_key_pressed('1'):
        player.selected_block = 1
    elif is_key_pressed('2'):
        player.selected_block = 2
    elif is_key_pressed('3'):
        player.selected_block = 3
    elif is_key_pressed('4'):
        player.selected_block = 4

    # Place block with SPACE - tries each cursor target in priority order
    if is_key_pressed(' ') and frame_count % 10 == 0:
        for cx, cy in player.get_cursor_targets():
            if 0 <= cx < GRID_W and 0 <= cy < GRID_H:
                if world.get_block(cx, cy) == 0:
                    sel = player.selected_block
                    if player.inventory.get(sel, 0) > 0:
                        world.set_block(cx, cy, sel)
                        player.inventory[sel] -= 1
                        show_message(f"Placed {BLOCK_TYPES[sel][0]}", 40)
                        break  # Only place one block per press

    # Break block with E - tries each cursor target in priority order
    if is_key_pressed('e') or is_key_pressed('E'):
        if frame_count % 10 == 0:
            for cx, cy in player.get_cursor_targets():
                if 0 <= cx < GRID_W and 0 <= cy < GRID_H:
                    block = world.get_block(cx, cy)
                    if block > 0 and BLOCK_TYPES.get(block, (None, None, False))[2]:
                        world.set_block(cx, cy, 0)
                        if block in player.inventory:
                            player.inventory[block] = player.inventory.get(block, 0) + 1
                        score += 10
                        show_message(f"Mined {BLOCK_TYPES[block][0]}! +10", 40)
                        break  # Only break one block per press

    # Gravity
    gravity_timer += 1
    if gravity_timer >= GRAVITY_SPEED:
        gravity_timer = 0

        if player.vy < 0:
            # Moving up (jumping)
            ny = player.y + player.vy
            if not world.is_solid(player.x, ny):
                player.y = ny
                player.vy += 1
            else:
                # Bonked head - check if we can do a partial jump (1 block)
                if player.vy == -2 and not world.is_solid(player.x, player.y - 1):
                    player.y -= 1
                    player.vy = 0
                else:
                    player.vy = 0
        else:
            # Falling down
            feet_y = player.y + 2  # Below the player
            if world.is_solid(player.x, feet_y):
                player.on_ground = True
                player.vy = 0
            else:
                player.y += 1
                player.on_ground = False

    # Keep player in bounds
    player.x = max(0, min(GRID_W - 1, player.x))
    player.y = max(0, min(GRID_H - 3, player.y))

    # Check health
    if player.health <= 0:
        game_over = True

def draw():
    """Draw the game world"""
    clear_screen()

    if not game_started:
        draw_rect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT, "#1a1a2e")
        draw_text("MINECRAFT 2D", 130, 200, "#4CAF50", "56px Arial")
        draw_text("A Block Building Adventure", 150, 260, "#aaaaaa", "22px Arial")
        draw_text("WASD = Move / Jump", 180, 340, "#cccccc", "20px Arial")
        draw_text("Arrow Keys = Aim Cursor", 165, 370, "#cccccc", "20px Arial")
        draw_text("E = Mine Block  |  SPACE = Place Block", 105, 400, "#cccccc", "20px Arial")
        draw_text("1-4 = Select Block Type", 170, 430, "#cccccc", "20px Arial")
        draw_text("Press SPACE to Start", 175, 510, "#FFD700", "26px Arial")
        return

    # Draw sky gradient (simplified)
    draw_rect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT, "#87CEEB")

    # Draw blocks
    for y in range(GRID_H):
        for x in range(GRID_W):
            block = world.grid[y][x]
            if block != 0:
                color = BLOCK_TYPES.get(block, ("?", "#ff00ff", False))[1]
                bx = x * BLOCK_SIZE
                by = y * BLOCK_SIZE
                draw_rect(bx, by, BLOCK_SIZE, BLOCK_SIZE, color)
                # Block border for depth
                draw_rect(bx, by, BLOCK_SIZE, 1, "#00000033")
                draw_rect(bx, by, 1, BLOCK_SIZE, "#00000033")

    # Draw cursor highlight on all target blocks
    for cx, cy in player.get_cursor_targets():
        if 0 <= cx < GRID_W and 0 <= cy < GRID_H:
            draw_rect(cx * BLOCK_SIZE, cy * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE, "#ffffff44")
            draw_rect(cx * BLOCK_SIZE, cy * BLOCK_SIZE, BLOCK_SIZE, 2, "#ffffff")
            draw_rect(cx * BLOCK_SIZE, cy * BLOCK_SIZE, 2, BLOCK_SIZE, "#ffffff")
            draw_rect(cx * BLOCK_SIZE + BLOCK_SIZE - 2, cy * BLOCK_SIZE, 2, BLOCK_SIZE, "#ffffff")
            draw_rect(cx * BLOCK_SIZE, cy * BLOCK_SIZE + BLOCK_SIZE - 2, BLOCK_SIZE, 2, "#ffffff")

    # Draw player (body)
    px = player.x * BLOCK_SIZE
    py = player.y * BLOCK_SIZE
    # Body
    draw_rect(px + 4, py + BLOCK_SIZE, BLOCK_SIZE - 8, BLOCK_SIZE - 2, player.color)
    # Head
    draw_rect(px + 3, py + 2, BLOCK_SIZE - 6, BLOCK_SIZE - 4, player.head_color)
    # Eyes
    draw_rect(px + 7, py + 8, 3, 3, "#333333")
    draw_rect(px + 15, py + 8, 3, 3, "#333333")

    # Draw HUD background
    draw_rect(0, 0, CANVAS_WIDTH, 36, "#00000088")

    # Draw score
    draw_text(f"Score: {score}", 10, 26, "#ffffff", "18px Arial")

    # Draw health
    draw_text(f"HP: {player.health}", 130, 26, "#ff6666", "18px Arial")

    # Draw selected block indicator
    sel = player.selected_block
    sel_name = BLOCK_TYPES.get(sel, ("?", "#fff", False))[0]
    sel_color = BLOCK_TYPES.get(sel, ("?", "#fff", False))[1]
    draw_rect(240, 8, 20, 20, sel_color)
    draw_text(f"{sel_name}", 265, 26, "#ffffff", "16px Arial")

    # Draw inventory hotbar
    hotbar_x = 380
    hotbar_blocks = [1, 2, 3, 4]
    for i, bid in enumerate(hotbar_blocks):
        bx = hotbar_x + i * 30
        bcolor = BLOCK_TYPES.get(bid, ("?", "#fff", False))[1]
        # Highlight selected
        if bid == player.selected_block:
            draw_rect(bx - 2, 5, 28, 28, "#FFD700")
        draw_rect(bx, 7, 24, 24, bcolor)
        count = player.inventory.get(bid, 0)
        draw_text(str(count), bx + 6, 26, "#ffffff", "12px Arial")
        draw_text(str(i + 1), bx + 8, 6, "#FFD700", "10px Arial")

    # Draw message
    if message_timer > 0 and message:
        draw_text(message, CANVAS_WIDTH // 2 - len(message) * 5, 60, "#FFD700", "20px Arial")

    # Draw game over
    if game_over:
        draw_rect(0, CANVAS_HEIGHT // 2 - 60, CANVAS_WIDTH, 120, "#000000cc")
        draw_text("GAME OVER", 180, CANVAS_HEIGHT // 2 - 10, "#ff4444", "40px Arial")
        draw_text(f"Final Score: {score}", 210, CANVAS_HEIGHT // 2 + 30, "#ffffff", "22px Arial")
        draw_text("Press SPACE to restart", 185, CANVAS_HEIGHT // 2 + 60, "#aaaaaa", "18px Arial")

# TODO: Add crafting system to combine blocks
# TODO: Add day/night cycle with changing sky colors
# TODO: Add more block types like bricks or glass
# TODO: Make mobs that walk around the world
# TODO: Add a hunger system
'''

        minecraft = get_or_create_game(
            name='minecraft',
            display_name='Minecraft 2D',
            description='Mine blocks, build structures, and explore a procedural world!',
            template_code=minecraft_template
        )

        # --- Minecraft Missions ---
        # Minecraft Mission 1: Change gravity speed
        get_or_create_mission(minecraft.id, "Change the Gravity", 1, {
            'description': "Find `GRAVITY_SPEED = 4` (around line 8) and change it. Try 2 for heavy gravity or 8 for moon-like low gravity!",
            'difficulty': "beginner",
            'validation_type': "variable_changed",
            'validation_data': json.dumps({
                'variable': 'GRAVITY_SPEED',
                'old_value': '4',
                'new_value_pattern': r'\d+',
                'success_message': 'The gravity feels totally different now! Try jumping around.',
                'failure_message': 'Find GRAVITY_SPEED and change it from 4 to another number.'
            }),
            'hints': json.dumps([
                "GRAVITY_SPEED is near the top of the file",
                "Smaller numbers = heavier gravity (fall faster)",
                "Larger numbers = lighter gravity (fall slower, like the moon!)"
            ])
        })

        # Minecraft Mission 2: Change player color
        get_or_create_mission(minecraft.id, "Customize Your Character", 2, {
            'description': "Find the player's `color` (around line 38) and change it from `\"#FF6347\"` to any color you like! Try `\"#00BFFF\"` for blue or `\"#FF69B4\"` for pink.",
            'difficulty': "beginner",
            'validation_type': "variable_changed",
            'validation_data': json.dumps({
                'variable': 'color',
                'old_value': '"#FF6347"',
                'new_value_pattern': r'"#[0-9A-Fa-f]+"',
                'success_message': 'Looking stylish! Your character has a new outfit.',
                'failure_message': 'Change self.color to a different hex color like "#00BFFF".'
            }),
            'hints': json.dumps([
                "Look for self.color = \"#FF6347\" in the Player class",
                "Hex colors start with # followed by 6 characters (0-9 and A-F)",
                "Try #00FF00 for green, #FF00FF for purple, or #FFD700 for gold!"
            ])
        })

        # Minecraft Mission 3: Add a new block type
        get_or_create_mission(minecraft.id, "Add a New Block Type", 3, {
            'description': "Add a new block to the BLOCK_TYPES dictionary! Add something like `11: (\"Diamond\", \"#00FFFF\", True),` after the Gold entry around line 28.",
            'difficulty': "intermediate",
            'validation_type': "code_contains",
            'validation_data': json.dumps({
                'text': '11:',
                'success_message': 'A brand new block type! You\'re expanding the world.',
                'failure_message': 'Add a new entry like 11: ("Diamond", "#00FFFF", True) to BLOCK_TYPES.'
            }),
            'hints': json.dumps([
                "BLOCK_TYPES is a dictionary near the top of the file",
                "Each entry has: id: (name, color, breakable)",
                "Add 11: (\"Diamond\", \"#00FFFF\", True), after the Gold line",
                "You can pick any name and color you want!"
            ])
        })

        # Minecraft Mission 4: Change the world generation
        get_or_create_mission(minecraft.id, "Reshape the World", 4, {
            'description': "Find the terrain generation height range. Change `GRID_H // 3` (around line 53) to `GRID_H // 4` to make taller mountains, or `GRID_H // 2` for flatter land!",
            'difficulty': "intermediate",
            'validation_type': "code_pattern",
            'validation_data': json.dumps({
                'pattern': r'max\(GRID_H\s*//\s*[^3]',
                'success_message': 'Wow! The terrain looks completely different now. Every world is unique!',
                'failure_message': 'Change the GRID_H // 3 value in the height clamping to reshape the terrain.'
            }),
            'hints': json.dumps([
                "Look for the line: h = max(GRID_H // 3, min(GRID_H - 6, h))",
                "GRID_H // 3 controls the minimum height of the terrain",
                "A smaller divisor (like 4) allows taller mountains",
                "A larger divisor (like 2) makes the land flatter"
            ])
        })

        # Minecraft Mission 5: Advanced Creative Feature
        get_or_create_mission(minecraft.id, "Add Your Own Creative Feature", 5, {
            'description': "Add 5+ lines of code to make Minecraft 2D your own! Ideas: day/night cycle, new mobs, TNT explosions, a crafting system, or anything you can imagine!",
            'difficulty': "advanced",
            'validation_type': "line_count_increased",
            'validation_data': json.dumps({
                'min_increase': 5,
                'success_message': 'Amazing! You\'ve made Minecraft 2D truly yours. Steve would be proud!',
                'failure_message': 'Add at least 5 more lines of code to create something new and creative.'
            }),
            'hints': json.dumps([
                "Add a day_time variable that increases each frame and changes the sky color",
                "Create a Mob class with simple left/right movement",
                "Add TNT: a block that destroys nearby blocks when broken",
                "Make torches that glow by drawing a yellow circle",
                "Be creative - there are no wrong answers!"
            ])
        })

        print("Database initialization complete.")

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

    # Initialize database before starting server (if not already done)
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        try:
            init_db()
        except Exception as e:
            print(f"⚠️  Database initialization skipped (startup): {e}")

    # Replit optimized: bind to 0.0.0.0 for external access
    port = 5000
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

"""
Pytest configuration and fixtures for Python Game Builder tests
"""
import pytest
import os
import tempfile
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


@pytest.fixture(scope='function')
def app():
    """Create and configure a test Flask application"""
    # Import here to get fresh app for each test
    from app import app as flask_app, db as _db, User, Game, CodeVersion

    # Create a temporary database file
    db_fd, db_path = tempfile.mkstemp()

    flask_app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'WTF_CSRF_ENABLED': False,
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
    })

    # Create database tables
    with flask_app.app_context():
        _db.create_all()

        # Add test game
        snake = Game(
            name='snake_test',
            display_name='Test Snake',
            description='Test game',
            template_code='# Test snake code\nclass Snake:\n    pass'
        )
        _db.session.add(snake)
        _db.session.commit()

    yield flask_app

    # Cleanup
    with flask_app.app_context():
        _db.session.remove()
        _db.drop_all()

    os.close(db_fd)
    try:
        os.unlink(db_path)
    except:
        pass


@pytest.fixture
def client(app):
    """Create a test client"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create a test CLI runner"""
    return app.test_cli_runner()


@pytest.fixture
def test_user(app):
    """Create a test user"""
    from app import db, User

    with app.app_context():
        user = User(username='testuser')
        db.session.add(user)
        db.session.commit()
        user_id = user.id

    return user_id


@pytest.fixture
def test_game(app):
    """Get the test game"""
    from app import db, Game

    with app.app_context():
        game = Game.query.filter_by(name='snake_test').first()
        game_id = game.id

    return game_id


@pytest.fixture
def test_code_version(app, test_user, test_game):
    """Create a test code version"""
    from app import db, CodeVersion

    with app.app_context():
        version = CodeVersion(
            user_id=test_user,
            game_id=test_game,
            code='# Test code\nprint("hello")',
            message='Test save',
            is_checkpoint=True
        )
        db.session.add(version)
        db.session.commit()
        version_id = version.id

    return version_id

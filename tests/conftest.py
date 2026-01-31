"""
Pytest configuration and fixtures for Python Game Builder tests
"""
import pytest
import os
import tempfile
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


@pytest.fixture(scope='function', autouse=False)
def app():
    """Create and configure a test Flask application with isolated database"""
    # Import the actual app and db from app.py
    import app as app_module
    from app import db as _db, Game

    # Create a temporary database file for this test
    db_fd, db_path = tempfile.mkstemp(suffix='.db')

    # Store original database URI
    original_db_uri = app_module.app.config['SQLALCHEMY_DATABASE_URI']

    # Configure the app to use the test database
    app_module.app.config['TESTING'] = True
    app_module.app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app_module.app.config['WTF_CSRF_ENABLED'] = False
    app_module.app.config['SECRET_KEY'] = 'test-secret-key'

    # Push an application context
    ctx = app_module.app.app_context()
    ctx.push()

    # Clean up any existing session
    _db.session.remove()

    # Drop and recreate all tables in the new database
    _db.drop_all()
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

    yield app_module.app

    # Cleanup
    _db.session.remove()
    _db.drop_all()

    # Pop the application context
    ctx.pop()

    # Close and remove the temp database file
    os.close(db_fd)
    try:
        os.unlink(db_path)
    except Exception:
        pass

    # Restore original configuration
    app_module.app.config['SQLALCHEMY_DATABASE_URI'] = original_db_uri


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

    user = User(username='testuser')
    db.session.add(user)
    db.session.commit()
    user_id = user.id

    return user_id


@pytest.fixture
def test_game(app):
    """Get the test game"""
    from app import db, Game

    game = Game.query.filter_by(name='snake_test').first()
    game_id = game.id

    return game_id


@pytest.fixture
def test_code_version(app, test_user, test_game):
    """Create a test code version"""
    from app import db, CodeVersion

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

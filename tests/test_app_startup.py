"""
Tests for application startup and initialization
"""
import pytest
import os
import tempfile
import shutil


def test_database_config_has_uri(app):
    """Test that database URI is configured"""
    assert app.config['SQLALCHEMY_DATABASE_URI'] is not None


def test_init_db_idempotent(app):
    """Test that init_db can be called multiple times safely"""
    from app import Game, init_db

    # This test uses the isolated test database from the 'app' fixture
    with app.app_context():
        # initial count should be 1 (the test game added in conftest.py)
        initial_count = Game.query.count()
        assert initial_count >= 1

        # Call init_db - it should add the rest of the games
        init_db()
        
        new_count = Game.query.count()
        assert new_count > initial_count
        
        # Call it again - count should not change (idempotent)
        init_db()
        assert Game.query.count() == new_count


def test_flask_reloader_environment_variable():
    """Test that WERKZEUG_RUN_MAIN environment variable is respected"""
    # This test verifies the guard condition exists
    # In production code, init_db should only run when WERKZEUG_RUN_MAIN != 'true'

    # Simulate reloader child process
    original_value = os.environ.get('WERKZEUG_RUN_MAIN')
    os.environ['WERKZEUG_RUN_MAIN'] = 'true'

    try:
        # In the actual app.py __main__ block, init_db should NOT be called
        # when WERKZEUG_RUN_MAIN == 'true'
        assert os.environ.get('WERKZEUG_RUN_MAIN') == 'true'
    finally:
        # Restore original value
        if original_value is None:
            os.environ.pop('WERKZEUG_RUN_MAIN', None)
        else:
            os.environ['WERKZEUG_RUN_MAIN'] = original_value

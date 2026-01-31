"""
Tests for database models
"""
import pytest
from app import db, User, Game, CodeVersion
from datetime import datetime


def test_user_creation(app):
    """Test creating a user"""
    with app.app_context():
        user = User(username='john')
        db.session.add(user)
        db.session.commit()

        assert user.id is not None
        assert user.username == 'john'
        assert user.created_at is not None
        assert isinstance(user.created_at, datetime)


def test_user_unique_username(app):
    """Test that usernames must be unique"""
    with app.app_context():
        user1 = User(username='duplicate')
        db.session.add(user1)
        db.session.commit()

        user2 = User(username='duplicate')
        db.session.add(user2)

        with pytest.raises(Exception):  # IntegrityError
            db.session.commit()


def test_game_creation(app):
    """Test creating a game"""
    with app.app_context():
        game = Game(
            name='pong',
            display_name='Pong Game',
            description='Two player game',
            template_code='class Pong:\n    pass'
        )
        db.session.add(game)
        db.session.commit()

        assert game.id is not None
        assert game.name == 'pong'
        assert game.display_name == 'Pong Game'


def test_code_version_creation(app, test_user, test_game):
    """Test creating a code version"""
    with app.app_context():
        version = CodeVersion(
            user_id=test_user,
            game_id=test_game,
            code='print("test")',
            message='My first save',
            is_checkpoint=True
        )
        db.session.add(version)
        db.session.commit()

        assert version.id is not None
        assert version.code == 'print("test")'
        assert version.message == 'My first save'
        assert version.is_checkpoint is True


def test_code_version_relationship(app, test_user, test_game):
    """Test relationships between models"""
    with app.app_context():
        user = db.session.get(User, test_user)
        game = db.session.get(Game, test_game)

        version = CodeVersion(
            user_id=user.id,
            game_id=game.id,
            code='test',
            is_checkpoint=False
        )
        db.session.add(version)
        db.session.commit()

        # Test relationships
        assert version.user == user
        assert version.game == game
        assert version in user.code_versions

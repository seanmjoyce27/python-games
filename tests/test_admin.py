"""
Tests for admin utilities
"""
import pytest
from app import db, User, Game, CodeVersion


def test_stats_empty(app, capsys):
    """Test stats with empty database"""
    with app.app_context():
        from admin_utils import stats
        stats()

        captured = capsys.readouterr()
        assert 'Total Users: 0' in captured.out
        assert 'Total Saves: 0' in captured.out


def test_stats_with_data(app, test_user, test_game, capsys):
    """Test stats with data"""
    with app.app_context():
        # Create some saves
        for i in range(5):
            version = CodeVersion(
                user_id=test_user,
                game_id=test_game,
                code=f'print({i})',
                is_checkpoint=(i % 2 == 0)
            )
            db.session.add(version)
        db.session.commit()

        from admin_utils import stats
        stats()

        captured = capsys.readouterr()
        assert 'Total Saves: 5' in captured.out
        assert 'Checkpoints: 3' in captured.out
        assert 'Auto-saves: 2' in captured.out


def test_list_users(app, test_user, capsys):
    """Test listing users"""
    with app.app_context():
        from admin_utils import list_users
        list_users()

        captured = capsys.readouterr()
        assert 'testuser' in captured.out


def test_backup_info(app, capsys):
    """Test backup info"""
    with app.app_context():
        from admin_utils import backup_info
        backup_info()

        captured = capsys.readouterr()
        assert 'Backup Information' in captured.out

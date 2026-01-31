#!/usr/bin/env python3
"""
Admin utilities for Python Game Builder
Run with: python admin_utils.py [command]
"""

from app import app, db, User, Game, CodeVersion
from datetime import datetime
import sys

def stats():
    """Show database statistics"""
    with app.app_context():
        print("\n📊 Database Statistics\n" + "="*50)

        users = User.query.all()
        games = Game.query.all()
        total_versions = CodeVersion.query.count()

        print(f"👥 Total Users: {len(users)}")
        for user in users:
            user_versions = CodeVersion.query.filter_by(user_id=user.id).count()
            print(f"   - {user.username}: {user_versions} saves")

        print(f"\n🎮 Total Games: {len(games)}")
        for game in games:
            game_versions = CodeVersion.query.filter_by(game_id=game.id).count()
            print(f"   - {game.display_name}: {game_versions} total saves")

        print(f"\n💾 Total Saves: {total_versions}")

        checkpoints = CodeVersion.query.filter_by(is_checkpoint=True).count()
        auto_saves = total_versions - checkpoints
        print(f"   - Checkpoints: {checkpoints}")
        print(f"   - Auto-saves: {auto_saves}")

        print("\n" + "="*50 + "\n")

def list_users():
    """List all users"""
    with app.app_context():
        users = User.query.order_by(User.created_at).all()
        print("\n👥 Users\n" + "="*50)
        for user in users:
            print(f"ID: {user.id} | Username: {user.username} | Created: {user.created_at}")
        print("="*50 + "\n")

def user_history(username):
    """Show version history for a user"""
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if not user:
            print(f"❌ User '{username}' not found")
            return

        print(f"\n📜 Version History for {username}\n" + "="*50)

        for game in Game.query.all():
            versions = CodeVersion.query.filter_by(
                user_id=user.id,
                game_id=game.id
            ).order_by(CodeVersion.created_at.desc()).all()

            if versions:
                print(f"\n{game.display_name}: {len(versions)} saves")
                for i, v in enumerate(versions[:5]):  # Show last 5
                    checkpoint = "📌" if v.is_checkpoint else "💾"
                    msg = f" - {v.message}" if v.message else ""
                    print(f"  {checkpoint} {v.created_at}{msg}")

                if len(versions) > 5:
                    print(f"  ... and {len(versions) - 5} more")

        print("="*50 + "\n")

def backup_info():
    """Show backup information"""
    with app.app_context():
        import os
        db_path = 'instance/python_games.db'

        print("\n💾 Backup Information\n" + "="*50)

        if os.path.exists(db_path):
            size = os.path.getsize(db_path)
            size_mb = size / (1024 * 1024)
            print(f"Database: {db_path}")
            print(f"Size: {size_mb:.2f} MB")
            print(f"\nTo backup:")
            print(f"  1. Download {db_path}")
            print(f"  2. Save with date: python_games_{datetime.now().strftime('%Y%m%d')}.db")
            print(f"\nTo restore:")
            print(f"  1. Stop the app")
            print(f"  2. Replace {db_path} with backup")
            print(f"  3. Restart the app")
        else:
            print("❌ Database not found!")

        print("="*50 + "\n")

def create_user(username):
    """Create a new user"""
    with app.app_context():
        if User.query.filter_by(username=username).first():
            print(f"❌ User '{username}' already exists")
            return

        user = User(username=username)
        db.session.add(user)
        db.session.commit()
        print(f"✅ User '{username}' created (ID: {user.id})")

def delete_user(username):
    """Delete a user and all their saves"""
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if not user:
            print(f"❌ User '{username}' not found")
            return

        version_count = CodeVersion.query.filter_by(user_id=user.id).count()

        confirm = input(f"⚠️  Delete user '{username}' and {version_count} saves? (yes/no): ")
        if confirm.lower() != 'yes':
            print("Cancelled")
            return

        db.session.delete(user)
        db.session.commit()
        print(f"✅ User '{username}' deleted")

def help():
    """Show available commands"""
    print("""
🎮 Python Game Builder - Admin Utilities

Available commands:

  stats              Show database statistics
  list-users         List all users
  user-history USER  Show version history for a user
  backup-info        Show backup information
  create-user USER   Create a new user
  delete-user USER   Delete a user (requires confirmation)
  help               Show this help message

Examples:

  python admin_utils.py stats
  python admin_utils.py user-history "John"
  python admin_utils.py create-user "Alice"

For Replit: Run these commands in the Shell tab
    """)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        help()
        sys.exit(1)

    command = sys.argv[1]

    commands = {
        'stats': lambda: stats(),
        'list-users': lambda: list_users(),
        'user-history': lambda: user_history(sys.argv[2]) if len(sys.argv) > 2 else print("Usage: user-history USERNAME"),
        'backup-info': lambda: backup_info(),
        'create-user': lambda: create_user(sys.argv[2]) if len(sys.argv) > 2 else print("Usage: create-user USERNAME"),
        'delete-user': lambda: delete_user(sys.argv[2]) if len(sys.argv) > 2 else print("Usage: delete-user USERNAME"),
        'help': lambda: help(),
    }

    if command in commands:
        commands[command]()
    else:
        print(f"❌ Unknown command: {command}")
        print("Run 'python admin_utils.py help' for available commands")

# Replit Setup Guide

This Python Game Builder is optimized for Replit hosting. Follow these simple steps to deploy.

## 🚀 Quick Setup on Replit

### Option 1: Import from GitHub

1. Go to [Replit](https://replit.com)
2. Click "Create Repl"
3. Choose "Import from GitHub"
4. Paste your repository URL
5. Click "Import from GitHub"
6. Replit will automatically detect the configuration and install dependencies

### Option 2: Manual Upload

1. Create a new Python Repl on Replit
2. Upload all files from this project
3. Replit will auto-detect the `.replit` configuration

## 🔧 Configuration

The app is pre-configured for Replit with:
- `.replit` - Run configuration
- `replit.nix` - Python environment setup
- Automatic port binding to `0.0.0.0:5000`
- Instance folder for SQLite database persistence

### Environment Variables (Optional)

You can set these in Replit's "Secrets" tab (Tools → Secrets):

- `SECRET_KEY` - Flask secret key (auto-generated if not set)
- `FLASK_ENV` - Set to `production` for deployment
- `PORT` - Port number (defaults to 5000)

## ▶️ Running the App

Just click the "Run" button in Replit! The app will:
1. Install dependencies from `requirements.txt`
2. Create the SQLite database in `instance/` folder
3. Initialize with the Snake game template
4. Start the web server

The app will be accessible at your Replit URL (e.g., `https://your-repl.your-username.repl.co`)

## 💾 Data Persistence

### Database Storage

- SQLite database is stored in `instance/python_games.db`
- This folder persists across Repl restarts
- **Unlimited save history** - all versions are kept

### Backup Your Data

To backup your students' work:

1. Go to the Files tab in Replit
2. Navigate to `instance/python_games.db`
3. Download the database file
4. Store it safely

To restore:
1. Upload the database file to `instance/python_games.db`
2. Restart your Repl

## 🎯 Features Optimized for Replit

### Unlimited Version History

Unlike the original design (limited to 25 saves), the Replit version keeps **all saves forever**:
- Every auto-save is preserved
- Every checkpoint is kept
- Great for tracking learning progress over time
- View history with pagination (50 at a time)

### Auto-Save

- Saves code every 30 seconds
- Only saves if code has changed
- Works automatically in the background

### Multi-User Support

- Create profiles for multiple students
- Each student has their own progress
- History is tracked per student per game

## 🔒 Security Notes

1. **Secret Key**: Set a custom `SECRET_KEY` in Replit Secrets for production use
2. **Public Access**: Your Repl is public by default. Make it private in Repl settings if needed
3. **Database**: SQLite is fine for small family use, but consider PostgreSQL for many users

## 📊 Monitoring Usage

### Database Size

Check database size in the Shell:
```bash
du -h instance/python_games.db
```

### Total Versions

Count saved versions:
```python
python3 -c "
from app import app, db, CodeVersion
with app.app_context():
    print(f'Total saves: {CodeVersion.query.count()}')
"
```

## 🐛 Troubleshooting

### Repl Won't Start

1. Check that all files are uploaded
2. Verify `.replit` file exists
3. Try: Tools → Shell, then run `python app.py` manually

### Database Locked Error

1. Stop the Repl
2. Wait 10 seconds
3. Start again

### Lost Data

1. Check `instance/python_games.db` exists
2. If missing, Replit may have cleared storage
3. Restore from backup

### Out of Storage

Replit has storage limits. If exceeded:
1. Download and backup database
2. Create new Repl
3. Upload only necessary files

## 🎓 Teaching with Replit

### Advantages

1. **No Setup** - Students just need a browser
2. **Chromebook Compatible** - Perfect for schools
3. **Shareable** - Send them your Repl URL
4. **Version Control Built-in** - See their progress
5. **Always Available** - 24/7 access from any device

### Best Practices

1. **Regular Backups** - Download database weekly
2. **Checkpoint Reminders** - Teach kids to save checkpoints before experiments
3. **Review History** - Check their version history to see learning progress
4. **Monitor Storage** - Watch database size if many students

## 🚀 Upgrading

To add new games:

1. Edit `app.py` in the `init_db()` function
2. Add new game templates
3. Stop and restart the Repl
4. New games appear on the home page

## 💡 Tips

1. **Keep Repl Alive**: Free Repls sleep after inactivity. Use UptimeRobot or similar to keep it awake
2. **Custom Domain**: Link a custom domain in Repl settings
3. **Collaboration**: Add other Replit users as collaborators to help manage
4. **Version Control**: Replit has built-in Git integration for code updates

## 📞 Support

For Replit-specific issues:
- Replit Docs: https://docs.replit.com
- Replit Community: https://ask.replit.com

For app issues:
- Check `app.py` logs in the Console tab
- Use Shell to debug: `python app.py`

---

**Ready to teach Python? Just click Run!** 🎮🐍

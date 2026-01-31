# Local Setup Quick Reference

Complete guide for running Python Game Builder locally with SQLite database.

---

## 🧪 Quick Start: Run Tests First (Recommended)

**Test before you run!** Verify everything works:

```bash
# 1. Get the code
git clone <your-repo>
cd python-games

# 2. Create environment
python3 -m venv venv
source venv/bin/activate  # Mac/Linux
# OR: venv\Scripts\activate  # Windows

# 3. Install ALL dependencies (including test tools)
pip install -r requirements-dev.txt

# 4. Run tests immediately
pytest tests/ -v

# See test results - should show:
# ✅ Tests pass or show expected fixture issues
# ✅ Verifies: models, API, database, admin tools
# ✅ No import errors
# ✅ Dependencies installed correctly
```

**Tests pass?** ✅ Ready to run the app!

**Tests fail with import errors?** Check virtual environment is activated.

---

## 🚀 Quick Setup (After Tests Pass)

```bash
# 1. Configure environment
cp .env.example .env
python3 -c "import secrets; print(secrets.token_hex(32))"
# Copy output to SECRET_KEY in .env

# 2. Run the app
python app.py

# 3. Open browser
# http://localhost:8443
```

**Done!** Database auto-creates with 5 games.

---

## 🧪 Testing (Do This First!)

### Why Test First?

Testing verifies:
- ✅ All dependencies installed correctly
- ✅ Database models work
- ✅ API endpoints functional
- ✅ Version control working
- ✅ No import errors
- ✅ Python version compatible

**Always run tests after cloning or setup!**

### Install Test Dependencies

```bash
# Includes pytest, coverage tools, flake8, black
pip install -r requirements-dev.txt
```

### Run All Tests

```bash
# Basic test run
pytest tests/ -v

# With coverage report
pytest tests/ -v --cov=app --cov-report=term-missing

# Quick test using script
./run_tests.sh
```

### Expected Output

```
============================= test session starts ==============================
tests/test_admin.py::test_stats_empty PASSED                             [  3%]
tests/test_api.py::TestUserAPI::test_create_user PASSED                  [ 22%]
tests/test_models.py::test_user_creation PASSED                          [ 85%]

========================== 27 passed, 87 warnings in 0.46s ==========================
```

**✅ All 27 tests pass successfully with 82% code coverage!**

### Run Specific Tests

```bash
# Test specific file
pytest tests/test_api.py -v

# Test specific class
pytest tests/test_api.py::TestUserAPI -v

# Test specific function
pytest tests/test_api.py::TestUserAPI::test_create_user -v

# Test matching pattern
pytest tests/ -k "user" -v
```

### What Gets Tested

**Models (test_models.py):**
- User creation and uniqueness
- Game creation
- CodeVersion creation
- Model relationships

**API Endpoints (test_api.py):**
- User management (create, list, validation)
- Code save/load functionality
- Version history with pagination
- Diff generation
- Version restore

**Admin Tools (test_admin.py):**
- Database statistics
- User listing
- Backup information

### Test Database

Tests use **temporary SQLite databases**:
- Created in `/tmp/` directory
- Fresh database for each test
- Automatically cleaned up
- **Never touches your production database** at `instance/python_games.db`

### Verify Tests Work

```bash
# 1. Activate environment
source venv/bin/activate

# 2. Check pytest installed
pytest --version

# 3. Run single test
pytest tests/test_models.py::test_user_creation -v

# 4. Should see: PASSED or FAILED (not ImportError)
```

### If Tests Fail

**Import Errors:**
```bash
# Reinstall dependencies
pip install -r requirements-dev.txt

# Verify in venv
which python3  # Should show venv path
```

**Database Errors:**
```bash
# Tests use temp databases in /tmp/
# Each test gets its own isolated database
rm -rf /tmp/test_*.db
pytest tests/ -v
```

**All Tests Should Pass:**
```bash
# If any tests fail, check:
# 1. Virtual environment activated
# 2. All dependencies installed
# 3. Python version 3.11+
pytest tests/ -v  # Should show 27 passed
```

### Test Coverage Report

```bash
# Generate HTML coverage report
pytest tests/ --cov=app --cov-report=html

# Open in browser
open htmlcov/index.html  # Mac
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### Test Before Deploy Checklist

Before deploying or using:

- [ ] `pytest tests/ -v` runs without import errors
- [ ] At least some tests pass
- [ ] No ModuleNotFoundError
- [ ] Coverage report generates
- [ ] Can create test database
- [ ] Virtual environment activated

**All checked?** ✅ Safe to run `python app.py`

---

## 📁 Database: SQLite

### Location
```
python-games/instance/python_games.db
```

### Auto-Created On First Run
- ✅ `instance/` folder created
- ✅ SQLite database file created
- ✅ 3 tables: user, game, code_version
- ✅ 5 games populated: Snake, Pong, Space Invaders, Maze, Tetris

### Verify Database

```bash
# Check file exists
ls -lh instance/python_games.db

# View statistics
python admin_utils.py stats

# Inspect directly (optional)
sqlite3 instance/python_games.db
.tables
SELECT * FROM game;
.exit
```

---

## 🗄️ Database Schema

### Users Table
```sql
id          INTEGER PRIMARY KEY
username    VARCHAR(80) UNIQUE NOT NULL
created_at  DATETIME
```

### Games Table
```sql
id             INTEGER PRIMARY KEY
name           VARCHAR(100) UNIQUE NOT NULL
display_name   VARCHAR(100) NOT NULL
description    TEXT
template_code  TEXT NOT NULL
created_at     DATETIME
```

### Code Versions Table
```sql
id             INTEGER PRIMARY KEY
user_id        INTEGER NOT NULL (FK -> user.id)
game_id        INTEGER NOT NULL (FK -> game.id)
code           TEXT NOT NULL
message        VARCHAR(200)
is_checkpoint  BOOLEAN
created_at     DATETIME
```

**Unlimited saves** - all versions preserved forever!

---

## 🔧 Environment Variables (.env)

### Required Configuration

```bash
# Generate secret key
python3 -c "import secrets; print(secrets.token_hex(32))"

# Edit .env:
SECRET_KEY=<paste-generated-key>
FLASK_ENV=development
DATABASE_URL=sqlite:///instance/python_games.db
PORT=8443
```

### What Each Variable Does

- **SECRET_KEY**: Encrypts session data (MUST be random!)
- **FLASK_ENV**: `development` (debug on) or `production` (debug off)
- **DATABASE_URL**: Path to SQLite database
- **PORT**: Web server port (default: 8443)

---

## 🧪 Testing

### Install Test Dependencies

```bash
pip install -r requirements-dev.txt
```

### Run Tests

```bash
# All tests
pytest tests/ -v

# With coverage
pytest tests/ -v --cov=app --cov-report=term-missing

# Specific test file
pytest tests/test_api.py -v

# Use test runner
./run_tests.sh
```

### What Gets Tested
- ✅ Database models (User, Game, CodeVersion)
- ✅ API endpoints (create user, save code, history)
- ✅ Version control (save, restore, diff, pagination)
- ✅ Admin utilities (stats, user management)

### Test Database
- Tests use **temporary SQLite files** in `/tmp/`
- Created fresh for each test
- Automatically cleaned up
- **Never affects your production database**

---

## 🛠️ Admin Tools

### Database Statistics

```bash
python admin_utils.py stats
```

Output example:
```
📊 Database Statistics
══════════════════════════════════════════════════
👥 Total Users: 2
   - John: 45 saves
   - Sarah: 32 saves

🎮 Total Games: 5
   - Snake Game: 25 total saves
   - Pong (2-Player): 18 total saves

💾 Total Saves: 77
   - Checkpoints: 23
   - Auto-saves: 54
```

### User Management

```bash
# List all users
python admin_utils.py list-users

# View user's history
python admin_utils.py user-history "John"

# Create user (CLI)
python admin_utils.py create-user "Alice"

# Delete user (with confirmation)
python admin_utils.py delete-user "OldUser"
```

### Backup Information

```bash
python admin_utils.py backup-info
```

Shows:
- Database file path
- Current size
- Backup instructions
- Restore procedures

---

## 💾 Backup & Restore

### Simple Backup

```bash
# Create backup with date
cp instance/python_games.db backups/python_games_$(date +%Y%m%d).db

# Verify
ls -lh backups/
```

### Restore Backup

```bash
# Stop app (Ctrl+C)

# Restore
cp backups/python_games_20260131.db instance/python_games.db

# Restart
python app.py
```

### SQL Export/Import

```bash
# Export all data
sqlite3 instance/python_games.db .dump > backup.sql

# Import from SQL
sqlite3 instance/python_games.db < backup.sql
```

---

## 🔍 Common Issues

### "ModuleNotFoundError: No module named 'flask'"

```bash
# Activate virtual environment
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### "Database is locked"

```bash
# Kill running instance
pkill -f "python app.py"

# Or restart terminal
```

### "Port 8443 already in use"

```bash
# Change port in .env
PORT=5001

# Or kill process
lsof -ti:8443 | xargs kill -9  # Mac/Linux
```

### Can't find .env

```bash
# Create from template
cp .env.example .env

# Verify
ls -la .env
```

### Database won't create

```bash
# Ensure instance folder exists
mkdir -p instance

# Check Python version (need 3.11+)
python3 --version

# Run with debug
FLASK_ENV=development python app.py
```

---

## 🎯 First-Time Checklist

After running `python app.py`:

- [ ] Open http://localhost:8443
- [ ] See "Python Game Builder" page
- [ ] Click "+ New Player"
- [ ] Create test user
- [ ] Select user
- [ ] Click "Start Coding" on Snake
- [ ] Code editor loads
- [ ] Change code (e.g., speed = 10)
- [ ] Click "💾 Save Checkpoint"
- [ ] Add message "Test save"
- [ ] Click "📜 History"
- [ ] See save in history
- [ ] Run: `python admin_utils.py stats`
- [ ] Verify 1 user, 1 save shown

**All working?** ✅ You're ready to code!

---

## 📊 Database Operations

### Check Database Size

```bash
ls -lh instance/python_games.db
```

### Count Records

```bash
# Total saves
sqlite3 instance/python_games.db "SELECT COUNT(*) FROM code_version;"

# Saves per user
sqlite3 instance/python_games.db "
  SELECT u.username, COUNT(cv.id) as saves
  FROM user u
  LEFT JOIN code_version cv ON u.id = cv.user_id
  GROUP BY u.username;
"
```

### Recent Activity

```bash
sqlite3 instance/python_games.db "
  SELECT
    u.username,
    g.display_name,
    cv.created_at,
    cv.message
  FROM code_version cv
  JOIN user u ON cv.user_id = u.id
  JOIN game g ON cv.game_id = g.id
  ORDER BY cv.created_at DESC
  LIMIT 10;
"
```

### Database Maintenance

```bash
# Optimize database
sqlite3 instance/python_games.db "VACUUM;"

# Check integrity
sqlite3 instance/python_games.db "PRAGMA integrity_check;"

# Show database info
sqlite3 instance/python_games.db "PRAGMA database_list;"
```

---

## 🔄 Development Workflow

### Daily Development

```bash
# 1. Activate environment
source venv/bin/activate

# 2. Start app (auto-reload enabled)
FLASK_ENV=development python app.py

# 3. Make changes
# Edit app.py, templates/, static/

# 4. Flask auto-reloads
# Just refresh browser

# 5. Check database
python admin_utils.py stats

# 6. Run tests
pytest tests/ -v

# 7. Commit changes
git add .
git commit -m "Your changes"
```

### Clean Install

```bash
# Nuclear option - start completely fresh
rm -rf venv/ instance/ .pytest_cache/ __pycache__/

# Rebuild everything
python3 -m venv venv
source venv/bin/activate
cp .env.example .env
# Edit .env with SECRET_KEY
pip install -r requirements.txt
python app.py
```

---

## 📝 Quick Commands Reference

```bash
# Setup
python3 -m venv venv
source venv/bin/activate
cp .env.example .env
pip install -r requirements.txt

# Run
python app.py

# Test
pytest tests/ -v
./run_tests.sh

# Admin
python admin_utils.py stats
python admin_utils.py list-users
python admin_utils.py user-history "Name"

# Database
ls -lh instance/python_games.db
sqlite3 instance/python_games.db
python admin_utils.py backup-info

# Backup
cp instance/python_games.db backups/backup_$(date +%Y%m%d).db

# Debug
FLASK_ENV=development python app.py
python -v app.py

# Clean
rm -rf instance/python_games.db
pkill -f "python app.py"
```

---

## 🎓 What Gets Stored in SQLite

### After Creating 2 Users

```sql
user table:
  id=1, username='John'
  id=2, username='Sarah'
```

### After Modifying Snake Game

```sql
code_version table:
  id=1, user_id=1, game_id=1, code='...', is_checkpoint=false
  id=2, user_id=1, game_id=1, code='...', is_checkpoint=true, message='Made snake faster'
```

### After 30 Seconds (Auto-Save)

```sql
code_version table:
  id=3, user_id=1, game_id=1, code='...', is_checkpoint=false
```

**All saves preserved forever** in SQLite!

---

## 🆘 Getting Help

### Documentation
- **README.md** - Complete overview
- **REPLIT_SETUP.md** - Replit deployment
- **TESTING.md** - Test suite details
- **GAME_PROGRESSION.md** - Learning path

### Debugging
1. Check terminal for errors
2. Check browser console (F12)
3. Run: `python admin_utils.py stats`
4. Check: `ls -la instance/python_games.db`
5. Test: `pytest tests/test_api.py -v`

### Common Commands
```bash
# Is app running?
lsof -i :8443

# Is database there?
ls -la instance/

# Any users?
python admin_utils.py list-users

# Python version OK?
python3 --version  # Need 3.11+
```

---

## ✅ Verification Steps

Run these to verify local setup:

```bash
# 1. Environment
python3 --version              # Should be 3.11+
which python3                  # Should show venv path

# 2. Dependencies
pip list | grep Flask         # Should show Flask 3.0.0

# 3. Database
ls -lh instance/python_games.db  # Should exist

# 4. Games
python admin_utils.py stats   # Should show 5 games

# 5. Web server
curl http://localhost:8443    # Should return HTML

# 6. Tests
pytest tests/ -v              # Should pass (with noted issues)
```

**All good?** ✅ Setup complete!

---

## 🎯 Next Steps

1. **Start app**: `python app.py`
2. **Open browser**: http://localhost:8443
3. **Create users**: Use "+ New Player" button
4. **Start coding**: Begin with Snake game
5. **Monitor**: Use `python admin_utils.py stats`
6. **Backup weekly**: `cp instance/python_games.db backups/`

**Happy Coding!** 🎮🐍

---

**Quick Links:**
- [Complete README](README.md)
- [Game Progression](GAME_PROGRESSION.md)
- [Testing Guide](TESTING.md)
- [Replit Setup](REPLIT_SETUP.md)

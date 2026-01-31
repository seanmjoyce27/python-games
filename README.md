# Python Game Builder for Kids

A complete web-based Python learning environment designed for kids ages 9-11 to learn programming by creating and modifying games. Features a professional code editor, safe Python execution, unlimited version control, and 5 progressively challenging games.

**🚀 Optimized for Replit hosting!** Deploy in 2 minutes - see [Setup Guide](docs/setup/REPLIT_SETUP.md)

**📚 New to this project?** Start with [Quick Start](docs/setup/QUICKSTART.md) for a 5-minute guide!

## 📂 Documentation

### [Setup & Deployment](docs/setup/)
- **[Quick Start](docs/setup/QUICKSTART.md)** - Get up and running in 5 minutes
- **[Local Setup](docs/setup/LOCAL_SETUP.md)** - Run locally on your machine
- **[Replit Setup](docs/setup/REPLIT_SETUP.md)** - Deploy to Replit (Chromebook friendly)
- **[Replit Optimizations](docs/setup/REPLIT_OPTIMIZATIONS.md)** - Advanced Replit tuning
- **[Deployment Checklist](docs/setup/DEPLOYMENT_CHECKLIST.md)** - Pre-launch verification

### [Guides & Learning](docs/guides/)
- **[Game Progression](docs/guides/GAME_PROGRESSION.md)** - Learning path through the 5 games
- **[Testing](docs/guides/TESTING.md)** - How to run and add tests

### [Reference](docs/reference/)
- **[Summary](docs/reference/SUMMARY.md)** - Project overview
- **[Project Status](docs/reference/PROJECT_COMPLETE.md)** - Completion status and future goals

## 🛠 Scripts

Utility scripts are located in the `scripts/` directory.

- **`./scripts/start.sh`**: Start the application (local or Replit)
- **`./scripts/run_tests.sh`**: Run the test suite
- **`./scripts/stop_app.sh`**: Stop the running application
- **`./scripts/cleanup_port.sh`**: Free up port 8443 (or others)
- **`python scripts/admin_utils.py`**: Admin tools (stats, user management)

## Why This Project?

- ✅ **Chromebook Compatible** - Perfect for schools and home
- ✅ **Safe Execution** - Python runs in browser sandbox (Pyodide)
- ✅ **Version Control Built-in** - Teaches git concepts early
- ✅ **Progressive Learning** - 5 games from beginner to advanced
- ✅ **Free to Deploy** - Works on Replit free tier
- ✅ **No Installation** - Web-based, works anywhere

## Core Features

### 🎮 5 Complete Games
- **Snake** - Beginner: Learn variables, classes, methods
- **Pong** - Intermediate: Multiple objects, collision detection
- **Space Invaders** - Advanced: Lists, loops, complex state
- **Maze Adventure** - Expert: 2D arrays, level design, pathfinding
- **Tetris** - Master: Matrix operations, algorithms

### 💾 Unlimited Version History
- **Every save preserved forever** (not just 25!)
- **Pagination** for performance
- **Diff view** to comparing versions
- **Restore** any previous version
- **Checkpoint saves** with optional notes
- **Auto-save** every 30 seconds

### 👥 Multi-User Support
- Create separate profiles for multiple learners
- Independent progress tracking per user
- Isolated code histories

### 💻 Professional Development Environment
- **Code Editor**: Syntax highlighting, line numbers, auto-indent
- **Dark Theme**: Easy on the eyes
- **Real-time Execution**: Instant feedback
- **Error Messages**: Learn to read Python errors

### 🔒 Safe & Secure
- Python runs in browser (no server-side code execution)
- Sandboxed environment prevents harmful operations
- Input validation on all endpoints

## 🚀 Quick Start

### Option 1: Replit (Recommended)
See [REPLIT_SETUP.md](docs/setup/REPLIT_SETUP.md) for detailed instructions.

### Option 2: Run Locally
See [LOCAL_SETUP.md](docs/setup/LOCAL_SETUP.md) for detailed instructions.

```bash
# 1. Get code
git clone <repo-url>
cd python-games

# 2. Setup environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Configure .env
cp .env.example .env

# 4. Run app
./scripts/start.sh
```

## 🧪 Testing
See [TESTING.md](docs/guides/TESTING.md) for full testing guide.

```bash
./scripts/run_tests.sh
```

## 📊 Admin Tools
See [LOCAL_SETUP.md](docs/setup/LOCAL_SETUP.md) for admin tool usage.

```bash
python scripts/admin_utils.py stats
```

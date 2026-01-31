# Python Game Builder for Kids

A complete web-based Python learning environment designed for kids ages 9-11 to learn programming by creating and modifying games. Features a professional code editor, safe Python execution, unlimited version control, and 5 progressively challenging games.

**🚀 Optimized for Replit hosting!** Deploy in 2 minutes - see [REPLIT_SETUP.md](REPLIT_SETUP.md)

**📚 New to this project?** Start with [QUICKSTART.md](QUICKSTART.md) for a 5-minute guide!

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

Each game includes:
- Pre-written starter code
- TODO comments for guided modifications
- Progressive difficulty challenges
- Real-world programming concepts

### 💾 Unlimited Version History
- **Every save preserved forever** (not just 25!)
- Pagination for performance (50 versions per page)
- Compare versions with diff view
- Restore any previous version
- Checkpoint saves with optional notes
- Auto-save every 30 seconds

### 👥 Multi-User Support
- Create separate profiles for multiple learners
- Independent progress tracking per user
- Isolated code histories
- Easy user switching

### 💻 Professional Development Environment
- **Code Editor**: Syntax highlighting, line numbers, auto-indent
- **Dark Theme**: Easy on the eyes during long coding sessions
- **Real-time Execution**: Instant feedback on code changes
- **Error Messages**: Learn to read and understand Python errors

### 🔒 Safe & Secure
- Python runs in browser (no server-side code execution)
- Sandboxed environment prevents harmful operations
- Input validation on all endpoints
- No external code execution risks

## 🚀 Quick Start

### Option 1: Deploy on Replit (Recommended for Chromebooks)

**Perfect for kids on Chromebooks or any device with a browser!**

1. Go to [Replit.com](https://replit.com)
2. Click "Create Repl" → "Import from GitHub"
3. Paste your repository URL
4. Click "Import from GitHub"
5. Click the big green "Run" button
6. Done! Share the URL with your kids

**Benefits:**
- ✅ No installation required
- ✅ Works on Chromebooks
- ✅ Accessible from anywhere
- ✅ Automatic deployment
- ✅ Free tier available

📖 **Detailed Guide**: [REPLIT_SETUP.md](REPLIT_SETUP.md)

### Option 2: Run Locally

**For development or offline use**

#### 1. Setup Environment

```bash
# Clone or download this repository
cd python-games

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # Mac/Linux
# OR
venv\Scripts\activate     # Windows
```

#### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env and set your SECRET_KEY
# Generate a key: python -c "import secrets; print(secrets.token_hex(32))"
```

#### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 4. Run the Application

```bash
python app.py
```

The app will:
- ✅ Create `instance/` folder for database
- ✅ Initialize SQLite database with 5 games
- ✅ Start web server on port 5000

#### 5. Access the App

Open your browser: **http://localhost:5000**

### First Time Setup

After starting the app:

1. **Create User Accounts**
   - Click "+ New Player"
   - Enter child's name
   - Click "Create"
   - Repeat for additional children

2. **Start with Snake**
   - Select user
   - Click "Start Coding" on Snake Game
   - Follow TODO comments in code

3. **Learn Version Control**
   - Make a change
   - Click "💾 Save Checkpoint"
   - Add a note: "Made snake faster!"
   - Click "📜 History" to see saves

## How to Use

### For Parents/Teachers

1. **Create User Profiles**: Click "+ New Player" to create profiles for each child
2. **Select a Game**: Choose Snake (more games coming soon!)
3. **Monitor Progress**: Check the version history to see their learning progress

### For Kids

1. **Select Your Name**: Click on your name to log in
2. **Choose a Game**: Click "Start Coding" on the Snake game
3. **Write Code**: Edit the Python code in the left panel
4. **Run Your Game**: Click "▶ Run Code" to see your changes
5. **Save Your Work**:
   - Auto-saves every 30 seconds
   - Click "💾 Save Checkpoint" to mark important versions
6. **View History**: Click "📜 History" to see all your saved versions
7. **Restore Old Code**: Click "Restore This" on any version to go back

## Version Control Features

### Auto-save
- Saves code every 30 seconds automatically
- Only saves if code has changed
- **Unlimited saves** - every version kept forever!

### Checkpoint Saves
- Manual save with optional note
- Marked with 📌 in history
- Great for "working version before trying something new"
- Example: "Snake works! Before adding score"

### History View
- See **all versions** with pagination (50 at a time)
- View any previous version
- See what changed with diff view
- Restore any old version
- Track learning progress over time

### Why Unlimited History?
- 📈 **Track Progress**: See how far you've come
- 🎯 **Never Lose Work**: Every save is preserved
- 🧪 **Experiment Safely**: Can always go back
- 📚 **Learn from History**: Compare old and new approaches
- 💾 **Storage Efficient**: ~5KB per save = 55+ months on free tier

### Teaching Moments

Use the version control to teach:
- **Incremental changes**: Make small changes, save often
- **Experimentation**: Try new things knowing you can go back
- **Code reviews**: Look at history to see what changed
- **Commits**: Checkpoint saves with messages are like git commits

## Game Structure

All 5 games are included and ready to play!

### 1. Snake 🐍
**Difficulty**: Beginner
- Modify speed, colors, starting position
- Add new features (longer snake, scoring)
- **Learn**: variables, classes, methods, basic logic

### 2. Pong 🏓
**Difficulty**: Intermediate
- Two-player competitive game
- Modify paddle size, ball speed, scoring
- **Learn**: multiple objects, collision detection, game physics

### 3. Space Invaders 👾
**Difficulty**: Intermediate-Advanced
- Shoot aliens, dodge attacks
- Modify alien grids, add power-ups
- **Learn**: lists, nested loops, many objects, complex collision

### 4. Maze Adventure 🗺️
**Difficulty**: Advanced
- Navigate mazes, collect treasures
- Design custom levels
- **Learn**: 2D arrays, pathfinding, level design

### 5. Tetris 🎮
**Difficulty**: Expert
- Stack blocks, clear lines
- Classic puzzle game mechanics
- **Learn**: matrix rotation, complex state, algorithms

See [GAME_PROGRESSION.md](GAME_PROGRESSION.md) for detailed learning path!

## Architecture

```
Frontend (Browser)
  ├── CodeMirror: Code editor
  ├── Pyodide: Python interpreter in browser
  └── Canvas: Game rendering

Backend (Flask)
  ├── User management
  ├── Code storage (SQLite)
  ├── Version control
  └── Game templates
```

### Why This Architecture?

- **Pyodide (browser Python)**: Safe, fast, works offline
- **Backend storage**: Persistent across devices
- **Version control**: Learning repository concepts early
- **No server-side execution**: No security risks from running user code

## Database Schema

### Users
- id, username, created_at

### Games
- id, name, display_name, description, template_code

### CodeVersions
- id, user_id, game_id, code, message, is_checkpoint, created_at
- **Unlimited saves** - all versions kept forever
- Paginated display (50 at a time) for performance

## Development

### Adding a New Game

1. Create game template in Python
2. Add to database via `init_db()` in app.py
3. Create game engine in `static/js/games/`
4. Add canvas rendering logic

### Project Structure

```
python-games/
├── app.py                 # Flask backend
├── requirements.txt       # Dependencies
├── templates/
│   ├── index.html        # Game selection
│   └── game.html         # Code editor + game
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── games/        # Game-specific JS
└── instance/
    └── python_games.db   # SQLite database
```

## Tips for Teaching

1. **Start Simple**: Let them change one variable first (speed)
2. **Guided Exploration**: "What happens if you change this?"
3. **Use History**: Show them how their code evolved
4. **Celebrate Bugs**: They're learning opportunities
5. **Version Control**: Teach them to save before big changes
6. **Read Error Messages**: Help them understand Python errors
7. **Follow the Progression**: Snake → Pong → Space Invaders → Maze → Tetris
8. **Read [GAME_PROGRESSION.md](GAME_PROGRESSION.md)**: Detailed week-by-week guide

## Chromebook Compatibility

This app is designed for Chromebooks:
- Web-based (no installation needed)
- Pyodide works in Chrome browser
- Touch-friendly interface
- Auto-save prevents data loss

## Safety & Privacy

- No external code execution
- Python runs in browser sandbox
- No internet required after initial load
- Data stored locally on your server
- No tracking or analytics

## 📊 Project Stats

- **Lines of Code**: 1,500+
- **Games**: 5 complete templates
- **Documentation**: 8 comprehensive guides
- **Tests**: 27 automated tests
- **Learning Timeline**: 19 weeks (5 months)
- **Target Age**: 9-11 years old
- **Cost**: $0 (free tier Replit)

## 📚 Complete Documentation

| Document | Purpose | For Whom |
|----------|---------|----------|
| [README.md](README.md) | Project overview | Everyone |
| [QUICKSTART.md](QUICKSTART.md) | 5-minute setup | Parents/Teachers |
| [REPLIT_SETUP.md](REPLIT_SETUP.md) | Replit deployment | Deployers |
| [GAME_PROGRESSION.md](GAME_PROGRESSION.md) | 19-week learning path | Learners/Parents |
| [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) | Pre-flight checklist | Deployers |
| [REPLIT_OPTIMIZATIONS.md](REPLIT_OPTIMIZATIONS.md) | Technical details | Developers |
| [TESTING.md](TESTING.md) | Test suite guide | Developers |
| [SUMMARY.md](SUMMARY.md) | Complete overview | Everyone |

## 🛠️ Admin Tools

Monitor and manage the learning environment:

```bash
# Show database statistics
python admin_utils.py stats

# List all users
python admin_utils.py list-users

# Show user's save history
python admin_utils.py user-history "John"

# Get backup information
python admin_utils.py backup-info

# Create new user
python admin_utils.py create-user "Alice"

# Delete user (with confirmation)
python admin_utils.py delete-user "Bob"
```

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Install test dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=app --cov-report=term-missing

# Or use the test runner
./run_tests.sh
```

**Test Coverage**: Models, API endpoints, version control, admin utilities

See [TESTING.md](TESTING.md) for detailed testing guide.

## 🎓 Learning Outcomes

After completing all 5 games, your child will:

### Programming Skills
- ✅ Read and understand Python code
- ✅ Modify existing programs confidently
- ✅ Debug basic errors independently
- ✅ Use classes and objects
- ✅ Work with lists and 2D arrays
- ✅ Understand game loops and state
- ✅ Create simple programs from scratch

### Software Engineering Concepts
- ✅ Version control (saves, checkpoints, restore)
- ✅ Incremental development
- ✅ Code organization
- ✅ Testing through experimentation
- ✅ Reading error messages
- ✅ Planning before coding

### Problem-Solving Skills
- ✅ Breaking problems into smaller steps
- ✅ Logical thinking
- ✅ Pattern recognition
- ✅ Persistence through challenges
- ✅ Creative expression

## 💾 Data Management

### Storage Requirements

**Per Save**: ~5 KB
**Example Usage**: 2 kids × 30 saves/day × 30 days = 9 MB/month
**Replit Free Tier**: 500 MB = ~55 months capacity

### Backup Strategy

#### Weekly Backup (Recommended)
1. Navigate to `instance/` folder in Replit
2. Download `python_games.db`
3. Save with date: `python_games_2026-01-31.db`

#### Restore from Backup
1. Stop the app
2. Upload backup file to `instance/python_games.db`
3. Restart the app

## 🔧 Troubleshooting

### Common Issues

**"Repl won't start"**
- Check Console tab for errors
- Verify all files are present
- Try Stop → Run again

**"Can't save code"**
- Verify user is selected
- Check internet connection
- Check browser console (F12)

**"Python won't load"**
- Wait 10-15 seconds (first load)
- Check browser console
- Try refreshing page

**"Lost my code"**
- Click "📜 History"
- Find last save
- Click "Restore This"

### Getting Help

1. Check documentation files
2. Run `python admin_utils.py stats` for diagnostics
3. Review browser console for JavaScript errors
4. Check Replit console for Python errors
5. Verify `.env` file is configured (for local setup)

## 🌟 Future Enhancements (Optional)

### Phase 1: Game Rendering
- [ ] Canvas-based game visualization
- [ ] Keyboard controls
- [ ] Sound effects

### Phase 2: Tutorial System
- [ ] Step-by-step guided tutorials
- [ ] Progressive hints
- [ ] Achievement badges
- [ ] Progress tracking dashboard

### Phase 3: Social Features
- [ ] Share code between users
- [ ] Export games as HTML
- [ ] Multiplayer games
- [ ] Code challenges

### Phase 4: Advanced Features
- [ ] Visual block coding mode
- [ ] More games (Breakout, Flappy Bird, etc.)
- [ ] Custom game builder
- [ ] Parent/teacher dashboard

## 📝 Contributing

This is a family learning project, but suggestions are welcome:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

MIT License - Free for personal and educational use

You are free to:
- ✅ Use commercially
- ✅ Modify
- ✅ Distribute
- ✅ Use privately

See [LICENSE](LICENSE) for full details.

## 🙏 Acknowledgments

- **Pyodide Team** - Python in the browser
- **Flask Team** - Web framework
- **CodeMirror** - Code editor
- **Replit** - Free hosting platform

## 📞 Support

### For Setup Issues
- Review [QUICKSTART.md](QUICKSTART.md)
- Check [REPLIT_SETUP.md](REPLIT_SETUP.md)
- Verify environment configuration

### For Learning Questions
- Follow [GAME_PROGRESSION.md](GAME_PROGRESSION.md)
- Start with easiest game (Snake)
- Use checkpoints before experiments
- Review version history together

### For Technical Issues
- Check [TESTING.md](TESTING.md)
- Review [REPLIT_OPTIMIZATIONS.md](REPLIT_OPTIMIZATIONS.md)
- Check browser console
- Review application logs

## 🎯 Success Metrics

Your child is learning successfully if they:
- [ ] Ask "what if" questions
- [ ] Experiment without fear
- [ ] Read error messages
- [ ] Use checkpoints regularly
- [ ] Explain their changes
- [ ] Debug independently
- [ ] Have fun coding!

---

## Quick Links

- 🚀 [Get Started in 5 Minutes](QUICKSTART.md)
- 📖 [Learning Path (19 weeks)](GAME_PROGRESSION.md)
- 🔧 [Deploy to Replit](REPLIT_SETUP.md)
- ✅ [Deployment Checklist](DEPLOYMENT_CHECKLIST.md)
- 📊 [Complete Project Details](SUMMARY.md)
- 🧪 [Testing Guide](TESTING.md)

---

**Version**: 1.0.0
**Last Updated**: 2026-01-31
**Python**: 3.11+
**Flask**: 3.0.0
**Built with ❤️ for young coders learning Python**

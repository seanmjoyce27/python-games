# Python Game Builder for Kids

A web-based Python learning environment designed for kids to learn programming by creating and modifying games. Features a code editor, real-time game preview, and version control to teach repository concepts.

**Optimized for Replit hosting!** See [REPLIT_SETUP.md](REPLIT_SETUP.md) for deployment.

## Features

- **Hybrid Architecture**: Python runs in the browser (Pyodide) for safety and speed
- **Unlimited Version History**: All saves preserved forever with pagination (optimized for Replit)
- **Auto-save**: Code automatically saves every 30 seconds
- **Checkpoint System**: Manual saves with optional notes
- **Multi-user**: Support for multiple learners with separate progress tracking
- **Game-based Learning**: Start with Snake, progress to more complex games
- **Replit Ready**: One-click deployment with persistent storage

## Quick Start

### Deploy on Replit (Recommended)

1. Import this repo to Replit
2. Click "Run"
3. Share the URL with your kids!

See [REPLIT_SETUP.md](REPLIT_SETUP.md) for detailed instructions.

### Run Locally

#### 1. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 3. Run the Application

```bash
python app.py
```

The app will:
- Initialize the database in `instance/` folder
- Create the Snake game template
- Start the server at http://localhost:5000

#### 4. Access the App

Open your browser and go to:
```
http://localhost:5000
```

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
- Keeps last 25 versions

### Checkpoint Saves
- Manual save with optional note
- Marked with 📌 in history
- Great for "working version before trying something new"

### History View
- See all 25 recent versions
- View any previous version
- See what changed with diff view
- Restore any old version

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

## Future Enhancements

- [ ] More games (Pong, Space Invaders, Maze)
- [ ] Tutorial system with progressive steps
- [ ] Achievements and badges
- [ ] Code sharing between users
- [ ] Export games as standalone HTML
- [ ] Multiplayer games
- [ ] Visual block coding mode for beginners
- [ ] Parent dashboard with progress tracking

## License

MIT License - Free for personal and educational use

## Support

Questions or issues? This is a learning project for your family!
Modify and extend it as you like.

---

**Built with ❤️ for young coders**

# Quick Start Guide

Get your kids coding in 5 minutes! 🚀

---

## For Replit (Recommended for Chromebooks)

### 1. Deploy to Replit
```
1. Go to https://replit.com
2. Click "Create Repl"
3. Choose "Import from GitHub"
4. Paste your repository URL
5. Click "Import from GitHub"
```

### 2. Run the App
```
Click the big green "Run" button at the top!
```

That's it! The app will:
- Install dependencies (including Gunicorn)
- Create database with 5 games
- Start Gunicorn production server
- Open in browser

### 3. Create User Accounts
```
1. Click "+ New Player"
2. Enter your son's name
3. Click "Create"
4. Repeat for second son
```

### 4. Start Coding!
```
1. Select a player
2. Click "Start Coding" on Snake Game
3. Change line 8: speed = 10
4. Click "▶ Run Code"
5. See what happens!
```

---

## For Local Setup (Mac/Windows/Linux)

### 1. Prerequisites
- Python 3.11 or higher
- PostgreSQL (for database)
- Terminal/Command Prompt

### 2. Setup (5 minutes)
```bash
# Clone or download this repo
cd python3-games

# Create virtual environment
python3 -m venv venv

# Create database (ensure postgres is running)
createdb python_games

# Activate it
source venv/bin/activate  # Mac/Linux
# OR
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### 3. Run
```bash
python3 app.py
```

Open your browser to: **http://localhost:8443**

---

## First Steps for Kids

### Day 1: Meet Snake 🐍
**Goal**: Change one thing

```python3
# Find this line (line 8):
self.speed = 5

# Try these:
self.speed = 10  # Faster!
self.speed = 2   # Slower
self.speed = 20  # Super fast!
```

**Learning**: Variables control behavior

---

### Day 2: Checkpoint Practice 💾
**Goal**: Learn to save progress

```
1. Make a change to speed
2. Click "💾 Save Checkpoint"
3. Type: "Made snake faster"
4. Click "📜 History"
5. See your save!
```

**Learning**: Version control saves your work

---

### Day 3: Experimentation 🧪
**Goal**: Break things (safely!)

```
1. Save a checkpoint first!
2. Change lots of things
3. Run the code
4. Did it break?
5. Click "📜 History" → "Restore This"
```

**Learning**: You can always go back

---

### Week 1 Challenge 🏆
**Goal**: Make snake start longer

```python3
# Find this line (line 8):
self.segments = [(10, 10)]

# Make it longer:
self.segments = [(10, 10), (9, 10), (8, 10)]
```

**Learning**: Lists hold multiple values

---

## Parent Tips

### ✅ Do This
- Let them make mistakes
- Ask "what do you think will happen?"
- Celebrate when code breaks (learning!)
- Review version history together
- Start with one game at a time

### ❌ Don't Do This
- Rush through games
- Fix their code for them
- Skip the simpler games
- Forget to save checkpoints
- Worry about "perfect" code

---

## Troubleshooting

### **"Repl won't start"**
- Check Console tab for errors
- Try: Stop and Run again
- Make sure all files uploaded

### **"Can't save code"**
- Check you selected a user
- Check internet connection
- Look at browser console (F12)

### **"Python won't load"**
- Wait 10-15 seconds first time
- Check browser console for errors
- Try refreshing page

### **"Lost my code"**
- Click "📜 History"
- Find last save
- Click "Restore This"

---

## Game Progression

### Recommended Order

1. **Snake** (1-2 weeks)
   - Start here
   - Learn basics
   - Build confidence

2. **Pong** (2-3 weeks)
   - Two-player fun
   - More complexity
   - Collision detection

3. **Space Invaders** (3-4 weeks)
   - Lots of objects
   - Arrays and loops
   - Complex interactions

4. **Maze** (3-4 weeks)
   - Level design
   - 2D arrays
   - Pathfinding

5. **Tetris** (4-6 weeks)
   - Most advanced
   - Matrix operations
   - Complete game

**Total**: ~19 weeks (5 months)

---

## Learning Milestones

### ✅ After Snake
- Can change variables
- Understands classes
- Knows what methods do

### ✅ After Pong
- Works with multiple objects
- Understands collision
- Can add simple features

### ✅ After Space Invaders
- Uses lists effectively
- Understands loops
- Manages game state

### ✅ After Maze
- Works with 2D arrays
- Designs levels
- Implements algorithms

### ✅ After Tetris
- Handles complex state
- Understands algorithms
- Can build games from scratch!

---

## Getting Help

### Documentation
- **README.md** - Project overview
- **GAME_PROGRESSION.md** - Detailed learning path
- **REPLIT_SETUP.md** - Replit guide
- **SUMMARY.md** - Complete project details

### Admin Tools
```bash
# Show stats
python3 admin_utils.py stats

# List users
python3 admin_utils.py list-users

# Show user's progress
python3 admin_utils.py user-history "John"
```

### Common Questions

**Q: How long for each game?**
A: Varies! Snake: 1-2 weeks, Tetris: 4-6 weeks

**Q: My kid is stuck, what do I do?**
A: Read error messages together, use version history

**Q: Can they skip games?**
A: Better not to - each builds on previous

**Q: How do I backup their work?**
A: Download `instance/python_games.db` file

---

## Next Session Template

Use this each time they code:

### Before Coding
1. ✅ Select your user
2. ✅ Choose your game
3. ✅ Load your last save

### During Coding
1. ✅ Read the TODOs
2. ✅ Change ONE thing
3. ✅ Run the code
4. ✅ See what happens
5. ✅ Save checkpoint if it works!

### After Coding
1. ✅ Save final checkpoint
2. ✅ Write a message about what you learned
3. ✅ Show parent what you did!

---

## Success Indicators

Your child is learning if they:
- [ ] Ask "what if" questions
- [ ] Want to try new ideas
- [ ] Read error messages
- [ ] Use checkpoints before experiments
- [ ] Explain their changes
- [ ] Debug their own code
- [ ] Have fun!

---

## Resources

### Keep Learning
- Python documentation: python3.org
- PyGame for games: pygame.org
- Code challenges: codingame.com
- Visual Python: scratch.mit.edu (younger)

### Communities
- r/learnpython3 (Reddit)
- Python Discord
- Local CoderDojo clubs
- School coding clubs

---

## Weekly Schedule Suggestion

### Light (2-3 hours/week)
- Monday: 30 min
- Wednesday: 30 min
- Saturday: 1 hour

### Regular (4-5 hours/week)
- After school: 30-45 min (3 days)
- Weekend: 2 hours

### Intensive (6+ hours/week)
- Daily: 45 min
- Weekend: 2-3 hours

**Recommended**: Start light, increase as they get excited!

---

## Celebration Ideas

### Mini Milestones
- Changed first variable → Sticker!
- First checkpoint save → High five!
- Fixed first bug → Ice cream!
- Completed first game → Photo!

### Major Milestones
- Completed 3 games → Pizza party!
- All 5 games done → Certificate!
- Built custom game → Share with family!

---

**Ready to start? Click Run and let's code!** 🎮

---

*For detailed information, see [GAME_PROGRESSION.md](../guides/GAME_PROGRESSION.md)*
*For technical setup, see [REPLIT_SETUP.md](REPLIT_SETUP.md)*
*For project details, see [SUMMARY.md](../reference/SUMMARY.md)*

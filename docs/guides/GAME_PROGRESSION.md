# Game Progression Guide

A structured learning path through all 5 games, designed for kids aged 9-11.

## Learning Philosophy

Each game teaches progressively more complex programming concepts:
1. **Variables & Simple Logic** → Snake
2. **Multiple Objects & Collision** → Pong
3. **Lists & Many Objects** → Space Invaders
4. **2D Arrays & Algorithms** → Maze
5. **Complex State Management** → Tetris

---

## Game 1: Snake 🐍
**Difficulty**: ⭐ Beginner
**Time**: 1-2 weeks

### Concepts Learned
- Classes and objects
- Methods and functions
- Variables (x, y, speed)
- Lists (segments)
- If/elif statements
- Basic movement logic

### Progression Steps

#### Week 1: Getting Comfortable
1. **Change the speed** (line 8)
   - Try 3 (slow), 10 (fast), 20 (super fast!)
   - What feels best?

2. **Change starting position** (lines 6-7)
   - Put snake in different corners
   - Try x=0, y=0 (top left)

3. **Make snake longer at start** (line 8)
   - Modify `self.segments` list
   - Add more tuples: `[(10,10), (9,10), (8,10)]`

#### Week 2: New Features
4. **Add a score variable**
   ```python
   self.score = 0
   ```

5. **Count food eaten**
   - Increment score in `grow()` method

6. **Add boundaries**
   - Check if x < 0 or x > 20
   - Game over if hit wall

### Success Criteria
- [ ] Changed at least 3 variables
- [ ] Made snake longer
- [ ] Added score tracking
- [ ] Understands how segments list works

---

## Game 2: Pong 🏓
**Difficulty**: ⭐⭐ Intermediate
**Time**: 2-3 weeks

### Concepts Learned
- Multiple objects (2 paddles, 1 ball)
- Object interaction (collision detection)
- Coordinate systems
- Speed and acceleration
- Game state (scores)

### Progression Steps

#### Week 1: Modify Basics
1. **Change paddle size** (lines 7-8)
   - Make them bigger: `height = 100`
   - Make them smaller: `height = 30`

2. **Adjust ball speed** (lines 21-22)
   - Slower: `speed_x = 3`
   - Faster: `speed_x = 8`

3. **Change winning score**
   - Find where score is checked
   - Change from 5 to 10

#### Week 2: Add Features
4. **Different paddle speeds**
   - Make player 2 faster
   - Or slower for handicap

5. **Ball speed increases**
   - Already in template! (line 36)
   - Try changing 1.05 to 1.1 (faster increase)

6. **Add sound effects** (in comments)
   - Print "PONG!" when ball hits paddle
   - Print "SCORE!" when point scored

#### Week 3: Advanced
7. **Power-ups**
   ```python
   class PowerUp:
       def __init__(self):
           self.type = "speed"  # or "size"
           self.active = False
   ```

8. **Angle based on hit location**
   - If ball hits top of paddle, bounce up more
   - If hits bottom, bounce down more

### Success Criteria
- [ ] Modified both paddles and ball
- [ ] Changed game rules (winning score)
- [ ] Added at least one new feature
- [ ] Understands collision detection

---

## Game 3: Space Invaders 👾
**Difficulty**: ⭐⭐⭐ Intermediate-Advanced
**Time**: 3-4 weeks

### Concepts Learned
- Lists of objects (many aliens, bullets)
- Nested loops (creating alien grid)
- Object lifetime (bullets disappear)
- Game over conditions
- Complex collision detection

### Progression Steps

#### Week 1: Understanding the Code
1. **Change alien grid size** (line 46)
   - More rows: `range(7)`
   - More columns: `range(10)`

2. **Adjust alien spacing** (lines 48-49)
   - Closer together: `col * 50`
   - Further apart: `col * 70`

3. **Modify player lives** (line 13)
   - Easy mode: `self.lives = 5`
   - Hard mode: `self.lives = 1`

#### Week 2: Enhance Gameplay
4. **Different alien types**
   ```python
   if row < 2:
       alien.points = 20  # Top rows worth more
   ```

5. **Faster aliens**
   - Change `speed = 2` to `speed = 5`
   - Make them speed up over time

6. **Bullet upgrades**
   - Shoot 2 bullets at once
   - Faster bullets: `speed = 15`

#### Week 3-4: Advanced Features
7. **Alien shooting back**
   ```python
   class AlienBullet:
       def __init__(self, x, y):
           self.speed = -5  # Goes down
   ```

8. **Shields/Barriers**
   - Add blocks player can hide behind
   - They break after hits

9. **Boss alien**
   - Bigger alien at top
   - Takes multiple hits
   - Worth lots of points

### Success Criteria
- [ ] Modified alien grid
- [ ] Added new alien behaviors
- [ ] Implemented power-ups or shields
- [ ] Understands list management

---

## Game 4: Maze Adventure 🗺️
**Difficulty**: ⭐⭐⭐ Advanced
**Time**: 3-4 weeks

### Concepts Learned
- 2D arrays (grid representation)
- Pathfinding concepts
- Collision with environment
- Level design
- Win conditions

### Progression Steps

#### Week 1: Design Mazes
1. **Understand the grid** (lines 17-27)
   - 0 = walkable path
   - 1 = wall
   - 2 = exit

2. **Create custom maze**
   - Draw on paper first
   - Translate to numbers
   - Test if solvable!

3. **Make bigger maze**
   - Expand to 15x15
   - Add more rooms

#### Week 2: Add Game Elements
4. **Collectible treasures**
   ```python
   # 3 = treasure
   if maze[player.y][player.x] == 3:
       score += 10
       maze[player.y][player.x] = 0  # Remove treasure
   ```

5. **Keys and doors**
   - 4 = locked door
   - 5 = key
   - Must collect key before exit

6. **Track best time**
   - Import time module
   - Record fastest solve

#### Week 3-4: Advanced
7. **Moving enemies**
   ```python
   class Enemy:
       def __init__(self, x, y):
           self.x = x
           self.y = y
           self.direction = "right"
   ```

8. **Multiple levels**
   - Array of different maze grids
   - Progress to next level at exit

9. **Fog of war**
   - Only show cells near player
   - Reveals as you explore

### Success Criteria
- [ ] Created at least 2 custom mazes
- [ ] Added collectibles
- [ ] Implemented enemies or obstacles
- [ ] Understands 2D array indexing

---

## Game 5: Tetris 🎮
**Difficulty**: ⭐⭐⭐⭐ Expert
**Time**: 4-6 weeks

### Concepts Learned
- Complex state management
- Matrix rotation
- Grid manipulation
- Line clearing algorithm
- Game loops and timing

### Progression Steps

#### Week 1-2: Understanding Tetris
1. **Study the pieces** (lines 54-61)
   - See how shapes are 2D arrays
   - Understand rotation

2. **Modify drop speed** (line 68)
   - Slower: `drop_speed = 1000`
   - Faster: `drop_speed = 200`

3. **Change scoring** (line 47)
   - More points per line
   - Bonus for multiple lines

#### Week 3-4: Add Features
4. **Next piece preview**
   ```python
   import random
   next_piece = random.choice(SHAPES)
   # Show it to player
   ```

5. **Hold piece feature**
   - Store current piece
   - Swap with held piece

6. **Ghost piece**
   - Show where piece will land
   - Draw transparent version

#### Week 5-6: Polish
7. **Progressive difficulty**
   ```python
   if score > 1000:
       drop_speed = 300  # Faster!
   ```

8. **Piece colors**
   - Different color per shape
   - Rainbow mode!

9. **Combo system**
   - Clear 2 lines in a row = 2x points
   - Clear 4 lines (Tetris!) = 4x points

### Success Criteria
- [ ] Fully understands piece rotation
- [ ] Implemented at least 2 new features
- [ ] Can explain line-clearing algorithm
- [ ] Built a complete game variation

---

## Learning Milestones

### After Snake (1-2 weeks)
✅ Understands basic Python syntax
✅ Can modify variables confidently
✅ Knows what classes and methods are

### After Pong (3-5 weeks)
✅ Works with multiple objects
✅ Understands collision detection
✅ Can add simple game mechanics

### After Space Invaders (6-9 weeks)
✅ Manages lists of objects
✅ Uses loops effectively
✅ Implements game states

### After Maze (9-13 weeks)
✅ Works with 2D arrays
✅ Designs levels/content
✅ Implements complex logic

### After Tetris (13-19 weeks)
✅ Handles complex state
✅ Understands algorithms
✅ Can build games from scratch!

---

## Teaching Tips

### For Parents

1. **Start Slow**
   - One variable change at a time
   - Celebrate small wins
   - Don't rush to next game

2. **Let Them Break Things**
   - Errors are learning opportunities
   - Version control lets them experiment safely
   - "What happens if...?" is great!

3. **Ask Questions**
   - "Why did that change the game?"
   - "Can you make it do X?"
   - "What would make this more fun?"

4. **Use Checkpoints**
   - Save before big changes
   - Name checkpoints clearly
   - Review history together

5. **Pair Programming**
   - Take turns typing
   - One person codes, other guides
   - Switch roles

### For Kids

1. **Read the TODOs**
   - They're hints for what to try
   - Start with easiest ones

2. **Change One Thing**
   - See what happens
   - If it breaks, restore version

3. **Keep Notes**
   - What did you learn?
   - Cool ideas for later?
   - Draw your game ideas!

4. **Share Your Work**
   - Show family your creations
   - Explain what you changed
   - Let them play!

---

## Beyond These Games

Once they've mastered all 5:

### Build Your Own
- Combine ideas from different games
- Create something totally new
- Design multiple levels

### Learn More Python
- Functions and parameters
- Classes inheritance
- File reading/writing

### New Game Ideas
- Breakout/Arkanoid
- Flappy Bird
- Platformer
- Racing game
- RPG adventure

---

## Progress Tracking

| Game | Started | Completed | Favorite Feature Added |
|------|---------|-----------|------------------------|
| Snake | _____ | _____ | _________________ |
| Pong | _____ | _____ | _________________ |
| Space Invaders | _____ | _____ | _________________ |
| Maze | _____ | _____ | _________________ |
| Tetris | _____ | _____ | _________________ |

**Total Learning Time**: ~19 weeks (5 months)
**Skill Level**: Beginner → Intermediate Python Programmer!

---

**Remember**: The goal isn't to rush through all games. It's to understand each one deeply and have fun building! 🎮✨

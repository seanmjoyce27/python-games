# 📚 Python Game Builder Documentation

Complete documentation for the Python Game Builder learning platform.

## 🚀 Getting Started

- **[Quick Start Guide](QUICKSTART.md)** - Get up and running in 5 minutes
- **[Avatar System](AVATAR_SYSTEM.md)** - How the 15 coding avatars work
- **[Mission Leaderboard](LEADERBOARD.md)** - Competitive ranking system
- **[Mission UX Improvements](MISSION_UX_IMPROVEMENTS.md)** - Streamlined mission workflow
- **[Syntax Error Banner](SYNTAX_ERROR_BANNER.md)** - Kid-friendly error messages
- **[Admin Panel](ADMIN.md)** - Managing students and monitoring progress

## 📖 Documentation Overview

### For Parents/Teachers

1. **[Quick Start Guide](QUICKSTART.md)**
   - Installation instructions
   - Starting the server
   - Basic usage

2. **[Admin Panel Guide](ADMIN.md)**
   - Accessing the admin dashboard
   - Managing coders
   - Viewing statistics
   - Default password info

3. **[Avatar System](AVATAR_SYSTEM.md)**
   - How kids choose avatars
   - List of all 15 avatars
   - How the system works

4. **[Mission Leaderboard](LEADERBOARD.md)**
   - How ranking works
   - Medal system for top 3
   - Motivating friendly competition

5. **[Mission UX Improvements](MISSION_UX_IMPROVEMENTS.md)**
   - Streamlined workflow
   - Active mission banner
   - One-click validation

### For Developers

- **Port Configuration**: App runs on port 8443 by default
- **Database**: SQLite stored in project root (Replit) or `instance/` (local)
- **Environment**: Configure via `.env` file

## 🎮 Features

### 5 Complete Games
- **Snake** - Classic snake game
- **Pong** - 2-player paddle game
- **Tetris** - Block stacking puzzle
- **Space Invaders** - Alien shooter
- **Maze Adventure** - Navigate mazes

### Learning Features
- **Code Editor** with syntax highlighting
- **Live Preview** - See changes immediately
- **Version History** - Unlimited auto-saves
- **Missions System** - Guided learning objectives
- **Mission Leaderboard** - Competitive rankings with medals
- **Real-time Feedback** - Instant code validation

### Platform Features
- **15 Kid-Friendly Avatars** - No usernames needed
- **Persistent Progress** - All work is saved
- **Admin Dashboard** - Monitor student progress
- **Mobile Friendly** - Works on Chromebooks

## 🔑 Quick Reference

### Default Credentials
- **Admin URL**: `http://localhost:8443/admin`
- **Admin Password**: `python123` (changeable in `.env`)

### Port Configuration
- **Default Port**: `8443`
- **Change in**: `.env` file or `PORT` environment variable

### Avatar System
- **Total Avatars**: 15
- **Selection Method**: Visual grid (no typing)
- **Uniqueness**: Each avatar can only be used once

## 📁 File Structure

```
python-games/
├── app.py                 # Main Flask application
├── templates/            # HTML templates
│   ├── index.html        # Avatar selection
│   ├── game.html         # Code editor + game
│   └── admin.html        # Admin dashboard
├── static/
│   └── css/
│       └── style.css     # All styling
├── docs/                 # Documentation (you are here)
│   ├── README.md         # This file
│   ├── QUICKSTART.md     # Getting started
│   ├── ADMIN.md          # Admin guide
│   ├── AVATAR_SYSTEM.md  # Avatar details
│   ├── LEADERBOARD.md    # Leaderboard system
│   └── MISSION_UX_IMPROVEMENTS.md  # Mission workflow
├── instance/             # Database (local dev)
│   └── python_games.db
└── .env                  # Configuration

```

## 🆘 Support

### Common Issues

**Port 8443 in use?**
- Change `PORT` in `.env` file

**Database not persisting on Replit?**
- Database now stores in project root on Replit (fixed)

**Admin password not working?**
- Default is `python123`
- Check `.env` file for `ADMIN_PASSWORD`

**Avatar already taken?**
- Each avatar can only be used once
- Delete from admin panel to free it up

## 🎯 Perfect For

- **Ages**: 9-14
- **Platform**: Chromebooks, laptops, desktops
- **Learning**: Python basics through game development
- **Environment**: Home or classroom

---

Built with ❤️ for young coders learning Python

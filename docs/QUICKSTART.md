# Quick Start Guide

## Starting the Application

1. **Install dependencies** (if needed):
   ```bash
   pip install flask flask-sqlalchemy flask-cors python-dotenv
   ```

2. **Start the server**:
   ```bash
   python app.py
   ```

3. **Access the application**:
   - Main app: `http://localhost:8443`
   - Admin panel: `http://localhost:8443/admin`

## Admin Access

### Default Credentials
- **URL**: `http://localhost:8443/admin`
- **Password**: `python123`

### Change Password
Edit `.env` file:
```
ADMIN_PASSWORD=your_new_password
```

## Port Configuration

The app runs on port **8443** by default (configured in `.env`).

To change the port, edit `.env`:
```
PORT=5000
```

Or set environment variable:
```bash
export PORT=5000
python app.py
```

## For Your Sons

1. Open the app: `http://localhost:8443`
2. Click "+ New Player" and enter their name
3. Choose a game (Snake, Pong, Tetris, Space Invaders, or Maze)
4. Start coding and learning Python!

## Admin Features

As an admin, you can:
- ✅ Create and delete student accounts
- ✅ View all code saves and progress
- ✅ Monitor mission completion
- ✅ See system statistics

Access the admin panel at `http://localhost:8443/admin` with password `python123`.

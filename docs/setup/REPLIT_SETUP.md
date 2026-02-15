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
- `gunicorn.conf.py` - Production server configuration
- Automatic port binding to `0.0.0.0:8443`

### Production Server (Gunicorn)

The deployment uses **Gunicorn**, a production-grade WSGI server:
- 2 worker processes for handling concurrent requests
- 30-second timeout for health checks
- Automatic logging to stdout/stderr

### Environment Variables (Secrets)

> [!IMPORTANT]
> Do **NOT** upload your `.env` file to Replit. It is not secure.
> Instead, use the **Secrets** tool (padlock icon in the sidebar).

You can set these in Replit's "Secrets" tab:

- `SECRET_KEY` - Flask secret key (auto-generated if not set)
- `FLASK_ENV` - Set to `production` for deployment
- `PORT` - Port number (defaults to 8443)
- `DATABASE_URL` - Connection string for PostgreSQL (Auto-set by Replit Deployments)

### Provisioning PostgreSQL in Replit

> [!IMPORTANT]
> A PostgreSQL database is **required**. The app will not work without one.

#### Step 1: Create the Database

1. In the bottom-left of your Repl, click **"Tools"**
2. Select **"Database"** from the tools list
3. Replit will provision a **Development Database** (PostgreSQL)
4. You'll see the database panel showing storage usage (e.g., `29.1MB / 10GB`)

The database is now created and available to your Repl.

#### Step 2: Set the Connection String

1. In the database panel, locate and copy the **connection string** (starts with `postgresql://`)
2. Click **"Secrets"** in the Tools menu (or the padlock icon in the sidebar)
3. Click **"+ New Secret"**:
   - **Key**: `DATABASE_URL`
   - **Value**: Paste the connection string you copied
4. **Stop and restart** your Repl for the secret to take effect

> [!TIP]
> If Replit automatically injects the database URL as an environment variable, you may not need to add it manually. Check by running `echo $DATABASE_URL` in the Shell tab.

#### Step 3: Verify the Connection

In the **Shell** tab, run:

```bash
python3 -c "
from app import app, db
with app.app_context():
    db.create_all()
    print('✅ Database connected successfully!')
"
```

#### For Deployments

When deploying via **"Republish"** or **"Deploy"** in the top-right:
- Replit carries over your Secrets (including `DATABASE_URL`) to the deployed app
- The same Development Database is used in both workspace and deployments
- Your data persists across deploys

## ▶️ Running the App

Just click the "Run" button in Replit! The app will:
1. Install dependencies from `requirements.txt` (including Gunicorn)
2. Connect to PostgreSQL and initialize the database
3. Seed game templates
4. Start the Gunicorn production server

The app will be accessible at your Replit URL (e.g., `https://your-repl.your-username.repl.co`)

## 💾 Data Persistence

### Database Storage
- Uses PostgreSQL (via `DATABASE_URL` environment variable)
  - ✅ Data persists across deployments
  - ✅ No data loss when pushing new code

### Backup Your Data

To backup your students' work:

1. Use `pg_dump` to export your PostgreSQL database
2. Store the SQL file safely

To restore:
1. Use `psql` to import the SQL file

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
3. **Database**: Ensure `DATABASE_URL` is set in Replit Secrets

## 📊 Monitoring Usage

### Database Stats

Check database stats in the Shell:
```bash
python3 scripts/admin_utils.py stats
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

1. Check that all files are uploaded (including `gunicorn.conf.py`)
2. Verify `.replit` file exists
3. Try: Tools → Shell, then run `gunicorn app:app -c gunicorn.conf.py` manually

### Database Connection Error

1. Verify `DATABASE_URL` is set correctly in Secrets
2. Ensure the PostgreSQL database is accessible
3. Stop and restart the Repl

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
- Check logs in the Console tab (Gunicorn logs to stdout)
- Use Shell to debug: `gunicorn app:app -c gunicorn.conf.py`

---

**Ready to teach Python? Just click Run!** 🎮🐍

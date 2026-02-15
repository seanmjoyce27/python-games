# Replit Optimizations Summary

This document outlines all optimizations made for Replit deployment.

## Changes from Original Design

### 1. Unlimited Save History ✅

**Original**: Limited to 25 saves per user per game
**Replit**: Unlimited saves with pagination

**Changes Made**:
- `app.py` - Removed 25-save limit in `save_code()` endpoint
- `app.py` - Added pagination to `get_history()` endpoint
- `game.html` - Added "Load More" functionality
- `style.css` - Added pagination UI styles

**Benefits**:
- Complete learning history preserved
- Track progress over months/years
- No data loss from overwrites

### 2. Database Configuration ✅

**Changes Made**:
- Database path: `sqlite:///instance/python_games.db`
- Auto-create `instance/` folder
- Persistent storage across Repl restarts

**Code**:
```python3
# 1. Use PostgreSQL if available (Replit Deployments)
# 2. Fallback to SQLite (Replit Workspace / Local)
database_url = os.environ.get('DATABASE_URL')

if database_url and database_url.startswith('postgres'):
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
else:
    database_url = f'sqlite:///{db_path}'

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
```

### 3. Production Server (Gunicorn) ✅

**Original**: Flask development server
**Replit**: Gunicorn production WSGI server

**Benefits**:
- Passes Replit health checks reliably
- Multi-worker support for concurrent requests
- 30-second timeout for health check compliance
- Production-ready logging

### 4. Configuration Files ✅

**New Files Created**:

1. `.replit` - Replit run configuration
   ```
   [deployment]
   run = ["sh", "-c", "gunicorn app:app -c gunicorn.conf.py"]
   ```

2. `gunicorn.conf.py` - Production server configuration
   ```python3
   bind = "0.0.0.0:8443"
   workers = 2
   timeout = 30
   ```

2. `replit.nix` - Python environment
   ```nix
   { pkgs }: {
     deps = [
       pkgs.python311
       pkgs.python311Packages.pip
     ];
   }
   ```

3. `pyproject.toml` - Modern Python project metadata
4. `start.sh` - Startup script with checks
5. `.env.example` - Environment variable template

### 5. Documentation ✅

**New Documents**:
- `REPLIT_SETUP.md` - Deployment guide
- `DEPLOYMENT_CHECKLIST.md` - Pre-flight checklist
- `REPLIT_OPTIMIZATIONS.md` - This file

**Updated**:
- `README.md` - Added Replit sections
- `.gitignore` - Added Replit-specific ignores

### 6. Admin Utilities ✅

**New**: `admin_utils.py` - Command-line tools

**Commands**:
- `stats` - Database statistics
- `list-users` - List all users
- `user-history USERNAME` - Show user's save history
- `backup-info` - Backup instructions
- `create-user USERNAME` - Create new user
- `delete-user USERNAME` - Delete user

**Usage in Replit**:
```bash
# In Shell tab
python3 admin_utils.py stats
```

## Performance Optimizations

### 1. Pagination

**Implementation**:
- Default: 50 versions per page
- Load more button for additional pages
- Total count displayed

**API Changes**:
```python3
# New parameters
{
    "limit": 50,
    "offset": 0
}

# Response includes
{
    "versions": [...],
    "total": 1234,
    "has_more": true
}
```

### 2. Database Efficiency

- Indexes on foreign keys
- Efficient queries with `.order_by()` and `.limit()`
- No unnecessary JOINs

### 3. Frontend Optimization

- Lazy loading of history
- Efficient event listeners
- No memory leaks in auto-save

## Storage Considerations

### Database Growth

**Estimate**: ~5 KB per save

**Example Growth**:
- 2 kids
- 1 game each
- 30 saves/day
- 30 days
= 2 × 1 × 30 × 30 × 5 KB = **9 MB/month**

**Replit Free Tier**: 500 MB storage
**Capacity**: ~55 months of saves

### Monitoring

```python3
# Check database size
python3 admin_utils.py backup-info
```

### Cleanup (if needed)

```sql
-- Delete auto-saves older than 6 months (keep checkpoints)
DELETE FROM code_version
WHERE is_checkpoint = 0
AND created_at < datetime('now', '-6 months');
```

## Environment Variables

### Required for Production

Set in Replit Secrets:

1. **SECRET_KEY** (Important!)
   ```python3
   import secrets
   print(secrets.token_hex(32))
   ```

2. **FLASK_ENV**
   ```
   production
   ```

### Optional

3. **PORT** - Default: 8443
4. **DATABASE_URL** - Default: sqlite:///instance/python_games.db

## Security Enhancements

1. ✅ Secret key from environment
2. ✅ Debug mode disabled in production
3. ✅ CORS properly configured
4. ✅ Database not in web root
5. ✅ No hardcoded credentials
6. ✅ Input validation on all endpoints

## Backup Strategy

### Manual Backup

1. Go to Files in Replit
2. Navigate to `instance/python_games.db`
3. Click three dots → Download

### Automated Backup (Advanced)

Add to cron job or scheduled task:
```bash
#!/bin/bash
DATE=$(date +%Y%m%d)
cp instance/python_games.db backups/python_games_$DATE.db
```

## Testing Checklist

- [x] App starts without errors
- [x] Database initializes
- [x] Users can be created
- [x] Code saves work
- [x] Auto-save works
- [x] Checkpoints work
- [x] History loads
- [x] Pagination works
- [x] Diff view works
- [x] Restore works
- [x] Multiple users isolated
- [x] Pyodide loads
- [x] Code editor works
- [x] Data persists across restarts

## Known Limitations

### Replit Free Tier

1. **Sleep after inactivity** - Use UptimeRobot to keep alive
2. **Storage limit** - 500 MB (sufficient for ~55 months)
3. **Concurrent users** - Limited for free tier
4. **Always-on** - Not available on free tier

### Solutions

- Upgrade to Replit Hacker plan for always-on
- Use external monitoring service
- Regular backups to prevent data loss

## Migration from Local

If you developed locally first:

```bash
# 1. Commit all changes
git add .
git commit -m "Ready for Replit"

# 2. Push to GitHub
git push origin main

# 3. Import to Replit from GitHub

# 4. Run in Replit
# Database will auto-initialize

# 5. Optional: Import existing database
# Upload instance/python_games.db to Replit
```

## Troubleshooting

### Repl Won't Start

1. Check `.replit` file exists
2. Verify `requirements.txt` is valid
3. Check Console for errors
4. Try: Shell → `gunicorn app:app -c gunicorn.conf.py`

### Database Not Persisting

1. Ensure `instance/` folder exists
2. Check file permissions
3. Verify database path in config
4. Check Replit storage limits

### Performance Issues

1. Check database size
2. Review number of saves
3. Test pagination
4. Monitor Repl CPU usage

### Import Errors

1. Verify all packages in `requirements.txt`
2. Check Python version (3.11+)
3. Try: Shell → `pip install -r requirements.txt`

## Future Optimizations

### Potential Improvements

1. **PostgreSQL**: For many concurrent users
2. **Redis**: For session management
3. **CDN**: For static assets
4. **Compression**: For save data
5. **Archive**: Move old saves to cold storage

### When to Upgrade

- More than 10 concurrent users
- Database > 400 MB
- Response times > 2 seconds
- Need always-on availability

## Support

### Replit Issues
- Status: https://status.replit.com
- Docs: https://docs.replit.com
- Community: https://ask.replit.com

### App Issues
- Check Console logs
- Run: `python3 admin_utils.py stats`
- Review error messages
- Test with fresh database

---

**Version**: 1.1.0 (Replit Optimized with Gunicorn)
**Last Updated**: 2026-01-31
**Python**: 3.11+
**Flask**: 3.0.0
**Gunicorn**: 21.2.0

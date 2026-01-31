# Deployment Checklist for Replit

Use this checklist when deploying to Replit.

## Pre-Deployment

- [ ] All code tested locally
- [ ] Database initializes correctly
- [ ] At least one user and game works
- [ ] Version history displays properly
- [ ] Auto-save working

## Replit Setup

### Initial Configuration

- [ ] Create new Repl or import from GitHub
- [ ] Verify `.replit` file is present
- [ ] Verify `replit.nix` file is present
- [ ] Check `requirements.txt` is complete

### Environment Variables

Set these in Replit Secrets (Tools → Secrets):

- [ ] `SECRET_KEY` - Generate a secure random key
  ```python
  import secrets
  secrets.token_hex(32)
  ```
- [ ] `FLASK_ENV` - Set to `production`
- [ ] `PORT` - Leave as default (8443) or customize

### First Run

- [ ] Click "Run" button
- [ ] Check Console for errors
- [ ] Verify database created in `instance/` folder
- [ ] Verify Snake game initialized
- [ ] Access the web preview

## Testing

### User Management

- [ ] Create first user (e.g., "TestKid1")
- [ ] Create second user (e.g., "TestKid2")
- [ ] Switch between users
- [ ] Verify separate progress

### Code Editor

- [ ] Code editor loads
- [ ] Syntax highlighting works
- [ ] Line numbers display
- [ ] Can type and edit code

### Game Functionality

- [ ] Load Snake game template
- [ ] Modify code (change speed)
- [ ] Run code (Pyodide loads)
- [ ] No console errors

### Version Control

- [ ] Auto-save works (wait 30 seconds)
- [ ] Manual checkpoint save works
- [ ] Add optional message to checkpoint
- [ ] View history modal opens
- [ ] See total save count
- [ ] Load more pagination works
- [ ] View older version
- [ ] See diff between versions
- [ ] Restore old version

## Performance Checks

- [ ] Page loads in under 3 seconds
- [ ] Pyodide loads in under 10 seconds
- [ ] History with 100+ saves loads smoothly
- [ ] Pagination loads additional saves
- [ ] No memory leaks (run for 10 minutes)

## Security Checks

- [ ] `SECRET_KEY` is set and not default
- [ ] `FLASK_ENV=production` (no debug mode)
- [ ] No sensitive data in code
- [ ] Database not exposed publicly
- [ ] CORS configured correctly

## User Experience

- [ ] Mobile responsive (test on phone)
- [ ] Chromebook compatible
- [ ] Works in Chrome browser
- [ ] Clear error messages
- [ ] Intuitive navigation

## Data Persistence

- [ ] Create test data
- [ ] Stop Repl
- [ ] Start Repl again
- [ ] Verify data persists
- [ ] Test database backup/restore

## Documentation

- [ ] README.md is clear
- [ ] REPLIT_SETUP.md is accurate
- [ ] Code has helpful comments
- [ ] Environment variables documented

## Monitoring Setup

- [ ] Note Repl URL
- [ ] Set up uptime monitoring (optional)
- [ ] Plan backup schedule
- [ ] Bookmark Repl admin page

## Share with Kids

- [ ] Share Repl URL
- [ ] Create their user accounts
- [ ] Give quick tutorial
- [ ] Show checkpoint saves
- [ ] Demonstrate version history

## Post-Deployment

### Week 1
- [ ] Check daily for issues
- [ ] Monitor database size
- [ ] Collect user feedback
- [ ] Fix any bugs

### Monthly
- [ ] Backup database
- [ ] Check storage usage
- [ ] Review version history
- [ ] Update if needed

## Troubleshooting Quick Reference

### Repl Won't Start
```bash
# In Shell tab
python app.py
# Check error messages
```

### Database Issues
```bash
# Check database exists
ls -la instance/
# Check database size
du -h instance/python_games.db
```

### Clear All Data (Start Fresh)
```bash
# CAUTION: This deletes everything!
rm instance/python_games.db
# Restart Repl
```

### Check Version Count
```python
python3 -c "
from app import app, db, CodeVersion
with app.app_context():
    print(f'Total saves: {CodeVersion.query.count()}')
"
```

## Success Criteria

Deployment is successful when:

1. ✅ Both kids can access the app
2. ✅ Code editor works smoothly
3. ✅ Auto-save working reliably
4. ✅ Version history shows all saves
5. ✅ No errors in console
6. ✅ Data persists across sessions
7. ✅ Chromebooks can access it
8. ✅ Kids can complete first tutorial

## Emergency Contacts

- Replit Status: https://status.replit.com
- Replit Docs: https://docs.replit.com
- Replit Ask: https://ask.replit.com

---

**Deployment Date**: _____________

**Deployed By**: _____________

**Repl URL**: _____________

**First Backup**: _____________

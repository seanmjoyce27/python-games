# Admin Panel Documentation

## Overview

The Python Game Builder includes a password-protected admin panel for managing students, viewing statistics, and monitoring the system.

## Accessing the Admin Panel

### URL
Navigate to: `http://localhost:8443/admin`

Or click the "Admin" link in the top-right corner of the home page.

### Default Password
The default admin password is: `python123`

⚠️ **IMPORTANT**: Change this password before deploying to production!

## Changing the Admin Password

### Option 1: Environment Variable (Recommended)
Set the `ADMIN_PASSWORD` environment variable:

```bash
export ADMIN_PASSWORD=your_secure_password
```

Or on Replit, add it to the Secrets tab.

### Option 2: .env File
Edit the `.env` file in the project root:

```
ADMIN_PASSWORD=your_secure_password
```

## Features

The admin dashboard provides:

### 📊 Statistics Overview
- **Total Students**: Number of registered students
- **Total Code Saves**: Number of code versions saved across all users
- **Active Missions**: Number of available missions

### 👥 Student Management
- View all students with their:
  - Username
  - Account creation date
  - Number of code saves
- **Create New Students**: Add students with custom usernames
- **Delete Students**: Remove students and all their associated data (with confirmation)

### 🎮 Game Templates
- View all available games
- See game IDs and display names
- Monitor which games are available to students

## Security Notes

1. **Password Protection**: The admin panel requires authentication
2. **Session-Based**: Uses Flask sessions (stays logged in until logout)
3. **Secure in Production**: 
   - Always change the default password
   - Set a strong `SECRET_KEY` environment variable
   - Use HTTPS in production

## Logout

Click the "Logout" button in the top-right corner of the admin dashboard to end your session.

## Troubleshooting

### "Incorrect password" error
- Verify the password matches your `ADMIN_PASSWORD` environment variable
- Check if `.env` file exists and is being loaded
- Default password is `python123` if no environment variable is set

### Admin panel not loading
- Ensure Flask is running on the correct port (default: 8443)
- Check that the `/admin` route is accessible
- Verify no errors in the Flask console

## Environment Variables

Required for admin panel:
- `ADMIN_PASSWORD`: Admin login password (default: `python123`)
- `SECRET_KEY`: Flask session secret (default: `dev-secret-key-change-in-production`)
- `PORT`: Server port (default: `8443`)

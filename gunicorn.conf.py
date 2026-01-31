# Gunicorn configuration file for production deployment

import os

# Bind to all interfaces on port 8443 (or PORT env var)
bind = f"0.0.0.0:{os.environ.get('PORT', '8443')}"

# Worker configuration
workers = int(os.environ.get('GUNICORN_WORKERS', '2'))
worker_class = 'sync'
threads = 2
timeout = 30

# Logging
accesslog = '-'  # Log to stdout
errorlog = '-'   # Log to stderr
loglevel = 'info'

# Process naming
proc_name = 'python-games'

# Preload app for faster worker startup
preload_app = True

# Graceful restart timeout
graceful_timeout = 30

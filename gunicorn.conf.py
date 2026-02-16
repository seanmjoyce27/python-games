# Gunicorn configuration file for production deployment

import os

# Worker configuration
workers = int(os.environ.get('GUNICORN_WORKERS', '2'))
worker_class = 'gthread'
threads = 2
timeout = 30

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'

# Process naming
proc_name = 'python-games'

# Graceful restart timeout
graceful_timeout = 30

# Server hooks
def when_ready(server):
    """Initialize database tables and seed data before workers start serving.

    This runs once in the master process after the app is loaded (preload_app = True)
    but before any worker begins accepting requests, eliminating the lazy-init delay
    that autoscale deployments would otherwise experience on the first request.
    """
    from app import init_db
    server.log.info("Initializing database...")
    init_db()
    server.log.info("Database initialization complete.")

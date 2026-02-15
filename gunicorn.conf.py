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

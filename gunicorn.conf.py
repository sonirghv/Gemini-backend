"""
Gunicorn Configuration - Production WSGI server configuration
Optimized settings for production deployment with proper worker management
"""

import multiprocessing
import os
from utils.env_utils import get_env_str, get_env_int, get_env_bool, is_production

# Server socket
bind = f"0.0.0.0:{get_env_int('PORT', 8000)}"
backlog = get_env_int("GUNICORN_BACKLOG", 2048)

# Worker processes
workers = get_env_int("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2 + 1)
worker_class = get_env_str("GUNICORN_WORKER_CLASS", "uvicorn.workers.UvicornWorker")
worker_connections = get_env_int("GUNICORN_WORKER_CONNECTIONS", 1000)
max_requests = get_env_int("GUNICORN_MAX_REQUESTS", 1000)
max_requests_jitter = get_env_int("GUNICORN_MAX_REQUESTS_JITTER", 50)

# Timeouts
timeout = get_env_int("GUNICORN_TIMEOUT", 30)
keepalive = get_env_int("GUNICORN_KEEPALIVE", 2)
graceful_timeout = get_env_int("GUNICORN_GRACEFUL_TIMEOUT", 30)

# Security
limit_request_line = get_env_int("GUNICORN_LIMIT_REQUEST_LINE", 4096)
limit_request_fields = get_env_int("GUNICORN_LIMIT_REQUEST_FIELDS", 100)
limit_request_field_size = get_env_int("GUNICORN_LIMIT_REQUEST_FIELD_SIZE", 8190)

# Logging
loglevel = get_env_str("GUNICORN_LOG_LEVEL", "info")
accesslog = get_env_str("GUNICORN_ACCESS_LOG", "-")  # stdout
errorlog = get_env_str("GUNICORN_ERROR_LOG", "-")   # stderr
access_log_format = get_env_str(
    "GUNICORN_ACCESS_LOG_FORMAT",
    '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'
)

# Process naming
proc_name = get_env_str("APP_NAME", "gemini-clone-api")

# Server mechanics
daemon = False
pidfile = get_env_str("GUNICORN_PID_FILE", "/tmp/gunicorn.pid") if is_production() else None
user = get_env_str("GUNICORN_USER", None)
group = get_env_str("GUNICORN_GROUP", None)
tmp_upload_dir = get_env_str("GUNICORN_TMP_UPLOAD_DIR", None)

# SSL (if enabled)
keyfile = get_env_str("SSL_KEYFILE", None)
certfile = get_env_str("SSL_CERTFILE", None)

# Preload application
preload_app = get_env_bool("GUNICORN_PRELOAD_APP", True)

# Worker lifecycle hooks
def on_starting(server):
    """Called just before the master process is initialized"""
    server.log.info("Starting Gunicorn server...")

def on_reload(server):
    """Called to recycle workers during a reload via SIGHUP"""
    server.log.info("Reloading Gunicorn server...")

def when_ready(server):
    """Called just after the server is started"""
    server.log.info(f"Gunicorn server is ready. Listening on {bind}")

def worker_int(worker):
    """Called just after a worker exited on SIGINT or SIGQUIT"""
    worker.log.info(f"Worker {worker.pid} received INT or QUIT signal")

def pre_fork(server, worker):
    """Called just before a worker is forked"""
    server.log.debug(f"Worker {worker.pid} is being forked")

def post_fork(server, worker):
    """Called just after a worker has been forked"""
    server.log.debug(f"Worker {worker.pid} has been forked")

def post_worker_init(worker):
    """Called just after a worker has initialized the application"""
    worker.log.debug(f"Worker {worker.pid} has initialized")

def worker_abort(worker):
    """Called when a worker received the SIGABRT signal"""
    worker.log.warning(f"Worker {worker.pid} received SIGABRT signal")

def pre_exec(server):
    """Called just before a new master process is forked"""
    server.log.info("Forking new master process")

def pre_request(worker, req):
    """Called just before a worker processes the request"""
    worker.log.debug(f"Processing request: {req.method} {req.path}")

def post_request(worker, req, environ, resp):
    """Called after a worker processes the request"""
    worker.log.debug(f"Completed request: {req.method} {req.path} - {resp.status}")

# Environment-specific settings
if is_production():
    # Production optimizations
    worker_tmp_dir = "/dev/shm"  # Use memory for worker temp files
    forwarded_allow_ips = "*"    # Allow all IPs for reverse proxy
else:
    # Development settings
    reload = get_env_bool("GUNICORN_RELOAD", True)
    reload_extra_files = [
        "utils/",
        "database/",
        ".env"
    ] 
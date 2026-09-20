import os

bind = "0.0.0.0:8000"
workers = 2

log_dir = os.environ.get("APP_LOG_DIR", "/var/log/app")
if os.path.isdir(log_dir):
    accesslog = os.path.join(log_dir, "access.log")
    errorlog = os.path.join(log_dir, "error.log")
else:
    accesslog = "-"
    errorlog = "-"

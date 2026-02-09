from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecom.settings')

app = Celery('ecom')

# Use Redis as broker and backend
app.conf.broker_url = os.getenv("REDIS_URL", "redis://localhost:637/0")
app.conf.result_backend = os.getenv("REDIS_URL", "redis://localhost:6379/1")

# Load Django settings (CELERY_ namespace)
app.config_from_object('django.conf:settings', namespace='CELERY')
app.conf.redis_max_connections = 2

app.conf.update(
    worker_hijack_root_logger=False, 
    worker_log_format="[%(asctime)s: %(levelname)s/%(processName)s] %(message)s",
    worker_task_log_format="[%(asctime)s: %(levelname)s/%(processName)s] %(task_name)s: %(message)s",
    worker_redirect_stdouts=True,
    worker_redirect_stdouts_level='INFO',
    worker_log_color=False
)

app.conf.task_serializer = "json"
app.conf.result_serializer = "json"
app.conf.accept_content = ["json"]
app.conf.timezone = "Africa/Lagos"
app.conf.enable_utc = True

# Optional: retry tasks on connection loss
app.conf.worker_cancel_long_running_tasks_on_connection_loss = True

# Auto discover tasks from each app/tasks.py
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")

# CELERY BEAT SCHEDULES
app.conf.beat_schedule = {
    "Clean-abandoned-carts": {
        "task": "core.tasks.carts.cleanup_abandoned_carts",
        "schedule": timedelta(minutes=1),
    },
}
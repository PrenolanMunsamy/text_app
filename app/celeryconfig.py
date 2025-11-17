from celery import Celery

app = Celery(
    "textapp",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

# Optional: tune concurrency
app.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='UTC',
    enable_utc=True,
)

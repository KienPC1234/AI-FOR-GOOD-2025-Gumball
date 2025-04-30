redis-server ./redis.conf
celery -A celery_app.celery_app worker -Q ai_queue --loglevel=info
python main.py
REM Optional: enable to monitor tasks
REM celery -A celery_app.celery_app flower
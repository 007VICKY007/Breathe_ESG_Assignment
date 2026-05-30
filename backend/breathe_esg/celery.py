import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "breathe_esg.settings.base")

app = Celery("breathe_esg")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

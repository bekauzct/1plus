"""Gunicorn sozlamalari. Request body hech qachon log'ga yozilmaydi (gunicorn uni log qilmaydi)."""

import multiprocessing
import os

bind = f"0.0.0.0:{os.environ.get('PORT', '8000')}"
workers = int(os.environ.get("WEB_CONCURRENCY", min(4, multiprocessing.cpu_count() * 2 + 1)))
threads = int(os.environ.get("GUNICORN_THREADS", "1"))
timeout = int(os.environ.get("GUNICORN_TIMEOUT", "60"))
graceful_timeout = 30
keepalive = 5
max_requests = 1000  # xotira sizishidan saqlanish (WeasyPrint)
max_requests_jitter = 100
worker_tmp_dir = "/dev/shm"
forwarded_allow_ips = os.environ.get("FORWARDED_ALLOW_IPS", "127.0.0.1")
accesslog = "-"
errorlog = "-"
# Faqat metod, yo'l (query string'siz), status, hajm va vaqt
access_log_format = '%(h)s "%(m)s %(U)s" %(s)s %(B)s %(M)sms'
limit_request_line = 4094
# gunicorn >= 25 boshqaruv soketi: read-only konteynerda kerak emas
control_socket_disable = True

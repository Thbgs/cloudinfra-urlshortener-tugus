"""
WSGI config for config project.

Mengekspos callable WSGI sebagai variabel di level modul bernama ``application``.
WSGI adalah antarmuka server Python sinkron yang digunakan Gunicorn di production (lihat Procfile).

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

# Beri tahu Django modul settings mana yang digunakan sebelum membangun aplikasi
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Callable WSGI yang akan dipanggil Gunicorn/uWSGI untuk setiap request HTTP
application = get_wsgi_application()

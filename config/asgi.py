"""
ASGI config for config project.

Mengekspos callable ASGI sebagai variabel di level modul bernama ``application``.
ASGI mendukung server async (misal: Daphne, Uvicorn) dan WebSocket selain HTTP biasa.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

# Beri tahu Django modul settings mana yang digunakan sebelum membangun aplikasi
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Callable ASGI yang dilayani oleh server berkemampuan async
application = get_asgi_application()

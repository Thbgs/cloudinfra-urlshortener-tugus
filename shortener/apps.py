from django.apps import AppConfig


class ShortenerConfig(AppConfig):
    # Gunakan primary key integer 64-bit secara default (menghindari batas int 32-bit pada tabel besar)
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'shortener'

from django.contrib import admin
from django.urls import path, include

# Konfigurasi URL utama — mendelegasikan ke urls.py masing-masing aplikasi
urlpatterns = [
    # Panel admin bawaan Django di /admin/
    path('admin/', admin.site.urls),
    # Pasang semua route aplikasi shortener di root situs (/, /api/*, /stats/*, dll.)
    path('', include('shortener.urls')),
]

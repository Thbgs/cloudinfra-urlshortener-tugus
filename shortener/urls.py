from django.urls import path
from . import views

urlpatterns = [
    # Halaman utama — menampilkan form pemendek URL beserta daftar tautan terbaru
    path('', views.IndexView.as_view(), name='index'),

    # Health check — mengembalikan JSON status database dan Redis (digunakan monitoring)
    path('health/', views.HealthCheckView.as_view(), name='health-check'),

    # API: buat URL pendek baru (POST dengan body JSON)
    path('api/shorten/', views.ShortenURLView.as_view(), name='shorten-url'),

    # API: daftar semua URL aktif yang dipersingkat (JSON terpaginasi)
    path('api/urls/', views.URLListView.as_view(), name='url-list'),

    # API: analitik JSON untuk kode pendek tertentu
    path('api/stats/<str:short_code>/', views.URLStatsAPIView.as_view(), name='url-stats-api'),

    # Halaman analitik HTML untuk kode pendek tertentu
    path('stats/<str:short_code>/', views.URLStatsView.as_view(), name='url-stats'),

    # Catch-all redirect — harus paling akhir agar tidak menutupi route di atas
    path('<str:short_code>/', views.RedirectURLView.as_view(), name='redirect-url'),
]

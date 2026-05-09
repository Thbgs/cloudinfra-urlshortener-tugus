from django.urls import path
from . import views

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('health/', views.HealthCheckView.as_view(), name='health-check'),
    path('api/shorten/', views.ShortenURLView.as_view(), name='shorten-url'),
    path('api/urls/', views.URLListView.as_view(), name='url-list'),
    path('api/stats/<str:short_code>/', views.URLStatsAPIView.as_view(), name='url-stats-api'),
    path('stats/<str:short_code>/', views.URLStatsView.as_view(), name='url-stats'),
    # catch-all redirect — must be last
    path('<str:short_code>/', views.RedirectURLView.as_view(), name='redirect-url'),
]

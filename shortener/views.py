import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
from django.core.cache import cache
from django.db import connections
from django.db.utils import OperationalError
from django.db.models import F
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import ShortenedURL, ClickAnalytics
from .serializers import ShortenedURLSerializer, CreateURLSerializer, ClickAnalyticsSerializer

logger = logging.getLogger(__name__)
CACHE_TIMEOUT = 3600  # 1 hour


class IndexView(APIView):
    """GET / — homepage with URL shortening form."""

    def get(self, request):
        recent_urls = ShortenedURL.objects.filter(is_active=True)[:10]
        return render(request, 'shortener/index.html', {'recent_urls': recent_urls})


class HealthCheckView(APIView):
    """GET /health/ — verifies database and Redis connectivity."""

    def get(self, request):
        result = {
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'services': {},
        }

        try:
            connections['default'].ensure_connection()
            result['services']['database'] = 'healthy'
        except OperationalError:
            result['services']['database'] = 'unhealthy'
            result['status'] = 'degraded'

        try:
            cache.set('_health_probe', 'ok', 10)
            result['services']['cache'] = (
                'healthy' if cache.get('_health_probe') == 'ok' else 'unhealthy'
            )
        except Exception:
            result['services']['cache'] = 'unhealthy'

        if any(v == 'unhealthy' for v in result['services'].values()):
            result['status'] = 'degraded'

        http_status = 200 if result['status'] == 'healthy' else 503
        return JsonResponse(result, status=http_status)


class ShortenURLView(APIView):
    """POST /api/shorten/ — create a shortened URL."""

    def post(self, request):
        serializer = CreateURLSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        url_obj = serializer.save()
        out = ShortenedURLSerializer(url_obj, context={'request': request})
        return Response(out.data, status=status.HTTP_201_CREATED)


class RedirectURLView(APIView):
    """GET /<short_code>/ — redirect to the original URL (Redis-cached)."""

    def get(self, request, short_code):
        cache_key = f'url:{short_code}'
        cached = cache.get(cache_key)

        if cached:
            url_id = cached['id']
            original_url = cached['original_url']
        else:
            try:
                url_obj = ShortenedURL.objects.get(short_code=short_code, is_active=True)
            except ShortenedURL.DoesNotExist:
                return render(request, 'shortener/404.html', status=404)

            if url_obj.is_expired:
                return render(request, 'shortener/expired.html', status=410)

            cache.set(cache_key, {'id': url_obj.pk, 'original_url': url_obj.original_url}, CACHE_TIMEOUT)
            url_id = url_obj.pk
            original_url = url_obj.original_url

        ClickAnalytics.objects.create(
            url_id=url_id,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:512],
            referer=request.META.get('HTTP_REFERER') or None,
        )
        ShortenedURL.objects.filter(pk=url_id).update(click_count=F('click_count') + 1)

        return redirect(original_url)


class URLStatsView(APIView):
    """GET /stats/<short_code>/ — HTML analytics page."""

    def get(self, request, short_code):
        url_obj = get_object_or_404(ShortenedURL, short_code=short_code)
        recent_clicks = url_obj.clicks.all()[:20]
        return render(request, 'shortener/stats.html', {
            'url': url_obj,
            'recent_clicks': recent_clicks,
        })


class URLStatsAPIView(APIView):
    """GET /api/stats/<short_code>/ — JSON analytics."""

    def get(self, request, short_code):
        url_obj = get_object_or_404(ShortenedURL, short_code=short_code)
        recent_clicks = url_obj.clicks.all()[:20]
        return Response({
            'url': ShortenedURLSerializer(url_obj, context={'request': request}).data,
            'recent_clicks': ClickAnalyticsSerializer(recent_clicks, many=True).data,
        })


class URLListView(APIView):
    """GET /api/urls/ — paginated list of all active shortened URLs."""

    def get(self, request):
        urls = ShortenedURL.objects.filter(is_active=True)
        serializer = ShortenedURLSerializer(urls, many=True, context={'request': request})
        return Response(serializer.data)

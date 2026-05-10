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
# Berapa lama data redirect di-cache di Redis sebelum perlu query database lagi
CACHE_TIMEOUT = 3600  # 1 jam


class IndexView(APIView):
    """GET / — halaman utama dengan form pemendek URL."""

    def get(self, request):
        # Tampilkan hanya 10 tautan aktif terbaru agar halaman tetap ringan
        recent_urls = ShortenedURL.objects.filter(is_active=True)[:10]
        return render(request, 'shortener/index.html', {'recent_urls': recent_urls})


class HealthCheckView(APIView):
    """GET /health/ — memverifikasi konektivitas database dan Redis."""

    def get(self, request):
        result = {
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'services': {},
        }

        # Coba lakukan pengecekan koneksi database yang ringan
        try:
            connections['default'].ensure_connection()
            result['services']['database'] = 'healthy'
        except OperationalError:
            result['services']['database'] = 'unhealthy'
            result['status'] = 'degraded'

        # Tulis key probe berumur pendek ke Redis lalu baca kembali untuk konfirmasi round-trip
        try:
            cache.set('_health_probe', 'ok', 10)
            result['services']['cache'] = (
                'healthy' if cache.get('_health_probe') == 'ok' else 'unhealthy'
            )
        except Exception:
            result['services']['cache'] = 'unhealthy'

        # Turunkan status keseluruhan jika ada layanan individual yang tidak sehat
        if any(v == 'unhealthy' for v in result['services'].values()):
            result['status'] = 'degraded'

        # HTTP 503 memberi tahu load balancer untuk mengalihkan traffic dari instance yang bermasalah
        http_status = 200 if result['status'] == 'healthy' else 503
        return JsonResponse(result, status=http_status)


class ShortenURLView(APIView):
    """POST /api/shorten/ — membuat URL yang dipersingkat."""

    def post(self, request):
        serializer = CreateURLSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        url_obj = serializer.save()
        # Serialkan ulang dengan serializer output lengkap agar respons menyertakan short_url
        out = ShortenedURLSerializer(url_obj, context={'request': request})
        return Response(out.data, status=status.HTTP_201_CREATED)


class RedirectURLView(APIView):
    """GET /<short_code>/ — redirect ke URL asli (di-cache di Redis)."""

    def get(self, request, short_code):
        cache_key = f'url:{short_code}'
        cached = cache.get(cache_key)

        if cached:
            # Cache hit: lewati query database sepenuhnya
            url_id = cached['id']
            original_url = cached['original_url']
        else:
            # Cache miss: ambil dari database dan isi cache untuk permintaan berikutnya
            try:
                url_obj = ShortenedURL.objects.get(short_code=short_code, is_active=True)
            except ShortenedURL.DoesNotExist:
                return render(request, 'shortener/404.html', status=404)

            # Tautan kedaluwarsa mendapat respons 410 Gone (berbeda dari 404 agar klien tahu tautan pernah ada)
            if url_obj.is_expired:
                return render(request, 'shortener/expired.html', status=410)

            # Hanya cache field yang dibutuhkan untuk redirect, bukan seluruh instance model
            cache.set(cache_key, {'id': url_obj.pk, 'original_url': url_obj.original_url}, CACHE_TIMEOUT)
            url_id = url_obj.pk
            original_url = url_obj.original_url

        # Catat klik ini: buat baris analitik terlebih dahulu
        ClickAnalytics.objects.create(
            url_id=url_id,
            ip_address=request.META.get('REMOTE_ADDR'),
            # Potong user agent sesuai max_length field untuk mencegah error database
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:512],
            referer=request.META.get('HTTP_REFERER') or None,
        )
        # Gunakan F() untuk menginkremen counter dengan satu SQL UPDATE, menghindari
        # race condition read-modify-write saat ada request bersamaan
        ShortenedURL.objects.filter(pk=url_id).update(click_count=F('click_count') + 1)

        return redirect(original_url)


class URLStatsView(APIView):
    """GET /stats/<short_code>/ — halaman analitik HTML."""

    def get(self, request, short_code):
        url_obj = get_object_or_404(ShortenedURL, short_code=short_code)
        # Batasi 20 klik terbaru agar loading halaman tetap cepat
        recent_clicks = url_obj.clicks.all()[:20]
        return render(request, 'shortener/stats.html', {
            'url': url_obj,
            'recent_clicks': recent_clicks,
        })


class URLStatsAPIView(APIView):
    """GET /api/stats/<short_code>/ — analitik JSON."""

    def get(self, request, short_code):
        url_obj = get_object_or_404(ShortenedURL, short_code=short_code)
        recent_clicks = url_obj.clicks.all()[:20]
        return Response({
            'url': ShortenedURLSerializer(url_obj, context={'request': request}).data,
            'recent_clicks': ClickAnalyticsSerializer(recent_clicks, many=True).data,
        })


class URLListView(APIView):
    """GET /api/urls/ — daftar terpaginasi semua URL aktif yang dipersingkat."""

    def get(self, request):
        # URL yang tidak aktif (soft-delete) dikecualikan dari daftar publik
        urls = ShortenedURL.objects.filter(is_active=True)
        serializer = ShortenedURLSerializer(urls, many=True, context={'request': request})
        return Response(serializer.data)

from django.contrib import admin
from .models import ShortenedURL, ClickAnalytics


@admin.register(ShortenedURL)
class ShortenedURLAdmin(admin.ModelAdmin):
    # Kolom yang ditampilkan di tabel daftar changelist
    list_display = ['short_code', 'title', 'original_url_truncated', 'click_count', 'created_at', 'expires_at', 'is_active']
    # Filter sidebar untuk segmentasi cepat
    list_filter = ['is_active', 'created_at']
    # Field yang digunakan oleh kotak pencarian admin
    search_fields = ['short_code', 'original_url', 'title']
    # Cegah editor mengubah field yang dikelola secara otomatis
    readonly_fields = ['click_count', 'created_at']
    list_per_page = 25

    def original_url_truncated(self, obj):
        # Potong URL panjang agar tidak meregangkan tabel admin
        url = obj.original_url
        return url[:60] + '…' if len(url) > 60 else url
    original_url_truncated.short_description = 'Original URL'


@admin.register(ClickAnalytics)
class ClickAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['url', 'clicked_at', 'ip_address', 'user_agent_truncated']
    list_filter = ['clicked_at']
    # Semua field dihasilkan oleh server; editor hanya boleh membaca, bukan mengedit record klik
    readonly_fields = ['url', 'clicked_at', 'ip_address', 'user_agent', 'referer']
    list_per_page = 50

    def user_agent_truncated(self, obj):
        # Potong string user-agent panjang agar tidak merusak tampilan tabel
        ua = obj.user_agent
        return ua[:80] + '…' if len(ua) > 80 else ua
    user_agent_truncated.short_description = 'User Agent'

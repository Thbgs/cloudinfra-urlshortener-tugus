from django.contrib import admin
from .models import ShortenedURL, ClickAnalytics


@admin.register(ShortenedURL)
class ShortenedURLAdmin(admin.ModelAdmin):
    list_display = ['short_code', 'title', 'original_url_truncated', 'click_count', 'created_at', 'expires_at', 'is_active']
    list_filter = ['is_active', 'created_at']
    search_fields = ['short_code', 'original_url', 'title']
    readonly_fields = ['click_count', 'created_at']
    list_per_page = 25

    def original_url_truncated(self, obj):
        url = obj.original_url
        return url[:60] + '…' if len(url) > 60 else url
    original_url_truncated.short_description = 'Original URL'


@admin.register(ClickAnalytics)
class ClickAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['url', 'clicked_at', 'ip_address', 'user_agent_truncated']
    list_filter = ['clicked_at']
    readonly_fields = ['url', 'clicked_at', 'ip_address', 'user_agent', 'referer']
    list_per_page = 50

    def user_agent_truncated(self, obj):
        ua = obj.user_agent
        return ua[:80] + '…' if len(ua) > 80 else ua
    user_agent_truncated.short_description = 'User Agent'

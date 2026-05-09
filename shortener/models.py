import string
import random
from django.db import models
from django.utils import timezone


def generate_short_code(length=6):
    chars = string.ascii_letters + string.digits
    while True:
        code = ''.join(random.choices(chars, k=length))
        if not ShortenedURL.objects.filter(short_code=code).exists():
            return code


class ShortenedURL(models.Model):
    original_url = models.URLField(max_length=2048)
    short_code = models.CharField(max_length=20, unique=True, db_index=True)
    title = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    click_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def is_expired(self):
        return bool(self.expires_at and timezone.now() > self.expires_at)

    def __str__(self):
        return f"{self.short_code} → {self.original_url[:60]}"


class ClickAnalytics(models.Model):
    url = models.ForeignKey(ShortenedURL, on_delete=models.CASCADE, related_name='clicks')
    clicked_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=512, blank=True)
    referer = models.URLField(max_length=2048, null=True, blank=True)

    class Meta:
        ordering = ['-clicked_at']

    def __str__(self):
        return f"Click on {self.url.short_code} at {self.clicked_at}"

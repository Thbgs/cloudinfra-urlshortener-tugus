from rest_framework import serializers
from .models import ShortenedURL, ClickAnalytics, generate_short_code


class ClickAnalyticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClickAnalytics
        fields = ['clicked_at', 'ip_address', 'user_agent', 'referer']


class ShortenedURLSerializer(serializers.ModelSerializer):
    short_url = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()

    class Meta:
        model = ShortenedURL
        fields = [
            'id', 'original_url', 'short_code', 'short_url', 'title',
            'created_at', 'expires_at', 'click_count', 'is_active', 'is_expired',
        ]
        read_only_fields = ['id', 'short_code', 'created_at', 'click_count']

    def get_short_url(self, obj):
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(f'/{obj.short_code}/')
        return f'/{obj.short_code}/'

    def get_is_expired(self, obj):
        return obj.is_expired


class CreateURLSerializer(serializers.Serializer):
    original_url = serializers.URLField(max_length=2048)
    custom_code = serializers.CharField(max_length=20, required=False, allow_blank=True)
    title = serializers.CharField(max_length=255, required=False, allow_blank=True)
    expires_at = serializers.DateTimeField(required=False, allow_null=True)

    def validate_custom_code(self, value):
        if not value:
            return value
        if ShortenedURL.objects.filter(short_code=value).exists():
            raise serializers.ValidationError("This custom code is already taken.")
        if not value.replace('-', '').replace('_', '').isalnum():
            raise serializers.ValidationError(
                "Custom code may only contain letters, numbers, hyphens, and underscores."
            )
        return value

    def create(self, validated_data):
        custom_code = validated_data.pop('custom_code', '') or ''
        short_code = custom_code if custom_code else generate_short_code()
        return ShortenedURL.objects.create(short_code=short_code, **validated_data)

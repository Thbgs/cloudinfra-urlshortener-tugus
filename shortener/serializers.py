from rest_framework import serializers
from .models import ShortenedURL, ClickAnalytics, generate_short_code


class ClickAnalyticsSerializer(serializers.ModelSerializer):
    """Mengserialkan record klik individual untuk API statistik."""
    class Meta:
        model = ClickAnalytics
        fields = ['clicked_at', 'ip_address', 'user_agent', 'referer']


class ShortenedURLSerializer(serializers.ModelSerializer):
    """Serializer baca lengkap untuk URL yang dipersingkat, termasuk field yang dihitung."""
    # Field yang dihitung: membangun URL pendek absolut (misal: https://example.com/aB3xYz/)
    short_url = serializers.SerializerMethodField()
    # Field yang dihitung: mendelegasikan ke properti is_expired di model
    is_expired = serializers.SerializerMethodField()

    class Meta:
        model = ShortenedURL
        fields = [
            'id', 'original_url', 'short_code', 'short_url', 'title',
            'created_at', 'expires_at', 'click_count', 'is_active', 'is_expired',
        ]
        # Field-field ini diatur oleh server dan tidak boleh diterima dari input klien
        read_only_fields = ['id', 'short_code', 'created_at', 'click_count']

    def get_short_url(self, obj):
        # Gunakan request yang masuk untuk membangun URL lengkap jika tersedia;
        # fallback ke path relatif root untuk pengujian atau konteks non-HTTP
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(f'/{obj.short_code}/')
        return f'/{obj.short_code}/'

    def get_is_expired(self, obj):
        return obj.is_expired


class CreateURLSerializer(serializers.Serializer):
    """Memvalidasi dan membuat URL pendek baru dari data yang dikirim klien."""
    original_url = serializers.URLField(max_length=2048)
    # Kode vanity opsional; jika tidak diisi, kode acak 6 karakter akan digenerate
    custom_code = serializers.CharField(max_length=20, required=False, allow_blank=True)
    title = serializers.CharField(max_length=255, required=False, allow_blank=True)
    expires_at = serializers.DateTimeField(required=False, allow_null=True)

    def validate_custom_code(self, value):
        # Nilai kosong berarti "generate otomatis untuk saya" — lewati validasi
        if not value:
            return value
        # Cegah kode pendek duplikat sebelum membentur unique constraint database
        if ShortenedURL.objects.filter(short_code=value).exists():
            raise serializers.ValidationError("This custom code is already taken.")
        # Hanya alfanumerik, tanda hubung, dan garis bawah yang diizinkan agar URL tetap bersih
        if not value.replace('-', '').replace('_', '').isalnum():
            raise serializers.ValidationError(
                "Custom code may only contain letters, numbers, hyphens, and underscores."
            )
        return value

    def create(self, validated_data):
        # Keluarkan custom_code sebelum diteruskan ke model (bukan field model)
        custom_code = validated_data.pop('custom_code', '') or ''
        # Gunakan kode vanity yang diberikan atau generate yang unik secara otomatis
        short_code = custom_code if custom_code else generate_short_code()
        return ShortenedURL.objects.create(short_code=short_code, **validated_data)

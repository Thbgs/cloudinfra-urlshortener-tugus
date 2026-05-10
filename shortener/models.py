import string
import random
from django.db import models
from django.utils import timezone


def generate_short_code(length=6):
    # Kumpulan karakter yang aman untuk URL: a-z, A-Z, 0-9 (62 pilihan → 56 miliar kombinasi di panjang 6)
    chars = string.ascii_letters + string.digits
    # Ulangi sampai ditemukan kode yang belum ada di database (tabrakan jarang tapi mungkin terjadi)
    while True:
        code = ''.join(random.choices(chars, k=length))
        if not ShortenedURL.objects.filter(short_code=code).exists():
            return code


class ShortenedURL(models.Model):
    # URL tujuan yang ingin dipersingkat pengguna; maks 2048 karakter sesuai batas panjang URL browser
    original_url = models.URLField(max_length=2048)
    # Kode unik yang diindeks dan digunakan dalam tautan pendek (misal: "aB3xYz")
    short_code = models.CharField(max_length=20, unique=True, db_index=True)
    # Label opsional yang mudah dibaca manusia (ditampilkan di admin dan halaman statistik)
    title = models.CharField(max_length=255, blank=True)
    # Diatur otomatis saat dibuat; digunakan untuk pengurutan dan analitik
    created_at = models.DateTimeField(auto_now_add=True)
    # Tanggal kedaluwarsa opsional; null berarti tautan tidak pernah kedaluwarsa
    expires_at = models.DateTimeField(null=True, blank=True)
    # Diinkremen secara atomik via ekspresi F() di views.py untuk menghindari race condition
    click_count = models.PositiveIntegerField(default=0)
    # Flag soft-delete; URL yang tidak aktif mengembalikan 404 tanpa menghapus data analitik
    is_active = models.BooleanField(default=True)

    class Meta:
        # Tautan terbaru muncul pertama di daftar admin dan respons API
        ordering = ['-created_at']

    @property
    def is_expired(self):
        # Mengembalikan True hanya jika tanggal kedaluwarsa diset DAN tanggal tersebut sudah lewat
        return bool(self.expires_at and timezone.now() > self.expires_at)

    def __str__(self):
        return f"{self.short_code} → {self.original_url[:60]}"


class ClickAnalytics(models.Model):
    # Setiap record klik milik tepat satu URL yang dipersingkat; hapus cascade agar
    # menghapus URL juga menghapus seluruh riwayat kliknya
    url = models.ForeignKey(ShortenedURL, on_delete=models.CASCADE, related_name='clicks')
    # Timestamp dicatat saat insert (auto_now_add mencegah manipulasi dari luar)
    clicked_at = models.DateTimeField(auto_now_add=True)
    # IP pengunjung; null jika berada di balik proxy yang menghapus header
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    # Dipotong hingga 512 karakter di views.py untuk mencegah string UA yang terlalu panjang
    user_agent = models.CharField(max_length=512, blank=True)
    # Halaman asal pengunjung; null jika navigasi langsung atau via HTTPS→HTTP
    referer = models.URLField(max_length=2048, null=True, blank=True)

    class Meta:
        # Klik terbaru tampil pertama di halaman statistik
        ordering = ['-clicked_at']

    def __str__(self):
        return f"Click on {self.url.short_code} at {self.clicked_at}"

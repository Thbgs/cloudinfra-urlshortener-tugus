from pathlib import Path
from decouple import config, Csv
import dj_database_url

# Path absolut ke root repositori (dua level di atas file ini)
BASE_DIR = Path(__file__).resolve().parent.parent

# --- Keamanan ------------------------------------------------------------------

# Secret key untuk penandatanganan kriptografi; harus dirahasiakan di production
SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-me-in-production')
# Set DEBUG=False di production agar stack trace tidak tampil di respons HTTP
DEBUG = config('DEBUG', default=True, cast=bool)
# Daftar hostname yang boleh dilayani situs ini (mencegah serangan HTTP Host header)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=Csv())

# Izinkan semua subdomain Heroku agar dyno dapat merespons tanpa konfigurasi ulang per aplikasi
ALLOWED_HOSTS += ['.herokuapp.com']

# Izinkan origin HTTPS Heroku untuk mengirim form (perlindungan CSRF)
CSRF_TRUSTED_ORIGINS = ['https://*.herokuapp.com']

# --- Definisi aplikasi --------------------------------------------------------

INSTALLED_APPS = [
    # Bawaan Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Pihak ketiga: Django REST Framework untuk endpoint JSON API
    'rest_framework',
    # Aplikasi URL shortener milik kita
    'shortener',
]

MIDDLEWARE = [
    # Memaksakan HTTPS dan menetapkan header keamanan (HSTS, X-Content-Type, dll.)
    'django.middleware.security.SecurityMiddleware',
    # Melayani file statis yang sudah dikompresi langsung dari Django (tanpa CDN terpisah)
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    # Memvalidasi token CSRF pada method HTTP tidak aman (POST, PUT, dll.)
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Menambahkan header X-Frame-Options untuk mencegah clickjacking
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        # Cari template di dalam direktori templates/ setiap aplikasi
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# --- Database -----------------------------------------------------------------

DATABASES = {
    'default': dj_database_url.config(
        # Buat URL postgres:// dari env var individual jika DATABASE_URL tidak tersedia
        default=config(
            'DATABASE_URL',
            default=f"postgres://{config('DB_USER', default='postgres')}:"
                    f"{config('DB_PASSWORD', default='')}@"
                    f"{config('DB_HOST', default='localhost')}:"
                    f"{config('DB_PORT', default='5432')}/"
                    f"{config('DB_NAME', default='urlshortener')}"
        ),
        # Pertahankan koneksi hingga 10 menit agar tidak ada biaya handshake per request
        conn_max_age=600,
        # Periksa koneksi sebelum digunakan ulang agar tidak crash akibat socket mati
        conn_health_checks=True,
    )
}

# --- Cache (Redis) ------------------------------------------------------------

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': config('REDIS_URL', default='redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            # Jika Redis mati, cache miss akan diteruskan ke database secara diam-diam
            # daripada melempar exception dan mematikan seluruh situs
            'IGNORE_EXCEPTIONS': True,
        },
        # TTL default: 1 jam (view redirect menimpa nilai ini per key)
        'TIMEOUT': 3600,
    }
}

# --- Validasi password --------------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# --- Internasionalisasi -------------------------------------------------------

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
# Simpan semua datetime sebagai UTC di database; konversi ke waktu lokal hanya di template
USE_TZ = True

# --- File statis (CSS, JS, gambar) -------------------------------------------

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
# Duplikat dihapus; whitenoise melayani dari STATIC_ROOT setelah collectstatic
STATIC_ROOT = BASE_DIR / 'staticfiles'
# Beri sidik jari (content hash) pada file statis agar browser dapat meng-cache secara agresif
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- Django REST Framework ---------------------------------------------------

REST_FRAMEWORK = {
    # Hanya tampilkan JSON (tanpa HTML API yang bisa di-browse di production)
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    # Terima JSON, form HTML, dan upload multipart
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ],
    # Paginate endpoint list dengan query param ?page=; 20 item per halaman
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# --- Logging -----------------------------------------------------------------

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    # Tulis semua log ke stdout agar log drain Heroku dapat menangkapnya
    'handlers': {'console': {'class': 'logging.StreamHandler'}},
    'root': {'handlers': ['console'], 'level': 'INFO'},
}

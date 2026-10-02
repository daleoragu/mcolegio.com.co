import os
from pathlib import Path
import dj_database_url

# --- Carga de variables de entorno ---
# Se especifica la ruta explícita al archivo .env para máxima fiabilidad.
BASE_DIR = Path(__file__).resolve().parent.parent
from dotenv import load_dotenv
load_dotenv(dotenv_path=BASE_DIR / '.env')

# --- Configuración General de Django ---
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'clave-secreta-por-defecto-para-local')
DEBUG = os.getenv('DJANGO_DEBUG', 'True') == 'True'

ALLOWED_HOSTS = [
    'mcolegio.com.co',
    '.mcolegio.com.co',
    'localhost',
    '127.0.0.1',
    '.localhost',
    'integradoapr.edu.co',
]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'notas.apps.NotasConfig',
    'crispy_forms',
    'crispy_bootstrap5',
    'storages',
    'elecciones',  # <--- NUEVA APLICACIÓN AGREGADA AQUÍ
    'pruebas',     # <--- Módulo de pruebas y páginas publicadas
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'notas.middleware.ColegioMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'notas.context_processors.contador_notificaciones',
                'notas.context_processors.notificaciones_destacadas',
                'notas.context_processors.colegio_context',
            ],
        },
    },
]
WSGI_APPLICATION = 'config.wsgi.application'

# --- Base de Datos ---
# Por defecto, usa SQLite para desarrollo local.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
# Si está en producción, usa la URL de la base de datos de DigitalOcean.
DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL:
    DATABASES['default'] = dj_database_url.config(conn_max_age=600, ssl_require=True, default=DATABASE_URL)

# --- Autenticación y Zonas Horarias ---
AUTH_PASSWORD_VALIDATORS = [{'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},{'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},{'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},{'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'}]
LANGUAGE_CODE = 'es-co'
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_TZ = True
LOGIN_URL = '/super-admin/login/'

# --- Archivos Estáticos (CSS, JS) ---
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
# STATICFILES_STORAGE fue eliminado en Django 5.1: ahora se define en STORAGES (abajo).

# --- LÓGICA DE ALMACENAMIENTO DE MEDIOS ---
# Django 5.1 eliminó DEFAULT_FILE_STORAGE y STATICFILES_STORAGE.
# A partir de Django 4.2 la configuración correcta es el diccionario STORAGES.

USE_SPACES = os.getenv('DO_SPACES_BUCKET_NAME')

WHITENOISE_STATICFILES = {
    'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
}

if USE_SPACES:
    # --- PRODUCCIÓN: DigitalOcean Spaces ---
    print("✅ Usando DigitalOcean Spaces para almacenamiento de medios.")

    AWS_ACCESS_KEY_ID = os.getenv('DO_SPACES_ACCESS_KEY')
    AWS_SECRET_ACCESS_KEY = os.getenv('DO_SPACES_SECRET_KEY')
    AWS_STORAGE_BUCKET_NAME = os.getenv('DO_SPACES_BUCKET_NAME')
    AWS_S3_REGION_NAME = os.getenv('DO_SPACES_REGION')
    AWS_S3_ENDPOINT_URL = f'https://{AWS_S3_REGION_NAME}.digitaloceanspaces.com'
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.{AWS_S3_REGION_NAME}.digitaloceanspaces.com'
    AWS_LOCATION = 'media'

    STORAGES = {
        'default': {
            'BACKEND': 'storages.backends.s3boto3.S3Boto3Storage',
            'OPTIONS': {
                'access_key': AWS_ACCESS_KEY_ID,
                'secret_key': AWS_SECRET_ACCESS_KEY,
                'bucket_name': AWS_STORAGE_BUCKET_NAME,
                'region_name': AWS_S3_REGION_NAME,
                'endpoint_url': AWS_S3_ENDPOINT_URL,
                'custom_domain': AWS_S3_CUSTOM_DOMAIN,
                'location': AWS_LOCATION,
                'default_acl': 'public-read',
                'querystring_auth': False,
                'file_overwrite': False,
                'object_parameters': {'CacheControl': 'max-age=86400'},
            },
        },
        'staticfiles': WHITENOISE_STATICFILES,
    }

    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/{AWS_LOCATION}/'

else:
    # --- DESARROLLO LOCAL ---
    print("⚪️ Usando almacenamiento local para medios (carpeta 'media').")

    MEDIA_URL = '/media/'
    MEDIA_ROOT = BASE_DIR / 'media'

    STORAGES = {
        'default': {
            'BACKEND': 'django.core.files.storage.FileSystemStorage',
        },
        'staticfiles': WHITENOISE_STATICFILES,
    }

# --- Otras Configuraciones ---
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
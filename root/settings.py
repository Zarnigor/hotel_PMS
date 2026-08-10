from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()
BASE_DIR = Path(__file__).resolve().parent.parent


SECRET_KEY = os.getenv('SECRET_KEY')


DEBUG = os.getenv('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = ['localhost', '127.0.0.1']



INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'drf_spectacular',
    'apps.room',
    'apps.reservation',
    'apps.guest',
]

MIDDLEWARE = [
    'root.logging_utils.RequestIDMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'root.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'root.wsgi.application'


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT')
    }
}

REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 20,
    'EXCEPTION_HANDLER': 'exceptions.custom_exception_handler',
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'PMS API',
    'DESCRIPTION': 'API hujjatlari',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,

    "ENUM_NAME_OVERRIDES": {
        "ReservationStatusEnum": "apps.reservation.models.Reservation.STATUS_CHOICES",
        "PaymentStatusEnum": "apps.payment.models.Payment.STATUS_CHOICES",
    },
}

CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND')

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Tashkent'

USE_I18N = True

USE_TZ = True


STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

LOG_DIR = BASE_DIR / 'logs'
LOG_DIR.mkdir(parents=True, exist_ok=True)

# DEBUG=True -> console handler (dev). DEBUG=False -> rotating JSON file
# handler, read by Filebeat -> Elasticsearch/Kibana (see filebeat.yml).
_LOG_HANDLERS = ['console'] if DEBUG else ['file']

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'request_id': {
            '()': 'root.logging_utils.RequestIDFilter',
        },
    },
    'formatters': {
        'verbose': {
            'format': '%(asctime)s level=%(levelname)s logger=%(name)s '
                       'module=%(module)s request_id=%(request_id)s message=%(message)s',
        },
        'json': {
            '()': 'root.logging_utils.JSONFormatter',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
            'formatter': 'verbose',
            'filters': ['request_id'],
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'INFO',
            'filename': str(LOG_DIR / 'django.log'),
            'maxBytes': 10 * 1024 * 1024,  # 10 MB
            'backupCount': 10,
            'formatter': 'json',
            'filters': ['request_id'],
        },
    },
    'root': {
        'handlers': _LOG_HANDLERS,
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': _LOG_HANDLERS,
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': _LOG_HANDLERS,
            'level': 'ERROR',
            'propagate': False,
        },
        'apps': {
            'handlers': _LOG_HANDLERS,
            'level': 'DEBUG',
            'propagate': False,
        },
        'exceptions': {
            'handlers': _LOG_HANDLERS,
            'level': 'INFO',
            'propagate': False,
        },
    },
}
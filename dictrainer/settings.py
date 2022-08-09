import os.path
import warnings

from django_docker_helpers.config import ConfigLoader

from . import __version__


# --------------- PATHS ---------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_NAME = os.path.basename(BASE_DIR)
PROJECT_PATH = os.path.abspath(os.path.dirname(__file__))
TEMP_DIR = os.path.join('/tmp', PROJECT_NAME)
FILE_UPLOAD_TEMP_DIR = TEMP_DIR     # for TemporaryUploadedFile
MEDIA_ROOT = os.path.join(PROJECT_PATH, 'media')
STATIC_ROOT = os.path.join(PROJECT_PATH, 'static')
USERMEDIA_ROOT = os.path.join(PROJECT_PATH, 'usermedia')

# ------
for path in (
    STATIC_ROOT, MEDIA_ROOT, USERMEDIA_ROOT, TEMP_DIR
):
    if not os.path.exists(path):
        os.makedirs(path, mode=0o755, exist_ok=True)


# ★★★★★★★★★★★★★★★ CONFIG LOADER ★★★★★★★★★★★★★★★ #
yml_conf = os.path.join(PROJECT_PATH, 'config',
                        os.environ.get('DJANGO_CONFIG_FILE_NAME', 'dev.yml'))
os.environ.setdefault('YAMLPARSER__CONFIG', yml_conf)

configure = ConfigLoader.from_env(
    suppress_logs=True,
    silent=True
)
# ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★ #

DEBUG = configure('debug', False)

if configure('security', False):
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True


# --------------- SECRET SETTINGS ---------------
SECRET_KEY = configure('common.secret_key', 'secret')

if SECRET_KEY == 'secret':
    warnings.warn('SECRET_KEY is not assigned! Production unsafe!')


# --------------- HOSTS ---------------
ALLOWED_HOSTS = configure('hosts', [])


INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    # 'django.contrib.sites',

    'dictionary',
    'bot',
]


AUTHENTICATION_BACKENDS = [
    'dictionary.permissions.DictionaryPermissionsBackend',
    'django.contrib.auth.backends.ModelBackend'
]


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

ROOT_URLCONF = 'dictrainer.urls'

MEDIA_URL = configure('common.standard.media_url', '/media/')
STATIC_URL = configure('common.standard.static_url', '/static/')
USERMEDIA_URL = configure('common.standard.usermedia_url', '/usermedia/')
ADMIN_MEDIA_PREFIX = configure('common.standard.admin_media_prefix', '/static/admin/')

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': (
            os.path.join(PROJECT_PATH, 'templates')
        ),
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.template.context_processors.media',
                'django.template.context_processors.csrf',
                'django.template.context_processors.tz',
                'django.template.context_processors.static',
            ],
        },
    },
]

WSGI_APPLICATION = 'dictrainer.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': configure('db.engine', 'django.db.backends.postgresql'),
        'HOST': configure('db.host', ''),
        'PORT': configure('db.port', '', coerce_type=int),

        'NAME': configure('db.name', 'dictrainer'),
        'USER': configure('db.user', ''),
        'PASSWORD': configure('db.password', ''),

        'CONN_MAX_AGE': configure('db.conn_max_age', 60, coerce_type=int)
    }
}


CACHES = {
    'default': {
        'KEY_PREFIX': 'dictrainer',
        'BACKEND': 'redis_cache.RedisCache',
        'LOCATION': configure('caches.redis.location', ['localhost:6379']),
        'OPTIONS': {
            'DB': configure('caches.redis.options.db', 0),
            'PARSER_CLASS': 'redis.connection.HiredisParser',
            'CONNECTION_POOL_CLASS': 'redis.BlockingConnectionPool',
            'CONNECTION_POOL_CLASS_KWARGS': configure('caches.redis.options.db.connection_pool_class_kwargs', {
                'max_connections': 50,
                'timeout': 20,
            }),
            'MAX_CONNECTIONS': configure('caches.redis.options.max_connections', 1000),
            'PICKLE_VERSION': 2,
        },
    },
}

SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_SERIALIZER = 'django.contrib.sessions.serializers.JSONSerializer'
SESSION_CACHE_ALIAS = 'default'


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

TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_L10N = True
USE_TZ = True
LOCALE_PATHS = (
    os.path.join(PROJECT_PATH, 'locale'),
)
LANGUAGES = (
    ('en', 'English'),
    ('ru', 'Russian'),
)


# BATTERIES
# =========

# DJANGO REST FRAMEWORK
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': ['garbage.api.authentication.CsrfExemptSessionAuthentication'],
    'DEFAULT_FILTER_BACKENDS': ['url_filter.integrations.drf.DjangoFilterBackend'],
    'DEFAULT_PERMISSION_CLASSES': [],
    'DEFAULT_RENDERER_CLASSES': ['rest_framework.renderers.JSONRenderer'],
    'TEST_REQUEST_DEFAULT_FORMAT': 'json'
}

# RAVEN
if configure('sentry', False):
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=configure('sentry.dsn', None),
        release=__version__,
        integrations=[DjangoIntegration()],
        send_default_pii=True,  # include user
    )


# MODULES
# =======

# BOT
BOT = {
    'TOKEN': configure('bot.token'),
    'THREADED': configure('bot.threaded', False, coerce_type=bool),
    'PROXY': {
        'http': configure('bot.proxy.http'),
        'https': configure('bot.proxy.https'),
    }
}

# dictionary
RECENT_PHRASES = configure('dictionary.recent_phrases', 40, coerce_type=int)
DICT_CONTENTS_PAGE_SIZE = 10

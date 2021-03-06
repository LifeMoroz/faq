"""
Django settings for faq project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

TORNADO_PORT = 6500
BACKEND_PORT = 9000
REDIS_PORT = 6381

HOST = 'faq'

QUESTION_CHAN_PREF = 'question'
USER_CHAN_PREF = 'user'
REALTIME_PREF = 'realtime'
UPDATES_TAG = 'updates'


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'bv)j+r8)n@ee91)@t!qjl0@(txl9epm1h+v9^rvzfa0*e(#^b$'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Cache invalidation on save signals
# DISABLE THIS ON DATA GENERATION
CACHE_INVALIDATION = True

TEMPLATE_DEBUG = False

ALLOWED_HOSTS = ['faq', 'faq.cygame.ru', HOST]


# load from local settings
try:
    from local_settings import *
except ImportError:
    pass


# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'questions',
    'debug_toolbar',
    'tagging',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'faq.urls'

WSGI_APPLICATION = 'faq.wsgi.application'

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.core.context_processors.tz',
    'django.contrib.messages.context_processors.messages',
    'questions.context.glob',
    'django.core.context_processors.request',
)


# EMAIL NOTIFICATIONS
EMAIL_HOST = 'smtp.yandex.ru'
EMAIL_HOST_USER = 'faq@cygame.ru'
EMAIL_HOST_PASSWORD = 'password12345'
EMAIL_LINKS_BASE = 'http://faq.cygame.ru'
EMAIL_FROM = 'faq@cygame.ru'
EMAIL_PORT = 25


# CACHE BACKEND (REDIS)
CACHES = {
    'default': {
        "BACKEND": "redis_cache.cache.RedisCache",
        "LOCATION": "127.0.0.1:%s:0" % REDIS_PORT,
        "OPTIONS": {
            "CLIENT_CLASS": "redis_cache.client.DefaultClient",
        }
    }
}

# REDIS SESSIONS
SESSION_ENGINE = 'redis_sessions.session'
SESSION_REDIS_HOST = 'localhost'
SESSION_REDIS_PORT = REDIS_PORT
SESSION_REDIS_PREFIX = 'faqsession'




if not DEBUG:
    TEMPLATE_LOADERS = (
        ('django.template.loaders.cached.Loader', (
            'django.template.loaders.filesystem.Loader',
            'django.template.loaders.app_directories.Loader',
        )),
    )


# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'faq_db',
        'USER': 'root',
        'PASSWORD': 'local',
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en'

TIME_ZONE = 'Europe/Moscow'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = '/static/'

STATIC_ROOT = os.path.join(BASE_DIR, 'static')

INTERNAL_IPS = ('127.0.0.1', )


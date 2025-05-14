
import os
from pathlib import Path
from corsheaders.defaults import default_headers


BASE_DIR = Path(__file__).resolve().parent.parent



SECRET_KEY = 'django-insecure-o6$c%o0n=4b^4ysu(#)4^=@_-a@w0^j6rkuu$5^fwin&uga!8b'


DEBUG = True

ALLOWED_HOSTS = ["*"] 


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'API',
    'rest_framework_simplejwt.token_blacklist',
    'rest_framework.authtoken'
    
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'IWE.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'IWE.wsgi.application'



DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# settings.py

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        # "LOCATION": "redis://api.indiaworldexports.in:6379/1"  # Database 1 in Redis
        "LOCATION": "redis://127.0.0.1:6379/1",

    }
}



#cors-origine Allow

CORS_ALLOWED_ORIGINS = [    
    "https://indiaworldexports.in",
    "https://api.indiaworldexports.in",
    "http://16.171.26.52:8000",
    "http://127.0.0.1:5500"
]



CORS_ALLOW_HEADERS = list(default_headers) + [
    'Authorization',
]

CORS_ALLOW_ALL_ORIGINS = True

CORS_ALLOW_CREDENTIALS = True
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
        'rest_framework.authentication.TokenAuthentication',
    ),
}


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

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True




MEDIA_ROOT = os.path.join(BASE_DIR, 'images/') # 'data' is my media folder
MEDIA_URL = '/media/'
STATIC_URL = 'static/'
STATIC_ROOT= os.path.join(BASE_DIR,'staticfiles')



DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = 'smtp.gmail.com' # Mailtrap SMTP server
EMAIL_PORT = 587
EMAIL_HOST_USER = "no.reply.indiaworldexports@gmail.com"
EMAIL_HOST_PASSWORD = "llaj fixm smbi qaai"
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False


PAYU_MERCHANT_KEY = 'your_merchant_key'
PAYU_MERCHANT_SALT = 'your_merchant_salt'
PAYU_BASE_URL = 'https://secure.payu.in/_payment'  # production
# PAYU_BASE_URL = 'https://test.payu.in/_payment'  # testing


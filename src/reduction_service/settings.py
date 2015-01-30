"""
    Base settings for the SNS reduction/analysis web application.
    
    @author: M. Doucet, Oak Ridge National Laboratory
    @copyright: 2014 Oak Ridge National Laboratory
"""
# Django settings for reduction service project.
import os
import django

DEBUG = True
TEMPLATE_DEBUG = DEBUG
DEBUG_TOOLBAR = False

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': '%s/.reduction_service/sqlite.db' % os.path.expanduser('~'),
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }
}
DATABASES['default']['CONN_MAX_AGE']=5

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = [ '.ornl.gov', '.sns.gov', 'localhost', '127.0.0.1']

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'America/Chicago'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 2

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = '/var/www/reduction_service/static/'

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = '/reduction_service/static/'

# Additional locations of static files
STATICFILES_DIRS = (
                    os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..','static')),
                    #os.path.join(os.path.dirname(django.__file__),'contrib','admin','static'),
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = '53yke&lgb)0xwkzw2aji92df0xllmf)1sgee#%xeiq*-mll&6o'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

DEBUG_TOOLBAR_PATCH_SETTINGS = False
MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)
if DEBUG_TOOLBAR:
    MIDDLEWARE_CLASSES = ('debug_toolbar.middleware.DebugToolbarMiddleware',) + MIDDLEWARE_CLASSES

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'webcache',
    }
}

ROOT_URLCONF = 'reduction_service.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'reduction_service.wsgi.application'

TEMPLATE_DIRS = (
                 os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..','templates')),
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'django.contrib.admindocs',
    'users',
    'remote',
    'catalog',
    'plotting',
    'reduction',
)
if DEBUG_TOOLBAR:
    INSTALLED_APPS = INSTALLED_APPS + ('debug_toolbar',)

SESSION_SERIALIZER = 'django.contrib.sessions.serializers.JSONSerializer'

AUTHENTICATION_BACKENDS = (
                           'django_auth_ldap.backend.LDAPBackend',
                           'django.contrib.auth.backends.ModelBackend',
                           )

AUTH_LDAP_SERVER_URI = ""
AUTH_LDAP_USER_DN_TEMPLATE = ""

# Wb monitor url
WEBMON_URL = 'https://monitor.sns.gov/report/'
# Set the following to the local domain name
ALLOWED_DOMAIN = 'ornl.gov'
LOGIN_URL = 'users.views.perform_login'
LANDING_VIEW = 'catalog.views.instrument_list'
ALTERNATE_LANDING_VIEW = 'eqsans.views.reduction_home'

# Fermi information
FERMI_HOST = 'fermi.ornl.gov'
FERMI_BASE_URL = '/MantidRemote/'

LOGGING = {
   'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format' : "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            'datefmt' : "%d/%b/%Y %H:%M:%S"
        },
    },
    'handlers': {
        'null': {
            'level':'DEBUG',
            'class':'django.utils.log.NullHandler',
        },
        'console':{
            'level':'INFO',
            'class':'logging.StreamHandler',
            'formatter': 'standard'
        },
    },
    'loggers': {
        'django': {
            'handlers':['console'],
            'propagate': True,
            'level':'WARN',
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'django_auth_ldap': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
        'remote': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
        'catalog': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
        'reduction': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
        'reduction.eqsans': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
        'reduction.seq': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
        
    }
}

# Import local settings if available
try:
    from local_settings import *
except ImportError, e:
    LOCAL_SETTINGS = False
    pass

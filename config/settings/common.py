# -*- coding: utf-8 -*-
"""
    Base settings for the SNS reduction/analysis web application.
    
    @author: Ricardo Leal, Oak Ridge National Laboratory
    @copyright: 2015 Oak Ridge National Laboratory

Django settings for reduction_server project.

For more information on this file, see
https://docs.djangoproject.com/en/dev/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/dev/ref/settings/

"""

from __future__ import absolute_import, unicode_literals
from django_auth_ldap.config import LDAPSearch, PosixGroupType
import ldap

import environ

ROOT_DIR = environ.Path(__file__) - 3  # (/a/b/myfile.py - 3 = /)
APPS_DIR = ROOT_DIR.path('reduction_server')
env = environ.Env()
env.read_env() # reading .env file

# DEBUG
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#debug
DEBUG = env.bool("DEBUG", False)

# APP CONFIGURATION
# ------------------------------------------------------------------------------
## Instruments with "Reduce" link must be specified here
REDUCTION_AVAILABLE = ('eqsans','seq',)


DJANGO_APPS = (
    # Default Django apps:
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Useful template tags:
    # 'django.contrib.humanize',

    # Admin
    'django.contrib.admin',
    'django.contrib.admindocs',
)
THIRD_PARTY_APPS = (
)

# Apps specific for this project go here.
LOCAL_APPS = (
    'reduction_server.users',  # custom users app
    # Your stuff: custom apps go here
    'reduction_server.remote',
    'reduction_server.catalog',
    'reduction_server.plotting',
    'reduction_server.reduction',
    'reduction_server.seq',
    'reduction_server.eqsans',
)

# See: https://docs.djangoproject.com/en/dev/ref/settings/#installed-apps
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# MIDDLEWARE CONFIGURATION
# ------------------------------------------------------------------------------
MIDDLEWARE_CLASSES = (
    # Make sure djangosecure.middleware.SecurityMiddleware is listed first
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

# MIGRATIONS CONFIGURATION
# ------------------------------------------------------------------------------
MIGRATION_MODULES = {
    'sites': 'reduction_server.contrib.sites.migrations'
}

# FIXTURE CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-FIXTURE_DIRS
FIXTURE_DIRS = (
    str(APPS_DIR.path('fixtures')),
)

# EMAIL CONFIGURATION
# ------------------------------------------------------------------------------
EMAIL_BACKEND = env('EMAIL_BACKEND', default='django.core.mail.backends.smtp.EmailBackend')

# MANAGER CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#admins
ADMINS = (
    ("""Ricardo M. Ferraz Leal""", 'ferrazlealrm@ornl.gov'),
    #('Mathieu','doucetm@ornl.gov'), ('Mathieu','mdoucet@gmail.com'),
)

# See: https://docs.djangoproject.com/en/dev/ref/settings/#managers
MANAGERS = ADMINS

# DATABASE CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#databases
DATABASES = {
    'default': env.db(), # Raises ImproperlyConfigured exception if DATABASE_URL not in os.environ
    'extra': env.db('POSTGRES_URL', default='postgres:///reduction_server')
}

DATABASES['default']['ATOMIC_REQUESTS'] = True


# GENERAL CONFIGURATION
# ------------------------------------------------------------------------------
# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'America/New_York'

# See: https://docs.djangoproject.com/en/dev/ref/settings/#language-code
LANGUAGE_CODE = 'en-us'

# See: https://docs.djangoproject.com/en/dev/ref/settings/#site-id
SITE_ID = 1

# See: https://docs.djangoproject.com/en/dev/ref/settings/#use-i18n
USE_I18N = True

# See: https://docs.djangoproject.com/en/dev/ref/settings/#use-l10n
USE_L10N = True

# See: https://docs.djangoproject.com/en/dev/ref/settings/#use-tz
USE_TZ = True

# TEMPLATE CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#templates
TEMPLATES = [
    {
        # See: https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-TEMPLATES-BACKEND
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # See: https://docs.djangoproject.com/en/dev/ref/settings/#template-dirs
        'DIRS': [
            str(APPS_DIR.path('templates')),
        ],
        'OPTIONS': {
            # See: https://docs.djangoproject.com/en/dev/ref/settings/#template-debug
            'debug': DEBUG,
            # See: https://docs.djangoproject.com/en/dev/ref/settings/#template-loaders
            # https://docs.djangoproject.com/en/dev/ref/templates/api/#loader-types
            'loaders': [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
            ],
            # See: https://docs.djangoproject.com/en/dev/ref/settings/#template-context-processors
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
                # Your stuff: custom template context processors go here
            ],
        },
    },
]


# STATIC FILE CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#static-root
STATIC_ROOT = str(ROOT_DIR('static'))

# See: https://docs.djangoproject.com/en/dev/ref/settings/#static-url
STATIC_URL = '/static/'

# See: https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#std:setting-STATICFILES_DIRS
STATICFILES_DIRS = (
    str(APPS_DIR.path('static')),
)

# See: https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#staticfiles-finders
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

# MEDIA CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#media-root
MEDIA_ROOT = ''

# See: https://docs.djangoproject.com/en/dev/ref/settings/#media-url
MEDIA_URL = ''

# URL Configuration
# ------------------------------------------------------------------------------
ROOT_URLCONF = 'reduction_server.urls'

# See: https://docs.djangoproject.com/en/dev/ref/settings/#wsgi-application
WSGI_APPLICATION = 'config.wsgi.application'

# AUTHENTICATION CONFIGURATION
# ------------------------------------------------------------------------------
AUTHENTICATION_BACKENDS = (
   'django_auth_ldap.backend.LDAPBackend',
   'django.contrib.auth.backends.ModelBackend',
)

# Some really nice defaults
ACCOUNT_AUTHENTICATION_METHOD = 'username'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'

# Custom user app defaults
# Select the correct user model
# AUTH_USER_MODEL = 'users.User'
# LOGIN_REDIRECT_URL = 'users:redirect'
# LOGIN_URL = 'account_login'

# SLUGLIFIER
AUTOSLUG_SLUGIFY_FUNCTION = 'slugify.slugify'


# LOGGING CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#logging
# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s '
                      '%(process)d %(thread)d %(message)s'
        },
        'standard': {
            'format' : "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            'datefmt' : "%d/%b/%Y %H:%M:%S"
        },
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True
        },
        'django.security.DisallowedHost': {
            'level': 'ERROR',
            'handlers': ['console', 'mail_admins'],
            'propagate': True
        },        
        # Mine:
        'django': {
            'handlers':['console'],
            'level':'DEBUG',
            'propagate': True,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'INFO',
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
        'catalog.icat': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
        'reduction': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
        'reduction.forms': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
        'eqsans': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
        'seq': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
        'main': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    }
}


# Location of root django.contrib.admin URL, use {% url 'admin:index' %}
ADMIN_URL = r'^admin/'

# Your common stuff: Below this line define 3rd party library settings
GRAVATAR_URL = "http://www.gravatar.com/avatar/"
ALLOW_GUESTS = True

# Authentication settings
AUTH_LDAP_SERVER_URI = "ldaps://data.sns.gov/"
AUTH_LDAP_BIND_DN = ''
AUTH_LDAP_BIND_PASSWORD = ''
AUTH_LDAP_USER_DN_TEMPLATE = 'uid=%(user)s,ou=Users,dc=sns,dc=ornl,dc=gov'
AUTH_LDAP_GROUP_SEARCH = LDAPSearch( 'ou=Groups,dc=sns,dc=ornl,dc=gov',
                                     ldap.SCOPE_SUBTREE, '(objectClass=posixGroup)')
AUTH_LDAP_GROUP_TYPE = PosixGroupType()
AUTH_LDAP_GLOBAL_OPTIONS = { ldap.OPT_X_TLS_REQUIRE_CERT : ldap.OPT_X_TLS_NEVER,}
AUTH_LDAP_ALWAYS_UPDATE_USER = True

#   ICAT server settings
ICAT_DOMAIN = 'icat.sns.gov'
ICAT_PORT = 2080

# Fermi information
FERMI_HOST = 'fermi.ornl.gov'
FERMI_BASE_URL = '/MantidRemote/'

#    Web monitor URL
WEBMON_URL = 'https://monitor.sns.gov/report/'


# Set the following to the local domain name
ALLOWED_DOMAIN = 'ornl.gov'
LOGIN_URL = 'reduction_server.users.views.perform_login'
LANDING_VIEW = 'catalog'
ALTERNATE_LANDING_VIEW = 'home'


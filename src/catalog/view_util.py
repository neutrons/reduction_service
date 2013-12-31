from django.conf import settings
import logging
import sys

def get_new_reduction_url(instrument, run=None, ipts=None):
    """
        Return link to new reduction page if available
    """
    url = None
    if instrument.lower() in settings.INSTALLED_APPS:
        try:
            instrument_app = __import__(instrument.lower())
            if hasattr(instrument_app, 'get_new_reduction_url'):
                url = instrument_app.get_new_reduction_url(run, ipts)
        except:
            logging.error('Error getting URL: %s' % sys.exc_value)
    return url

def get_webmon_url(instrument, run=None, ipts=None):
    """
        Return link to web monitor (monitor.sns.gov)
    """
    if hasattr(settings, 'WEBMON_URL'):
        return "%s%s/%s/" % (settings.WEBMON_URL, instrument.lower(), run)
    return None

def get_remote_jobs_url(instrument):
    url = None
    if instrument.lower() in settings.INSTALLED_APPS:
        try:
            instrument_app = __import__(instrument.lower())
            if hasattr(instrument_app, 'get_remote_jobs_url'):
                url = instrument_app.get_remote_jobs_url()
        except:
            logging.error('Error getting URL: %s' % sys.exc_value)
    return url

def get_reduction_url(instrument):
    url = None
    if instrument.lower() in settings.INSTALLED_APPS:
        try:
            instrument_app = __import__(instrument.lower())
            if hasattr(instrument_app, 'get_reduction_url'):
                url = instrument_app.get_reduction_url()
        except:
            logging.error('Error getting URL: %s' % sys.exc_value)
    return url
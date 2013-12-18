from django.conf import settings
import logging
import sys

def get_new_reduction_url(instrument, run, ipts):
    url = None
    if instrument.lower() in settings.INSTALLED_APPS:
        try:
            instrument_app = __import__(instrument.lower())
            if hasattr(instrument_app, 'get_new_reduction_url'):
                url = instrument_app.get_new_reduction_url(run, ipts)
        except:
            logging.error('Error getting URL: %s' % sys.exc_value)
    else:
        if hasattr(settings, 'WEBMON_URL'):
            url = "%s%s/%s/" % (settings.WEBMON_URL, instrument.lower(), run)
    return url
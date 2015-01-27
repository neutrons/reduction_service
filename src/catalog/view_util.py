"""
    Catalog auxiliary view functions for the SNS analysis/reduction web application.
    
    @author: R. Leal, Oak Ridge National Laboratory
    @author: M. Doucet, Oak Ridge National Laboratory
    @copyright: 2015 Oak Ridge National Laboratory
"""


from django.conf import settings
import logging
import sys

logger = logging.getLogger('catalog')

def fill_template_values(request, **template_args):
    """
        Fill template values for catalog app
        The template URL values will be filled according to the app __init__.py functions
    """
    if 'instrument' in template_args:
        instrument = template_args['instrument']
        template_args['new_reduction_url'] = get_new_reduction_url(instrument)
        template_args['reduction_url'] = get_reduction_url(instrument)
        template_args['remote_url'] = get_remote_jobs_url(instrument)
    return template_args

def get_new_reduction_url(instrument, run=None, ipts=None):
    """
        Return link to new reduction page if available
    """
    url = None
    if instrument.lower() in settings.INSTALLED_APPS:
        try:
            instrument_app = __import__(instrument.lower())
            if hasattr(instrument_app, 'get_new_reduction_url'):
                url = instrument_app.get_new_reduction_url(run, ipts,instrument_name=instrument.lower())
        except Exception as e:
            logger.exception(e)
            logger.error('Error getting URL: %s' % sys.exc_value)
    return url

def get_reduction_url(instrument):
    url = None
    if instrument.lower() in settings.INSTALLED_APPS:
        try:
            instrument_app = __import__(instrument.lower())
            if hasattr(instrument_app, 'get_reduction_url'):
                url = instrument_app.get_reduction_url(instrument_name=instrument.lower())
        except Exception as e:
            logger.exception(e)
            logger.error('Error getting URL: %s' % sys.exc_value)
    return url

def get_remote_jobs_url(instrument):
    url = None
    if instrument.lower() in settings.INSTALLED_APPS:
        try:
            instrument_app = __import__(instrument.lower())
            if hasattr(instrument_app, 'get_remote_jobs_url'):
                url = instrument_app.get_remote_jobs_url(instrument_name=instrument.lower())
        except Exception as e:
            logger.exception(e)
            logger.error('Error getting URL: %s' % sys.exc_value)
    return url


def get_webmon_url(instrument, run=None, ipts=None):
    """
        Return link to web monitor (monitor.sns.gov)
    """
    if hasattr(settings, 'WEBMON_URL'):
        return "%s%s/%s/" % (settings.WEBMON_URL, instrument.lower(), run)
    return None



def get_new_batch_url(instrument, run=None, ipts=None):
    url = None
    if instrument.lower() in settings.INSTALLED_APPS:
        try:
            instrument_app = __import__(instrument.lower())
            if hasattr(instrument_app, 'get_new_batch_url'):
                url = instrument_app.get_new_batch_url(run, ipts)
        except Exception as e:
            logger.exception(e)
            logger.error('Error getting URL: %s' % sys.exc_value)
    return url
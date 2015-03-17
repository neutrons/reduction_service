"""
    Catalog auxiliary view functions for the SNS analysis/reduction web application.
    
    @author: R. Leal, Oak Ridge National Laboratory
    @author: M. Doucet, Oak Ridge National Laboratory
    @copyright: 2015 Oak Ridge National Laboratory
"""


from django.conf import settings
import logging
import sys
import inspect
import time
import pprint

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
              
        template_args['reduction_dialog'] = get_reduction_dialog_settings(instrument,
            ipts = template_args['experiment'] if 'experiment' in template_args.keys() else None) 
                                                                          
        
    return template_args

def _get_function_from_instrument_name(instrument_name,function_name):
    """
    Gets a function call object from an instrument name.
    Functions are available in reduction.<instrument name>.__init__
    """
    instrument = instrument_name.lower()
    module_str = instrument
    module = __import__ (module_str)
    try:
        func_to_call = getattr(module, function_name)
        return func_to_call
    except Exception as e:
        logger.exception(e)
        logger.error('Error getting function <%s> from module <%s>: %s' %(function_name, module_str, sys.exc_value) )
        return None

def get_new_reduction_url(instrument, run=None, ipts=None):
    """
        Return link to new reduction page if available
    """
    if instrument.lower() in settings.REDUCTION_AVAILABLE:
        this_function_name = inspect.stack()[0][3]
        func = _get_function_from_instrument_name(instrument, this_function_name)
        if func is not None:
            return func(run, ipts,instrument_name=instrument.lower())
        else:
            logger.debug("%s has no function %s."%(instrument, this_function_name))
            return None
    else:
        logger.debug("Reduction not available for %s."%(instrument))


def get_reduction_url(instrument):
    if instrument.lower() in settings.REDUCTION_AVAILABLE:
        this_function_name = inspect.stack()[0][3]
        func = _get_function_from_instrument_name(instrument, this_function_name)
        if func is not None:
            return func(instrument_name=instrument.lower())
        else:
            logger.debug("%s has no function %s."%(instrument, this_function_name))
            return None
    else:
        logger.debug("Reduction not available for %s."%(instrument))


def get_remote_jobs_url(instrument):

    if instrument.lower() in settings.REDUCTION_AVAILABLE:
        this_function_name = inspect.stack()[0][3]
        func = _get_function_from_instrument_name(instrument, this_function_name)
        if func is not None:
            return func(instrument_name=instrument.lower())
        else:
            logger.debug("%s has no function %s."%(instrument, this_function_name))
            return None
    else:
        logger.debug("Reduction not available for %s."%(instrument))


def get_new_batch_url(instrument, run=None, ipts=None):
    if instrument.lower() in settings.REDUCTION_AVAILABLE:
        this_function_name = inspect.stack()[0][3]
        func = _get_function_from_instrument_name(instrument, this_function_name)
        if func is not None:
            return func(run, ipts)
        else:
            logger.debug("%s has no function %s."%(instrument, this_function_name))
            return None
    else:
        logger.debug("Reduction not available for %s."%(instrument))

def get_webmon_url(instrument, run=None, ipts=None):
    """
        Return link to web monitor (monitor.sns.gov)
    """
    if hasattr(settings, 'WEBMON_URL'):
        return "%s%s/%s/" % (settings.WEBMON_URL, instrument.lower(), run)
    return None

def get_reduction_dialog_settings(instrument,ipts):
    if instrument.lower() in settings.REDUCTION_AVAILABLE:
        this_function_name = inspect.stack()[0][3]
        func = _get_function_from_instrument_name(instrument, this_function_name)
        if func is not None:
            return func(ipts)
        else:
            logger.debug("%s has no function %s."%(instrument, this_function_name))
            return None
    else:
        logger.debug("Reduction not available for %s."%(instrument))
                                             

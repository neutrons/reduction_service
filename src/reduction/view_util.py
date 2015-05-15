"""
    Utilities for general reduction views

    @author: R. Leal, Oak Ridge National Laboratory
    @copyright: 2015 Oak Ridge National Laboratory
"""


from reduction.models import RemoteJob
import remote.view_util
import importlib
import logging
from django.shortcuts import redirect

logger = logging.getLogger('reduction.view_util')

def get_latest_job(request, reduction_process):
    """
        Return the latest completed job for this reduction
        @param request: request object
        @param reduction_process: ReductionProcess object
    """
    latest_jobs = RemoteJob.objects.filter(reduction=reduction_process)
    if len(latest_jobs)>0:
        latest_job = latest_jobs.latest('id')
        # Check whether the job completed
        job_info = remote.view_util.query_job(request, latest_job.remote_id)
        if job_info is not None and 'JobStatus' in job_info and job_info['JobStatus']=='COMPLETED':
            return latest_job
    return None

def import_module_from_app(instrument_name_lowercase, module_name):
    """
    Note that all forms must be in reduction.<instrument name>.<module>
    @return the forms module from an instrument name 
    """
    module_str = "%s.%s"%(instrument_name_lowercase,module_name)
    instrument_module = importlib.import_module(module_str)
    return instrument_module

def redirect_if_view_exists(instrument_name, view_function, **kwargs):
    """
    if view_function function exists for an instrument_name it redirects to it
    Note! It only works for get! Posts are not redirected :
    HTTP POST data cannot go with redirect
    """
    try:
        this_instrument_view = import_module_from_app(instrument_name,'views')
        if view_function in dir(this_instrument_view):
            logger.debug("** %s has a view function named %s... Redirecting!!!."%(instrument_name, view_function))
            methodToCall = getattr(this_instrument_view, view_function)
            logger.debug("%s - %s - %s" % (this_instrument_view, view_function, methodToCall))
            return redirect(methodToCall, **kwargs);
    except Exception, e:
        logger.debug(e)
        return None
        
            
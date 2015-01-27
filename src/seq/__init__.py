"""
    Functions to buildup reduction URLs for SEQ
    They are called by the catalog.view_util
    
    TODO: This might havd to be merged with eqsans.__init__ into reduction.__init__ as this looks common stuff
    
    @author: R. Leal, Oak Ridge National Laboratory
    @author: M. Doucet, Oak Ridge National Laboratory
    @copyright: 2015 Oak Ridge National Laboratory
"""

from django.core.urlresolvers import reverse

def get_new_reduction_url(run=None, ipts=None, instrument_name=None):
    """
        Returns the URL to use to create a new run
        @param run: run number [string or integer]
        @param ipts: experiment name [string]
    """
    if run is None:
        return reverse('reduction.views.reduction_options', args=[instrument_name] )
    return reverse('reduction.views.reduction_options', args=[instrument_name] )+"?reduction_name=Reduction for %s&expt_name=%s&data_file=%s" % (run, ipts, run)

def get_new_batch_url(run=None, ipts=None):
    if run is None:
        return reverse('reduction.views.reduction_configuration', args={'instrument_name': 'seq' })
    return reverse('reduction.views.reduction_configuration',args={'instrument_name': 'seq' })+"?reduction_name=Reduction for %s&experiment=%s&data_file=%s" % (run, ipts, run)

def get_remote_jobs_url(ipts=None, instrument_name=None):
    return reverse('reduction.views.reduction_jobs', args=[instrument_name])

def get_reduction_url(ipts=None, instrument_name=None):
    return reverse('reduction.views.reduction_home', args=[instrument_name] )
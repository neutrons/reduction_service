"""
    Functions to buildup reduction URLs for EQSANS
    They are called by the catalog.view_util
    
    TODO: This might havd to be merged with seq.__init__ into reduction.__init__ as this looks common stuff
    
    @author: R. Leal, Oak Ridge National Laboratory
    @author: M. Doucet, Oak Ridge National Laboratory
    @copyright: 2015 Oak Ridge National Laboratory
"""

from django.core.urlresolvers import reverse
import json

INSTRUMENT_NAME="eqsans"

def get_reduction_dialog_settings(ipts):
    """
    This return the json to generate the reduction dialog
    """
    dialog_json = [
       {
          "name":"Single",
          "desc":"A <b>single</b> reduction, which will create a reduction job only for this run.",
          "href": get_new_reduction_url(),
          "parameters" : { "reduction_name" :  "Single reduction for ${run}",
                          "expt_name" : ipts,
                          "data_file" : "${run}"
                          }
       },
       {
          "name":"Batch",
          "desc":"A reduction <b>batch</b>, which will create a configuration that you can use with multiple runs.",
          "href": get_new_batch_url(),
          "parameters" : { "reduction_name" :  "Batch reduction for exp: %s run: ${run}"%ipts,
                          "experiment" : ipts,
                          "data_file" : "${run}"
                          }
       }
    ]
    #return dialog_json;
    return json.dumps(dialog_json);


def get_new_reduction_url(run=None, ipts=None):
    """
        Returns the URL to use to create a new run
        @param run: run number [string or integer]
        @param ipts: experiment name [string]
    """
    if run is None:
        return reverse('reduction.views.reduction_options', kwargs={'instrument_name': INSTRUMENT_NAME } )
    return reverse('reduction.views.reduction_options', kwargs={'instrument_name': INSTRUMENT_NAME } )+"?reduction_name=Reduction for %s&expt_name=%s&data_file=%s" % (run, ipts, run)

def get_new_batch_url(run=None, ipts=None):
    if run is None:
        return reverse('reduction.views.reduction_configuration', kwargs={'instrument_name': INSTRUMENT_NAME })
    return reverse('reduction.views.reduction_configuration',kwargs={'instrument_name': INSTRUMENT_NAME })+"?reduction_name=Reduction for %s&experiment=%s&data_file=%s" % (run, ipts, run)

def get_remote_jobs_url(ipts=None, instrument_name=None):
    return reverse('reduction.views.reduction_jobs', args=[instrument_name])

def get_reduction_url(ipts=None, instrument_name=None):
    return reverse('reduction.views.reduction_home', args=[instrument_name] )
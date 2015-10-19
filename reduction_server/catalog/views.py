"""
    Catalog views for the SNS analysis/reduction web application.
    
    @author: M. Doucet, Oak Ridge National Laboratory
    @copyright: 2014 Oak Ridge National Laboratory
"""
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.core.urlresolvers import reverse
from django.views.decorators.cache import cache_page
from django.conf import settings
from django.http import HttpResponse
from django.template import RequestContext

from icat_server_communication import get_ipts_runs, get_instruments, get_experiments, get_run_info, get_ipts_runs_as_json, get_experiments_as_json
import reduction_server.catalog.view_util as catalog_view_util
import reduction_server.remote.view_util as remote_view_util
import reduction_server.users.view_util as users_view_util
import json
import logging
import time
import inspect
import pprint

from reduction_server.view_util import Breadcrumbs

logger = logging.getLogger('catalog')

@login_required
def instrument_list(request):
    """
        Return a list of available instruments
        @param request: request object
    """
    breadcrumbs = Breadcrumbs("home", None)
    instruments = get_instruments()
    
    logger.debug("Catalog: %s : List of instruments = %s"%(inspect.stack()[0][3],instruments))
    
    template_values = {'breadcrumbs': breadcrumbs}
    if len(instruments)==0:
#         if settings.DEBUG:
#             instruments=['eqsans']
        template_values['user_alert'] = ['Could not get instrument list from the catalog']
    template_values['instruments'] = instruments
    template_values = remote_view_util.fill_template_values(request, **template_values)
    template_values = catalog_view_util.fill_template_values(request, **template_values)
    template_values = users_view_util.fill_template_values(request, **template_values)
    return render_to_response('catalog/instrument_list.html',
                              template_values)
    
@login_required
def experiment_list(request, instrument):
    """
        Return the list of experiments for a given instrument
        @param request: request object
        @param instrument: instrument name
    """
    
    breadcrumbs = Breadcrumbs("home", reverse('home'))
    breadcrumbs.append("%s catalog"%instrument.lower())
    
    experiments = get_experiments(instrument.upper())
    
    logger.debug("Catalog: %s : len(experiment list) = %s for %s"%(inspect.stack()[0][3],len(experiments),instrument))
    
    template_values = {'experiments': experiments,
                       'instrument': instrument,
                       'title': '%s experiments' % instrument.upper(),
                       'breadcrumbs': breadcrumbs}
    if len(experiments)==0:
        template_values['user_alert'] = ['Could not get experiment list from the catalog']
    template_values = remote_view_util.fill_template_values(request, **template_values)
    template_values = catalog_view_util.fill_template_values(request, **template_values)
    template_values = users_view_util.fill_template_values(request, **template_values)
    return render_to_response('catalog/experiment_list.html',
                              template_values,
                              context_instance=RequestContext(request))
    
@login_required
def experiment_run_list(request, instrument, ipts):
    """
        Return a list of runs for a given experiment with the reduce link.
        The reduce link will generate a JQuery Dialog unique per instrument
        The configuration of the Dialog Box are in <instrument_name>.__init__.py
        under the funtion get_reduction_dialog_settings(ipts, run)
        @param request: request object
        @param instrument: instrument name
        @param ipts: experiment name
    """
    
    logger.debug("Catalog: %s : instrument = %s, IPTS = %s"%(inspect.stack()[0][3],instrument,ipts))
    
    
    
    breadcrumbs = Breadcrumbs("home", reverse('catalog'))
    breadcrumbs.append_experiment_list(instrument)
    breadcrumbs.append(ipts.lower())
        
    template_values = {'instrument': instrument,
                       'experiment': ipts,
                       'title': '%s %s' % (instrument.upper(), ipts.upper()),
                       'breadcrumbs': breadcrumbs}

    if users_view_util.is_experiment_member(request, instrument, ipts) is False:
        template_values['user_alert'] = ["You do not have access to this experiment data."]
    else:
        runs = get_ipts_runs(instrument.upper(), ipts)
        template_values['run_data'] = runs
        if len(runs) == 0:
            template_values['user_alert'] = ['No runs were found for instrument %s experiment %s' % (instrument, ipts)]
    # Fill in Fermi auth values, login info,
    template_values = remote_view_util.fill_template_values(request, **template_values)
    template_values = catalog_view_util.fill_template_values(request, **template_values)
    template_values = users_view_util.fill_template_values(request, **template_values)
    return render_to_response('catalog/experiment_run_list.html', template_values)
    
@login_required
@cache_page(120)
def run_info(request, instrument, run_number):
    """
         Ajax call to get run information (retrieved from ICAT)
         @param request: request object
         @param instrument: instrument name
         @param run_number: run number
    """ 
    info_dict = get_run_info(instrument, run_number)
    response = HttpResponse(json.dumps(info_dict), content_type="application/json")
    # Ricardo : commenting this to avoid : AssertionError: Hop-by-hop headers not allowed
    # response['Connection'] = 'close'
    return response

@login_required
def download_autoreduced(request, instrument, ipts):
    """
        Download all the auto-reduced files for a given experiment.
        @param request: request object
        @param instrument: instrument name
        @param ipts: experiment name
    """
    # Start a new transaction
    transaction = remote_view_util.transaction(request, start=True)
    if transaction is None:
        
        breadcrumbs = Breadcrumbs()
        breadcrumbs.append_experiment_list(instrument)
        
        template_values = {'message':"Could not connect to Fermi and establish transaction",
                           'back_url': reverse('catalog_experiments', args=[instrument]),
                           'breadcrumbs': breadcrumbs,}
        template_values = remote_view_util.fill_template_values(request, **template_values)
        template_values = catalog_view_util.fill_template_values(request, **template_values)
        return render_to_response('remote/failed_connection.html',
                                  template_values)

    file_name = "%s_%s.zip" % (instrument.upper(), ipts)
    code =  'import os\n'
    code += 'import zipfile\n'
    code += 'output_zip_file = zipfile.ZipFile("%s", "w")\n' % file_name
    code += 'for f in os.listdir("/SNS/%s/%s/shared/autoreduce"):\n' % (instrument.upper(), ipts.upper())
    code += '    output_zip_file.write("/SNS/%s/%s/shared/autoreduce/"+f, f)\n' % (instrument.upper(), ipts.upper())
    code += 'output_zip_file.close()\n'
    jobID = remote_view_util.submit_job(request, transaction, code)

    return redirect(reverse('catalog_download_link', args=[jobID, file_name]))

@login_required
def download_link(request, job_id, filename):
    """
        Waiting page to get a link to download a zip file containing
        all the auto-reduced data for a given IPTS.
        @param request: request object
        @param job_id: remote job ID 
    """
    template_values = remote_view_util.fill_job_values(request, job_id)
    template_values = remote_view_util.fill_template_values(request, **template_values)
    template_values = catalog_view_util.fill_template_values(request, **template_values)
    template_values['title'] = 'Download area'
    template_values['file_name'] = filename
    return render_to_response('catalog/download_link.html',
                              template_values)
    

# @login_required
# #@cache_page(60)
# def run_range(request, instrument, ipts):
#     """
#          Ajax call to get all the possible runs for an experiment (retrieved from ICAT)
#          @param request: request object
#          @param instrument: instrument name
#          @param ipts: experiment id
#     """ 
#     info_dict = get_ipts_run_range(instrument, ipts)
#     response = HttpResponse(json.dumps(info_dict), content_type="application/json")
#     return response

@login_required
@cache_page(20)
def runs_json(request, instrument, ipts):
    """
         Ajax call to get all the possible runs for an experiment (retrieved from ICAT)
         @param request: request object
         @param instrument: instrument name
         @param ipts: experiment id
    """ 
    logger.debug("Fecthing runs as jsons for ipts = %s"%ipts)
    info_dict = get_ipts_runs_as_json(instrument, ipts)
    response = HttpResponse(json.dumps(info_dict), content_type="application/json")
    return response

@login_required
@cache_page(20)
def experiments_json(request, instrument):
    """
         Ajax call to get all the possible experiments (retrieved from ICAT)
         @param request: request object
         @param instrument: instrument name
         @param ipts: experiment id
    """ 
    experiment_list = get_experiments_as_json(instrument)
    
    for exp in experiment_list:
        ipts = exp['value']
        if users_view_util.is_experiment_member(request, instrument, ipts ) is False:
            experiment_list.remove(exp)
    
    # TODO: Filter permissions
    response = HttpResponse(json.dumps(experiment_list), content_type="application/json")
    return response


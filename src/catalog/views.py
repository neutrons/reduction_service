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

from icat_server_communication import get_ipts_runs, get_instruments, get_experiments, get_run_info
import catalog.view_util
import remote.view_util
import users.view_util
import reduction_service.view_util
import json
import logging
import time

logger = logging.getLogger('catalog')

@login_required
def instrument_list(request):
    """
        Return a list of available instruments
        @param request: request object
    """
    breadcrumbs = "home"
    instruments = get_instruments()
    template_values = {'breadcrumbs': breadcrumbs}
    if len(instruments)==0:
        if settings.DEBUG:
            instruments=['eqsans']
        template_values['user_alert'] = ['Could not get instrument list from the catalog']
    template_values['instruments'] = instruments
    template_values = reduction_service.view_util.fill_template_values(request, **template_values)
    return render_to_response('catalog/instrument_list.html',
                              template_values)
    
@login_required
def experiment_list(request, instrument):
    """
        Return the list of experiments for a given instrument
        @param request: request object
        @param instrument: instrument name
    """
    breadcrumbs = "<a href='%s'>home</a> &rsaquo; %s catalog" % (reverse('home'), instrument.lower())
    experiments = get_experiments(instrument.upper())
    template_values = {'experiments': experiments,
                       'instrument': instrument,
                       'title': '%s experiments' % instrument.upper(),
                       'breadcrumbs': breadcrumbs}
    if len(experiments)==0:
        template_values['user_alert'] = ['Could not get experiment list from the catalog']
    template_values = reduction_service.view_util.fill_template_values(request, **template_values)
    template_values = catalog.view_util.fill_template_values(request, **template_values)
    return render_to_response('catalog/experiment_list.html',
                              template_values)
    
@login_required
def experiment_run_list(request, instrument, ipts):
    """
        Return a list of runs for a given experiment
        @param request: request object
        @param instrument: instrument name
        @param ipts: experiment name
    """
    breadcrumbs = "<a href='%s'>home</a> &rsaquo; <a href='%s'>%s catalog</a> &rsaquo; %s" % (reverse('catalog.views.instrument_list'),
                                                                                             reverse('catalog.views.experiment_list', args=[instrument]),
                                                                                             instrument.lower(),
                                                                                             ipts.lower(),
                                                                                             )
    template_values = {'instrument': instrument,
                       'experiment': ipts,
                       'title': '%s %s' % (instrument.upper(), ipts.upper()),
                       'breadcrumbs': breadcrumbs}

    if users.view_util.is_experiment_member(request, instrument, ipts) is False:
        template_values['user_alert'] = ["You do not have access to this experiment data."]
    else:
        runs = get_ipts_runs(instrument.upper(), ipts)
        template_values['run_data'] = runs
        if len(runs)==0:
            template_values['user_alert'] = ['No runs were found for instrument %s experiment %s' % (instrument, ipts)]
    template_values = reduction_service.view_util.fill_template_values(request, **template_values)
    template_values = catalog.view_util.fill_template_values(request, **template_values)
    return render_to_response('catalog/experiment_run_list.html',
                              template_values)
    
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
    transaction = remote.view_util.transaction(request, start=True)
    if transaction is None:
        breadcrumbs = "<a href='%s'>home</a>" % reverse(settings.LANDING_VIEW)
        breadcrumbs += " &rsaquo; <a href='%s'>%s reduction</a>" % (reverse('catalog.views.experiment_list', args=[instrument]), instrument)
        template_values = {'message':"Could not connect to Fermi and establish transaction",
                           'back_url': reverse('catalog.views.experiment_list', args=[instrument]),
                           'breadcrumbs': breadcrumbs,}
        template_values = reduction_service.view_util.fill_template_values(request, **template_values)
        return render_to_response('remote/failed_connection.html',
                                  template_values)

    file_name = "%s_%s.zip" % (instrument.upper(), ipts)
    code =  'import os\n'
    code += 'import zipfile\n'
    code += 'output_zip_file = zipfile.ZipFile("%s", "w")\n' % file_name
    code += 'for f in os.listdir("/SNS/%s/%s/shared/autoreduce"):\n' % (instrument.upper(), ipts.upper())
    code += '    output_zip_file.write("/SNS/%s/%s/shared/autoreduce/"+f, f)\n' % (instrument.upper(), ipts.upper())
    code += 'output_zip_file.close()\n'
    jobID = remote.view_util.submit_job(request, transaction, code)

    return redirect(reverse('catalog.views.download_link', args=[jobID, file_name]))

@login_required
def download_link(request, job_id, filename):
    """
        Waiting page to get a link to download a zip file containing
        all the auto-reduced data for a given IPTS.
        @param request: request object
        @param job_id: remote job ID 
    """
    template_values = remote.view_util.fill_job_dictionary(request, job_id)
    template_values = reduction_service.view_util.fill_template_values(request, **template_values)
    template_values = catalog.view_util.fill_template_values(request, **template_values)
    template_values['title'] = 'Download area'
    template_values['file_name'] = filename
    return render_to_response('catalog/download_link.html',
                              template_values)
    


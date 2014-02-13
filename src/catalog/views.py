from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django.conf import settings
from django.http import HttpResponse

from icat_server_communication import get_ipts_runs, get_instruments, get_experiments, get_ipts_info, get_run_info
import catalog.view_util
import reduction_service.view_util
import logging
import sys
import json

@login_required
def instrument_list(request):
    """
        Return a list of available instruments
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
def experiment_run_list(request, instrument, ipts='IPTS-8340'):

    breadcrumbs = "<a href='%s'>home</a> &rsaquo; <a href='%s'>%s catalog</a> &rsaquo; %s" % (reverse('catalog.views.instrument_list'),
                                                                                             reverse('catalog.views.experiment_list', args=[instrument]),
                                                                                             instrument.lower(),
                                                                                             ipts.lower(),
                                                                                             )
    runs = get_ipts_runs(instrument.upper(), ipts)
    # Backward compatibility while we are developing ICAT in parallel
    if len(runs)==0:
        icat_ipts = get_ipts_info(instrument.upper(), ipts)
        if 'run_range' in icat_ipts:
            try:
                toks = icat_ipts['run_range'].split('-')
                r_min = int(toks[0])
                r_max = int(toks[1])
                for r in range(r_min, r_max+1):
                    runs.append({'id':r,
                                 'webmon_url': catalog.view_util.get_webmon_url(instrument, r, ipts),
                                 'reduce_url': catalog.view_util.get_new_reduction_url(instrument, r, ipts)})
            except:
                logging.error("Problem generating run list: %s" % sys.exc_value)

    template_values = {'run_data': runs,
                       'instrument': instrument,
                       'experiment': ipts,
                       'title': '%s %s' % (instrument.upper(), ipts.upper()),
                       'breadcrumbs': breadcrumbs}
    if len(runs)==0:
        template_values['user_alert'] = ['No runs were found for instrument %s experiment %s' % (instrument, ipts)]
    template_values = reduction_service.view_util.fill_template_values(request, **template_values)
    template_values = catalog.view_util.fill_template_values(request, **template_values)
    return render_to_response('catalog/experiment_run_list.html',
                              template_values)
    
@login_required
#@cache_page(120)
def run_info(request, instrument, run_number):
    """
         Ajax call to get run information (retrieved from ICAT)
         @param instrument: instrument name
         @param run_number: run number
    """ 
    info_dict = get_run_info(instrument, run_number)
    response = HttpResponse(json.dumps(info_dict), content_type="application/json")
    response['Connection'] = 'close'
    return response

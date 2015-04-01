
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.conf import settings
from django.forms.formsets import formset_factory
from django.http import HttpResponse

from reduction.models import Instrument, Experiment
import reduction_service.view_util
import reduction.view_util
import remote.view_util
import forms as reduction_forms
from reduction.models import ReductionProcess, RemoteJob, ReductionConfiguration, RemoteJobSet
from catalog.icat_server_communication import get_ipts_info
import copy
import importlib
import inspect
import logging
from django.template.defaultfilters import pprint
import pprint

from reduction_service.view_util import Breadcrumbs

logger = logging.getLogger('reduction')

def _import_module_from_app(instrument_name_lowercase, module_name):
    """
    Note that all forms must be in reduction.<instrument name>.<module>
    @return the forms module from an instrument name 
    """
    module_str = "%s.%s"%(instrument_name_lowercase,module_name)
    instrument_module = importlib.import_module(module_str)
    return instrument_module
   

@login_required
def reduction_home(request, instrument_name):
    """
        Home page for the <instrument_name> reduction.
        This will show a list of experiments for which the user have set up reductions.
        @param request: request object
    """
    logger.debug("Reduction: %s instrument_name=%s"%(inspect.stack()[0][3],instrument_name))
    
    instrument = get_object_or_404(Instrument, name=instrument_name)
    
    experiments = Experiment.objects.experiments_for_instrument(instrument, owner=request.user)
    
    breadcrumbs = Breadcrumbs()
    breadcrumbs.append("%s reduction"%instrument_name)    
    
    template_values = {'title': str.capitalize(str(instrument_name)) + ' Reduction',
                       'experiments':experiments,
                       'breadcrumbs': breadcrumbs,
                       'instrument' : instrument_name, }
    template_values = reduction_service.view_util.fill_template_values(request, **template_values)
    return render_to_response('%s/reduction_home.html'%instrument_name,
                              template_values)


@login_required
def experiment(request, ipts, instrument_name):
    """
        List of reductions and configurations for a given experiment
        @param request: request object
        @param ipts: experiment name
        
        #TODO create new reduction using a pre-existing one as a template
    """
    
    logger.debug("Reduction: %s instrument_name=%s"%(inspect.stack()[0][3],instrument_name))
    
    instrument_name_capitals = str.capitalize(str(instrument_name))
    instrument_name_lowercase = str.lower(str(instrument_name))
    
    # Get experiment object
    uncategorized = Experiment.objects.get_uncategorized(instrument_name)
    try:
        experiment_obj = Experiment.objects.get(name=ipts)
    except:
        experiment_obj = uncategorized
    
    IS_UNCATEGORIZED = experiment_obj.is_uncategorized()

    reduction_start_form = reduction_forms.ReductionStart(request.GET)

    icat_ipts = {}
    if not IS_UNCATEGORIZED:
        icat_ipts = get_ipts_info(str.capitalize(str(instrument_name)), ipts)

    # Get all the user's reductions
    red_list = []
    if 'run_number' in request.GET:
        red_list = ReductionProcess.objects.filter(owner=request.user,
                                                   data_file__contains=request.GET['run_number'])
        if len(red_list) == 0:
            create_url = reverse('reduction_options',
                                  kwargs={'instrument_name': instrument_name_lowercase})
            create_url += '?reduction_name=Reduction for r%s' % request.GET['run_number']
            create_url += '&expt_id=%d' % experiment_obj.id
            create_url += '&data_file=%s' % request.GET['run_number']
            return redirect(create_url)
    else:
        for item in ReductionProcess.objects.filter(owner=request.user,
                                                    experiments=experiment_obj).order_by('data_file'):
            if not item in red_list:
                red_list.append(item)

    reductions = []
    for r in red_list:
        data_dict = r.get_data_dict()
        data_dict['id'] = r.id
        data_dict['config'] = r.get_config()
        latest_job = reduction.view_util.get_latest_job(request, r)
        if latest_job is not None:
            data_dict['completed_job'] = reverse('reduction_job_details',
                                                 kwargs={'job_id' : latest_job.remote_id,
                                                         'instrument_name': instrument_name_lowercase })
        try:
            run_id = int(data_dict['data_file'])
            data_dict['webmon_url'] = "https://monitor.sns.gov/report/%s/%s/" %(instrument_name,run_id)
        except:
            pass
        reductions.append(data_dict)
        
    # Get all user configurations
    config_list = ReductionConfiguration.objects.filter(owner=request.user,
                                                        experiments=experiment_obj).order_by('name')
    configurations = []
    for item in config_list:
        data_dict = item.get_data_dict()
        data_dict['id'] = item.id
        latest_jobs = RemoteJobSet.objects.filter(configuration=item)
        if len(latest_jobs) > 0:
            latest_job = latest_jobs.latest('id')
            data_dict['latest_job'] = latest_job.id
            # data_dict['latest_job'] = reverse('eqsans.views.configuration_query', args=[latest_job.id])
        configurations.append(data_dict)
    
    breadcrumbs = Breadcrumbs()
    breadcrumbs.append_reduction(instrument_name_lowercase)
    breadcrumbs.append(ipts.lower())
    
    template_values = {'reductions': reductions,
                       'configurations': configurations,
                       'title': '%s %s' % (instrument_name_capitals, ipts),
                       'breadcrumbs': breadcrumbs,
                       'ipts_number': ipts,
                       'back_url': reverse('reduction_experiment', kwargs={'ipts' : ipts, 'instrument_name': instrument_name_lowercase }),
                       'icat_info': icat_ipts,
                       'form': reduction_start_form,
                       'is_categorized': not IS_UNCATEGORIZED,
                       'instrument' : instrument_name_lowercase, }
    if 'icat_error' in icat_ipts:
        template_values['user_alert'] = [icat_ipts['icat_error']]
    template_values = reduction_service.view_util.fill_template_values(request, **template_values)
    #logger.debug(pprint.pformat(reductions))
    
    return render_to_response('%s/experiment.html' % instrument_name_lowercase,
                              template_values)
    
@login_required
def delete_reduction(request, reduction_id, instrument_name):
    """
        Delete a reduction process entry
        @param request: request object
        @param reduction_id: primary key of reduction object
    """
    
    logger.debug("Reduction: %s instrument_name=%s"%(inspect.stack()[0][3],instrument_name))
    
    reduction_proc = get_object_or_404(ReductionProcess, pk=reduction_id, owner=request.user)
    reduction_proc.delete()
    if 'back_url' in request.GET:
        return redirect(request.GET['back_url'])
    return redirect(reverse('reduction_home', args=[instrument_name]))




@login_required
def reduction_options(request, reduction_id=None, instrument_name=None):
    """
        Display the reduction options form:
        
        If reduction_id exists already then it can be submitted as a new job
            
        @param request: request object
        @param reduction_id: pk of reduction process object
    """
    
    logger.debug("Reduction: %s instrument_name=%s"%(inspect.stack()[0][3],instrument_name))
    
    instrument_name_capitals = str.capitalize(str(instrument_name))
    instrument_name_lowercase = str.lower(str(instrument_name))
    instrument_forms = _import_module_from_app(instrument_name_lowercase,'forms')
    
    template_values = {}
    # Get reduction and configuration information
    config_obj = None
    if reduction_id is not None:
        reduction_proc = get_object_or_404(ReductionProcess, pk=reduction_id, owner=request.user)
        config_obj = reduction_proc.get_config()
    
    if request.method == 'POST':
        #logger.debug(pprint.pformat(request.POST.items()))
        
        options_form = instrument_forms.ReductionOptions(request.POST)
        # If the form is valid update or create an entry for it (if the data_file is different, a new entry is created!)
        if options_form.is_valid():
            reduction_id = options_form.to_db(request.user, reduction_id)
            template_values['message'] = "Reduction parameters for reduction %s were sucessfully updated."%reduction_id
            if reduction_id is not None:
                return redirect(reverse('reduction_options',
                                        kwargs={'reduction_id' : reduction_id, 'instrument_name' : instrument_name})+
                                        "?message=%s"%template_values['message'])
    else:
        if reduction_id is not None:
            initial_values = instrument_forms.ReductionOptions.data_from_db(request.user, reduction_id)
        else:
            initial_values = copy.deepcopy(request.GET)
            if 'expt_name' in request.GET:
                initial_values['experiment'] = request.GET['expt_name']
        options_form = instrument_forms.ReductionOptions(initial=initial_values)
    
    breadcrumbs = Breadcrumbs()
    breadcrumbs.append_reduction(instrument_name_lowercase)
    
    if config_obj is not None:
        breadcrumbs.append_configuration(instrument_name_lowercase,config_obj.id)
    if reduction_id is not None:
        breadcrumbs.append("reduction %s" % reduction_id)
    else:
        breadcrumbs.append("new reduction")

    # ICAT info url
    icat_url = reverse('catalog.views.run_info', args=[instrument_name_capitals, '0000'])
    icat_url = icat_url.replace('/0000', '')
    # TODO: add New an Save-As functionality
    template_values.update({'options_form': options_form,
                       'title': '%s Reduction' % instrument_name_capitals,
                       'breadcrumbs': breadcrumbs,
                       'reduction_id': reduction_id,
                       'icat_url': icat_url,
                       'instrument' : instrument_name_lowercase, })
    # Get existing jobs for this reduction
    if reduction_id is not None:
        existing_jobs = RemoteJob.objects.filter(reduction=reduction_proc)
        if len(existing_jobs) > 0:
            template_values['existing_jobs'] = existing_jobs.order_by('id')
        template_values['expt_list'] = reduction_proc.experiments.all()
        
    
    if 'message' in request.GET:
        template_values['message'] = request.GET['message']
    
    template_values = reduction_service.view_util.fill_template_values(request, **template_values)
    #logger.debug(pp.pformat(template_values))
    return render_to_response('%s/reduction_options.html' % instrument_name_lowercase,
                              template_values)

@login_required
def reduction_jobs(request, instrument_name):
    """
        Return a list of the remote reduction jobs.
        The jobs are those that are owned by the user and have an
        entry in the database.
        
        @param request: request object
    """
    logger.debug("Reduction: %s instrument_name=%s"%(inspect.stack()[0][3],instrument_name))
    
    instrument_name = str(instrument_name).lower()
    
    jobs = RemoteJob.objects.filter(transaction__owner=request.user)
    status_data = []
    for job in jobs:
        if not job.transaction.is_active or job.reduction.get_config() is not None:
            continue
        j_data = {'id': job.remote_id,
                  'name': job.reduction.name,
                  'reduction_id': job.reduction.id,
                  'start_date': job.transaction.start_time,
                  'data': job.reduction.data_file,
                  'trans_id': job.transaction.trans_id,
                  'experiments': job.reduction.get_experiments()
                 }
        status_data.append(j_data)
    
    # Get config jobs
    config_jobs = RemoteJobSet.objects.filter(transaction__owner=request.user)
    config_data = []
    for job in config_jobs:
        logger.debug("Config jobs: %s"%job)
        if not job.transaction.is_active:
            continue
        j_data = {'id': job.id,
                  'config_id': job.configuration.id,
                  'name': job.configuration.name,
                  'trans_id': job.transaction.trans_id,
                  'experiments': job.configuration.get_experiments()
                 }
        config_data.append(j_data)
        
    breadcrumbs = Breadcrumbs()
    breadcrumbs.append_reduction(str.lower(str(instrument_name)))
    breadcrumbs.append("jobs")
    template_values = {'status_data': status_data,
                       'config_data': config_data,
                       'back_url': request.path,
                       'breadcrumbs': breadcrumbs,
                       'instrument' : instrument_name, }
    template_values = reduction_service.view_util.fill_template_values(request, **template_values)   
    return render_to_response('%s/reduction_jobs.html' % instrument_name,
                              template_values)    






    

@login_required
def reduction_script(request, reduction_id, instrument_name):
    """
        Display a script representation of a reduction process.
        
        @param request: request object
        @param reduction_id: pk of the ReductionProcess object
    """
    
    logger.debug("Reduction: %s instrument_name=%s"%(inspect.stack()[0][3],instrument_name))
    
    instrument_name_lowercase = str.lower(str(instrument_name))
    
    instrument_forms = _import_module_from_app(instrument_name_lowercase,'forms')
    
    data = instrument_forms.ReductionOptions.data_from_db(request.user, reduction_id)
    
    breadcrumbs = Breadcrumbs()
    breadcrumbs.append_reduction(instrument_name_lowercase)
    breadcrumbs.append("reduction %s"%reduction_id,".")
    breadcrumbs.append("script")
    
    template_values = {'reduction_name': data['reduction_name'],
                       'breadcrumbs': breadcrumbs,
                       'code': instrument_forms.ReductionOptions.as_mantid_script(data) }
    template_values = reduction_service.view_util.fill_template_values(request, **template_values)
    return render_to_response('reduction/reduction_script.html', template_values)

@login_required
def py_reduction_script(request, reduction_id, instrument_name):
    """
        Return the python script for a reduction process.
        
        @param request: request object
        @param reduction_id: pk of the ReductionProcess object
    """
    
    logger.debug("Reduction: %s instrument_name=%s"%(inspect.stack()[0][3],instrument_name))
    
    instrument_name_lowercase = str.lower(str(instrument_name))
    instrument_forms = _import_module_from_app(instrument_name_lowercase,'forms')
    
    data = instrument_forms.ReductionOptions.data_from_db(request.user, reduction_id) 
    response = HttpResponse(instrument_forms.ReductionOptions.as_mantid_script(data))
    response['Content-Disposition'] = 'attachment; filename="%s_reduction.py"' % instrument_name_lowercase
    response['Content-Type'] = "text/x-python;charset=UTF-8"
    response["Content-Description"] = "File Transfer";
    return response

@login_required
def xml_reduction_script(request, reduction_id, instrument_name):
    """
        Return the xml representation of a reduction process that the user
        can load into Mantid.
        
        @param request: request object
        @param reduction_id: pk of the ReductionProcess object
    """
    
    logger.debug("Reduction: %s instrument_name=%s"%(inspect.stack()[0][3],instrument_name))
    
    instrument_name_lowercase = str.lower(str(instrument_name))
    instrument_forms = _import_module_from_app(instrument_name_lowercase,'forms')
    data = instrument_forms.ReductionOptions.data_from_db(request.user, reduction_id) 
    response = HttpResponse(instrument_forms.ReductionOptions.as_xml(data))
    response['Content-Disposition'] = 'attachment; filename="%s_reduction.xml"' % instrument_name_lowercase
    response['Content-Type'] = "text/xml;charset=UTF-8"
    response["Content-Description"] = "File Transfer";
    return response

@login_required
def submit_job(request, reduction_id, instrument_name):
    """
        Submit a reduction script to Fermi.

        @param request: request object
        @param reduction_id: pk of the ReductionProcess object
    """
    
    logger.debug("Reduction: %s instrument_name=%s"%(inspect.stack()[0][3],instrument_name))
    
    instrument_name_lowercase = str.lower(str(instrument_name))
    instrument_forms = _import_module_from_app(instrument_name_lowercase,'forms')
    
    # TODO: Make sure the submission errors are clearly reported
    reduction_proc = get_object_or_404(ReductionProcess, pk=reduction_id, owner=request.user)

    # Start a new transaction
    transaction = remote.view_util.transaction(request, start=True)
    if transaction is None:
        
        breadcrumbs = Breadcrumbs()
        breadcrumbs.append_reduction(instrument_name_lowercase)
        breadcrumbs.append_reduction_options(instrument_name_lowercase, reduction_id)
        
        template_values = {'message':"Could not connect to Fermi and establish transaction",
                           'back_url': reverse('reduction_options',
                                  kwargs={'reduction_id' : reduction_id, 'instrument_name': instrument_name_lowercase}),
                           'breadcrumbs': breadcrumbs, }
        template_values = reduction_service.view_util.fill_template_values(request, **template_values)
        return render_to_response('remote/failed_connection.html', template_values)

    data = instrument_forms.ReductionOptions.data_from_db(request.user, reduction_id)
    code = instrument_forms.ReductionOptions.as_mantid_script(data, transaction.directory)
    jobID = remote.view_util.submit_job(request, transaction, code)
    if jobID is not None:
        job = RemoteJob(reduction=reduction_proc,
                        remote_id=jobID,
                        properties=reduction_proc.properties,
                        transaction=transaction)
        job.save()
        logger.debug("Created a RemoteJob: %s",job)
    return redirect(reverse('reduction_options',
                                  kwargs={'reduction_id' : reduction_id, 
                                          'instrument_name': instrument_name_lowercase})+(
                    "?message=Job %s sucessfully submitted."%jobID)
                    )



@login_required
def job_details(request, job_id, instrument_name):
    """
        Show status of a given remote job.
        
        @param request: request object
        @param job_id: pk of the RemoteJob object
        
    """
    instrument_name_lowercase = str.lower(str(instrument_name))
    instrument_name_capitals = str.capitalize(str(instrument_name))
    
    logger.debug("Views: %s job_id=%s"%(inspect.stack()[0][3],job_id))
    
    remote_job = get_object_or_404(RemoteJob, remote_id=job_id)

    breadcrumbs = Breadcrumbs()
    breadcrumbs.append('eqsans reduction',reverse('reduction_home',
                                                  kwargs={'instrument_name': instrument_name_lowercase }))
    breadcrumbs.append_reduction_options(instrument_name_lowercase, remote_job.reduction.id )
    breadcrumbs.append('jobs',reverse('reduction_jobs',
                                      kwargs={'instrument_name': instrument_name_lowercase }))
    breadcrumbs.append("job %s" % job_id)
    
    template_values = {'remote_job': remote_job,
                       'parameters': remote_job.get_data_dict(),
                       'reduction_id': remote_job.reduction.id,
                       'breadcrumbs': breadcrumbs,
                       'back_url': request.path,
                       'instrument': instrument_name_lowercase}
    template_values = remote.view_util.fill_job_dictionary(request, job_id, **template_values)
    template_values = reduction_service.view_util.fill_template_values(request, **template_values)
    template_values['title'] = "%s job results"%instrument_name_capitals
    
    # Go through the files and find data to plot
    if 'job_files' in template_values and 'trans_id' in template_values:
        view_util = _import_module_from_app(instrument_name_lowercase,'view_util')
        template_values = view_util.set_into_template_values_job_files(template_values, request, remote_job)
#     import pprint
#     logger.debug(pprint.pformat(template_values))
    return render_to_response('%s/reduction_job_details.html'%instrument_name_lowercase,
                              template_values)
###################

    
# @login_required
# def configuration_query(request, remote_set_id, instrument_name):
#     logger.debug("%s remote_set_id=%s instrument_name=%s"%(inspect.stack()[0][3],remote_set_id,instrument_name))
#     instrument_name_lowercase = str.lower(str(instrument_name))
#     return redirect(reverse('%s.views.configuration_query'%instrument_name_lowercase,
#                                   kwargs={'remote_set_id' : remote_set_id,}))
#     
# @login_required
# def configuration_iq(request, remote_set_id, instrument_name):
#     logger.debug("%s remote_set_id=%s instrument_name=%s"%(inspect.stack()[0][3],remote_set_id,instrument_name))
#     instrument_name_lowercase = str.lower(str(instrument_name))
#     return redirect(reverse('%s.views.configuration_iq'%instrument_name_lowercase,
#                                   kwargs={'remote_set_id' : remote_set_id,}))

# @login_required
# def job_details(request, job_id, instrument_name):
#     logger.debug("%s job_id=%s instrument_name=%s"%(inspect.stack()[0][3],job_id,instrument_name))
#     instrument_name_lowercase = str.lower(str(instrument_name))
#     forward_url = reverse('%s_job_details'%instrument_name_lowercase, kwargs={'job_id' : job_id})
#     return redirect(forward_url)
    

from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.conf import settings
from django.forms.formsets import formset_factory

from reduction.models import Instrument, Experiment
import reduction_service.view_util
import reduction.view_util
import forms as reduction_forms
from reduction.models import ReductionProcess, RemoteJob, ReductionConfiguration, RemoteJobSet
from catalog.icat_server_communication import get_ipts_info
import copy
import importlib

def _import_forms_from_app(instrument_name_lowercase):
    """
    @return the forms module from an instrument app 
    """
    instrument_forms = importlib.import_module(instrument_name_lowercase + ".forms")
    return instrument_forms

@login_required
def reduction_home(request, instrument_name):
    """
        Home page for the EQSANS reduction
        @param request: request object
    """
    
    instrument = get_object_or_404(Instrument, name=instrument_name)
    
    experiments = Experiment.objects.experiments_for_instrument(instrument, owner=request.user)

    breadcrumbs = "<a href='%s'>home</a> &rsaquo; %s reduction" % (reverse(settings.LANDING_VIEW), instrument_name)
    template_values = {'title': str.capitalize(str(instrument_name)) + ' Reduction',
                       'experiments':experiments,
                       'breadcrumbs': breadcrumbs,
                       'instrument' : instrument_name, }
    template_values = reduction_service.view_util.fill_template_values(request, **template_values)
    return render_to_response('reduction/reduction_home.html',
                              template_values)


@login_required
def experiment(request, ipts, instrument_name):
    """
        List of reductions and configurations for a given experiment
        @param request: request object
        @param ipts: experiment name
        
        #TODO create new reduction using a pre-existing one as a template
    """
    
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
        icat_ipts = get_ipts_info( str.capitalize(str(instrument_name)), ipts)

    # Get all the user's reductions
    red_list = []
    if 'run_number' in request.GET:
        red_list = ReductionProcess.objects.filter(owner=request.user,
                                                   data_file__contains=request.GET['run_number'])
        if len(red_list) == 0:
            create_url  = reverse('eqsans.views.reduction_options')
            create_url +=  '?reduction_name=Reduction for r%s' % request.GET['run_number']
            create_url +=  '&expt_id=%d' % experiment_obj.id
            create_url +=  '&data_file=%s' % request.GET['run_number']
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
            data_dict['completed_job'] = reverse('eqsans.views.job_details', args=[latest_job.remote_id])
        try:
            run_id = int(data_dict['data_file'])
            data_dict['webmon_url'] = "https://monitor.sns.gov/report/eqsans/%s/" % run_id
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
        if len(latest_jobs)>0:
            latest_job = latest_jobs.latest('id')
            data_dict['latest_job'] = latest_job.id
            #data_dict['latest_job'] = reverse('eqsans.views.reduction_configuration_query', args=[latest_job.id])
        configurations.append(data_dict)
    
    breadcrumbs = "<a href='%s'>home</a>" % reverse(settings.LANDING_VIEW)
    breadcrumbs += " &rsaquo; <a href='%s'>%s reduction</a>" % ( reverse('reduction.views.reduction_home', args=[instrument_name_lowercase]),
                                                                     instrument_name_lowercase )
    
    breadcrumbs += " &rsaquo; %s" % ipts.lower()
    template_values = {'reductions': reductions,
                       'configurations': configurations,
                       'title': '%s %s' % (instrument_name_capitals, ipts),
                       'breadcrumbs': breadcrumbs,
                       'ipts_number': ipts,
                       'back_url': reverse('reduction.views.experiment', kwargs={'ipts' : ipts, 'instrument_name': instrument_name_lowercase }),
                       'icat_info': icat_ipts,
                       'form': reduction_start_form,
                       'is_categorized': not IS_UNCATEGORIZED,
                       'instrument' : instrument_name_lowercase, }
    if 'icat_error' in icat_ipts:
        template_values['user_alert'] = [icat_ipts['icat_error']]
    template_values = reduction_service.view_util.fill_template_values(request, **template_values)
    return render_to_response('%s/experiment.html'%instrument_name_lowercase,
                              template_values)
    
@login_required
def delete_reduction(request, reduction_id, instrument_name):
    """
        Delete a reduction process entry
        @param request: request object
        @param reduction_id: primary key of reduction object
    """
    reduction_proc = get_object_or_404(ReductionProcess, pk=reduction_id, owner=request.user)
    reduction_proc.delete()
    if 'back_url' in request.GET:
        return redirect(request.GET['back_url'])
    return redirect(reverse('reduction.views.reduction_home', args=[instrument_name]))




@login_required
def reduction_options(request, reduction_id=None, instrument_name=None):
    """
        Display the reduction options form
        @param request: request object
        @param reduction_id: pk of reduction process object
    """
    
    instrument_name_capitals = str.capitalize(str(instrument_name))
    instrument_name_lowercase = str.lower(str(instrument_name))
    
    instrument_forms = _import_forms_from_app(instrument_name_lowercase)
    
    # Get reduction and configuration information
    config_obj = None
    if reduction_id is not None:
        reduction_proc = get_object_or_404(ReductionProcess, pk=reduction_id, owner=request.user)
        config_obj = reduction_proc.get_config()
    
    if request.method == 'POST':
        options_form = instrument_forms.ReductionOptions(request.POST)
        # If the form is valid update or create an entry for it
        if options_form.is_valid():
            reduction_id = options_form.to_db(request.user, reduction_id)
            if reduction_id is not None:
                return redirect(reverse('reduction.views.reduction_options', args=[reduction_id,instrument_name]))
    else:
        if reduction_id is not None:
            initial_values = instrument_forms.ReductionOptions.data_from_db(request.user, reduction_id)
        else:
            initial_values = copy.deepcopy(request.GET)
            if 'expt_name' in request.GET:
                initial_values['experiment'] = request.GET['expt_name']
        options_form = instrument_forms.ReductionOptions(initial=initial_values)

    breadcrumbs = "<a href='%s'>home</a>" % reverse(settings.LANDING_VIEW)
    breadcrumbs += " &rsaquo; <a href='%s'>%s reduction</a>" % (reverse('reduction.views.reduction_home', args=[instrument_name_lowercase]),
                                                                instrument_name_lowercase)

    if config_obj is not None:
        breadcrumbs += " &rsaquo; <a href='%s'>configuration %s</a>" % (reverse('%s.views.reduction_configuration'%instrument_name_lowercase, args=[config_obj.id]), config_obj.id)
    if reduction_id is not None:
        breadcrumbs += " &rsaquo; reduction %s" % reduction_id
    else:
        breadcrumbs += " &rsaquo; new reduction"

    # ICAT info url
    icat_url = reverse('catalog.views.run_info', args=[instrument_name_capitals, '0000'])
    icat_url = icat_url.replace('/0000','')
    #TODO: add New an Save-As functionality
    template_values = {'options_form': options_form,
                       'title': '%s Reduction'%instrument_name_capitals,
                       'breadcrumbs': breadcrumbs,
                       'reduction_id': reduction_id,
                       'icat_url': icat_url,
                       'instrument' : instrument_name_lowercase, }
    # Get existing jobs for this reduction
    if reduction_id is not None:
        existing_jobs = RemoteJob.objects.filter(reduction=reduction_proc)
        if len(existing_jobs)>0:
            template_values['existing_jobs'] = existing_jobs.order_by('id')
        template_values['expt_list'] = reduction_proc.experiments.all()
    template_values = reduction_service.view_util.fill_template_values(request, **template_values)
    return render_to_response('%s/reduction_options.html'%instrument_name_lowercase,
                              template_values)

@login_required
def reduction_jobs(request, instrument_name):
    """
        Return a list of the remote reduction jobs for EQSANS.
        The jobs are those that are owned by the user and have an
        entry in the database.
        
        @param request: request object
    """
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
        if not job.transaction.is_active:
            continue
        j_data = {'id': job.id,
                  'config_id': job.configuration.id,
                  'name': job.configuration.name,
                  'trans_id': job.transaction.trans_id,
                  'experiments': job.configuration.get_experiments()
                 }
        config_data.append(j_data)
    
    breadcrumbs = "<a href='%s'>home</a>" % reverse(settings.LANDING_VIEW)
    breadcrumbs += " &rsaquo; <a href='%s'>%s reduction</a>" % (reverse('eqsans.views.reduction_home'),instrument_name)
    breadcrumbs += " &rsaquo; jobs"
    template_values = {'status_data': status_data,
                       'config_data': config_data,
                       'back_url': request.path,
                       'breadcrumbs': breadcrumbs,
                       'instrument' : instrument_name, }
    template_values = reduction_service.view_util.fill_template_values(request, **template_values)   
    return render_to_response('%s/reduction_jobs.html'%instrument_name,
                              template_values)    

@login_required
def reduction_configuration(request, config_id=None, instrument_name=None):
    """
        Show the reduction properties for a given configuration,
        along with all the reduction jobs associated with it.
        
        @param request: The request object
        @param config_id: The ReductionConfiguration pk
    """
    
    instrument_name_capitals = str.capitalize(str(instrument_name))
    instrument_name_lowercase = str.lower(str(instrument_name))
    
    instrument_forms = _import_forms_from_app(instrument_name_lowercase)
    
    # Create a form for the page
    default_extra = 1 if config_id is None and not (request.method == 'GET' and 'data_file' in request.GET) else 0
    try:
        extra = int(request.GET.get('extra', default_extra))
    except:
        extra = default_extra
    ReductionOptionsSet = formset_factory(instrument_forms.ReductionOptions, extra=extra)

    # The list of relevant experiments will be displayed on the page
    expt_list = None
    job_list = None
    # Deal with data submission
    if request.method == 'POST':
        options_form = ReductionOptionsSet(request.POST)
        config_form = instrument_forms.ReductionConfigurationForm(request.POST)
        # If the form is valid update or create an entry for it
        if options_form.is_valid() and config_form.is_valid():
            # Save the configuration
            config_id = config_form.to_db(request.user, config_id)
            # Save the individual reductions
            for form in options_form:
                form.to_db(request.user, None, config_id)
            if config_id is not None:
                return redirect(reverse('reduction.views.reduction_configuration',
                                        kwargs={'config_id' : config_id, 'instrument_name': instrument_name }))
        else:
            # There's a proble with the data, the validated form 
            # will automatically display what the problem is to the user
            pass
    else:
        # Deal with the case of creating a new configuration
        if config_id is None:
            initial_values = []
            if 'data_file' in request.GET:
                initial_values = [{'data_file': request.GET.get('data_file','')}]
            options_form = ReductionOptionsSet(initial=initial_values)
            initial_config = {}
            if 'experiment' in request.GET:
                initial_config['experiment'] = request.GET.get('experiment','')
            if 'reduction_name' in request.GET:
                initial_config['reduction_name'] = request.GET.get('reduction_name','')
            config_form = instrument_forms.ReductionConfigurationForm(initial=initial_config)
        # Retrieve existing configuration
        else:
            reduction_config = get_object_or_404(ReductionConfiguration, pk=config_id, owner=request.user)
            initial_config = instrument_forms.ReductionConfigurationForm.data_from_db(request.user, reduction_config)
            
            initial_values = []
            for item in reduction_config.reductions.all():
                props = instrument_forms.ReductionOptions.data_from_db(request.user, item.pk)
                initial_values.append(props)
                
            options_form = ReductionOptionsSet(initial=initial_values)
            config_form = instrument_forms.ReductionConfigurationForm(initial=initial_config)
            expt_list = reduction_config.experiments.all()
            job_list = RemoteJobSet.objects.filter(configuration=reduction_config)

    breadcrumbs = "<a href='%s'>home</a>" % reverse(settings.LANDING_VIEW)
    breadcrumbs += " &rsaquo; <a href='%s'>%s reduction</a>" % ( reverse('reduction.views.reduction_home', args=[instrument_name_lowercase]),
                                                                     instrument_name_lowercase )
    if config_id is not None:
        breadcrumbs += " &rsaquo; configuration %s" % config_id
    else:
        breadcrumbs += " &rsaquo; new configuration"

    # ICAT info url
    icat_url = reverse('catalog.views.run_info', args=['EQSANS', '0000'])
    icat_url = icat_url.replace('/0000','')
    #TODO: add New an Save-As functionality
    template_values = {'config_id': config_id,
                       'options_form': options_form,
                       'config_form': config_form,
                       'expt_list': expt_list,
                       'existing_job_sets': job_list,
                       'title': '%s Reduction'%instrument_name_capitals,
                       'breadcrumbs': breadcrumbs,
                       'icat_url': icat_url,
                       'instrument' : instrument_name, }

    template_values = reduction_service.view_util.fill_template_values(request, **template_values)
    return render_to_response('eqsans/reduction_table.html',
                              template_values)
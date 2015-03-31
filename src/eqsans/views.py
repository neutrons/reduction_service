"""
    EQSANS views for the SNS analysis/reduction web application.
    
    @author: M. Doucet, Oak Ridge National Laboratory
    @copyright: 2014 Oak Ridge National Laboratory
"""
from django.http import HttpResponse
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.conf import settings

from reduction.models import ReductionProcess, RemoteJob, ReductionConfiguration, RemoteJobSet
from reduction.models import Instrument, Experiment
import reduction_service.view_util
import remote.view_util
import reduction.view_util
import view_util
from catalog.icat_server_communication import get_ipts_info
from . import forms
from django.forms.formsets import formset_factory
import copy
import zipfile
import StringIO
import logging
import inspect

from eqsans.forms import ReductionConfigurationForm, ReductionOptions
from reduction_service.view_util import Breadcrumbs

instrument_name = 'eqsans'
instrument_name_capitals = str.capitalize(str(instrument_name))
instrument_name_lowercase = str.lower(str(instrument_name))
logger = logging.getLogger(instrument_name_lowercase)


@login_required
def configuration_options(request, config_id=None):
    """
        Show the reduction properties for a given configuration,
        along with all the reduction jobs associated with it.
        Called when clicked Reduce->Batch Button, or new configuration
        
        @param request: The request object
        @param config_id: The ReductionConfiguration pk
    """
    
    logger.debug("configuration_options: %s"%inspect.stack()[0][3])
    
    template_values = {}
    
    
    
    # Create a form for the page
    default_extra = 1 if config_id is None and not (request.method == 'GET' and 'data_file' in request.GET) else 0
    try:
        extra = int(request.GET.get('extra', default_extra))
    except:
        extra = default_extra

    ReductionOptionsSet = formset_factory(ReductionOptions, extra=extra)

    # The list of relevant experiments will be displayed on the page
    expt_list = None
    job_list = None
    # Deal with data submission
    if request.method == 'POST':
        
        #logger.debug(pprint.pformat(request.POST.items()))
        options_form = ReductionOptionsSet(request.POST)
        config_form = ReductionConfigurationForm(request.POST)
        # If the form is valid update or create an entry for it
        if options_form.is_valid() and config_form.is_valid():
            # Save the configuration
            config_id = config_form.to_db(request.user, config_id)
            # Save the individual reductions
            template_values['message'] = "Configuration and reduction parameters were sucessfully updated."
            for form in options_form:
                form.to_db(request.user, None, config_id)
            if config_id is not None:
                return redirect(reverse('eqsans:configuration_options',
                                        kwargs={'config_id' : config_id} ) +
                                "?message=%s"%template_values['message']
                                )
        else:
            # There's a proble with the data, the validated form 
            # will automatically display what the problem is to the user
            pass
    else:
        # Deal with the case of creating a new configuration
        if config_id is None:
            initial_values = []
            if 'data_file' in request.GET:
                initial_values = [{'data_file': request.GET.get('data_file', '')}]
            options_form = ReductionOptionsSet(initial=initial_values)
            initial_config = {}
            if 'experiment' in request.GET:
                initial_config['experiment'] = request.GET.get('experiment', '')
            if 'reduction_name' in request.GET:
                initial_config['reduction_name'] = request.GET.get('reduction_name', '')
            config_form = ReductionConfigurationForm(initial=initial_config)
        # Retrieve existing configuration
        else:
            reduction_config = get_object_or_404(ReductionConfiguration, pk=config_id, owner=request.user)
            initial_config = ReductionConfigurationForm.data_from_db(request.user, reduction_config)
            
            initial_values = []
            for item in reduction_config.reductions.all():
                props = ReductionOptions.data_from_db(request.user, item.pk)
                initial_values.append(props)
                
            options_form = ReductionOptionsSet(initial=initial_values)
            config_form = ReductionConfigurationForm(initial=initial_config)
            expt_list = reduction_config.experiments.all()
            job_list = RemoteJobSet.objects.filter(configuration=reduction_config)

    breadcrumbs = Breadcrumbs()
    breadcrumbs.append_reduction(instrument_name_lowercase)
    if config_id is not None:
        breadcrumbs.append("configuration %s" % config_id)
    else:
        breadcrumbs.append("new configuration")

    # ICAT info url
    icat_url = reverse('catalog.views.run_info', args=[instrument_name_capitals, '0000'])
    icat_url = icat_url.replace('/0000', '')
    # TODO: add New an Save-As functionality
    template_values.update({'config_id': config_id,
                       'options_form': options_form,
                       'config_form': config_form,
                       'expt_list': expt_list,
                       'existing_job_sets': job_list,
                       'title': '%s Reduction' % instrument_name_capitals,
                       'breadcrumbs': breadcrumbs,
                       'icat_url': icat_url,
                       'instrument' : instrument_name, })

    template_values = reduction_service.view_util.fill_template_values(request, **template_values)
    if 'message' in request.GET:
        template_values['message'] = request.GET['message']
    return render_to_response('%s/reduction_table.html' % instrument_name_lowercase,
                              template_values)

@login_required
def configuration_job_delete(request, config_id, reduction_id):
    """
        Delete a reduction from a configuration
        @param request: request object
        @param config_id: pk of configuration this reduction belongs to
        @param reduction_id: pk of the reduction object
    """
    logger.debug("Reduction: %s"%(inspect.stack()[0][3]))
    
    reduction_config = get_object_or_404(ReductionConfiguration, pk=config_id, owner=request.user)
    reduction_proc = get_object_or_404(ReductionProcess, pk=reduction_id, owner=request.user)
    if reduction_proc in reduction_config.reductions.all():
        reduction_config.reductions.remove(reduction_proc)
        reduction_proc.delete()
    return redirect(reverse('eqsans:configuration_options', kwargs={'config_id' : config_id}))
    
@login_required
def configuration_delete(request, config_id, instrument_name):
    """
        Delete a configuration
        @param request: request object
        @param config_id: pk of configuration this reduction belongs to
    """
    
    logger.debug("Reduction: %s instrument_name=%s"%(inspect.stack()[0][3],instrument_name))
    
    instrument_name_lowercase = str.lower(str(instrument_name))
    
    reduction_config = get_object_or_404(ReductionConfiguration, pk=config_id, owner=request.user)
    for item in reduction_config.reductions.all():
        reduction_config.reductions.remove(item)
        item.delete()
    reduction_config.delete()
    if 'back_url' in request.GET:
        return redirect(request.GET['back_url'])
    return redirect(reverse('reduction_home', args=[instrument_name_lowercase]))
    
@login_required
def configuration_query(request, remote_set_id):
    """
        Query all jobs in a job set
        @param request: request object
        @param remote_id: pk of RemoteJobSet object
    """
    logger.debug("EQSANS: %s remote_set_id=%s"%(inspect.stack()[0][3],remote_set_id))
    
    job_set = get_object_or_404(RemoteJobSet, pk=remote_set_id)
    
    breadcrumbs = Breadcrumbs()
    breadcrumbs.append('eqsans reduction',reverse('reduction_home',
                                                  kwargs={'instrument_name': instrument_name_lowercase }))
    breadcrumbs.append_configuration(instrument_name_lowercase, job_set.configuration.id)
    breadcrumbs.append('jobs',reverse('reduction_jobs', kwargs={'instrument_name': instrument_name_lowercase}))
    breadcrumbs.append("job results")
    
    template_values = {'remote_set_id': remote_set_id,
                       'configuration_title': job_set.configuration.name,
                       'configuration_id': job_set.configuration.id,
                       'breadcrumbs': breadcrumbs,
                       'title': 'EQSANS job results',
                       'trans_id': job_set.transaction.trans_id,
                       'job_directory': job_set.transaction.directory,
                       'back_url': request.path,
                       'instrument': instrument_name_lowercase}
    
    # Get status of each job
    job_set_info = []
    first_job = None
    for item in job_set.jobs.all():
        job_info = remote.view_util.query_job(request, item.remote_id)
        if job_info is not None:
            first_job = item
            job_info['reduction_name'] = item.reduction.name
            job_info['reduction_id'] = item.reduction.id
            job_info['job_id'] = item.remote_id
            job_info['parameters'] = item.get_data_dict()
            job_set_info.append(job_info)
    template_values['job_set_info'] = job_set_info
    
    # Show list of files in the transaction
    template_values['job_files'] = remote.view_util.query_files(request, job_set.transaction.trans_id)

    # I(q) plots
    plot_data = []
    if first_job is not None and template_values['job_files'] is not None:
        for f in template_values['job_files']:
            if f.endswith('_Iq.txt'):
                plot_info = view_util.process_iq_output(request, first_job, 
                                                        template_values['trans_id'], f)
                plot_info['name'] = f
                plot_data.append(plot_info)
    template_values['plot_data'] = plot_data
 
    # Link to download all I(q) files
    template_values = reduction_service.view_util.fill_template_values(request, **template_values)
    return render_to_response('eqsans/configuration_query.html', template_values)
    
@login_required
def configuration_iq(request, remote_set_id):
    """
        @param request: request object
        @param remote_id: pk of RemoteJobSet object
    """
    
    logger.debug("EQSANS: %s remote_set_id=%s"%(inspect.stack()[0][3],remote_set_id))
    
    job_set = get_object_or_404(RemoteJobSet, pk=remote_set_id)
    files = remote.view_util.query_files(request, job_set.transaction.trans_id)
    
    str_io = StringIO.StringIO()
    output_zip_file = zipfile.ZipFile(str_io, 'w')
    for f in files:
        if f.endswith('_Iq.txt'):
            file_data = remote.view_util.download_file(request, job_set.transaction, f)
            fd = StringIO.StringIO()
            fd.write(file_data)
            output_zip_file.writestr(f, fd.getvalue())
            fd.close()
    output_zip_file.close()
    # Create response with correct MIME-type
    resp = HttpResponse(str_io.getvalue(), mimetype = "application/x-zip-compressed")
    resp['Content-Disposition'] = 'attachment; filename=%s' % 'iq_transaction_%s.zip' % job_set.transaction.trans_id
    resp["Content-Description"] = "File Transfer";
    resp["Content-type"] = "application/octet-stream";
    resp["Content-Transfer-Encoding"] = "binary";
    str_io.close()
    return resp

@login_required
def configuration_submit(request, config_id):
    """
        Submit all reductions for this configuration.
        @param request: request object
        @param config_id: pk of configuration
    """
    logger.debug("Reduction: %s"%(inspect.stack()[0][3]))
    
    reduction_config = get_object_or_404(ReductionConfiguration, pk=config_id, owner=request.user)
    reductions = reduction_config.reductions.all()
    if len(reductions) > 0:
        # Start a new transaction
        transaction = remote.view_util.transaction(request, start=True)
        job_set = RemoteJobSet(transaction=transaction,
                               configuration=reduction_config)
        job_set.save()
        # Loop through the reductions and submit them
        JobIDs = []
        for item in reductions:
            data = ReductionOptions.data_from_db(request.user, item.id)
            code = ReductionOptions.as_mantid_script(data, transaction.directory)
            jobID = remote.view_util.submit_job(request, transaction, code)
            if jobID is not None:
                JobIDs.append(jobID)
                job = RemoteJob(reduction=item,
                                remote_id=jobID,
                                properties=item.properties,
                                transaction=transaction)
                job.save()
                job_set.jobs.add(job)
    return redirect(reverse('eqsans:configuration_options',
                            kwargs={'config_id' : config_id})+
                    "?message=Jobs %s sucessfully submitted."%', '.join(JobIDs)
                    )


@login_required
def test_result(request, job_id='-1'):
    """
        Dummy job for development when ORNL resources are not available
    """
    from test_util import get_dummy_data
    template_values = get_dummy_data(request, job_id)
    return render_to_response('eqsans/reduction_job_details.html',
                              template_values)
    




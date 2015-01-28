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





    
@login_required
def reduction_configuration_submit(request, config_id):
    """
        Submit all reductions for this configuration.
        @param request: request object
        @param config_id: pk of configuration
    """
    reduction_config = get_object_or_404(ReductionConfiguration, pk=config_id, owner=request.user)
    reductions = reduction_config.reductions.all()
    if len(reductions)>0:
        # Start a new transaction
        transaction = remote.view_util.transaction(request, start=True)
        job_set = RemoteJobSet(transaction=transaction,
                               configuration=reduction_config)
        job_set.save()
        # Loop through the reductions and submit them
        for item in reductions:
            data = forms.ReductionOptions.data_from_db(request.user, item.id)
            code = forms.ReductionOptions.as_mantid_script(data, transaction.directory)
            jobID = remote.view_util.submit_job(request, transaction, code)
            if jobID is not None:
                job = RemoteJob(reduction=item,
                                remote_id=jobID,
                                properties=item.properties,
                                transaction=transaction)
                job.save()
                job_set.jobs.add(job)
    return redirect(reverse('reduction.views.reduction_configuration',
                                        kwargs={'config_id' : config_id, 'instrument_name': 'eqsans' }))
    
@login_required
def reduction_configuration_query(request, remote_set_id):
    """
        Query all jobs in a job set
        @param request: request object
        @param remote_id: pk of RemoteJobSet object
    """
    job_set = get_object_or_404(RemoteJobSet, pk=remote_set_id)
    
    breadcrumbs = "<a href='%s'>home</a>" % reverse(settings.LANDING_VIEW)
    breadcrumbs += " &rsaquo; <a href='%s'>eqsans reduction</a>" % reverse('eqsans.views.reduction_home')
    breadcrumbs += " &rsaquo; <a href='%s'>configuration %s</a>" % (reverse('reduction.views.reduction_configuration',
                                        kwargs={'config_id' : job_set.configuration.id, 'instrument_name': 'eqsans' }), job_set.configuration.id)
    breadcrumbs += " &rsaquo; <a href='%s'>jobs</a>" % reverse('reductions.views.reduction_jobs',args=['eqsans'])
    breadcrumbs += " &rsaquo; job results"
    
    template_values = {'remote_set_id': remote_set_id,
                       'configuration_title': job_set.configuration.name,
                       'configuration_id': job_set.configuration.id,
                       'breadcrumbs': breadcrumbs,
                       'title': 'EQSANS job results',
                       'trans_id': job_set.transaction.trans_id,
                       'job_directory': job_set.transaction.directory,
                       'back_url': request.path}
    
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
    return render_to_response('eqsans/reduction_configuration_query.html', template_values)
    
@login_required
def reduction_configuration_iq(request, remote_set_id):
    """
        @param request: request object
        @param remote_id: pk of RemoteJobSet object
    """
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
    str_io.close()
    return resp

@login_required
def reduction_configuration_job_delete(request, config_id, reduction_id):
    """
        Delete a reduction from a configuration
        @param request: request object
        @param config_id: pk of configuration this reduction belongs to
        @param reduction_id: pk of the reduction object
    """
    reduction_config = get_object_or_404(ReductionConfiguration, pk=config_id, owner=request.user)
    reduction_proc = get_object_or_404(ReductionProcess, pk=reduction_id, owner=request.user)
    if reduction_proc in reduction_config.reductions.all():
        reduction_config.reductions.remove(reduction_proc)
        reduction_proc.delete()
    return redirect(reverse('reduction.views.reduction_configuration',
                                        kwargs={'config_id' : config_id, 'instrument_name': 'eqsans' }))
    
@login_required
def reduction_configuration_delete(request, config_id):
    """
        Delete a configuration
        @param request: request object
        @param config_id: pk of configuration this reduction belongs to
    """
    reduction_config = get_object_or_404(ReductionConfiguration, pk=config_id, owner=request.user)
    for item in reduction_config.reductions.all():
        reduction_config.reductions.remove(item)
        item.delete()
    reduction_config.delete()
    if 'back_url' in request.GET:
        return redirect(request.GET['back_url'])
    return redirect(reverse('eqsans.views.reduction_home'))
    
@login_required
def reduction_script(request, reduction_id):
    """
        Display a script representation of a reduction process.
        
        @param request: request object
        @param reduction_id: pk of the ReductionProcess object
    """
    data = forms.ReductionOptions.data_from_db(request.user, reduction_id)
    
    breadcrumbs = "<a href='%s'>home</a>" % reverse(settings.LANDING_VIEW)
    breadcrumbs += " &rsaquo; <a href='%s'>eqsans reduction</a>" % reverse('eqsans.views.reduction_home')
    breadcrumbs += " &rsaquo; <a href='.'>reduction %s</a> &rsaquo; script" % reduction_id
    
    template_values = {'reduction_name': data['reduction_name'],
                       'breadcrumbs': breadcrumbs,
                       'code': forms.ReductionOptions.as_mantid_script(data) }
    template_values = reduction_service.view_util.fill_template_values(request, **template_values)
    return render_to_response('eqsans/reduction_script.html',
                              template_values)

@login_required
def py_reduction_script(request, reduction_id):
    """
        Return the python script for a reduction process.
        
        @param request: request object
        @param reduction_id: pk of the ReductionProcess object
    """
    data = forms.ReductionOptions.data_from_db(request.user, reduction_id) 
    response = HttpResponse(forms.ReductionOptions.as_mantid_script(data))
    response['Content-Disposition'] = 'attachment; filename="eqsans_reduction.py"'
    return response

@login_required
def xml_reduction_script(request, reduction_id):
    """
        Return the xml representation of a reduction process that the user
        can load into Mantid.
        
        @param request: request object
        @param reduction_id: pk of the ReductionProcess object
    """
    data = forms.ReductionOptions.data_from_db(request.user, reduction_id) 
    response = HttpResponse(forms.ReductionOptions.as_xml(data))
    response['Content-Disposition'] = 'attachment; filename="eqsans_reduction.xml"'
    return response

@login_required
def submit_job(request, reduction_id):
    """
        Submit a reduction script to Fermi.

        @param request: request object
        @param reduction_id: pk of the ReductionProcess object
    """
    #TODO: Make sure the submission errors are clearly reported
    reduction_proc = get_object_or_404(ReductionProcess, pk=reduction_id, owner=request.user)

    # Start a new transaction
    transaction = remote.view_util.transaction(request, start=True)
    if transaction is None:
        breadcrumbs = "<a href='%s'>home</a>" % reverse(settings.LANDING_VIEW)
        breadcrumbs += " &rsaquo; <a href='%s'>eqsans reduction</a>" % reverse('eqsans.views.reduction_home')
        breadcrumbs += " &rsaquo; <a href='%s'>reduction</a>" % reverse('eqsans.views.reduction_options', args=[reduction_id])
        template_values = {'message':"Could not connect to Fermi and establish transaction",
                           'back_url': reverse('eqsans.views.reduction_options', args=[reduction_id]),
                           'breadcrumbs': breadcrumbs,}
        template_values = reduction_service.view_util.fill_template_values(request, **template_values)
        return render_to_response('remote/failed_connection.html',
                                  template_values)

    data = forms.ReductionOptions.data_from_db(request.user, reduction_id)
    code = forms.ReductionOptions.as_mantid_script(data, transaction.directory)
    jobID = remote.view_util.submit_job(request, transaction, code)
    if jobID is not None:
        job = RemoteJob(reduction=reduction_proc,
                        remote_id=jobID,
                        properties=reduction_proc.properties,
                        transaction=transaction)
        job.save()
    return redirect(reverse('eqsans.views.reduction_options', args=[reduction_id]))

@login_required
def job_details(request, job_id):
    """
        Show status of a given remote job.
        
        @param request: request object
        @param job_id: pk of the RemoteJob object
        
    """
    remote_job = get_object_or_404(RemoteJob, remote_id=job_id)

    breadcrumbs = "<a href='%s'>home</a>" % reverse(settings.LANDING_VIEW)
    breadcrumbs += " &rsaquo; <a href='%s'>eqsans reduction</a>" % reverse('eqsans.views.reduction_home')
    breadcrumbs += " &rsaquo; <a href='%s'>reduction %s</a>" % (reverse('eqsans.views.reduction_options', args=[remote_job.reduction.id]), remote_job.reduction.id)
    breadcrumbs += " &rsaquo; <a href='%s'>jobs</a>" % reverse('reductions.views.reduction_jobs',args=['eqsans'])
    breadcrumbs += " &rsaquo; %s" % job_id

    template_values = {'remote_job': remote_job,
                       'parameters': remote_job.get_data_dict(),
                       'reduction_id': remote_job.reduction.id,
                       'breadcrumbs': breadcrumbs,
                       'back_url': request.path}
    template_values = remote.view_util.fill_job_dictionary(request, job_id, **template_values)
    template_values = reduction_service.view_util.fill_template_values(request, **template_values)
    template_values['title'] = "EQSANS job results"
    
    # Go through the files and find data to plot
    if 'job_files' in template_values and 'trans_id' in template_values:
        for f in template_values['job_files']:
            if f.endswith('_Iq.txt'):
                plot_info = view_util.process_iq_output(request, remote_job, 
                                                        template_values['trans_id'], f)
                template_values.update(plot_info)
            elif f.endswith('_Iqxy.nxs'):
                plot_info = view_util.process_iqxy_output(request, remote_job, 
                                                          template_values['trans_id'], f)
                template_values.update(plot_info)
    
    return render_to_response('eqsans/reduction_job_details.html',
                              template_values)

@login_required
def test_result(request, job_id='-1'):
    """
        Dummy job for development when ORNL resources are not available
    """
    from test_util import get_dummy_data
    template_values = get_dummy_data(request, job_id)
    return render_to_response('eqsans/reduction_job_details.html',
                              template_values)
    




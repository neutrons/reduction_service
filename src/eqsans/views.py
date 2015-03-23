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

from reduction_service.view_util import Breadcrumbs

logger = logging.getLogger('eqsans')
    
@login_required
def reduction_configuration_query(request, remote_set_id):
    """
        Query all jobs in a job set
        @param request: request object
        @param remote_id: pk of RemoteJobSet object
    """
    logger.debug("EQSANS: %s remote_set_id=%s"%(inspect.stack()[0][3],remote_set_id))
    
    job_set = get_object_or_404(RemoteJobSet, pk=remote_set_id)
    
    breadcrumbs = Breadcrumbs()
    breadcrumbs.append('eqsans reduction',reverse('reduction.views.reduction_home',
                                                  kwargs={'instrument_name': 'eqsans' }))
    breadcrumbs.append_configuration('eqsans', job_set.configuration.id)
    breadcrumbs.append('jobs',reverse('reduction.views.reduction_jobs',
                                      kwargs={'instrument_name': 'eqsans' }))
    breadcrumbs.append("job results")
    
    template_values = {'remote_set_id': remote_set_id,
                       'configuration_title': job_set.configuration.name,
                       'configuration_id': job_set.configuration.id,
                       'breadcrumbs': breadcrumbs,
                       'title': 'EQSANS job results',
                       'trans_id': job_set.transaction.trans_id,
                       'job_directory': job_set.transaction.directory,
                       'back_url': request.path,
                       'instrument': 'eqsans'}
    
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
def job_details(request, job_id):
    """
        Show status of a given remote job.
        
        @param request: request object
        @param job_id: pk of the RemoteJob object
        
    """
    
    logger.debug("EQSANS: %s job_id=%s"%(inspect.stack()[0][3],job_id))
    
    remote_job = get_object_or_404(RemoteJob, remote_id=job_id)

    breadcrumbs = Breadcrumbs()
    breadcrumbs.append('eqsans reduction',reverse('reduction.views.reduction_home',
                                                  kwargs={'instrument_name': 'eqsans' }))
    breadcrumbs.append_reduction_options('eqsans', remote_job.reduction.id )
    breadcrumbs.append('jobs',reverse('reduction.views.reduction_jobs',
                                      kwargs={'instrument_name': 'eqsans' }))
    breadcrumbs.append("job %s" % job_id)
    
    template_values = {'remote_job': remote_job,
                       'parameters': remote_job.get_data_dict(),
                       'reduction_id': remote_job.reduction.id,
                       'breadcrumbs': breadcrumbs,
                       'back_url': request.path,
                       'instrument': 'eqsans'}
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
#     import pprint
#     logger.debug(pprint.pformat(template_values))
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
    




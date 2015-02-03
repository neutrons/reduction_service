"""
    Views for the remote submission to Fermi
    
    @author: M. Doucet, Oak Ridge National Laboratory
    @copyright: 2014 Oak Ridge National Laboratory
"""
from django.http import HttpResponse
from django.shortcuts import render_to_response, redirect
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.conf import settings

import reduction_service.view_util
import remote.view_util

import logging

logger = logging.getLogger('remote')

@login_required
def query_remote_jobs(request):
    """
        Query the Fermi remote service for the user's jobs.
        @param request: request object
    """
    template_values = {'back_url': request.path,
                       'status_data': remote.view_util.get_remote_jobs(request)}
    template_values = reduction_service.view_util.fill_template_values(request, **template_values)
    return render_to_response('remote/query_remote_jobs.html',
                              template_values)

@login_required
def authenticate(request):
    """
        Authenticate and return to the previous page.
        @param request: request object
    """
    redirect_url = reverse(settings.LANDING_VIEW)
    if 'redirect' in request.POST:
        redirect_url = request.POST['redirect']
    if request.method == 'POST':
        form = remote.view_util.FermiLoginForm(request.POST, request.FILES)
        if form.is_valid():
            status, reason = remote.view_util.authenticate(request)
            if status is not 200:
                breadcrumbs = "<a href='%s'>home</a>" % reverse(settings.LANDING_VIEW)
                message = "Could not authenticate with Fermi"
                if len(reason)>0:
                    message += "<p>Server message: %s" % reason
                template_values = {'message': message,
                                   'back_url': redirect_url,
                                   'breadcrumbs': breadcrumbs,}
                template_values = reduction_service.view_util.fill_template_values(request, **template_values)
                return render_to_response('remote/failed_connection.html',
                                          template_values)
    return redirect(redirect_url)
      
@login_required
def job_details(request, job_id):
    """
        Show job details
        @param request: request object
        @param job_id: pk of the RemoteJob object
    """
    template_values = remote.view_util.fill_job_dictionary(request, job_id)
    template_values = reduction_service.view_util.fill_template_values(request, **template_values)
    return render_to_response('remote/job_details.html',
                              template_values)
    
@login_required
def download_file(request, trans_id, filename, delete=False):
    """
        Get a file from the compute node. The transaction name
        corresponds to the name it is given by the remote submission service.
        @param request: request object
        @param trans_id: remote name of the transaction
        @param filename: name of the file to download
        @param delete: if True, the transaction will be deleted
    """
    file_content = remote.view_util.download_file(request, trans_id, filename)
    if delete is True:
        remote.view_util.stop_transaction(request, trans_id)
    response = HttpResponse(file_content)
    response['Content-Disposition'] = 'attachment; filename="%s"' % filename
    response["Content-Description"] = "File Transfer";
    response["Content-type"] = "application/octet-stream";
    response["Content-Transfer-Encoding"] = "binary";
    return response
 
@login_required
def download_file_and_delete(request, trans_id, filename):
    """
        Download a file and delete the transaction after the download.
        @param request: request object
        @param trans_id: remote name of the transaction
        @param filename: name of the file to download
    """
    return download_file(request, trans_id, filename, delete=True)

@login_required
def stop_transaction(request, trans_id):
    """
        Stop an existing remote transaction. The transaction name
        corresponds to the name it is given by the remote submission service.
        @param request: request object
        @param trans_id: remote transaction ID
    """
    remote.view_util.stop_transaction(request, trans_id)
    redirect_url = reverse('remote.views.query_remote_jobs')
    if 'back_url' in request.GET:
        redirect_url = request.GET['back_url']
    return redirect(redirect_url)

from django.http import HttpResponse, Http404
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.core.context_processors import csrf
from django.utils.dateparse import parse_datetime

from models import ReductionJob, Transaction

import users.view_util
import remote.view_util

import httplib
from base64 import b64encode
import json
import logging
import sys

# The following should be in settings
FERMI_HOST = 'fermi.ornl.gov'
FERMI_BASE_URL = '/MantidRemote/'
FERMI_QUERY = '/MantidRemote/query'

@login_required
def query_remote_jobs(request):
    """
        Query the Fermi remote service for the user's jobs.
        The response will be like this:
        
        { "3954": { "CompletionDate": "2013-10-29T17:13:08+00:00",
                    "StartDate": "2013-10-29T17:12:32+00:00",
                    "SubmitDate": "2013-10-29T17:12:31+00:00",
                    "JobName": "eqsans",
                    "ScriptName": "job_submission_0.py",
                    "JobStatus": "COMPLETED",
                    "TransID": 57 } }
    """
    sessionid = request.session.get('fermi', '')
    template_values = {}
    try:
        conn = httplib.HTTPSConnection(FERMI_HOST, timeout=30)
        conn.request('GET', FERMI_QUERY, headers={'Cookie': sessionid})
        r = conn.getresponse()
        logging.error(r.status)
        # Check to see whether we need authentication
        jobs = json.loads(r.read())
        need_authentication = True
        if r.status == 401:
            pass
        elif r.status == 404:
            need_authentication = False
            template_values['errors'] = "Fermi service could not be found [404]"
        else:
            need_authentication = False
            status_data = []
            for key in jobs:
                jobs[key]['ID'] = key
                jobs[key]['CompletionDate'] = parse_datetime(jobs[key]['CompletionDate'])
                jobs[key]['StartDate'] = parse_datetime(jobs[key]['StartDate'])
                jobs[key]['SubmitDate'] = parse_datetime(jobs[key]['SubmitDate'])
                status_data.append(jobs[key])
            template_values['status_data'] = status_data
        template_values['need_authentication'] = need_authentication

    except:
        logging.error("Could not connect to status page: %s" % sys.exc_value)
        template_values['errors'] = "Could not connect to Fermi: %s" % sys.exc_value
    
    template_values = users.view_util.fill_template_values(request, **template_values)   
    template_values = remote.view_util.fill_template_values(request, **template_values)
    return render_to_response('remote/query_remote_jobs.html',
                              template_values)

@login_required
def authenticate(request):
    """
        Authenticate and return to the previous page    
    """
    if request.method == 'POST':
        form = remote.view_util.FermiLoginForm(request.POST, request.FILES)
        if form.is_valid():
            status = remote.view_util.authenticate(request)
    return redirect(request.POST['redirect'])
      
@login_required
def job_details(request, job_id):
    """
        Show job details
    """
    # Query basic job info
    job_info = remote.view_util.query_job(request, job_id)
    if job_info is None:
        raise Http404

    # Get list of files for this transaction
    transaction = get_object_or_404(Transaction, trans_id=job_info['TransID'])
    files = remote.view_util.query_files(request, transaction.trans_id)

    template_values = {'title':'Reduction job %s' % job_id,
                       'job_id': job_id,
                       'trans_id': transaction.trans_id,
                       'job_info': job_info,
                       'job_directory': transaction.directory,
                       'job_files': files}
    template_values = users.view_util.fill_template_values(request, **template_values)   
    template_values = remote.view_util.fill_template_values(request, **template_values)
    return render_to_response('remote/job_details.html',
                              template_values)
    
@login_required
def download_file(request, trans_id, filename):
    """
        Get a file from the compute node
        
    """
    file_content = remote.view_util.download_file(request, trans_id, filename)
    response = HttpResponse(file_content)
    response['Content-Disposition'] = 'attachment; filename="%s"' % filename
    return response
 

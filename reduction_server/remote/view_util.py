"""
    Utilities used to communicated with the remote jobs submission
    service on Fermi.
    
    @author: M. Doucet, Oak Ridge National Laboratory
    @copyright: 2014 Oak Ridge National Laboratory
"""
from django import forms
from django.utils.dateparse import parse_datetime
import httplib, urllib
from base64 import b64encode
import json
import logging
import sys
from models import Transaction
from reduction_server.reduction.models import RemoteJob, RemoteJobSet
from django.conf import settings
from django.contrib import messages

logger = logging.getLogger('remote.view_util')

def get_authentication_status(request):
    """
        Get the authentication status of the user on Fermi
        @param request: request object
    """
    sessionid = request.session.get('fermi', '')
    fermi_uid = request.session.get('fermi_uid', '')
    if len(sessionid)>0 and len(fermi_uid)>0:
        return fermi_uid
    if len(sessionid)==0:
        return None
    try:
        conn = httplib.HTTPSConnection(settings.FERMI_HOST, timeout=0.5)
        conn.request('GET', settings.FERMI_BASE_URL+'info', headers={'Cookie':sessionid})
        r = conn.getresponse()  
        info = json.loads(r.read())
        if "Authenticated_As" in info:
            request.session['fermi_uid'] = info["Authenticated_As"]
            return info["Authenticated_As"]
        if "Err_Msg" in info:
            logger.error("MantidRemote: %s" % info["Err_Msg"])
    except:
        logger.error("Could not obtain information from Fermi: %s" % sys.exc_value)
    return None

def fill_template_values(request, **template_args):
    """
        Fill template values for remote submission
        @param request: request object
        @param template_args: dictionary of template parameters
    """
    fermi_user = get_authentication_status(request)
    template_args['fermi_authenticated'] = fermi_user is not None
    template_args['fermi_uid'] = fermi_user
    template_args['current_path'] = request.path

    return template_args

def authenticate(request):
    """
        Authenticate with Fermi
        @param request: request object
    """
    reason = ''
    try:
        conn = httplib.HTTPSConnection(settings.FERMI_HOST, timeout=0.5)
        userAndPass = b64encode(b"%s:%s" % (request.POST['username'], request.POST['password'])).decode("ascii")
        headers = { 'Authorization' : 'Basic %s' %  userAndPass }
        conn.request('GET', settings.FERMI_BASE_URL+'authenticate', headers=headers)
        r = conn.getresponse()
        if not r.status == 200:
            try:
                info = json.loads(r.read())
                if "Err_Msg" in info:
                    logger.error("MantidRemote: %s" % info["Err_Msg"])
                    reason = info["Err_Msg"]
            except:
                logger.error("MantidRemote: %s" % sys.exc_value)
        sessionid = r.getheader('set-cookie', '')
        if len(sessionid)>0:
            request.session['fermi']=sessionid
            request.session['fermi_uid']=request.POST['username']
        return r.status, reason
    except Exception, e:
        logger.error("Could not authenticate with Fermi: %s" % sys.exc_value)
        logger.exception(str(e))
        messages.add_message(request, messages.ERROR, "Could not authenticate with Fermi: %s" % sys.exc_value)
    return 500, reason

def transaction(request, start=False):
    """
        Start a transaction with Fermi
        @param request: request object
        @param start: if True, a new transaction will be started if we didn't already have one
    """
    if start is not True:
        transID = request.session.get('fermi_transID', None)
        if transID is not None:
            transactions = Transaction.objects.filter(trans_id=transID)
            if len(transactions)>0:
                logger.debug("Transaction ID = %s from the database."%transID)
                return transactions[0]
    try:
        logger.debug("Connecting to %s to start a transaction."%settings.FERMI_HOST)
        conn = httplib.HTTPSConnection(settings.FERMI_HOST, timeout=0.5)
        conn.request('GET', settings.FERMI_BASE_URL+'transaction?Action=Start',
                            headers={'Cookie':request.session.get('fermi', '')})
        r = conn.getresponse()
        if not r.status == 200:
            logger.error("Fermi transaction call failed: %s" % r.status)
        info = json.loads(r.read())
        if "Err_Msg" in info:
            logger.error("MantidRemote: %s" % info["Err_Msg"])
        
        logger.debug("Connection to fermi returned TransID = %s."%info["TransID"])
        request.session['fermi_transID'] = info["TransID"]
        transaction_obj = Transaction(trans_id = info["TransID"],
                                  directory = info["Directory"],
                                  owner = request.user)
        transaction_obj.save()
        logger.debug("Transaction created: %s"%transaction_obj)
        return transaction_obj
    except Exception, e:
        logger.error("Could not get new transaction ID: %s" % sys.exc_value)
        logger.exception(str(e))
        messages.add_message(request, messages.ERROR, "Could not get new transaction ID: %s" % sys.exc_value)
    return None

def stop_transaction(request, trans_id):
    """
        Stop an existing transaction
        @param request: request object
        @param trans_id: name of the remote transaction
        
        The call to Fermi will look like this:
          https://fermi.ornl.gov/MantidRemote/transaction?Action=Stop&TransID=<trans_id>
    """
    # First, let's see if we know about this transaction
    transaction_obj = None
    transactions = Transaction.objects.filter(trans_id=trans_id)
    if len(transactions)>0:
        transaction_obj = transactions[0]
        
    if transaction_obj is None:
        logger.error("Local transaction %s does not exist" % trans_id)
        messages.add_message(request, messages.ERROR, "Local transaction %s does not exist" % trans_id)
    elif not transaction_obj.owner == request.user:
        logger.error("User %s trying to stop transaction %s belonging to %s" % (request.user,
                                                                                 trans_id,
                                                                                 transaction_obj.owner))
        messages.add_message(request, messages.ERROR, "User %s trying to stop transaction %s belonging to %s" % (request.user,
                                                                                 trans_id,
                                                                                 transaction_obj.owner))
    else:
        # Here we can delete the existing DB entry for this transaction
        transaction_obj.is_active = False
        transaction_obj.save()
        
        # Once I invalidate the transaction I remove the job.
        # This will remove jobs from Remote jobs right menu
        RemoteJob.objects.filter(transaction_id=transaction_obj.id).delete()
        # Ric : because once deleted they appear on the right side menu!
        RemoteJobSet.objects.filter(transaction_id=transaction_obj.id).delete()
        
    request.session['fermi_transID'] = None
    # Regardless of whether we have a local transaction with that ID,
    # try to stop the remote transaction
    try:
        conn = httplib.HTTPSConnection(settings.FERMI_HOST, timeout=0.5)
        conn.request('GET', settings.FERMI_BASE_URL+'transaction?Action=Stop&TransID=%s' % trans_id,
                            headers={'Cookie':request.session.get('fermi', '')})
        r = conn.getresponse()
        if not r.status == 200:
            logger.error("Could not close Fermi transaction: %s" % r.status)
            info = json.loads(r.read())
            if "Err_Msg" in info:
                logger.error("MantidRemote: %s" % info["Err_Msg"])
                messages.add_message(request, messages.ERROR, "MantidRemote: %s" % info["Err_Msg"])
        else:
            messages.add_message(request, messages.SUCCESS, "Transaction %s successfully stopped"%trans_id )
    except:
        logger.error("Could not close Fermi transaction: %s" % sys.exc_value)
        messages.add_message(request, messages.ERROR, "Could not close Fermi transaction: %s" % sys.exc_value)

    
def submit_job(request, transaction, script_code, number_of_nodes = 1, cores_per_node=1, script_name='web_submission.py'):
    """
        Submit a job to be executed on Fermi
        @param request: request object
        @param transaction: Transaction object
        @param script_code: code to be executed by the compute node
        @param script_name: name given to the remote script to be executed
    """
    jobID = None

    # Submit job
    post_data = urllib.urlencode({'TransID': transaction.trans_id,
                                  'NumNodes': number_of_nodes,
                                  'CoresPerNode': cores_per_node,
                                  'ScriptName': script_name,
                                  script_name: script_code})
    try:
        logger.debug("Submiting transaction id %s to %s."%(transaction.trans_id,settings.FERMI_HOST))
        conn = httplib.HTTPSConnection(settings.FERMI_HOST, timeout=5)
        conn.request('POST', settings.FERMI_BASE_URL+'submit',
                     body=post_data,
                     headers={'Cookie':request.session.get('fermi', '')})
        r = conn.getresponse()
        resp = json.loads(r.read())
        if "Err_Msg" in resp:
            logger.error("MantidRemote: %s" % resp["Err_Msg"])
            messages.add_message(request, messages.ERROR, "MantidRemote: %s" % resp["Err_Msg"])
        if 'JobID' in resp:
            jobID = request.session['fermi_jobID'] = resp['JobID']
    except:
        logger.error("Could not submit job: %s" % sys.exc_value)
        messages.add_message(request, messages.ERROR, "Could not submit job: %s" % sys.exc_value)
    return jobID

def query_remote_job(request, remote_job_remote_id):
    """
        Query Fermi for a specific job
        @param request: request object
        @param remote_job_remote_id: remote job id string
        
        The call to Fermi will look like this:
            https://fermi.ornl.gov/MantidRemote/query?JobID=7665
        
        and will return a json payload like the following:
        { "7665": { "CompletionDate": "2014-02-14T21:25:58+00:00",
                    "StartDate": "2014-02-14T21:25:37+00:00",
                    "SubmitDate": "2014-02-14T21:25:36+00:00",
                    "JobName": "Unknown",
                    "ScriptName": "web_submission.py",
                    "JobStatus": "COMPLETED",
                    "TransID": 136 } }
    """
    try:
        conn = httplib.HTTPSConnection(settings.FERMI_HOST, timeout=1.5)
        conn.request('GET', '%squery?JobID=%s' % (settings.FERMI_BASE_URL, remote_job_remote_id),
                     headers={'Cookie':request.session.get('fermi', '')})
        r = conn.getresponse()
        if r.status == 200:
            job_info = json.loads(r.read())[remote_job_remote_id]
            job_info['CompletionDate'] = parse_datetime(job_info['CompletionDate'])
            job_info['StartDate'] = parse_datetime(job_info['StartDate'])
            job_info['SubmitDate'] = parse_datetime(job_info['SubmitDate'])
            return job_info
        else:
            logger.error("Could not get job info: %s %s" % (r.status,r.reason))
            messages.add_message(request, messages.ERROR, "Could not get job info for job %s: %s %s" % (remote_job_remote_id, r.status,r.reason))
    except:
        logger.error("Could not get job info: %s" % sys.exc_value)
        messages.add_message(request, messages.ERROR, "Could not get job info for job %s: %s" % (remote_job_remote_id, sys.exc_value))
    return None

def get_remote_jobs(request):
    """
        Query the Fermi remote service for the user's jobs.
        @param request: request object
        
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
    status_data = []
    try:
        conn = httplib.HTTPSConnection(settings.FERMI_HOST, timeout=30)
        conn.request('GET', '%squery' % settings.FERMI_BASE_URL, headers={'Cookie': sessionid})
        r = conn.getresponse()
        # Check to see whether we need authentication
        jobs = json.loads(r.read())
        for key in jobs:
            jobs[key]['ID'] = key
            jobs[key]['CompletionDate'] = parse_datetime(jobs[key]['CompletionDate'])
            jobs[key]['StartDate'] = parse_datetime(jobs[key]['StartDate'])
            jobs[key]['SubmitDate'] = parse_datetime(jobs[key]['SubmitDate'])
            status_data.append(jobs[key])
    except:
        logger.error("Could not connect to status page: %s" % sys.exc_value)
        messages.add_message(request, messages.ERROR, "Could not connect to status page: %s" % sys.exc_value)
    
    return status_data
    
def query_files(request, trans_id):
    """
        Query files for a given transaction
        @param request: request object
        @param trans_id: remote name of the transaction
        
        The call to Fermi will look like this:
            https://fermi.ornl.gov/MantidRemote/files?TransID=136
            
        and the reply will look like this:
        {"Files": ["7665.fermi-mgmt3.ornl.gov.ER",
                   "7665.fermi-mgmt3.ornl.gov.OU",
                   "submit.sh",
                   "web_submission.py"]}
    """
    try:
        conn = httplib.HTTPSConnection(settings.FERMI_HOST, timeout=1.5)
        conn.request('GET', '%sfiles?TransID=%s' % (settings.FERMI_BASE_URL, trans_id),
                     headers={'Cookie':request.session.get('fermi', '')})
        r = conn.getresponse()
        if r.status == 200:
            file_list = json.loads(r.read())['Files']
            return file_list
        else:
            logger.error("Could not get files for transaction: %s" % r.status)
            messages.add_message(request, messages.ERROR, "Could not get files for transaction: %s" % r.status)
    except:
        logger.error("Could not get files for transaction: %s" % sys.exc_value)
        messages.add_message(request, messages.ERROR, "Could not get files for transaction: %s" % sys.exc_value)
    return None

def download_file(request, trans_id, filename):
    """
        Download a file from the compute node.
        @param request: request object
        @param trans_id: remote name for the transaction
        @param filename: name of the file to be downloaded
        
        The call to Fermi will look like this:
          https://fermi.ornl.gov/MantidRemote/download?TransID=90&File=submit.sh
    """
    try:

        conn = httplib.HTTPSConnection(settings.FERMI_HOST, timeout=60)
        url = '%sdownload?TransID=%s&File=%s' % (settings.FERMI_BASE_URL, trans_id, filename)
        logger.debug("Getting: %s"%url)
        conn.request('GET', url,
                     headers={'Cookie':request.session.get('fermi', '')})
        r = conn.getresponse()
        if r.status == 200:
            return r.read()
        else:
            logger.error("Could not get file from compute node: %s" % r.status)
            logger.error( r.read() )
            messages.add_message(request, messages.ERROR, "Could not get file from compute node: %s" % r.status)
    except:
        logger.error("Could not get file from compute node: %s" % sys.exc_value)
        messages.add_message(request, messages.ERROR, "Could not get file from compute node: %s" % sys.exc_value)
    return None

def fill_job_values(request, remote_job_remote_id, **template_values):
    """
        Fill in a dictionary with job information.
        It does not access the database. Only gets information from fermi.
        @param request: request object
        @param remote_job_id: remote job id string
        @param template_values: dictionary to fill
    """
    # Verify whether we are dealing with a test job.
    # There is only one allowed test job and it has '-1' as its ID.
    if remote_job_remote_id == '-1':
        template_values['trans_id'] = -1
        template_values['job_files'] = ['4065_Iq.txt', '4065_Iqxy.nxs']

    template_values['title'] = 'Job %s' % remote_job_remote_id
    template_values['remote_job_remote_id'] = remote_job_remote_id

    # Query basic job info
    job_info = query_remote_job(request, remote_job_remote_id)
    if job_info is None:
        template_values['user_alert'] = ["Could not find job on Fermi"]
        template_values['job_not_found'] = True
        return template_values
    template_values['job_info'] = job_info
    
    # Get list of files for this transaction
    transactions = Transaction.objects.filter(trans_id=job_info['TransID'])
    if len(transactions)>0:
        transaction = transactions[0]
        template_values['job_files'] = query_files(request, transaction.trans_id)
        template_values['trans_id'] = transaction.trans_id
        template_values['job_directory'] = transaction.directory
    return template_values


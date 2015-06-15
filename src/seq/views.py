from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render_to_response, redirect
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.contrib import messages

import inspect

from seq import INSTRUMENT_NAME
from reduction.models import ReductionConfiguration, RemoteJobSet, RemoteJob
    
import reduction.view_util
import remote

import logging
logger = logging.getLogger('seq.views')


@login_required
def configuration_submit(request, config_id):
    """
    General reduction uses the /reduction URL prefix.
    
    For SEQ, it is specific. A configuration is a single submission.
    Thus the URL is:
    /seq/configuration/(?P<config_id>\d+)/submit$
    http://localhost:8000/seq/configuration/75/submit
    
    @param request: request object
    @param config_id: pk of configuration
    """
    
    
    logger.debug("Specific SEQ Submit: %s"%(inspect.stack()[0][3]))

 
    instrument_forms = reduction.view_util.import_module_from_app(INSTRUMENT_NAME,'forms')
    
    forms_handler = instrument_forms.ConfigurationFormHandler(request,config_id)
     
    reduction_config = get_object_or_404(ReductionConfiguration, pk=config_id, owner=request.user)
     
     
    reductions = reduction_config.reductions.all()
    
    if len(reductions) <= 0:
        messages.add_message(request, messages.ERROR, message="No jobs submitted. Configuration %s does not have any reduction data files associated."%config_id)
    else:
        # Start a new transaction
        transaction = remote.view_util.transaction(request, start=True)
        job_set = RemoteJobSet(transaction=transaction,
                               configuration=reduction_config)
        job_set.save()
        
        code = forms_handler.get_mantid_script(None, transaction.directory)
        
        jobID = remote.view_util.submit_job(request, transaction, code)
#         import random
#         jobID = random.randrange(9899898)
        
        if jobID is not None:
            # In EQSANS one config gas several reductions. For DEQ is different. We just use one reduction! 
            job = RemoteJob(reduction=reductions[0],
                            remote_id=jobID,
                            properties=reductions[0].properties,
                            transaction=transaction)
            job.save()
            job_set.jobs.add(job) 
            messages.add_message(request, messages.SUCCESS, 
                                 message="Job set %s sucessfully submitted. <a href='%s' class='message-link'>Click to see the results this job set</a>."%
                                 (job_set.id, reverse('configuration_query', kwargs={'remote_set_id' : job_set.id, 'instrument_name' : "seq"})))
        else:
            messages.add_message(request, messages.ERROR, message="The job was not submitted. There was an internal problem with Fermi. The administrators have been notified.")
    
    redirect_url = reverse('configuration_options',
                           kwargs={'config_id' : config_id, 'instrument_name' : INSTRUMENT_NAME})
    logger.debug("Redirecting to %s"%redirect_url)
    return redirect(redirect_url)

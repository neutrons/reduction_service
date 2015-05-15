from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render_to_response, redirect
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
import inspect
from django.http import HttpResponse

from seq import INSTRUMENT_NAME

import logging
logger = logging.getLogger('seq.views')


@login_required
def configuration_submit(request, config_id):
    """
    
    TODO!
    """
    
    logger.debug("Specific SEQ Submit: %s"%(inspect.stack()[0][3]))
    
    return HttpResponse('#TODO!')
    

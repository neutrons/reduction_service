"""
    Forms for general reduction
    
    @author: M. Doucet, Oak Ridge National Laboratory
    @author: R. Leal, Oak Ridge National Laboratory
    @copyright: 2015 Oak Ridge National Laboratory
"""
from django import forms
from reduction.models import Experiment
import sys

import logging
logger = logging.getLogger('reduction.forms')

def process_experiment(reduction_obj, expt_string, instrument_name):
    """
        Process the experiment string of a form and find/create
        the appropriate Experiment object
        
        This should be common to several <instrument>.forms
        
        @param reduction_obj: ReductionProcess or ReductionConfiguration object
        @param expt_string: string taken from the reduction form
    """
    # Find experiment
    uncategorized_expt = Experiment.objects.get_uncategorized(instrument_name)
    expts = expt_string.split(',')
    for item in expts:
        # Experiments have unique names of no more than 24 characters
        expt_objs = Experiment.objects.filter(name=item.upper().strip()[:24])
        if len(expt_objs)>0:
            if expt_objs[0] not in reduction_obj.experiments.all():
                reduction_obj.experiments.add(expt_objs[0])
        else:
            expt_obj = Experiment(name=item.upper().strip()[:24])
            expt_obj.save()
            reduction_obj.experiments.add(expt_obj)
    
    # Clean up the uncategorized experiment object if we found
    # at least one suitable experiment to associate with this reduction
    if len(expts)>0:
        if uncategorized_expt in reduction_obj.experiments.all():
            try:
                reduction_obj.experiments.remove(uncategorized_expt)
            except:
                logger.error("Could not remote uncategorized expt: %s" % sys.exc_value)
    else:
        reduction_obj.experiments.add(uncategorized_expt)

class ReductionStart(forms.Form):
    """
        Simple form to select run to reduce
    """
    run_number = forms.IntegerField(required=False)
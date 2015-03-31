"""
    Forms for general reduction
    
    @author: M. Doucet, Oak Ridge National Laboratory
    @author: R. Leal, Oak Ridge National Laboratory
    @copyright: 2015 Oak Ridge National Laboratory
"""
from django import forms
from reduction.models import Experiment
import sys
import time

import logging
logger = logging.getLogger('main')

def _now_in_text():
    time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

class Reduction(forms.Form):
    """
        Super class for Reduction form
        
        
    """
    # Reduction name
    reduction_name = forms.CharField(required=False, initial="Reduction of %s"%_now_in_text() )
    reduction_id = forms.IntegerField(required=False, widget=forms.HiddenInput)
    expt_id = forms.IntegerField(required=False, widget=forms.HiddenInput)
    experiment = forms.CharField(required=False, initial='uncategorized')
    nickname = forms.CharField(required=False, initial='')


class Configuration(forms.Form):
    """
        Super class for Reduction for configuration
        
    """
    # General information
    reduction_name = forms.CharField(required=False, initial="Configuration of %s"%_now_in_text())
    experiment = forms.CharField(required=True, initial='uncategorized')
    
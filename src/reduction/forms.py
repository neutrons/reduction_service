"""
    Forms for general reduction
    
    @author: M. Doucet, Oak Ridge National Laboratory
    @author: R. Leal, Oak Ridge National Laboratory
    @copyright: 2015 Oak Ridge National Laboratory
"""
from django import forms


import logging
logger = logging.getLogger('reduction.forms')

class ReductionStart(forms.Form):
    """
        Simple form to select run to reduce
    """
    run_number = forms.IntegerField(required=False)
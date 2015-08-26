# coding: utf-8

"""
    Forms for related to fermi
    
    
    @author: R. Leal, Oak Ridge National Laboratory
    @copyright: 2015 Oak Ridge National Laboratory
"""

from django import forms

class FermiLoginForm(forms.Form):
    """
        Simple form to submit authentication
    """
    username = forms.CharField()
    password = forms.CharField()

class FermiProcessingForm(forms.Form):
    '''
    Job Submission
    
    Implementation Specific POST Variables    
    NumNodes : <number_of_nodes>
    CoresPerNode: <cores_per_node>

    '''
    number_of_nodes = forms.IntegerField(max_value=4, min_value=1, initial=1, help_text = 'NumNodes : <number_of_nodes>')
    cores_per_node =  forms.IntegerField(max_value=8, min_value=1, initial=1, help_text = 'CoresPerNode: <cores_per_node>')







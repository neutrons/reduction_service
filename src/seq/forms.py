"""
    Forms for SEQ reduction
    
    TODO: Copied from EQSANS! Need to be changed
    
    @author: R. Leal, Oak Ridge National Laboratory
    @author: M. Doucet, Oak Ridge National Laboratory
    @copyright: 2015 Oak Ridge National Laboratory
"""

from django import forms
from django.shortcuts import get_object_or_404
from reduction.models import ReductionProcess
from reduction.models import Instrument
from reduction.forms import process_experiment
from reduction_service.forms_util import build_script
import time
import sys
import json
import logging
import copy
import os.path

logger = logging.getLogger('seq.forms')
scripts_location = os.path.join(os.path.dirname(__file__),"scripts")

class ReductionOptions(forms.Form):
    """
        Reduction parameter form
        URL: /reduction/eqsans/reduction/
        
    """
    # Reduction name
    reduction_name = forms.CharField(required=False)
    reduction_id = forms.IntegerField(required=False, widget=forms.HiddenInput)
    expt_id = forms.IntegerField(required=False, widget=forms.HiddenInput)
    experiment = forms.CharField(required=False, initial='uncategorized')
    # 
    data_file = forms.CharField(required=True)
    raw_vanadium = forms.CharField(required=False, initial='')
    processed_vanadium = forms.CharField(required=False, initial='')
    
    grouping_file = forms.ChoiceField([("/SNS/SEQ/shared/autoreduce/SEQ_1x1_grouping.xml","1 x 1"),
                                       ("/SNS/SEQ/shared/autoreduce/SEQ_2x1_grouping.xml","2 x 1"),
                                       ("/SNS/SEQ/shared/autoreduce/SEQ_2x2_grouping.xml","2 x 2"),
                                       ("/SNS/SEQ/shared/autoreduce/SEQ_4x1_grouping.xml","4 x 1"),
                                       ("/SNS/SEQ/shared/autoreduce/SEQ_4x2_grouping.xml","4 x 2")])
    energy_binning_min = forms.FloatField(required=True, initial=-1.0)
    energy_binning_step = forms.FloatField(required=True, initial=0.005)
    energy_binning_max = forms.FloatField(required=True, initial=0.95)
    
    
    
    @classmethod
    def as_xml(cls, data):
        """
            Create XML from the current data.
            @param data: dictionary of reduction properties
            
            #TODO
        """
        xml  = "<Reduction>\n"
        xml += "<instrument_name>SEQ</instrument_name>\n"
        xml += "<timestamp>%s</timestamp>\n" % time.ctime()
        xml += "</Reduction>"

        return xml

    def to_db(self, user, reduction_id=None):
        """
            Save reduction properties to DB.
            
            
            
            @param user: User object
            @param reduction_id: pk of the ReductionProcess entry
            @param config_id: pk of the ReductionConfiguration entry
        """
        if not self.is_valid():
            raise RuntimeError, "Reduction options form invalid"
        
        if reduction_id is None:
            reduction_id = self.cleaned_data['reduction_id']
            
        # Find or create a reduction process entry and update it
        if reduction_id is not None:
            reduction_proc = get_object_or_404(ReductionProcess, pk=reduction_id, owner=user)
            # If the user changed the data to be reduced, create a new reduction process entry
            new_reduction = not reduction_proc.data_file == self.cleaned_data['data_file']
        else:
            new_reduction = True
            
        if new_reduction:
            seq = Instrument.objects.get(name='seq')
            reduction_proc = ReductionProcess(owner=user, instrument=seq)
        reduction_proc.name = self.cleaned_data['reduction_name']
        reduction_proc.data_file = self.cleaned_data['data_file']
        reduction_proc.save()
        
        # Set the parameters associated with the reduction process entry

        property_dict = copy.deepcopy(self.cleaned_data)
        property_dict['reduction_id'] = reduction_proc.id

        try:
            properties = json.dumps(property_dict)
            reduction_proc.properties = properties
            reduction_proc.save()
        except:
            logger.error("Could not process reduction properties: %s" % sys.exc_value)
        
        # Find experiment
        process_experiment(reduction_proc, self.cleaned_data['experiment'])
                
        return reduction_proc.pk
    
    @classmethod
    def data_from_db(cls, user, reduction_id):
        """
            Return a dictionary that we can use to populate a form
            @param user: User object
            @param reduction_id: ReductionProcess primary key
        """
        reduction_proc = get_object_or_404(ReductionProcess, pk=reduction_id, owner=user)
        data = reduction_proc.get_data_dict()
        # Ensure all the fields are there
        for f in cls.base_fields:
            if not f in data:
                data[f]=cls.base_fields[f].initial

        expt_list = reduction_proc.experiments.all()
        data['experiment'] = ', '.join([str(e.name) for e in expt_list if len(str(e.name))>0])
        return data
    
    @classmethod
    def as_mantid_script(cls, data, output_path='/tmp'):
        """
            Return the Mantid script associated with the current parameters
            @param data: dictionary of reduction properties
            @param output_path: output path to use in the script
            
            Parameters to substitute:
            raw_vanadium : "/SNS/SEQ/IPTS-13532/nexus/SEQ_64933.nxs.h5"
            processed_vanadium : "van64933mask64_2X2.nxs"
            mask:
                MaskBTPParameters.append({'Pixel': '1-8,121-128'})
                MaskBTPParameters.append({'Bank': '99-102,114,115,75,76,38,39'})
                MaskBTPParameters.append({'Bank': '64'})
            energy_binning_min : [-1.0*EGuess,0.005*EGuess,0.95*EGuess]
            energy_binning_step
            energy_binning_max
            grouping : "/SNS/SEQ/shared/autoreduce/SEQ_2x2_grouping.xml" 
                #Typically an empty string '', choose 2x1 or some other grouping file created by GenerateGroupingSNSInelastic or GenerateGroupingPowder
            
        """
        script_file_path = os.path.join(scripts_location,'reduce.py')
        data.update({'output_path' : output_path})
        script = build_script(script_file_path, cls, data)
        logger.debug("\n-------------------------\n"+script+"\n-------------------------\n")
        return script


    def is_reduction_valid(self):
        """
            Check whether the form data would produce a valid reduction script
        """
        return True


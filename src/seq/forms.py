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
from django.core.exceptions import ValidationError
import time
import sys
import json
import logging
import copy
import os.path
import re

logger = logging.getLogger('seq.forms')
scripts_location = os.path.join(os.path.dirname(__file__), "scripts")

class ReductionOptions(forms.Form):
    """
        Reduction parameter form       
    """
    # Reduction name
    reduction_name = forms.CharField(required=False, initial=time.strftime("Reduction of %Y-%m-%d %H:%M:%S", time.localtime()) )
    reduction_id = forms.IntegerField(required=False, widget=forms.HiddenInput)
    expt_id = forms.IntegerField(required=False, widget=forms.HiddenInput)
    experiment = forms.CharField(required=False, initial='uncategorized')
    # 
    data_file = forms.CharField(required=True)
    raw_vanadium = forms.CharField(required=True)
    
    grouping_file = forms.ChoiceField([("/SNS/SEQ/shared/autoreduce/SEQ_1x1_grouping.xml", "1 x 1"),
                                       ("/SNS/SEQ/shared/autoreduce/SEQ_2x1_grouping.xml", "2 x 1"),
                                       ("/SNS/SEQ/shared/autoreduce/SEQ_2x2_grouping.xml", "2 x 2"),
                                       ("/SNS/SEQ/shared/autoreduce/SEQ_4x1_grouping.xml", "4 x 1"),
                                       ("/SNS/SEQ/shared/autoreduce/SEQ_4x2_grouping.xml", "4 x 2")])
    energy_binning_min = forms.FloatField(required=True, initial=-1.0)
    energy_binning_step = forms.FloatField(required=True, initial=0.005)
    energy_binning_max = forms.FloatField(required=True, initial=0.95)
    
    
    error_message_mask = {'invalid': "Not a valid ranged input. Use for example: 1-8,121-128"}
    help_text="Use ranged input. E.g.: 1-8,121-128."
    field_regex=r'^[\d\-,]+$'
    
    masked_bank1 = forms.RegexField(regex=field_regex, required=False, help_text=help_text,
                                   error_messages=error_message_mask)
    masked_tube1 = forms.RegexField(regex=field_regex, required=False, help_text=help_text,
                                   error_messages=error_message_mask)
    masked_pixel1 = forms.RegexField(regex=field_regex, required=False, help_text=help_text,
                                    error_messages=error_message_mask, initial="1-8,121-128")
    parameter1 = forms.CharField(widget=forms.HiddenInput(), required=False)
     
    masked_bank2 = forms.RegexField(regex=field_regex, required=False, help_text=help_text,
                                   error_messages=error_message_mask, initial="99-102,114,115,75,76,38,39")
    masked_tube2 = forms.RegexField(regex=field_regex, required=False, help_text=help_text,
                                   error_messages=error_message_mask)
    masked_pixel2 = forms.RegexField(regex=field_regex, required=False, help_text=help_text,
                                    error_messages=error_message_mask)
    parameter2 = forms.CharField(widget=forms.HiddenInput(), required=False)

    masked_bank3 = forms.RegexField(regex=field_regex, required=False, help_text=help_text,
                                   error_messages=error_message_mask, initial="64")
    masked_tube3 = forms.RegexField(regex=field_regex, required=False, help_text=help_text,
                                   error_messages=error_message_mask)
    masked_pixel3 = forms.RegexField(regex=field_regex, required=False, help_text=help_text,
                                    error_messages=error_message_mask)
    parameter3 = forms.CharField(widget=forms.HiddenInput(), required=False)

    masked_bank4 = forms.RegexField(regex=field_regex, required=False, help_text=help_text,
                                   error_messages=error_message_mask)
    masked_tube4 = forms.RegexField(regex=field_regex, required=False, help_text=help_text,
                                   error_messages=error_message_mask)
    masked_pixel4 = forms.RegexField(regex=field_regex, required=False, help_text=help_text,
                                    error_messages=error_message_mask)
    parameter4 = forms.CharField(widget=forms.HiddenInput(), required=False)

    def clean_parameter1(self):
            data = self.masks_as_python(1)
            if len(data) > 0:
                return data
            return None
    def clean_parameter2(self):
            data = self.masks_as_python(2)
            if len(data) > 0:
                return data
            return None
    def clean_parameter3(self):
            data = self.masks_as_python(3)
            if len(data) > 0:
                return data
            return None
    def clean_parameter4(self):
            data = self.masks_as_python(4)
            if len(data) > 0:
                return data
            return None
            
    def masks_as_python(self,number):
        """
            Return a string representing the Mantid command to run
            for this mask item.
        """
        bank = "masked_bank%s"%number
        tube = "masked_tube%s"%number
        pixel = "masked_pixel%s"%number
        entry_dict = {}
        if bank in self.cleaned_data and len(self.cleaned_data[bank].strip())>0:
            entry_dict["Bank"] = str(self.cleaned_data[bank])
        if tube in self.cleaned_data and len(self.cleaned_data[tube].strip())>0:
            entry_dict["Tube"] = str(self.cleaned_data[tube])
        if pixel in self.cleaned_data and len(self.cleaned_data[pixel].strip())>0:
            entry_dict["Pixel"] = str(self.cleaned_data[pixel])
        if len(entry_dict)==0:
            return ""
        return "%s" % str(entry_dict)
#     # 
#     def clean_masked_bank1(self):
#         data = self.cleaned_data['masked_bank1']
#         if len(data) > 0:
#             data = self._hyphen_range(data)
#         return data
#     
#     def clean_masked_tube1(self):
#         data = self.cleaned_data['masked_tube1']
#         if len(data) > 0:
#             data = self._hyphen_range(data)
#         return data
#     
#     def clean_masked_pixel1(self):
#         data = self.cleaned_data['masked_pixel1']
#         if len(data) > 0:
#             data = self._hyphen_range(data)
#         return data
# 
#     
#     def _hyphen_range(self, s):
#         """ Takes a range in form of "a-b" and generate a list of numbers between a and b inclusive.
#         Also accepts comma separated ranges like "a-b,c-d,f" will build a list which will include
#         Numbers from a to b, a to d and f"""
#         s="".join(s.split())#removes white space
#         r=set()
#         for x in s.split(','):
#             t=x.split('-')
#             if len(t) not in [1,2]:
#                 logger.error("hash_range is given its arguement as "+s+" which seems not correctly formated.")
#             r.add(int(t[0])) if len(t)==1 else r.update(set(range(int(t[0]),int(t[1])+1)))
#         l=list(r)
#         l.sort()
#         l_in_str = ','.join(str(x) for x in l)
#         return l_in_str

    
    @classmethod
    def as_xml(cls, data):
        """
            Create XML from the current data.
            @param data: dictionary of reduction properties
            
            #TODO
        """
        xml = "<Reduction>\n"
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
                data[f] = cls.base_fields[f].initial

        expt_list = reduction_proc.experiments.all()
        data['experiment'] = ', '.join([str(e.name) for e in expt_list if len(str(e.name)) > 0])
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
        script_file_path = os.path.join(scripts_location, 'reduce.py')
        data.update({'output_path' : output_path})
        script = build_script(script_file_path, cls, data)
        logger.debug("\n-------------------------\n" + script + "\n-------------------------\n")
        return script


    def is_reduction_valid(self):
        """
            Check whether the form data would produce a valid reduction script
        """
        return True

def validate_integer_list(value):
    """
        Allow for "1,2,3" and "1-3"
        
        @param value: string value to parse
    """
    # Look for a list of ranges
    range_list = value.split(',')
    for _ in range_list:
        for item in range.split('-'):
            try:
                int(item.strip())
            except:
                raise ValidationError(u'Error parsing %s for a range of integers' % value)

class MaskForm(forms.Form):
    """
        Simple form for a mask entry.
        A combination of banks, tubes, pixels can be specified.
    """
    bank = forms.CharField(required=False, initial='', validators=[validate_integer_list])
    tube = forms.CharField(required=False, initial='', validators=[validate_integer_list])
    pixel = forms.CharField(required=False, initial='', validators=[validate_integer_list])
    remove = forms.BooleanField(required=False, initial=False)
    
    @classmethod
    def to_tokens(cls, value):
        """
            Takes a block of Mantid script and extract the
            dictionary argument. The template should be like
            
            MaskBTPParameters({'Bank':'', 'Tube':'', 'Pixel':''})
            
            @param value: string value for the code snippet
        """
        mask_list = []
        try:
            lines = value.split('\n')
            for line in lines:
                if 'MaskBTPParameters' in line:
                    mask_strings = re.findall("append\((.+)\)", line.strip())
                    for item in mask_strings:
                        mask_list.append(eval(item.lower()))
        except:
            logging.error("MaskForm count not parse a command line: %s" % sys.exc_value)
        return mask_list
    
    @classmethod
    def to_python(cls, mask_list, indent='    '):
        """
            Take a block of Mantid script from a list of mask forms
            
            @param mask_list: list of MaskForm objects
            @param indent: string indentation to add to each line
        """
        command_list = ''
        for mask in mask_list:
            if 'remove' in mask.cleaned_data and mask.cleaned_data['remove'] == True:
                continue
            command_str = str(mask)
            if len(command_str) > 0:
                command_list += "%s%s\n" % (indent, command_str)
        return command_list

    def __str__(self):
        """
            Return a string representing the Mantid command to run
            for this mask item.
        """
        entry_dict = {}
        if 'bank' in self.cleaned_data and len(self.cleaned_data['bank'].strip()) > 0:
            entry_dict["Bank"] = str(self.cleaned_data['bank'])
        if 'tube' in self.cleaned_data and len(self.cleaned_data['tube'].strip()) > 0:
            entry_dict["Tube"] = str(self.cleaned_data['tube'])
        if 'pixel' in self.cleaned_data and len(self.cleaned_data['pixel'].strip()) > 0:
            entry_dict["Pixel"] = str(self.cleaned_data['pixel'])
        if len(entry_dict) == 0:
            return ""
        return "MaskBTPParameters.append(%s)" % str(entry_dict)

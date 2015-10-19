"""
    Forms for EQSANS reduction
    
    @author: M. Doucet, Oak Ridge National Laboratory
    @copyright: 2014 Oak Ridge National Laboratory
"""
from django import forms
from django.shortcuts import get_object_or_404
from reduction_server.reduction.models import ReductionProcess, ReductionConfiguration
from reduction_server.reduction.models import Instrument
from reduction_server.reduction.forms import process_experiment
from reduction_server.forms_util import build_script, is_xml_valid
from django.forms.formsets import formset_factory
from reduction_server.reduction.forms import ConfigurationFormHandlerBase
from django.contrib import messages
import time
import sys
import json
import logging
import copy
import os.path
import pprint
from reduction_server.eqsans import INSTRUMENT_NAME

logger = logging.getLogger('eqsans.forms')
scripts_location = os.path.join(os.path.dirname(__file__),"scripts")

class ReductionConfigurationForm(forms.Form):
    """
        Configuration form for EQSANS reduction
        URL: /reduction/eqsans/configuration/
    """
    # General information
    reduction_name = forms.CharField(required=False, initial='Configuration')
    experiment = forms.CharField(required=True, initial='uncategorized')
    absolute_scale_factor = forms.FloatField(required=False, initial=1.0)
    dark_current_run = forms.CharField(required=False, initial='')
    sample_aperture_diameter = forms.FloatField(required=False, initial=10.0)
    beam_radius = forms.FloatField(required=False, initial=3.0, widget=forms.HiddenInput)
    fit_frames_together = forms.BooleanField(required=False, initial=False, widget=forms.HiddenInput)
    theta_dependent_correction = forms.BooleanField(required=False, initial=True, widget=forms.HiddenInput)
    mask_file = forms.CharField(required=False, initial='')
    
    # Beam center
    direct_beam_run = forms.CharField(required=True)
    
    # Sensitivity
    sensitivity_file = forms.CharField(required=False, initial='')
    sensitivity_min = forms.FloatField(required=False, initial=0.4)
    sensitivity_max = forms.FloatField(required=False, initial=2.0)
    
    # Data
    sample_thickness = forms.FloatField(required=False, initial=1.0)
    transmission_empty = forms.CharField(required=True)

    @classmethod
    def data_from_db(cls, user, reduction_config):
        """
            Return a dictionary that we can use to populate the initial
            contents of a form
            @param user: User object
            @param reduction_config: ReductionConfiguration object
        """
        data = reduction_config.get_data_dict()
        # Ensure all the fields are there
        for f in cls.base_fields:
            if not f in data:
                data[f]=cls.base_fields[f].initial
        expt_list = reduction_config.experiments.all()
        data['experiment'] = ', '.join([str(e.name) for e in expt_list if len(str(e.name))>0])
        return data

    def to_db(self, user, config_id=None):
        """
            Save a configuration to the database
            @param user: User object
            @param config_id: PK of the config object to update (None for creation)
        """
        instrument = Instrument.objects.get(name=INSTRUMENT_NAME)
        # Find or create a reduction process entry and update it
        if config_id is not None:
            reduction_config = get_object_or_404(ReductionConfiguration, pk=config_id, owner=user)
            reduction_config.name = self.cleaned_data['reduction_name']
        else:
            reduction_config = ReductionConfiguration(owner=user,
                                                      instrument=instrument,
                                                      name=self.cleaned_data['reduction_name'])
            reduction_config.save()
        
        # Find experiment
        process_experiment(reduction_config, self.cleaned_data['experiment'],INSTRUMENT_NAME)
                
        # Set the parameters associated with the reduction process entry
        try:
            property_dict = copy.deepcopy(self.cleaned_data)
            # Make sure we have a background transmission empty
            property_dict['background_transmission_empty']=property_dict['transmission_empty']
            # This configuration requires that we fit the beam center
            property_dict['fit_direct_beam'] = True
            # Set the sensitivity calculation flag as needed
            if len(property_dict['sensitivity_file'])>0:
                property_dict['perform_sensitivity']=True
            properties = json.dumps(property_dict)
            reduction_config.properties = properties
            reduction_config.save()
        except:
            logger.error("Could not process reduction properties: %s" % sys.exc_value)
        
        return reduction_config.pk


class ReductionOptions(forms.Form):
    """
        Reduction parameter form
        URL: /reduction/eqsans/reduction/
        
    """
    # Reduction name
    reduction_name = forms.CharField(required=False, initial=time.strftime("Reduction of %Y-%m-%d %H:%M:%S", time.localtime()) )
    reduction_id = forms.IntegerField(required=False, widget=forms.HiddenInput)
    expt_id = forms.IntegerField(required=False, widget=forms.HiddenInput)
    experiment = forms.CharField(required=False, initial='uncategorized')
    nickname = forms.CharField(required=False, initial='')
    # General options
    absolute_scale_factor = forms.FloatField(required=False, initial=1.0)
    dark_current_run = forms.CharField(required=False, initial='')
    sample_aperture_diameter = forms.FloatField(required=False, initial=10.0)
    mask_file = forms.CharField(required=False, initial='')
    
    # Beam center
    beam_center_x = forms.FloatField(required=False, initial=96.0)
    beam_center_y = forms.FloatField(required=False, initial=128.0)
    fit_direct_beam = forms.BooleanField(required=False, initial=False,
                                         help_text='Select to fit the beam center')
    direct_beam_run = forms.CharField(required=False, initial='')
    
    # Sensitivity
    perform_sensitivity = forms.BooleanField(required=False, initial=False,
                                             label='Perform sensitivity correction',
                                             help_text='Select to enable sensitivity correction')
    sensitivity_file = forms.CharField(required=False, initial='')
    sensitivity_min = forms.FloatField(required=False, initial=0.4)
    sensitivity_max = forms.FloatField(required=False, initial=2.0)
    
    # Data
    data_file = forms.CharField(required=True)
    sample_thickness = forms.FloatField(required=False, initial=1.0)
    transmission_sample = forms.CharField(required=True)
    transmission_empty = forms.CharField(required=False)
    beam_radius = forms.FloatField(required=False, initial=3.0, widget=forms.HiddenInput)
    fit_frames_together = forms.BooleanField(required=False, initial=False, widget=forms.HiddenInput)
    theta_dependent_correction = forms.BooleanField(required=False, initial=True, widget=forms.HiddenInput)
    
    # Background
    subtract_background = forms.BooleanField(required=False, initial=False,
                                             help_text='Select to enable background subtraction')
    background_file = forms.CharField(required=False, initial='')
    background_transmission_sample = forms.CharField(label='Transmission sample', required=False, initial='')
    background_transmission_empty = forms.CharField(label='Transmission empty', required=False, initial='')
    
    @classmethod
    def as_xml(cls, data):
        """
            Create XML from the current data.
            @param data: dictionary of reduction properties
        """
        data['timestamp'] = time.ctime();
        dark_corr = data['dark_current_run'] and str(len(data['dark_current_run'])>0)
        data['dark_corr'] = dark_corr
        if data['beam_radius'] is None:
            data['beam_radius']=cls.base_fields['beam_radius'].initial
        
        xml_file_path = os.path.join(scripts_location,'reduce.xml')
        xml = build_script(xml_file_path, cls, data)
        
        if is_xml_valid(xml):
            logger.debug("\n-------------------------\n"+xml+"\n-------------------------\n")
            return xml
        else:
            logger.error("XML is not valid!")
            return None
    
    def to_db(self, user, reduction_id=None, config_id=None):
        """
            Save reduction properties to DB.
            If we supply a config_id, the properties from that
            configuration will take precedence.
            If no config_id is supplied and the reduction_id 
            provided is found to be associated to a configuration,
            make a new copy of the reduction object so that we
            don't corrupt the configured reduction.
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
            new_reduction = not reduction_proc.data_file==self.cleaned_data['data_file']
            # If the reduction process is configured and the config isn't the provided one
            config_obj = reduction_proc.get_config()
            new_reduction = new_reduction or (config_obj is not None and not config_obj.id == config_id)
        else:
            new_reduction = True
            
        if new_reduction:
            eqsans = Instrument.objects.get(name=INSTRUMENT_NAME)
            reduction_proc = ReductionProcess(owner=user,
                                              instrument=eqsans)
        reduction_proc.name = self.cleaned_data['reduction_name']
        reduction_proc.data_file = self.cleaned_data['data_file']
        reduction_proc.save()
        
        # Set the parameters associated with the reduction process entry
        config_property_dict = {}
        property_dict = copy.deepcopy(self.cleaned_data)
        property_dict['reduction_id'] = reduction_proc.id
        if config_id is not None:
            reduction_config = get_object_or_404(ReductionConfiguration, pk=config_id, owner=user)
            if reduction_proc not in reduction_config.reductions.all():
                reduction_config.reductions.add(reduction_proc)
            config_property_dict = json.loads(reduction_config.properties)
            property_dict.update(config_property_dict)
            reduction_proc.name = reduction_config.name
            reduction_proc.save()
            for item in reduction_config.experiments.all():
                if item not in reduction_proc.experiments.all():
                    reduction_proc.experiments.add(item)
        try:
            properties = json.dumps(property_dict)
            reduction_proc.properties = properties
            reduction_proc.save()
        except:
            logger.error("Could not process reduction properties: %s" % sys.exc_value)
        
        # Find experiment
        process_experiment(reduction_proc, self.cleaned_data['experiment'], instrument_name=INSTRUMENT_NAME)
                
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
        if len(data['background_file'])>0:
            data['subtract_background']=True
        expt_list = reduction_proc.experiments.all()
        data['experiment'] = ', '.join([str(e.name) for e in expt_list if len(str(e.name))>0])
        return data
    
    @classmethod
    def as_mantid_script(cls, data, output_path='/tmp'):
        """
            Return the Mantid script associated with the current parameters
            @param data: dictionary of reduction properties
            @param output_path: output path to use in the script
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
    


    ########################################

class ConfigurationFormHandler(ConfigurationFormHandlerBase):
    '''
    Class to handle the configuration action.
    It will create and validate forms. It creates arbirary formsets
    
    '''
    def __init__(self, request,config_id):
        self.request = request
        self.config_id = config_id
        self.options_form = None
        self.config_form = None
        self._build_forms()
        
        
    def _get_reduction_option_forset(self):
        # Create a form for the page
        default_extra = 1 if self.config_id is None and not (self.request.method == 'GET' and 'data_file' in self.request.GET) else 0
        try:
            extra = int(self.request.GET.get('extra', default_extra))
        except:
            extra = default_extra
        
        logger.debug("Extra = %s"%extra)
        ReductionOptionsSet = formset_factory(ReductionOptions, extra=extra)
        return ReductionOptionsSet
    
    def _build_forms(self):
        if self.request.method == 'POST':
            self._build_forms_from_post()
        else:
            self._build_forms_from_get()
    
    def _build_forms_from_post(self):
        ReductionOptionsSet = self._get_reduction_option_forset()
        self.config_form = ReductionConfigurationForm(self.request.POST)
        self.options_form = ReductionOptionsSet(self.request.POST)
        
    
    def _build_forms_from_get(self):
        # Deal with the case of creating a new configuration
        ReductionOptionsSet = self._get_reduction_option_forset()
        if self.config_id is None:
            initial_values = []
            if 'data_file' in self.request.GET:
                initial_values = [{'data_file': self.request.GET.get('data_file', '')}]
            self.options_form = ReductionOptionsSet(initial=initial_values)
            
            initial_config = {}
            if 'experiment' in self.request.GET:
                initial_config['experiment'] = self.request.GET.get('experiment', '')
            if 'reduction_name' in self.request.GET:
                initial_config['reduction_name'] = self.request.GET.get('reduction_name', '')
            self.config_form = ReductionConfigurationForm(initial=initial_config)
        # Retrieve existing configuration
        else:
            reduction_config = get_object_or_404(ReductionConfiguration, pk=self.config_id, owner=self.request.user)
            initial_config = ReductionConfigurationForm.data_from_db(self.request.user, reduction_config)
            
            initial_values = []
            for item in reduction_config.reductions.all():
                props = ReductionOptions.data_from_db(self.request.user, item.pk)
                initial_values.append(props)
                
            self.options_form = ReductionOptionsSet(initial=initial_values)
            self.config_form = ReductionConfigurationForm(initial=initial_config)
    
    def are_forms_valid(self):
        if self.options_form.is_valid() and self.config_form.is_valid():
            return True
        else:
            messages.add_message(self.request, messages.ERROR,
                                 'The form is not valid. Please see messages next to the fields above.')
            logger.error("config_form: %s"%self.config_form.errors)
            logger.error("options_form: %s"%self.options_form.errors)
            return False
            
    def save_forms(self):
        """
        return config_id
        """
        config_id = self.config_form.to_db(self.request.user, self.config_id)
        for form in self.options_form:
            form.to_db(self.request.user, None, config_id)
        
        messages.add_message(self.request, messages.SUCCESS, "Configuration %d and reduction parameters were sucessfully updated."%(config_id))
        return config_id
    
    def get_forms(self):
        return {'options_form': self.options_form,
                'config_form': self.config_form }
    
    
    def get_mantid_script(self, reduction_id, transaction_directory):
        """
        @param reductions: all the reductions for this configuration
        @param transaction: Transaction for this job submission 
        """

        data = ReductionOptions.data_from_db(self.request.user, reduction_id)
        code = ReductionOptions.as_mantid_script(data, transaction_directory)
        
        return code
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    


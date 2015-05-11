# coding: utf-8

"""
    Forms for SEQ reduction
    
    
    @author: R. Leal, Oak Ridge National Laboratory
    @copyright: 2015 Oak Ridge National Laboratory
"""

from django import forms
from django.shortcuts import get_object_or_404
from reduction.models import ReductionProcess, ReductionConfiguration
from reduction.models import Instrument
from reduction.forms import process_experiment
from reduction_service.forms_util import build_script
from django.core.exceptions import ValidationError
from reduction_service.forms_util import build_script, is_xml_valid
from reduction.forms import ConfigurationFormHandlerBase
from django.forms.formsets import formset_factory
from django.contrib import messages
import time
import sys
import json
import logging
import copy
import os.path
import re
import pprint
import tempfile

from seq import INSTRUMENT_NAME

logger = logging.getLogger('seq.forms')
scripts_location = os.path.join(os.path.dirname(__file__), "scripts")


ranged_field_error_message = {'invalid': "Not a valid ranged input. Use for example: 1-8,121-128"}
ranged_field_help_text = "Use ranged input. E.g.: 1-8,12,21,44,121-128."
ranged_field_regex = r'^[\d\-,]+$'
    

class ConfigurationForm(forms.Form):
    
    required_css_class = 'required'
    
    # General information
    reduction_name = forms.CharField(required=False, 
                                     initial=time.strftime("Batch of %Y-%m-%d %H:%M:%S", time.localtime()))
    experiment = forms.CharField(required=True, initial='uncategorized')
    
    # <!-- DEFAULTS section -->
    # <defaults Instrument="ARCS" FilterBadPulses="False" Save="summary" />
    filter_bad_pulses =  forms.BooleanField(required=False, initial=False)
    
    save_choices = [(i,i) for i in ['summary', 'phx', 'spe', 'nxspe', 'par', 'jpg', 'nxs', 'mdnxs', 'iofq','iofe',
                                          'iofphiecolumn','iofphiearray','iofqecolumn','iofqearray','sqw','vannorm']]
    
    save_format = forms.MultipleChoiceField(required=True, widget=forms.SelectMultiple, initial=save_choices[0],
                                      choices=save_choices, help_text="Hit 'Ctrl' for multiple selection." )
    
#     <!-- CALIBRATION AND MaskING section -->
#     <calibration SaveProcDetVanFilename="van37350_white_uposcB.nxs"
#         DetVanIntRangeUnits="wavelength" NormalizedCalibration="True">
# 
#         <VanRuns>37350</VanRuns>
#         <DetVanIntRangeLow>0.35</DetVanIntRangeLow>
#         <DetVanIntRangeHigh>0.75</DetVanIntRangeHigh>
# 
#         <Mask algorithm="MaskBTP" Pixel="1-7" />
#         <Mask algorithm="MaskBTP" Pixel="122-128" />
#         <Mask algorithm="MaskBTP" Bank="71" Pixel="1-14" />
#         <Mask algorithm="MaskBTP" Bank="71" Pixel="114-128" />
#         <Mask algorithm="MaskBTP" Bank="70" Pixel="1-12" />
#         <Mask algorithm="MaskBTP" Bank="70" Pixel="117-128" />
#         <Mask algorithm="MaskAngle" MaxAngle="2.5" />
# 
#         <Mask HighCounts='1E12' LowCounts='0.1' HighOutlier='100'
#             LowOutlier='0.01' MedianTestHigh='1.75' MedianTestLow='0.25'
#             MedianTestCorrectForSolidAngle='1' ErrorBarCriterion='3.3'
#             MedianTestLevelsUp='1' />
# 
# 
#     </calibration>

    processed_vanadium_filename = forms.CharField(widget=forms.HiddenInput(), required=False, 
                                                  initial= tempfile.NamedTemporaryFile(delete=True).name)
    
    units_choices = [(i,i) for i in ['Wavelength', 'DeltaE', 'DeltaE_inWavenumber', 'Energy', 'Energy_inWavenumber',
                    'Momentum', 'MomentumTransfer', 'QSquared', 'TOF', 'dspacing']]
    units = forms.ChoiceField(choices=units_choices,initial=units_choices[0],required=True)
    
    normalized_calibration  = forms.BooleanField(required=True, initial=True)
    
    vanadium_runs = forms.RegexField(regex=ranged_field_regex, required=True, help_text=ranged_field_help_text,
                                   widget=forms.TextInput(attrs={'size':'60'}), error_messages=ranged_field_error_message)
    
    help_text_vanadium_limits = "The vanadium data is integrated between vanadium_min and vanadium_max for the given units." 
    vanadium_min = forms.FloatField(required=True, help_text = help_text_vanadium_limits, initial=0.35)
    vanadium_max = forms.FloatField(required=True, help_text = help_text_vanadium_limits, initial=0.75)

        
    mask_angle_min = forms.FloatField(required=False,initial=0)
    mask_angle_max = forms.FloatField(required=False,initial=2.5)
    
    
    high_counts = forms.FloatField(required=True,initial=1e12)
    low_counts = forms.FloatField(required=True,initial=0.1) 
    high_outlier  = forms.FloatField(required=True,initial=100)
    low_outlier = forms.FloatField(required=True,initial=0.01) 
    median_test_high = forms.FloatField(required=True,initial=1.75) 
    median_test_low = forms.FloatField(required=True,initial=0.25)
    median_test_correct_for_solid_angle = forms.BooleanField(required=False, initial=True)
    error_bar_criterion = forms.FloatField(required=True,initial=3.3)
    median_test_levels_up = forms.BooleanField(required=False, initial=True)
    

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
    
    def to_db(self, user, config_id=None, properties={}):
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
            property_dict.update(properties)
            properties = json.dumps(property_dict)
            reduction_config.properties = properties
            reduction_config.save()
        except:
            logger.error("Could not process reduction properties: %s" % sys.exc_value)
        
        return reduction_config.pk

class MaskForm(forms.Form):
    """
        Simple form for a mask entry.
        #     <calibration processedfilename="van37350_white_uposc.nxs"
        (...)
        # 
        #         <mask algorithm="MaskBTP" Pixel="1-7" />
        #         <mask algorithm="MaskBTP" Pixel="122-128" />
        #         <mask algorithm="MaskBTP" Bank="71" Pixel="1-14" />
        #         <mask algorithm="MaskBTP" Bank="71" Pixel="114-128" />
        #         <mask algorithm="MaskBTP" Bank="70" Pixel="1-12" />
        #         <mask algorithm="MaskBTP" Bank="70" Pixel="117-128" />
        (...)
        #     </calibration>

    """
    required_css_class = 'required'
    
    bank = forms.RegexField(regex=ranged_field_regex, required=True, help_text=ranged_field_help_text,
                                   error_messages=ranged_field_error_message)
    tube = forms.RegexField(regex=ranged_field_regex, required=True, help_text=ranged_field_help_text,
                                   error_messages=ranged_field_error_message)
    pixel = forms.RegexField(regex=ranged_field_regex, required=True, help_text=ranged_field_help_text,
                                   error_messages=ranged_field_error_message)
    


class ScanForm(forms.Form):
    """
        Reduction parameters form
        
        This will be a scan! 

        <scan runs="37878" save='nxspe, summary' friendlyname="REDwithsummary"
            friendlynamelogs='SensorB' calce='false' t0='4.2' efixed='710.45'
            emin="-100" emax="685" ebin="1" grouping='powder' scantype='single' />
        
    """
    
    required_css_class = 'required'
    
    # Reduction name
    reduction_name = forms.CharField(required=False, widget=forms.HiddenInput )
    reduction_id = forms.IntegerField(required=False, widget=forms.HiddenInput)
    expt_id = forms.IntegerField(required=False, widget=forms.HiddenInput)
    experiment = forms.CharField(required=False, initial='uncategorized',widget=forms.HiddenInput)
    # Scans:    
    data_runs = forms.RegexField(regex=ranged_field_regex, required=True, help_text=ranged_field_help_text,
                                   error_messages=ranged_field_error_message, widget=forms.TextInput(attrs={'size':'60'}))
    # this will include all the runs in comma format
    data_file = forms.CharField(required=False,widget=forms.HiddenInput)
    
    save_format = forms.MultipleChoiceField(required=True, widget=forms.SelectMultiple, initial=ConfigurationForm.save_choices[0],
                                      choices= ConfigurationForm.save_choices, help_text="Hit 'Ctrl' for multiple selection." )
    
    friendly_name = forms.CharField(required=False, initial='Scan for ', widget=forms.TextInput(attrs={'size':'60'}))
    
    calc_e = forms.BooleanField(required=False, initial=False, help_text=r"Set to true to fit the beam monitors for the incident energy. If the efixed keyvalue is set, then calce will use that value as the starting point for the fitting. If efixed is not set, then calce will use the value that was saved to the data file during the measurement as the starting point for the fitting. Set typically line by line in the data section, in the defaults section, or in the instrument defaults file. If calce is set to false, one must set the efixed value.")
    
    t_0 = forms.FloatField(required=False, help_text=r"This is the time in microseconds that the peak in the neutron pulse takes to leave the moderator. If the incident energy is fitted, than the value of t0 from this fit is used, regardless if t0 is set or not. The t0 value is typically set line by line in the data section or in the defaults section. Example: t0='12.75'.")
    
    energy_fixed = forms.FloatField(required=False, help_text=r"The incident energy in meV to be used for the data reduction. If calce is set to false, then efixed must be set and will be used without fitting the beam monitors for the incident energy. Set typically line by line in the data section or in the defaults section. Example: efixed='12.7'.")
    
    energy_min = forms.FloatField(required=False, help_text=r"The minimum energy transfer in meV for the energy binning. The default value in the code is set to choose emin as -0.5 times the incident energy. Set typically line by line in the data section or in the defaults section. Example, emin='-10'.")
    energy_max = forms.FloatField(required=False, help_text=r"The maximum energy transfer in meV for the energy binning. The default value in the code is set to choose emax as 1.0 times the incident energy. Set typically line by line in the data section or in the defaults section. Example, emax='10'.")

    energy_bin = forms.FloatField(required=False, initial=100, help_text=r"Bin size in energy transfer in meV units for energy binning. Default value in the code is set to choose ebin based upon 100 steps between emin and emax. Set typically line by line in the data section or in the defaults section. Example, ebin='0.5'.") 

    
    grouping_choices = [(i,i) for i in ["%dx%d"%(v,h) for v in [1,2,4,8,16,32,64,128] for h in [1,2,4,8]] + ['powder']]
    grouping = forms.ChoiceField(choices=grouping_choices,initial=grouping_choices[0],required=True, 
                                 help_text=r"This is the name of the grouping file to be used in the data reduction. Pre-generated grouping files can be placed in the current directory within which one is running the reduction code. If no grouping value is given, then the default value is 1X1. The VXH grouping corresponds to V pixels grouped vertically and H pixels grouped horizontally. For instruments with “8pack” detectors V can have the values of (1,2,4,8,16,32,64,128), and H can have the values (1,2,4,8). These '8pack' style grouping files are generated automatically by the reduction routines. It is not recommended to bin the data with V>4 or H>1. The grouping can also be set to grouping='powder'. In this case, a powder grouping of the detectors based upon the anglestep value will be used. This keyword is set typically line by line in the data section or in the defaults section. Example: grouping='2X1'.")

    scan_choices = [(i,i) for i in ['single','step','sweep']]
    scan_type = forms.ChoiceField(choices=scan_choices,initial=scan_choices[0],required=True, 
                                  help_text=r"The scantype keywords determines how runs are combined in a given call of the <scan> reduction line. scantype can be, single, step, or sweep. single will combine all of the data together for a single reduction. step will individually reduce all of the given runs listed. sweep will combine all of the data together, and then bin them according to the log parameter chosen by the keywords logvalue, logvaluemin, logvaluemax, and logvaluestep. Note that currently there must be more than one value in the logvalue for sweep mode to work correctly (see Appendix 4). Example: scantype='step'.")
    
    
    def as_table(self):
        """Returns this form rendered as HTML <tr>s -- excluding the <table></table>.
        """
        return self._html_output(
            normal_row = u'<tr%(html_class_attr)s><th title="%(help_text)s">%(label)s</th><td>%(errors)s%(field)s</td></tr>',
            error_row = u'<tr><td colspan="2">%s</td></tr>',
            row_ender = u'</td></tr>',
            help_text_html = u'%s',
            errors_on_separate_row = False)
        
    def _hyphen_range(self, s):
        """ Takes a range in form of "a-b" and generate a list of numbers between a and b inclusive.
        Also accepts comma separated ranges like "a-b,c-d,f" will build a list which will include
        Numbers from a to b, a to d and f"""
        s="".join(s.split())#removes white space
        r=set()
        for x in s.split(','):
            t=x.split('-')
            if len(t) not in [1,2]:
                logger.error("hash_range is given its arguement as "+s+" which seems not correctly formated.")
            r.add(int(t[0])) if len(t)==1 else r.update(set(range(int(t[0]),int(t[1])+1)))
        l=list(r)
        l.sort()
        l_in_str = ','.join(str(x) for x in l)
        return l_in_str
    
    def clean_data_file(self):
        """
        This will split the ranges and data_runs and will put the data in data_file
        data_file is part of the reduction_process table
        """
        try:
            data = self.cleaned_data['data_runs']
        except:
            data = ""
        if len(data) > 0:
            data = self._hyphen_range(data)
        return data
    
    
    @classmethod
    def as_xml(cls, data):
        """
            Create XML from the current data.
            @param data: dictionary of reduction properties
        """
        data['timestamp'] = time.ctime();
                
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
            instrument = Instrument.objects.get(name=INSTRUMENT_NAME)
            reduction_proc = ReductionProcess(owner=user,
                                              instrument=instrument)
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



class ConfigurationFormHandler(ConfigurationFormHandlerBase):
    '''
    Class to handle the configuration action.
    It will create and validate forms. It creates arbirary formsets
    
    '''
    def __init__(self, request,config_id):
        self.request = request
        self.config_id = config_id
        #forms
        self.scans_form = None
        self.config_form = None
        self.masks_form = None
        self._build_forms()
        
    
    def _build_forms(self):
        if self.request.method == 'POST':
            self._build_forms_from_post()
        else:
            self._build_forms_from_get()
    
    def _build_forms_from_post(self):
        ScanFormSet = formset_factory(ScanForm,extra=0, can_delete=False)
        MaskFormSet = formset_factory(MaskForm,extra=0, can_delete=False)
        self.config_form = ConfigurationForm(self.request.POST)
        self.scans_form = ScanFormSet(self.request.POST, prefix="sf")
        self.masks_form = MaskFormSet(self.request.POST, prefix="mf")
        
    
    def _build_forms_from_get(self):
        """
        if self.config_id exists we have to get the forms content from the DB and fill in the forms we are creating
        Otherwise, just create empty forms!
        """
        
        if self.config_id is None:
            # New form
            
            initial_values = []
            if 'data_file' in self.request.GET:
                initial_values = [{'data_runs': self.request.GET.get('data_file', '')}]
                ScanFormSet = formset_factory(ScanForm,extra=0)
            else:
                ScanFormSet = formset_factory(ScanForm,extra=1)
            self.scans_form = ScanFormSet(initial=initial_values, prefix="sf")
            
            initial_config = {}
            if 'experiment' in self.request.GET:
                initial_config['experiment'] = self.request.GET.get('experiment', '')
            if 'reduction_name' in self.request.GET:
                initial_config['reduction_name'] = self.request.GET.get('reduction_name', '')
            self.config_form = ConfigurationForm(initial=initial_config)
            MaskFormSet = formset_factory(MaskForm,extra=1)
            self.masks_form = MaskFormSet(prefix="mf")
        
        else:
            # Retrieve existing configuration
            reduction_config = get_object_or_404(ReductionConfiguration, pk=self.config_id, owner=self.request.user)
            initial_config = ConfigurationForm.data_from_db(self.request.user, reduction_config)
            
            logger.debug("initial_config: %s" % initial_config)
            ScanFormSet = formset_factory(ScanForm,extra=0)
            initial_values = []
            for item in reduction_config.reductions.all():
                props = ScanForm.data_from_db(self.request.user, item.pk)
                initial_values.append(props)
            
            
            self.scans_form = ScanFormSet(initial=initial_values, prefix="sf")
            self.config_form = ConfigurationForm(initial=initial_config)
            MaskFormSet = formset_factory(MaskForm,extra=0)
            if initial_config.get('mask'):
                self.masks_form = MaskFormSet(initial=initial_config['mask'],prefix="mf")
            else:
                self.masks_form = MaskFormSet(prefix="mf")
    
    def are_forms_valid(self):
        
        if self.scans_form.is_valid() and self.config_form.is_valid() and self.masks_form.is_valid():
            return True
        else:
            messages.add_message(self.request, messages.ERROR, 'The form is not valid. Please see messages next to the fields above.')
            if self.config_form.errors:
                logger.error("config_form: %s" % self.config_form.errors)
            if self.scans_form.errors:
                logger.error("scans_form: %s" % self.scans_form.errors)
            if self.masks_form.errors:
                logger.error("masks_form: %s" % self.masks_form.errors)
            return False
            
    def save_forms(self):
        """
        return config_id
        """
        logger.debug("Scans Form:\n%s"%self.scans_form.cleaned_data)
        logger.debug("Masks Form:\n%s"%self.masks_form.cleaned_data)
            
        config_id = self.config_form.to_db(self.request.user, self.config_id,
                                           properties = {'mask' : self.masks_form.cleaned_data})
        
        for form in self.scans_form:
            form.to_db(self.request.user, None, config_id )
            
        messages.add_message(self.request, messages.SUCCESS,
                             "Configuration %d and reduction parameters were sucessfully updated."%(config_id))
        return config_id
    
    def get_forms(self):
        return {'scans_form': self.scans_form,
                'config_form': self.config_form,
                'masks_form': self.masks_form,}
    
    
    def get_mantid_script(self, reduction_id, transaction_directory):
        """
        @param reductions: all the reductions for this configuration
        @param transaction: Transaction for this job submission 
        """

        data = ScanForm.data_from_db(self.request.user, reduction_id)
        code = ScanForm.as_mantid_script(data, transaction_directory)
        
        return code
    
    





















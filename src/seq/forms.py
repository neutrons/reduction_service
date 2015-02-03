"""
    Forms for SEQ reduction
    
    TODO: Copied from EQSANS! Need to be changed
    
    @author: R. Leal, Oak Ridge National Laboratory
    @author: M. Doucet, Oak Ridge National Laboratory
    @copyright: 2015 Oak Ridge National Laboratory
"""
from django import forms
from django.shortcuts import get_object_or_404
from reduction.models import ReductionProcess, ReductionConfiguration
from reduction.models import Instrument, Experiment
import time
import sys
import json
import logging
import copy
logger = logging.getLogger('seq.forms')


def _process_experiment(reduction_obj, expt_string):
    """
        Process the experiment string of a form and find/create
        the appropriate Experiment object
        @param reduction_obj: ReductionProcess or ReductionConfiguration object
        @param expt_string: string taken from the reduction form
    """
    # Find experiment
    uncategorized_expt = Experiment.objects.get_uncategorized('seq')
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


class ReductionConfigurationForm(forms.Form):
    """
        Configuration form for EQSANS reduction
    """
    # General information
    reduction_name = forms.CharField(required=False, initial='Configuration')
    experiment = forms.CharField(required=True, initial='uncategorized')
    

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
        eqsans = Instrument.objects.get(name='eqsans')
        # Find or create a reduction process entry and update it
        if config_id is not None:
            reduction_config = get_object_or_404(ReductionConfiguration, pk=config_id, owner=user)
            reduction_config.name = self.cleaned_data['reduction_name']
        else:
            reduction_config = ReductionConfiguration(owner=user,
                                                      instrument=eqsans,
                                                      name=self.cleaned_data['reduction_name'])
            reduction_config.save()
        
        # Find experiment
        _process_experiment(reduction_config, self.cleaned_data['experiment'])
                
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
    """
    # Reduction name
    reduction_name = forms.CharField(required=False)
    reduction_id = forms.IntegerField(required=False, widget=forms.HiddenInput)
    expt_id = forms.IntegerField(required=False, widget=forms.HiddenInput)
    experiment = forms.CharField(required=False, initial='uncategorized')
    nickname = forms.CharField(required=False, initial='')
    
    # General options
    
    
    # Data
    data_file = forms.CharField(required=True)
    
    
    # Background
    
    
    @classmethod
    def as_xml(cls, data):
        """
            Create XML from the current data.
            @param data: dictionary of reduction properties
        """
        xml  = "<Reduction>\n"
        xml += "<instrument_name>SEQ</instrument_name>\n"
        xml += "<timestamp>%s</timestamp>\n" % time.ctime()
        xml += "<Instrument>\n"
        xml += "  <name>SEQ</name>\n"

        xml += "  <UseDataDirectory>False</UseDataDirectory>\n"
        xml += "  <OutputDirectory></OutputDirectory>\n" # TODO
        xml += "</Instrument>\n"

        xml += "</Reduction>"

        return xml

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
            eqsans = Instrument.objects.get(name='eqsans')
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
        _process_experiment(reduction_proc, self.cleaned_data['experiment'])
                
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
        script =  "# EQSANS reduction script\n"
        script += "import mantid\n"
        script += "from mantid.simpleapi import *\n"
        script += "from reduction_workflow.instruments.sans.sns_command_interface import *\n"
        script += "config = ConfigService.Instance()\n"
        script += "config['instrumentName']='EQSANS'\n"

        if 'mask_file' in data and len(data['mask_file'])>0:
            script += "mask_ws = Load(Filename=\"%s\")\n" % data['mask_file']
            script += "ws, masked_detectors = ExtractMask(InputWorkspace=mask_ws, OutputWorkspace=\"__edited_mask\")\n"
            script += "detector_ids = [int(i) for i in masked_detectors]\n"

        script += "EQSANS()\n"
        script += "SolidAngle(detector_tubes=True)\n"
        script += "TotalChargeNormalization()\n"
        if data['absolute_scale_factor'] is not None:
            script += "SetAbsoluteScale(%s)\n" % data['absolute_scale_factor']

        script += "AzimuthalAverage(n_bins=100, n_subpix=1, log_binning=False)\n" # TODO
        script += "IQxQy(nbins=100)\n" # TODO
        script += "OutputPath(\"%s\")\n" % output_path
        
        script += "UseConfigTOFTailsCutoff(True)\n"
        script += "UseConfigMask(True)\n"
        script += "Resolution(sample_aperture_diameter=%s)\n" % data['sample_aperture_diameter']
        script += "PerformFlightPathCorrection(True)\n"
        
        if 'mask_file' in data and len(data['mask_file'])>0:
            script += "MaskDetectors(detector_ids)\n"
        if data['dark_current_run'] and len(data['dark_current_run'])>0:
            script += "DarkCurrentFile='%s',\n" % data['dark_current_run']
        
        if data['fit_direct_beam']:
            script += "DirectBeamCenter(\"%s\")\n" % data['direct_beam_run']
        else:
            script += "SetBeamCenter(%s, %s)\n" % (data['beam_center_x'],
                                                   data['beam_center_y'])
            
        if data['perform_sensitivity']:
            script += "SensitivityCorrection(\"%s\", min_sensitivity=%s, max_sensitivity=%s, use_sample_dc=True)\n" % \
                        (data['sensitivity_file'], data['sensitivity_min'], data['sensitivity_max'])
        else:
            script += "NoSensitivityCorrection()\n"
            
        beam_radius = data['beam_radius']
        if beam_radius is None:
            beam_radius=cls.base_fields['beam_radius'].initial
        script += "DirectBeamTransmission(\"%s\", \"%s\", beam_radius=%s)\n" % (data['transmission_sample'],
                                                                                data['transmission_empty'],
                                                                                beam_radius)
        
        script += "ThetaDependentTransmission(%s)\n" % data['theta_dependent_correction']
        if data['nickname'] is not None and len(data['nickname'])>0:
            script += "AppendDataFile([\"%s\"], \"%s\")\n" % (data['data_file'], data['nickname'])
        else:
            script += "AppendDataFile([\"%s\"])\n" % data['data_file']
        script += "CombineTransmissionFits(%s)\n" % data['fit_frames_together']
        
        if data['subtract_background']:
            script += "Background(\"%s\")\n" % data['background_file']
            script += "BckThetaDependentTransmission(%s)\n" % data['theta_dependent_correction']
            script += "BckCombineTransmissionFits(%s)\n" % data['fit_frames_together']
            script += "BckDirectBeamTransmission(\"%s\", \"%s\", beam_radius=%g)\n" % (data['background_transmission_sample'],
                                                                                       data['background_transmission_empty'],
                                                                                       beam_radius)
        
        script += "SaveIq(process='None')\n"
        script += "Reduce()"

        return script

    def is_reduction_valid(self):
        """
            Check whether the form data would produce a valid reduction script
        """
        return True
    



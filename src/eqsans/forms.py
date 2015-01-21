"""
    Forms for EQSANS reduction
    
    @author: M. Doucet, Oak Ridge National Laboratory
    @copyright: 2014 Oak Ridge National Laboratory
"""
from django import forms
from django.shortcuts import get_object_or_404
from models import ReductionProcess, ReductionConfiguration
from reduction.models import Instrument, Experiment
import time
import sys
import json
import logging
import copy
logger = logging.getLogger('eqsans.forms')

def _process_experiment(reduction_obj, expt_string):
    """
        Process the experiment string of a form and find/create
        the appropriate Experiment object
        @param reduction_obj: ReductionProcess or ReductionConfiguration object
        @param expt_string: string taken from the reduction form
    """
    # Find experiment
    uncategorized_expt = Experiment.objects.get_uncategorized('eqsans')
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
        xml  = "<Reduction>\n"
        xml += "<instrument_name>EQSANS</instrument_name>\n"
        xml += "<timestamp>%s</timestamp>\n" % time.ctime()
        xml += "<Instrument>\n"
        xml += "  <name>EQSANS</name>\n"
        xml += "  <solid_angle_corr>True</solid_angle_corr>\n"
        dark_corr = data['dark_current_run'] and str(len(data['dark_current_run'])>0)
        xml += "  <dark_current_corr>%s</dark_current_corr>\n" % dark_corr
        xml += "  <dark_current_data>%s</dark_current_data>\n" % data['dark_current_run']

        xml += "  <n_q_bins>100</n_q_bins>\n" # TODO
        xml += "  <log_binning>False</log_binning>\n"  #TODO

        xml += "  <normalization>2</normalization>\n" # 2 is monitor normalization
        xml += "  <UseDataDirectory>False</UseDataDirectory>\n"
        xml += "  <OutputDirectory></OutputDirectory>\n" # TODO
        xml += "</Instrument>\n"
        
        xml += "<AbsScale>\n"
        xml += "  <scaling_factor>%s</scaling_factor>\n" % data['absolute_scale_factor']
        xml += "  <calculate_scale>False</calculate_scale>\n"
        xml += "</AbsScale>\n"

        # TOF cutoff and correction
        xml += "<TOFcorr>\n"
        xml += "  <use_config_cutoff>True</use_config_cutoff>\n"
        xml += "  <perform_flight_path_corr>True</perform_flight_path_corr>\n"
        xml += "</TOFcorr>\n"
        
        # Mask
        if 'mask_file' in data and len(data['mask_file'])>0:
            xml += "<UseConfigMask>True</UseConfigMask>\n"
            xml += "<Mask>\n"
            xml += "  <DetectorIDs></DetectorIDs>\n"
            xml += "  <mask_file>%s</mask_file>\n" % data['mask_file']
            xml += "  <use_mask_file>True</use_mask_file>\n"
            xml += "</Mask>\n"
        
        # Resolution
        xml += "<ComputeResolution>False</ComputeResolution>\n" # TODO
        xml += "<SampleApertureDiameter>%s</SampleApertureDiameter>\n" % data['sample_aperture_diameter']

        # TOF correction
        xml += "<PerformTOFCorrection>True</PerformTOFCorrection>\n"

        xml += "<Sensitivity>\n"
        xml += "  <sensitivity_corr>%s</sensitivity_corr>\n" % data['perform_sensitivity']
        xml += "  <sensitivity_data>%s</sensitivity_data>\n" % data['sensitivity_file']
        xml += "  <use_sample_dark>True</use_sample_dark>\n"
        xml += "  <sensitivity_min>%s</sensitivity_min>\n" % data['sensitivity_min']
        xml += "  <sensitivity_max>%s</sensitivity_max>\n" % data['sensitivity_max']
        xml += "  <use_sample_beam_center>True</use_sample_beam_center>\n"
        xml += "</Sensitivity>\n"

        # Beam center
        beam_radius = data['beam_radius']
        if beam_radius is None:
            beam_radius=cls.base_fields['beam_radius'].initial
        xml += "<BeamFinder>\n"
        if not data['fit_direct_beam']:
            xml += "  <position>\n"
            xml += "    <x>%s</x>\n" % data['beam_center_x']
            xml += "    <y>%s</y>\n" % data['beam_center_y']
            xml += "  </position>\n"
        xml += "  <use_finder>%s</use_finder>\n" % data['fit_direct_beam']
        xml += "  <beam_file>%s</beam_file>\n" % data['direct_beam_run']
        xml += "  <use_direct_beam>True</use_direct_beam>\n"
        xml += "  <beam_radius>%s</beam_radius>\n" % beam_radius
        xml += "</BeamFinder>\n"
        
        # Sample transmission
        xml += "<Transmission>\n"
        xml += "  <calculate_trans>True</calculate_trans>\n"
        xml += "  <theta_dependent>%s</theta_dependent>\n" % data['theta_dependent_correction']
        xml += "  <DirectBeam>\n"
        xml += "    <sample_file>%s</sample_file>\n" % data['transmission_sample']
        xml += "    <direct_beam>%s</direct_beam>\n" % data['transmission_empty']
        xml += "    <beam_radius>%g</beam_radius>\n" % beam_radius
        xml += "  </DirectBeam>\n"
        xml += "  <combine_transmission_frames>%s</combine_transmission_frames>\n" % data['fit_frames_together']
        xml += "</Transmission>\n"
        xml += "<SampleData>\n"
        xml += "  <separate_jobs>False</separate_jobs>\n"
        xml += "  <sample_thickness>%g</sample_thickness>\n" % data['sample_thickness']
        xml += "  <data_file>%s</data_file>\n" % data['data_file']
        xml += "</SampleData>\n"
        
        # Background
        xml += "<Background>\n"
        xml += "  <background_corr>%s</background_corr>\n" % data['subtract_background']
        xml += "  <background_file>%s</background_file>\n" % data['background_file']
        xml += "  <bck_trans_enabled>True</bck_trans_enabled>\n"
        xml += "  <calculate_trans>True</calculate_trans>\n"
        xml += "  <theta_dependent>%s</theta_dependent>\n" % data['theta_dependent_correction']
        xml += "  <DirectBeam>\n"
        xml += "    <sample_file>%s</sample_file>\n" % data['background_transmission_sample']
        xml += "    <direct_beam>%s</direct_beam>\n" % data['background_transmission_empty']
        xml += "    <beam_radius>%s</beam_radius>\n" % beam_radius
        xml += "  </DirectBeam>\n"
        xml += "  <combine_transmission_frames>%s</combine_transmission_frames>\n" % data['fit_frames_together']
        xml += "</Background>\n"
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
    
class ReductionStart(forms.Form):
    """
        Simple form to select run to reduce
    """
    run_number = forms.IntegerField(required=False)


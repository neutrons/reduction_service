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
from reduction.models import Instrument
from reduction.forms import process_experiment
import time
import sys
import json
import logging
import copy
logger = logging.getLogger('seq.forms')



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
    vanadium_run = forms.CharField(required=False, initial='')
    processed_vanadium_run = forms.CharField(required=False, initial='')
    
    grouping_file = forms.ChoiceField([(11,"1 x 1"), (21,"2 x 1"), (22,"2 x 2"), (41,"4 x 1"), (42,"4 x 2")])
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


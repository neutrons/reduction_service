from django import forms
from django.shortcuts import get_object_or_404
from models import ReductionProcess, BoolReductionProperty, FloatReductionProperty, CharReductionProperty

class ReductionOptions(forms.Form):
    """
        Simple form to select a data file on the user's machine
    """
    # Reduction name
    reduction_name = forms.CharField(required=False)
    # General options
    absolute_scale_factor = forms.FloatField(required=False, initial=1.0)
    dark_current_run = forms.CharField(required=False)
    sample_aperture_diameter = forms.FloatField(required=False)
    
    # Beam center
    beam_center_x = forms.FloatField(required=False)
    beam_center_y = forms.FloatField(required=False)
    fit_direct_beam = forms.BooleanField(required=False, initial=True)
    direct_beam_run = forms.CharField(required=False)
    
    # Sensitivity
    perform_sensitivity = forms.BooleanField(required=False, initial=True)
    sensitivity_file = forms.CharField(required=False)
    sensitivity_min = forms.FloatField(required=False)
    sensitivity_max = forms.FloatField(required=False)
    
    # Data
    data_file = forms.CharField(required=False)
    sample_thickness = forms.FloatField(required=False, initial=1.0)
    transmission_sample = forms.CharField(required=False)
    transmission_empty = forms.CharField(required=False)
    beam_radius = forms.FloatField(required=False, initial=3.0)
    fit_frames_together = forms.BooleanField(required=False, initial=False)
    theta_dependent_correction = forms.BooleanField(required=False, initial=True)
    
    # Background
    subtract_background = forms.BooleanField(required=False, initial=False)
    background_file = forms.CharField(required=False)
    background_transmission_sample = forms.CharField(required=False)
    background_transmission_empty = forms.CharField(required=False)
    
    @classmethod
    def as_xml(cls, data):
        """
            Create XML from the current data.
        """
        xml  = "<Instrument>\n"
        xml += "  <name>EQSANS</name>\n"
        xml += "  <solid_angle_corr>True</solid_angle_corr>\n"
        xml += "  <dark_current_corr>%s</dark_current_corr>\n" % str(len(data['dark_current_run'])>0)
        xml += "  <dark_current_data>%s</dark_current_data>\n" % data['dark_current_run']

        xml += "  <n_q_bins>100</n_q_bins>\n" # TODO
        xml += "  <log_binning>False</log_binning>\n"  #TODO

        xml += "  <normalization>2</normalization>\n" # 2 is monitor normalization
        xml += "  <UseDataDirectory>False</UseDataDirectory>\n"
        xml += "  <OutputDirectory>'/tmp'</OutputDirectory>\n" # TODO
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
        xml += "<UseConfigMask>True</UseConfigMask>\n"
        
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

        xml += "<BeamFinder>\n"
        xml += "  <position>\n"
        xml += "    <x>%s</x>\n" % data['beam_center_x']
        xml += "    <y>%s</y>\n" % data['beam_center_y']
        xml += "  </position>\n"
        xml += "  <use_finder>%s</use_finder>\n" % data['fit_direct_beam']
        xml += "  <beam_file>%s</beam_file>\n" % data['direct_beam_run']
        xml += "  <use_direct_beam>True</use_direct_beam>\n"
        xml += "  <beam_radius>%s</beam_radius>\n" % data['beam_radius']
        xml += "</BeamFinder>\n"
        return xml

    def to_db(self, user, reduction_id=None):
        """
        """
        if not self.is_valid():
            raise RuntimeError, "Reduction options form invalid"
        
        # Find or create a reduction process entry and update it
        if reduction_id is not None:
            reduction_proc = get_object_or_404(ReductionProcess, pk=reduction_id, owner=user)
        else:
            # Make sure we don't try to store a string that's longer than allowed
            reduction_proc = ReductionProcess(owner=user)
        reduction_proc.name=self.cleaned_data['reduction_name'][:128]
        reduction_proc.save()
        
        # Clean up the old values
        FloatReductionProperty.objects.filter(reduction=reduction_proc).delete()
        BoolReductionProperty.objects.filter(reduction=reduction_proc).delete()
        CharReductionProperty.objects.filter(reduction=reduction_proc).delete()

        # Set the parameters associated with the reduction process entry
        for name, field in self.fields.items():
            if name == 'reduction_name': continue
            property_cls = None
            if isinstance(field, forms.FloatField):
                property_cls = FloatReductionProperty
            elif isinstance(field, forms.CharField):
                property_cls = CharReductionProperty
            elif isinstance(field, forms.BooleanField):
                property_cls = BoolReductionProperty
            if property_cls is not None and self.cleaned_data[name] is not None:
                property_cls(reduction=reduction_proc,
                             name=name,
                             value=self.cleaned_data[name]).save()
        return reduction_proc.pk
    
    @classmethod
    def data_from_db(cls, user, reduction_id):
        reduction_proc = get_object_or_404(ReductionProcess, pk=reduction_id, owner=user)
        data = reduction_proc.get_data_dict()
        # Ensure all the fields are there
        for f in cls.base_fields:
            if not f in data:
                data[f]=''
        return data
    
    @classmethod
    def as_mantid_script(self, data):
        """
            Return the Mantid script associated with the current parameters
        """
        script =  "# EQSANS reduction script\n"
        script += "import mantid\n"
        script += "from mantid.simpleapi import *\n"
        script += "from reduction_workflow.instruments.sans.sns_command_interface import *\n"
        script += "config = ConfigService.Instance()\n"
        script += "config['instrumentName']='EQSANS'\n"

        script += "EQSANS()\n"
        script += "SolidAngle(detector_tubes=True)\n"
        script += "TotalChargeNormalization()\n"
        script += "SetAbsoluteScale(%g)\n" % data['absolute_scale_factor']

        script += "AzimuthalAverage(n_bins=100, n_subpix=1, log_binning=False)\n" # TODO
        script += "IQxQy(nbins=100)\n" # TODO
        script += "OutputPath('\tmp')\n" # TODO
        
        script += "UseConfigTOFTailsCutoff(True)\n"
        script += "UseConfigMask(True)\n"
        #script += "Resolution(sample_aperture_diameter=10)\n" # TODO
        script += "PerformFlightPathCorrection(True)\n"
        
        if len(data['dark_current_run'])>0:
            script += "\tDarkCurrentFile='%s',\n" % data['dark_current_run']
        
        if data['fit_direct_beam']:
            script += "DirectBeamCenter(\"%s\")\n" % data['direct_beam_run']
        else:
            script += "SetBeamCenter(%f, %f)\n" % (data['beam_center_x'],
                                                   data['beam_center_y'])
            
        if data['perform_sensitivity']:
            script += "SensitivityCorrection(\"%s\", min_sensitivity=%s, max_sensitivity=%s, use_sample_dc=True)\n" % \
                        (data['sensitivity_file'], data['sensitivity_min'], data['sensitivity_max'])
        else:
            script += "NoSensitivityCorrection()\n"
            
        script += "DirectBeamTransmission(, , beam_radius=3)\n"
        
        script += "ThetaDependentTransmission(True)\n"
        script += "AppendDataFile([\"%s\"])\n" % data['data_file']
        script += "CombineTransmissionFits(False)\n"
        script += "SaveIq(process='None')\n"
        script += "Reduce()"

        return script

    def is_reduction_valid(self):
        """
            Check whether the form data would produce a valid reduction script
        """
        return True
        
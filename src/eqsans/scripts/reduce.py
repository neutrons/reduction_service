# EQSANS reduction script
import mantid
from mantid.simpleapi import *
from reduction_workflow.instruments.sans.sns_command_interface import *

config = ConfigService.Instance()
config['instrumentName']='EQSANS'

{% if mask_file %}
mask_ws = Load(Filename='{{ mask_file }}')
ws, masked_detectors = ExtractMask(InputWorkspace=mask_ws, OutputWorkspace='__edited_mask')
detector_ids = [int(i) for i in masked_detectors]
{% endif %}

EQSANS()
SolidAngle(detector_tubes=True)
TotalChargeNormalization()

{% if absolute_scale_factor %}
SetAbsoluteScale({{ absolute_scale_factor }})
{% endif %}

AzimuthalAverage(n_bins=100, n_subpix=1, log_binning=False) # TODO
IQxQy(nbins=100) # TODO
OutputPath('{{ output_path }}')  
        
UseConfigTOFTailsCutoff(True)
UseConfigMask(True)
Resolution(sample_aperture_diameter={{ sample_aperture_diameter }})
PerformFlightPathCorrection(True)

{% if mask_file %}     
MaskDetectors(detector_ids)
{% endif %}


{% if dark_current_run %}
DarkCurrentFile='{{dark_current_run}}'
{% endif %}

{% if fit_direct_beam %}
DirectBeamCenter('{{fit_direct_beam}}') 
{% else %}
SetBeamCenter({{beam_center_x}},{{beam_center_y}})
{% endif %}

{% if perform_sensitivity %}            
SensitivityCorrection({{sensitivity_file}},
                      min_sensitivity={{sensitivity_min}},
                      max_sensitivity={{sensitivity_max}},
                      use_sample_dc=True)
{% else %}
NoSensitivityCorrection()
{% endif %}

{% if beam_radius %}
beam_radius_val = {{beam_radius}}
{% else %}
beam_radius_val = {{beam_radius_default}}
{% endif %}

DirectBeamTransmission({{transmission_sample}}, {{transmission_empty}}, beam_radius=beam_radius_val)
        
ThetaDependentTransmission({{theta_dependent_correction}})

{% if nickname %}
AppendDataFile(['{{data_file}}'], '{{nickname}}')
{% else %}
AppendDataFile(['{{data_file}}'])
{% endif %}    

CombineTransmissionFits({{fit_frames_together}})

{% if subtract_background %}
Background('{{background_file}}')
BckThetaDependentTransmission({{theta_dependent_correction}})
BckCombineTransmissionFits({{fit_frames_together}})
BckDirectBeamTransmission('{{background_transmission_sample}}', '{{background_transmission_empty}}', beam_radius=beam_radius_val)
{% endif %}    
        
SaveIq(process='None')
Reduce()
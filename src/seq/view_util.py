"""
    Utilities for SEQ views

    @author: 
    @copyright: 2014 Oak Ridge National Laboratory
"""
import logging
import remote.view_util
from plotting.models import Plot1D
import sys
from math import sqrt

logger = logging.getLogger('seq')


def process_DeltaE_data(file_content, return_raw=False):
    """
        Process the content of an enrgy transfer file and return a string representation
        of the data that we can ship to the client for plotting.
        @param file_content: content of the data file
        @param return_raw: if True, return the array instead of a string
    """
    data = []
    for l in file_content.split('\n'):
        toks = l.split()
        if len(toks)>=2:
            try:
                deltaE = float(toks[0])
                i = float(toks[1])
                data.append([deltaE, i, sqrt(i)])
            except:
                logger.debug("Problems parsing: " + l)
                pass
    if return_raw:
        return data
    return str(data)

def process_DeltaE_output(request, remote_job, trans_id, filename):
    """
        @param request: request object
        @param remote_job: RemoteJob object
        @param filename: data file containing plot data
    """
    template_values = {}
    # Do we read this data already?
    plot_object = remote_job.get_first_plot(filename=filename, owner=request.user)
    if plot_object is not None and plot_object.first_data_layout() is not None:
        data_str = plot_object.first_data_layout().dataset.data
    else:
        # If we don't have data stored, read it from file
        logger.warning("Retrieving %s from compute resource" % filename)
        file_content = remote.view_util.download_file(request, trans_id, filename)
        if file_content is not None:
            try:
                data_str = process_DeltaE_data(file_content)
                plot_object = Plot1D.objects.create_plot(request.user,
                                                         data=data_str,
                                                         filename=filename,
                                                         x_label = "Delta E",
                                                         is_y_log = True)
                remote_job.plots.add(plot_object)
            except:
                logger.error("Could not process DeltaE(i) file: %s" % sys.exc_value)
    
    template_values['plot_1d'] = data_str
    template_values['plot_object'] = plot_object
    template_values['plot_1d_id'] = plot_object.id if plot_object is not None else None
    return template_values

def set_into_template_values_job_files(template_values, request, remote_job):
    
    for f in template_values['job_files']:
        if f.endswith('_DeltaE.txt'):
            plot_info = process_DeltaE_output(request, remote_job, 
                                                    template_values['trans_id'], f)
            template_values.update(plot_info)
        
    return template_values

def set_into_template_values_plots(template_values, request, first_job):
    plot_data = []
    
    ### TODO!! See eqsans
    logger.warning("set_into_template_values_plots not implemeented yet!")
    
    template_values['plot_data'] = plot_data
    return template_values

        
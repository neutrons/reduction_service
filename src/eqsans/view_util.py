"""
    Utilities for EQSANS views

    @author: M. Doucet, Oak Ridge National Laboratory
    @copyright: 2014 Oak Ridge National Laboratory
"""
from plotting.models import Plot1D, Plot2D
import remote.view_util
import h5py
import tempfile
import numpy
import sys
import logging
logger = logging.getLogger('eqsans.view_util')

def process_iq_output(request, remote_job, trans_id, filename):
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
                data_str = process_Iq_data(file_content)
                plot_object = Plot1D.objects.create_plot(request.user,
                                                         data=data_str,
                                                         filename=filename)
                remote_job.plots.add(plot_object)
            except:
                logger.error("Could not process I(q) file: %s" % sys.exc_value)
    
    template_values['plot_1d'] = data_str
    template_values['plot_object'] = plot_object
    template_values['plot_1d_id'] = plot_object.id if plot_object is not None else None
    return template_values

def process_iqxy_output(request, remote_job, trans_id, filename):
    """
        @param request: request object
        @param remote_job: RemoteJob object
        @param filename: data file containing plot data
    """
    template_values = {}
    
    # Do we read this data already?
    plot_object2d = remote_job.get_plot_2d(filename=filename, owner=request.user)
    if plot_object2d is None:
        # If we don't have data stored, read it from file
        logger.warning("Retrieving %s from compute resource" % filename)
        file_content = remote.view_util.download_file(request, trans_id, filename)
        if file_content is not None:
            try:
                data_str_2d, x_str, y_str, z_min, z_max = process_Iqxy_data(file_content)
                plot_object2d = Plot2D.objects.create_plot(user=request.user, data=data_str_2d,
                                                           x_axis=x_str, y_axis=y_str,
                                                           z_min=z_min, z_max=z_max, 
                                                           filename=filename)
                remote_job.plots2d.add(plot_object2d)
            except:
                logger.error("Could not process nexus file: %s" % sys.exc_value)

    template_values['plot_2d'] = plot_object2d
    return template_values

def process_Iq_data(file_content, return_raw=False):
    """
        Process the content of an I(q) file and return a string representation
        of the data that we can ship to the client for plotting.
        @param file_content: content of the data file
        @param return_raw: if True, return the array instead of a string
    """
    data = []
    for l in file_content.split('\n'):
        toks = l.split()
        if len(toks)>=3:
            try:
                q = float(toks[0])
                iq = float(toks[1])
                diq = float(toks[2])
                data.append([q, iq, diq])
            except:
                pass
    if return_raw:
        return data
    return str(data)

def process_Iqxy_data(file_content):
    """
        Process the content of an I(qx,qy) file and return a string representation
        of the data that we can ship to the client for plotting.
        @param file_content: content of the data file
    """
    fd = tempfile.NamedTemporaryFile()
    fd.write(file_content)
    fd.seek(0)
    
    numpy.set_printoptions(threshold='nan', nanstr='0', infstr='0')
    fd = h5py.File(fd.name, 'r')
    g = fd['mantid_workspace_1']
    y = g['workspace']['axis1']
    x = g['workspace']['axis2']
    values = g['workspace']['values']
    z_max = numpy.amax(values)
    numpy.set_string_function( lambda x: '['+','.join(map(lambda y:'['+','.join(map(lambda z: "%.4g" % z,y))+']',x))+']' )
    data_str_2d = values[:].__repr__()
    numpy.set_string_function( lambda x: '['+','.join(map(lambda z: "%.4g" % z,x))+']' )

    y_str = y[:].__repr__()
    x_str = x[:].__repr__()
    return data_str_2d, x_str, y_str, 0.0, z_max
        
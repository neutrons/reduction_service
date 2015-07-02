"""
    Utilities for SEQ views

    @author: 
    @copyright: 2014 Oak Ridge National Laboratory
"""
import logging
import remote.view_util
from plotting.models import Plot1D, Plot2D
import sys
import numpy as np
import pprint

logger = logging.getLogger('seq.util')

def process_sqw_1d_output(request, remote_job, trans_id, filename):
    """
        @param request: request object
        @param remote_job: RemoteJob object
        @param filename: data file containing plot data
    """
    plot_parameters = {}
    # Have we read these data before?
    plot_object = None#remote_job.get_first_plot(filename=filename, owner=request.user)
    if plot_object is not None and plot_object.first_data_layout() is not None:
        data_str = plot_object.first_data_layout().dataset.data
    else:
        # If we don't have data stored, read it from file
        logger.warning("Retrieving %s from compute resource" % filename)
        file_content = remote.view_util.download_file(request, trans_id, filename)
        if file_content is not None:
            try:
                data_str = process_sqw_1d_data(file_content)
                if data_str is not None and len(data_str) > 3:
                    plot_object = Plot1D.objects.create_plot(request.user,
                                                             data=data_str,
                                                             filename=filename,
                                                             x_label = "Delta E",
                                                             is_y_log = True)
                    remote_job.plots.add(plot_object)
            except:
                logger.error("Could not process DeltaE(i) file: %s" % sys.exc_value)
    
    plot_parameters['plot_1d_name'] = filename
    plot_parameters['plot_1d'] = data_str
    plot_parameters['plot_object'] = plot_object
    plot_parameters['plot_1d_id'] = plot_object.id if plot_object is not None else None
    return plot_parameters


def process_sqw_2d_output(request, remote_job, trans_id, filename):
    """
        @param request: request object
        @param remote_job: RemoteJob object
        @param filename: data file containing plot data
    """
    plot_parameters = {}
    
    # Have we read these data before?
    plot_object2d = None #remote_job.get_plot_2d(filename=filename, owner=request.user)
    if plot_object2d is None:
        # If we don't have data stored, read it from file
        logger.warning("Retrieving %s from compute resource" % filename)
        file_content = remote.view_util.download_file(request, trans_id, filename)
        if file_content is not None:
            try:
                data_str_2d, x_str, y_str, z_min, z_max = process_sqw_2d_data(file_content)
                plot_object2d = Plot2D.objects.create_plot(user=request.user,
                                                           data=data_str_2d,
                                                           x_axis=x_str,
                                                           y_axis=y_str,
                                                           z_min=z_min,
                                                           z_max=z_max, 
                                                           filename=filename,
                                                           x_label='|Q| [1/&Aring;]',
                                                           y_label='E [meV]')
                remote_job.plots2d.add(plot_object2d)
            except Exception, e:
                logger.error("Could not process 2D file (%s): %s" % (filename,sys.exc_value))
                logger.exception(e)
                
    plot_parameters['plot_2d_name'] = filename                
    plot_parameters['plot_2d'] = plot_object2d
    return plot_parameters

###

def process_sqw_1d_data(file_content, return_raw=False):
    """
        Process the content of an enrgy transfer file and return a string representation
        of the data that we can ship to the client for plotting.
        @param file_content: content of the data file
        @param return_raw: if True, return the array instead of a string
    """
    data = []
    for l in file_content.split('\n'):
        if not l.startswith("#"):
            toks = l.split()
            if len(toks)>=2:
                try:
                    deltaE = float(toks[0])
                    s = float(toks[1])
                    e = float(toks[2])
                    data.append([deltaE, s, e])
                except Exception, e:
                    logger.exception(e)
                    logger.debug("Problems parsing: " + l)
                    pass
    if return_raw:
        return data
    return str(data)



def process_sqw_2d_data(file_content):
    """
        Process the content of an enrgy transfer file and return a string representation
        of the data that we can ship to the client for plotting.
        @param file_content: content of the data file
        @return: data_str_2d, x_str, y_str, z_min, z_max
    """
    
    lines = file_content.split('\n')
        
    lines_as_list = [i.split() for i in lines[1:] if len(i) > 0 ]
    
    data = np.array( lines_as_list ,dtype=np.float32)
    x = data[:,0]
    y = data[:,1]
    z = data[:,2]
    
    x = np.unique(x)
    y = np.unique(y)
    
    x_str = str(list(x))
    y_str = str(list(y))
    
    # np.amax returns NaN
    z_max = np.nanmax(z)
    
    z_reshaped = z.reshape((len(x), len(y)))
    z_as_list = list(list(i) for i in z_reshaped)
    data_str_2d = str(z_as_list)
    
    return data_str_2d, x_str, y_str, 0.0, z_max


###


def set_into_template_values_job_files(template_values, request, remote_job):
    '''
    If the files output by mantid in fermi are plots, builds the plots
    Called by reduction_query
    '''
    
    template_values['plots']=[]
    
    this_reduction_prefix = template_values['parameters']['friendly_name']
    
    for f in template_values['job_files']:
        if f.endswith('_sqw_1d.dat') and f.startswith(this_reduction_prefix):
            logger.debug("Adding plot %s."%f)
            plot_info = process_sqw_1d_output(request, remote_job, 
                                                    template_values['trans_id'], f)
            template_values['plots'].append(plot_info)
        elif f.endswith('_sqw_2d.dat') and f.startswith(this_reduction_prefix):
            logger.debug("Adding plot %s."%f)
            plot_info = process_sqw_2d_output(request, remote_job, 
                                                      template_values['trans_id'], f)
            template_values['plots'].append(plot_info)
    return template_values
    

def set_into_template_values_plots(template_values, request, first_job):
    '''
    Only plot 1D (called only by confuguration query (?))
    '''
    plot_data = []
    if first_job is not None and template_values['job_files'] is not None:
        for f in template_values['job_files']:
            if f.endswith('_sqw_1d.dat'):
                plot_info = process_sqw_1d_output(request,
                                              first_job,
                                              template_values['trans_id'],
                                              f)
                plot_info['name'] = f
                plot_data.append(plot_info)
#             if f.endswith('_sqw_2d.dat'):
#                 plot_info = process_sqw_2d_output(request,
#                                                   first_job, 
#                                                   template_values['trans_id'], 
#                                                   f)                
#                 plot_info['name'] = f
#                 plot_data.append(plot_info)
    template_values['plot_data'] = plot_data
    return template_values

        
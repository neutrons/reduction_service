"""
    Test utilities for deployment where ORNL services are 
    not available
"""
from django.core.urlresolvers import reverse
from django.conf import settings

from reduction.models import ReductionProcess, RemoteJob, Instrument
from plotting.models import Plot1D, Plot2D
from remote.models import Transaction
import users.view_util
import remote.view_util
import view_util
import numpy
import h5py
import os

def get_dummy_data(request, job_id):
    """
        Create a dummy job and plot data
        @param request: request object
        @param job_id: RemoteJob pk
    """
    try:
        remote_job = RemoteJob.objects.get(remote_id=job_id)
    except:
        eqsans = Instrument.objects.get(name='eqsans')
        reduction = ReductionProcess(instrument=eqsans,
                                     name='Dummy job',
                                     owner=request.user,
                                     data_file='/tmp/dummy.nxs')
        reduction.save()
        try:
            transaction = Transaction.objects.get(trans_id=-1)
        except:
            transaction = Transaction(trans_id=-1,
                                      owner=request.user,
                                      directory='/tmp')
            transaction.save()
        remote_job = RemoteJob(reduction=reduction,
                              remote_id='-1',
                              transaction=transaction)
        remote_job.save()
        
    breadcrumbs = "<a href='%s'>home</a>" % reverse(settings.LANDING_VIEW)
    breadcrumbs += " &rsaquo; <a href='%s'>eqsans reduction</a>" % reverse('reduction.views.reduction_home',args=['eqsans'])
    breadcrumbs += " &rsaquo; <a href='%s'>jobs</a>" % reverse('eqsans.views.reduction_jobs')
    breadcrumbs += " &rsaquo; dummy job"

    template_values = {'remote_job': remote_job,
                       'parameters': remote_job.reduction.get_data_dict(),
                       'reduction_id': remote_job.reduction.id,
                       'breadcrumbs': breadcrumbs,
                       'back_url': request.path}
    template_values = remote.view_util.fill_job_dictionary(request, job_id, **template_values)
    template_values = users.view_util.fill_template_values(request, **template_values)
    template_values = remote.view_util.fill_template_values(request, **template_values)
    
    # Go through the files and find data to plot
    f = os.path.join(os.path.split(__file__)[0],'..','plotting','data','4065_Iq.txt')
                
    # Do we read this data already?
    plot_object = remote_job.get_first_plot(filename='4065_Iq.txt', owner=request.user)
    if plot_object is not None and plot_object.first_data_layout() is not None:
        data_str = plot_object.first_data_layout().dataset.data
    else:
        # If we don't have data stored, read it from file
        file_content = open(f,'r').read()
        data_str = view_util.process_Iq_data(file_content)
        plot_object = Plot1D.objects.create_plot(request.user,
                                                 data=data_str,
                                                 filename='4065_Iq.txt')
        remote_job.plots.add(plot_object)
    
    template_values['plot_1d'] = data_str
    template_values['plot_object'] = plot_object
    template_values['plot_1d_id'] = plot_object.id if plot_object is not None else None
    
    # Now the 2D data
    f = os.path.join(os.path.split(__file__)[0],'..','plotting','data','4065_Iqxy.nxs')
    plot_object2d = remote_job.get_plot_2d(filename='4065_Iqxy.nxs', owner=request.user)
    if plot_object2d is None:
        numpy.set_printoptions(threshold='nan', nanstr='0', infstr='0')
        fd = h5py.File(f, 'r')
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
        plot_object2d = Plot2D.objects.create_plot(user=request.user, data=data_str_2d,
                                                   x_axis=x_str, y_axis=y_str,
                                                   z_min=0.0, z_max=z_max, filename='4065_Iqxy.nxs')
        remote_job.plots2d.add(plot_object2d)

    template_values['plot_2d'] = plot_object2d

    return template_values

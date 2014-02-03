from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.conf import settings
from django.http import HttpResponse
import users.view_util
import remote.view_util
import h5py
import numpy
import os
from plotting.models import Plot1D, PlotLayout

import logging
logger = logging.getLogger('plotting')

@login_required
def adjust_1d(request, plot_id):
    plot_1d = get_object_or_404(Plot1D, pk=plot_id, owner=request.user)
    data_str = plot_1d.data.all()[0].dataset.data
    
    # Get layout options
    if plot_1d.layout is None:
        layout = PlotLayout(owner=request.user)
        layout.save()
        plot_1d.layout = layout
        plot_1d.save()
    
    breadcrumbs = "<a href='%s'>home</a> &rsaquo; plotting" % reverse(settings.LANDING_VIEW)
    template_values = {'next':request.path,
                       'data': data_str,
                       'plot1d': plot_1d,
                       'breadcrumbs': breadcrumbs}
    if 'back' in request.GET:
        template_values['back_url'] = request.GET['back']
    template_values = users.view_util.fill_template_values(request, **template_values)
    template_values = remote.view_util.fill_template_values(request, **template_values)
    return render_to_response('plotting/adjust_1d.html',
                              template_values)
    
@login_required
def updated_parameters_1d(request, plot_id):
    plot_1d = get_object_or_404(Plot1D, pk=plot_id, owner=request.user)
    if 'width' in request.GET:
        plot_1d.layout.width = request.GET['width']
    if 'height' in request.GET:
        plot_1d.layout.height = request.GET['height']
    if 'log_scale' in request.GET:
        plot_1d.layout.is_y_log = request.GET['log_scale']=='true'
    if 'x_label' in request.GET:
        plot_1d.layout.x_label = request.GET['x_label']
    if 'y_label' in request.GET:
        plot_1d.layout.y_label = request.GET['y_label']
        
    data_layout = plot_1d.first_data_layout()
    if 'color' in request.GET:
        data_layout.color = request.GET['color']
    if 'marker_size' in request.GET:
        data_layout.size = request.GET['marker_size']
        
    data_layout.save()
    plot_1d.layout.save()
    
    return HttpResponse()

    
@login_required
def adjust_2d(request, plot_id=None):
    """
        
    """
    numpy.set_printoptions(threshold='nan', nanstr='0', infstr='0')
    f = h5py.File(os.path.join(os.path.split(__file__)[0],'data','4065_Iqxy.nxs'), 'r')
    g = f['mantid_workspace_1']
    y = g['workspace']['axis1']
    x = g['workspace']['axis2']
    values = g['workspace']['values']

    numpy.set_string_function( lambda x: '['+','.join(map(lambda y:'['+','.join(map(lambda z: "%.4g" % z,y))+']',x))+']' )
    data2d = values[:].__repr__()
    numpy.set_string_function( lambda x: '['+','.join(map(lambda z: "%.4g" % z,x))+']' )

    breadcrumbs = "<a href='%s'>home</a>  &rsaquo; plotting" % reverse(settings.LANDING_VIEW)

    template_values = {'data2d': data2d,
                       'max_iq': numpy.amax(values),
                       'qx': x[:].__repr__(), 'qy': y[:].__repr__(),
                       'breadcrumbs': breadcrumbs}
    template_values = users.view_util.fill_template_values(request, **template_values)
    template_values = remote.view_util.fill_template_values(request, **template_values)
    return render_to_response('plotting/adjust_2d.html',
                              template_values)


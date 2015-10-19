from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.conf import settings
from django.http import HttpResponse
import reduction_server.view_util
from .models import Plot1D, Plot2D, PlotLayout
from reduction_server.view_util import Breadcrumbs

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
    template_values = {'data': data_str,
                       'plot1d': plot_1d,
                       'breadcrumbs': breadcrumbs}
    if 'back' in request.GET:
        template_values['back_url'] = request.GET['back']
    template_values = reduction_server.view_util.fill_template_values(request, **template_values)
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
def adjust_2d(request, plot_id):
    """
        Update the layout parameters for a given 1D plot
        
        @param request: http request object
        @param plot_id: pk of the Plot1D entry
        
    """
    plot_2d = get_object_or_404(Plot2D, pk=plot_id, owner=request.user)
    breadcrumbs = Breadcrumbs()
    breadcrumbs.append("plotting")
    
    template_values = {'plot_2d': plot_2d,
                       'breadcrumbs': breadcrumbs}
    if 'back' in request.GET:
        template_values['back_url'] = request.GET['back']
        
    template_values = reduction_server.view_util.fill_template_values(request, **template_values)
    return render_to_response('plotting/adjust_2d.html',
                              template_values)

@login_required
def updated_parameters_2d(request, plot_id):
    """
        Update the layout parameters for a given 2D plot
        
        @param request: http request object
        @param plot_id: pk of the Plot2D entry
    """
    plot_2d = get_object_or_404(Plot2D, pk=plot_id, owner=request.user)
    if 'width' in request.GET:
        plot_2d.layout.width = request.GET['width']
    if 'height' in request.GET:
        plot_2d.layout.height = request.GET['height']
    if 'log_scale' in request.GET:
        plot_2d.layout.is_y_log = request.GET['log_scale']=='true'
    if 'x_label' in request.GET:
        plot_2d.layout.x_label = request.GET['x_label']
    if 'y_label' in request.GET:
        plot_2d.layout.y_label = request.GET['y_label']
    plot_2d.layout.save()
    return HttpResponse()

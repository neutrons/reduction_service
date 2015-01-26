
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.conf import settings


from reduction.models import Instrument, Experiment
import reduction_service.view_util

# Create your views here.

@login_required
def reduction_home(request, instrument_name):
    """
        Home page for the EQSANS reduction
        @param request: request object
    """
    
    instrument = get_object_or_404(Instrument, name=instrument_name)
    
    experiments = Experiment.objects.experiments_for_instrument(instrument, owner=request.user)

    breadcrumbs = "<a href='%s'>home</a> &rsaquo; %s reduction" % (reverse(settings.LANDING_VIEW), instrument_name)
    template_values = {'title': str.capitalize(str(instrument_name)) + ' Reduction',
                       'experiments':experiments,
                       'breadcrumbs': breadcrumbs}
    template_values = reduction_service.view_util.fill_template_values(request, **template_values)
    return render_to_response(instrument_name + '/reduction_home.html',
                              template_values)

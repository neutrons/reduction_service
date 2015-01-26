from django.core.urlresolvers import reverse
import users.view_util
import remote.view_util

def fill_template_values(request, **template_args):
    """
        Fill template values for the whole application
    """
    template_args = users.view_util.fill_template_values(request, **template_args)
    template_args = remote.view_util.fill_template_values(request, **template_args)
    
    # It may be the case that we are currently viewing a part of the site
    # belonging to an instrument-specific app. In this case, we'll already have
    # an instrument entry in the dictionary. We should exclude that instrument.
    
    instrument = None
    if 'instrument' in template_args:
        instrument = template_args['instrument']
    reduction_apps = []
    for instr in ['eqsans']:
        if not instrument==instr:
            reduction_apps.append({'name':instr,
                                   'url': reverse('reduction.views.reduction_home', args=[instr])})
    template_args['reduction_apps'] = reduction_apps
    return template_args
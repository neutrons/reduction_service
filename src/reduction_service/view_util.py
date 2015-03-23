from django.core.urlresolvers import reverse
import users.view_util
import remote.view_util
from django.conf import settings

class Breadcrumbs(object):
    '''
    Forms the navigation horizontal bar.
    E.g:
    home > eqsans reduction > ipts-13502
    The last one never has a link
    '''
    separator = " &rsaquo; "
    link_tempate = "<a href='%s'>%s</a>"
    
    
    def __init__(self, name="home", href=settings.LANDING_VIEW):
        self.content = []
        try:
            self.content.append( (name, reverse(href) ) )
        except:
            self.content.append( (name, href) )
        
        
    def _build_link(self, name, href):
        if href is None:
            return name
        else:
            return self.link_tempate%(href,name)
    
    def append(self, name, href=None):
        '''
        Regular tuple name and link
        '''
        self.content.append((name,href))
    
    
    def append_reduction(self,instrument):
        self.append("%s reduction"%instrument, 
                    reverse('reduction.views.reduction_home', args=[instrument]))
    
    def append_reduction_options(self,instrument, reduction_id):
        self.append("%s reduction"%instrument, 
                    reverse('reduction.views.reduction_options',
                            kwargs={'reduction_id' : reduction_id,
                                    'instrument_name': instrument}) )
    
    def append_configuration(self,instrument, configuration_id):
        self.append("configuration %s"%configuration_id, 
                    reverse('reduction.views.reduction_configuration',
                               kwargs={'config_id' : configuration_id,
                                       'instrument_name' : instrument}) )

    def append_reduction_jobs(self,instrument):
        self.append("%s jobs"%instrument, 
                    reverse('reduction.views.reduction_jobs',
                            kwargs={'instrument_name': instrument}))
                
    def append_experiment_list(self,instrument):
        self.append("%s catalog"%instrument, reverse('catalog.views.experiment_list', args=[instrument]))
        
    def __str__(self):
        ret = ""
        for idx,i in enumerate(self.content):
            ret += self._build_link(i[0],i[1])
            if idx < len(self.content)-1:
                ret += self.separator
        return ret
    
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
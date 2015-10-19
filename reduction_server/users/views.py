"""
    User management
"""
from django.shortcuts import render_to_response, redirect
from django.core.urlresolvers import reverse
from django.contrib.auth import login, logout, authenticate
from django.template import RequestContext

# Application-specific imports
from django.conf import settings
from .view_util import fill_template_values

import reduction_server.remote.view_util as remote_view_util 
from reduction_server.view_util import Breadcrumbs

def perform_login(request):
    """
        Perform user authentication
    """
    user = None  
    login_failure = None
    if request.method == 'POST':
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(username=username, password=password)
        if user is not None and not user.is_anonymous():
            login(request,user)
        else:
            login_failure = "Invalid username or password"
    
    if request.user.is_authenticated():
        # Try to authenticate with Fermi
        remote_view_util.authenticate(request)
        
        # If we came from a given page and just needed 
        # authentication, go back to that page.
        if "next" in request.GET:
            redirect_url = request.GET["next"]
            return redirect(redirect_url)
        return redirect(reverse(settings.LANDING_VIEW))
    else:
        # Breadcrumbs
        breadcrumbs = Breadcrumbs()
        breadcrumbs.append("login")
        
        template_values = {'breadcrumbs': breadcrumbs,
                           'login_failure': login_failure}
        template_values = fill_template_values(request, **template_values)
        
        return render_to_response('users/authenticate.html', template_values,
                              context_instance=RequestContext(request))

def perform_logout(request):
    """
        Logout user
    """
    logout(request)
    return redirect(reverse(settings.LANDING_VIEW))
        
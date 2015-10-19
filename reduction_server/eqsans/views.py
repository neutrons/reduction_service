"""
    EQSANS views for the SNS analysis/reduction web application.
    
    @author: M. Doucet, Oak Ridge National Laboratory
    @copyright: 2014 Oak Ridge National Laboratory
"""

from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required

@login_required
def test_result(request, job_id='-1'):
    """
        Dummy job for development when ORNL resources are not available
    """
    from test_util import get_dummy_data
    template_values = get_dummy_data(request, job_id)
    return render_to_response('eqsans/reduction_query.html',
                              template_values)
    




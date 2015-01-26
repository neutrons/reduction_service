"""
    Utilities for general reduction views

    @author: R. Leal, Oak Ridge National Laboratory
    @copyright: 2015 Oak Ridge National Laboratory
"""


from reduction.models import RemoteJob
import remote.view_util

import logging
logger = logging.getLogger('reduction.view_util')

def get_latest_job(request, reduction_process):
    """
        Return the latest completed job for this reduction
        @param request: request object
        @param reduction_process: ReductionProcess object
    """
    latest_jobs = RemoteJob.objects.filter(reduction=reduction_process)
    if len(latest_jobs)>0:
        latest_job = latest_jobs.latest('id')
        # Check whether the job completed
        job_info = remote.view_util.query_job(request, latest_job.remote_id)
        if job_info is not None and 'JobStatus' in job_info and job_info['JobStatus']=='COMPLETED':
            return latest_job
    return None


        
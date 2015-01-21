"""
    Reduction task models.
    TODO: Some of the models here are meant to be common to all instruments and are
    not specific to EQSANS. Those should be pulled out as we start building the common
    reduction framework.
    
    @author: M. Doucet, Oak Ridge National Laboratory
    @copyright: 2014 Oak Ridge National Laboratory
"""
from django.db import models
from django.contrib.auth.models import User
from remote.models import Transaction
from plotting.models import Plot1D, Plot2D
import logging
logger = logging.getLogger("eqsans")
import json
import sys
    
from reduction.models import ReductionProcess, ReductionConfiguration
    
class RemoteJob(models.Model):
    reduction = models.ForeignKey(ReductionProcess)
    remote_id = models.CharField(max_length = 30, unique=True)
    transaction = models.ForeignKey(Transaction)
    properties = models.TextField()
    plots = models.ManyToManyField(Plot1D, null=True, blank=True, related_name='_remote_job_plot+')
    plots2d = models.ManyToManyField(Plot2D, null=True, blank=True, related_name='_remote_job_plot2d+')
    
    def get_data_dict(self):
        """
            Return a dictionary of properties for this entry
        """
        data = {'reduction_name': self.reduction.name}
        try:
            data = json.loads(self.properties)
        except:
            logger.error("Could not retrieve properties: %s" % sys.exc_value)
        return data

    def get_first_plot(self, filename, owner):
        """
            Return the first plot object associated with this remote job, or None
            @param filename: filename we are looking for
            @param owner: job owner
        """
        plots = self.plots.all().filter(filename=filename, owner=owner)
        if len(plots)>0:
            # The plot has to have at least one data set
            plot1d = plots[0].first_data_layout()
            if plot1d is not None:
                return plots[0]
        return None
    
    def get_plot_2d(self, filename, owner):
        """
            Return the first 2D plot object associated with this remote job, or None
            @param filename: filename we are looking for
            @param owner: job owner
        """
        plots = self.plots2d.all().filter(filename=filename, owner=owner)
        if len(plots)>0:
            return plots[0]
        return None

class RemoteJobSet(models.Model):
    """
        Defines a set of RemoteJob objects belonging to the same transaction
    """
    transaction = models.ForeignKey(Transaction)
    configuration = models.ForeignKey(ReductionConfiguration)
    jobs = models.ManyToManyField(RemoteJob, related_name='_remote_set_jobs')
    timestamp = models.DateTimeField('timestamp', auto_now=True)
"""
    Reduction task models common to all instruments
    to build a common reduction framework.
    
    @author: M. Doucet, Oak Ridge National Laboratory
    @author: R. Leal, Oak Ridge National Laboratory
    @copyright: 2015 Oak Ridge National Laboratory
"""

from django.db import models
from django.contrib.auth.models import User

from remote.models import Transaction
from plotting.models import Plot1D, Plot2D

import json
import sys

import logging
logger = logging.getLogger("reduction")


UNCATEGORIZED = 'uncategorized'

class Instrument(models.Model):
    name = models.CharField(max_length=24)
    
    def __str__(self):
        return self.name

class ExperimentManager(models.Manager):
    
    def experiments_for_instrument(self, instrument, owner):
        """
            Return a list of experiments for a given instrument,
            for which there is at least one reduction process owned by 'owner'.
            
            @param instrument: Instrument object
            @param owner: owner of the reduction processes
        """
        reductions = ReductionProcess.objects.filter(instrument=instrument, owner=owner).prefetch_related('experiments')
        experiments = []
        for r in reductions:
            for e in r.experiments.all():
                if e not in experiments and len(e.name.strip())>0:
                    experiments.append(e)
        return experiments

    def get_uncategorized(self, instrument):
        expt_list = super(ExperimentManager, self).get_queryset().filter(name=UNCATEGORIZED)
        if len(expt_list)>0:
            expt = expt_list[0]
        else:
            expt = Experiment(name=UNCATEGORIZED)
            expt.save()
        if instrument is not None:
            instrument_id = Instrument.objects.get_or_create(name=instrument.lower())
            expt.instruments.add(instrument_id[0])
        return expt
        
class Experiment(models.Model):
    """
        Table holding IPTS information
    """
    name = models.CharField(max_length=24, unique=True)
    instruments = models.ManyToManyField(Instrument, related_name='_ipts_instruments+')
    created_on = models.DateTimeField('Timestamp', auto_now_add=True)
    objects = ExperimentManager()
    
    def __unicode__(self):
        return self.name
    
    def is_uncategorized(self):
        return self.name == UNCATEGORIZED
    
class ReductionProcess(models.Model):
    """
        Reduction process definition
    """
    instrument = models.ForeignKey(Instrument)
    experiments = models.ManyToManyField(Experiment, related_name='_reduction_experiment+')
    name = models.TextField()
    owner = models.ForeignKey(User)
    data_file = models.TextField()
    properties = models.TextField()
    timestamp = models.DateTimeField('timestamp', auto_now=True)
    
    def __str__(self):
        return "%s - %s" % (self.id, self.name)
    
    def get_config(self):
        """
            Return the reduction configuration associated to with this entry
        """
        configs = ReductionConfiguration.objects.filter(reductions=self)
        if len(configs)>1:
            logger.error("More than one configuration found for ReductionProcess id=%s" % self.id)
        if len(configs)>0:
            return configs[0]
        return None
        
    def get_data_dict(self):
        """
            Return a dictionary of properties for this entry
        """
        data = {}
        try:
            data = json.loads(self.properties)
        except:
            logger.error("Could not retrieve properties: %s" % sys.exc_value)
        data.update({'reduction_name': self.name,
                     'reduction_id': self.id})
        return data
    
    def get_experiments(self):
        try:
            expts = []
            for item in self.experiments.all():
                if len(str(item).strip())>0:
                    expts.append(str(item).strip())
            return ', '.join(expts) 
        except:
            return ''

class ReductionConfiguration(models.Model):
    """
        Common reduction properties used for a given configuration
    """
    instrument = models.ForeignKey(Instrument)
    experiments = models.ManyToManyField(Experiment, related_name='_configuration_experiment+')
    name = models.TextField()
    owner = models.ForeignKey(User)
    reductions = models.ManyToManyField(ReductionProcess, related_name='_configuration_reduction+')
    properties = models.TextField()
    timestamp = models.DateTimeField('timestamp', auto_now=True)

    def __str__(self):
        return "%s - %s" % (self.id, self.name)
    
    def get_data_dict(self):
        """
            Return a dictionary of properties for this entry
        """
        data = {}
        try:
            data.update(json.loads(self.properties))
        except:
            logger.error("Could not retrieve properties: %s" % sys.exc_value)
        data.update({'reduction_name': self.name,
                     'configuration_id': self.id})
        return data
    
    def get_experiments(self):
        try:
            expts = []
            for item in self.experiments.all():
                if len(str(item).strip())>0:
                    expts.append(str(item).strip())
            return ', '.join(expts) 
        except:
            return ''

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
    
    def __str__(self):
        d = { 'reduction' : self.reduction,
        'remote_id' : self.remote_id,
        'transaction' : self.transaction}
        return str(d)

class RemoteJobSet(models.Model):
    """
        Defines a set of RemoteJob objects belonging to the same transaction
    """
    transaction = models.ForeignKey(Transaction)
    configuration = models.ForeignKey(ReductionConfiguration)
    jobs = models.ManyToManyField(RemoteJob, related_name='_remote_set_jobs')
    timestamp = models.DateTimeField('timestamp', auto_now=True)
    
    def __str__(self):
        s = "RemoteJobSet transaction id = %s is active = %s."%(self.transaction.trans_id,self.transaction.is_active)
        return s


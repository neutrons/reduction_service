"""
    Reduction task models common to all instruments
    to build a common reduction framework.
    
    @author: M. Doucet, Oak Ridge National Laboratory
    @author: R. Leal, Oak Ridge National Laboratory
    @copyright: 2015 Oak Ridge National Laboratory
"""

from django.db import models
from django.contrib.auth.models import User

import logging
logger = logging.getLogger("reduction")
import json
import sys

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
        expt_list = super(ExperimentManager, self).get_query_set().filter(name=UNCATEGORIZED)
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


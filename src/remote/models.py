from django.db import models
from django.contrib.auth.models import User

class JobStatus(models.Model):
    """
        Table of job status codes
    """ 
    status = models.CharField(max_length=24)
    
    def __str__(self):
        return self.status

class ReductionJob(models.Model):
    """
        Table of Fermi jobs
    """
    job_id = models.IntegerField(unique=True)
    status = models.ForeignKey(JobStatus)
    title = models.CharField(max_length=128)
    owner = models.ForeignKey(User)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    
    def __str__(self):
        # return str(self.trans_id)
        d = {'job_id':self.job_id,
             'status' : self.status,
             'title' : self.title,
             'owner' : self.owner,
             'start_time' : self.start_time,
             'end_time' : self.end_time}
        return str(d)
    
class Transaction(models.Model):
    trans_id = models.IntegerField(unique=True)   
    owner = models.ForeignKey(User)
    directory = models.TextField()
    is_active = models.BooleanField(default=True)
    start_time = models.DateTimeField(auto_now=False, auto_now_add=True)

    def __str__(self):
        # return str(self.trans_id)
        d = {'trans_id':self.trans_id,
             'owner' : self.owner,
             'directory' : self.directory,
             'is_active' : self.is_active,
             'start_time' : self.start_time }
        return str(d)

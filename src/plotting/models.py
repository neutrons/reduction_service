"""
    Models used to store plotting data and options
"""
from django.db import models
from django.contrib.auth.models import User

class PlotLayout(models.Model):
    """
        Options for a plotting area,
        which means everything except the options
        related to the data points.
    """
    owner = models.ForeignKey(User)
    title = models.TextField(default='')
    width = models.IntegerField(default=550)
    height = models.IntegerField(default=250)
    is_x_log = models.BooleanField(default=False)
    is_y_log = models.BooleanField(default=False)
    x_label = models.TextField(default='Q [1/&Aring;]')
    y_label = models.TextField(default='Intensity')
    
    def __str__(self):
        return "%s-%s" % (self.owner, self.id)

class DataSet(models.Model):
    """
        Data set. Used as cache.
    """
    owner = models.ForeignKey(User)
    data  = models.TextField()
    #filename = models.TextField()
    
    def __str__(self):
        return str(self.owner)
    
class DataLayout(models.Model):
    """
        Options related to the plotted data.
    """
    owner = models.ForeignKey(User)
    color = models.CharField(max_length=12, default='#0077cc')
    size  = models.IntegerField(default=2)
    dataset = models.ForeignKey(DataSet)
    
    def __str__(self):
        return "%s-%s" % (self.owner, self.id)
    
class Plot1DManager(models.Manager):
    def create_plot(self, user, data, filename, **kwargs):
        """
            Create a default plot, with all associated DB entries
            @param user: owner of the plot
            @param data: string representation of the data
            @param filename: name of the file that contained the data
            @param kwargs: Usefull to change plot layout (e.g. y_label)
        """
        dataset = DataSet(owner=user, data=data)
        dataset.save()
        datalayout = DataLayout(owner=user, dataset=dataset)
        datalayout.save()
        plotlayout = PlotLayout(owner=user, **kwargs)
        plotlayout.save()
        plot1d = Plot1D(owner=user, filename=filename, layout=plotlayout)
        plot1d.save()
        plot1d.data.add(datalayout)
        return plot1d

class Plot1D(models.Model):
    """
        Put together a plot
    """
    owner = models.ForeignKey(User)
    filename = models.TextField()
    data = models.ManyToManyField(DataLayout)
    layout = models.ForeignKey(PlotLayout, null=True, blank=True)
    objects = Plot1DManager()
    
    def __str__(self):
        return self.filename
    
    def first_data_layout(self):
        """
            Return the first data set to be plotted
        """
        if len(self.data.all())>0:
            return self.data.all()[0]
        return None
    
class Plot2DManager(models.Manager):
    def create_plot(self, user, data, x_axis, y_axis, z_min, z_max, filename, **kwargs):
        """
            Create a default plot, with all associated DB entries
            @param user: owner of the plot
            @param data: string representation of the data
            @param x_axis: string representation of the x axis
            @param y_axis: string representation of the y axis
            @param z_min: minimum value of the plotted data in z
            @param z_max: maximum value of the plotted data in z
            @param filename: name of the plotted data file
        """
        plotlayout = PlotLayout(owner=user, width=550, height=550,**kwargs)
                                
        plotlayout.save()
        plot2d = Plot2D(owner=user, filename=filename, layout=plotlayout,
                        data=data, x_axis=x_axis, y_axis=y_axis,
                        z_min=z_min, z_max=z_max)
        plot2d.save()
        return plot2d

class Plot2D(models.Model):
    """
        Put together a 2D plot
    """
    owner = models.ForeignKey(User)
    filename = models.TextField()
    data = models.TextField()
    x_axis = models.TextField()
    y_axis = models.TextField()
    z_min = models.FloatField()
    z_max = models.FloatField()
    layout = models.ForeignKey(PlotLayout, null=True, blank=True)
    objects = Plot2DManager()
    
    def __str__(self):
        return self.filename
    
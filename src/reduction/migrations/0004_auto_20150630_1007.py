# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reduction', '0003_remotejob_remotejobset'),
    ]

    operations = [
        migrations.AlterField(
            model_name='remotejob',
            name='plots',
            field=models.ManyToManyField(related_name='_remote_job_plot+', to='plotting.Plot1D', blank=True),
        ),
        migrations.AlterField(
            model_name='remotejob',
            name='plots2d',
            field=models.ManyToManyField(related_name='_remote_job_plot2d+', to='plotting.Plot2D', blank=True),
        ),
        migrations.AlterField(
            model_name='remotejob',
            name='remote_id',
            field=models.CharField(max_length=30),
        ),
    ]

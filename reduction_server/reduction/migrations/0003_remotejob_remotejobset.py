# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('remote', '__first__'),
        ('plotting', '__first__'),
        ('reduction', '0002_auto_20150121_1444'),
    ]

    operations = [
        migrations.CreateModel(
            name='RemoteJob',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('remote_id', models.CharField(unique=True, max_length=30)),
                ('properties', models.TextField()),
                ('plots', models.ManyToManyField(related_name='_remote_job_plot+', null=True, to='plotting.Plot1D', blank=True)),
                ('plots2d', models.ManyToManyField(related_name='_remote_job_plot2d+', null=True, to='plotting.Plot2D', blank=True)),
                ('reduction', models.ForeignKey(to='reduction.ReductionProcess')),
                ('transaction', models.ForeignKey(to='remote.Transaction')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='RemoteJobSet',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('timestamp', models.DateTimeField(auto_now=True, verbose_name=b'timestamp')),
                ('configuration', models.ForeignKey(to='reduction.ReductionConfiguration')),
                ('jobs', models.ManyToManyField(related_name='_remote_set_jobs', to='reduction.RemoteJob')),
                ('transaction', models.ForeignKey(to='remote.Transaction')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]

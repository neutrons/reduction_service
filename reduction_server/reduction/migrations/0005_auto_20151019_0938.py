# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reduction', '0004_auto_20150630_1007'),
    ]

    operations = [
        migrations.AlterField(
            model_name='experiment',
            name='instruments',
            field=models.ManyToManyField(to='reduction.Instrument'),
        ),
        migrations.AlterField(
            model_name='reductionconfiguration',
            name='experiments',
            field=models.ManyToManyField(to='reduction.Experiment'),
        ),
        migrations.AlterField(
            model_name='reductionconfiguration',
            name='reductions',
            field=models.ManyToManyField(to='reduction.ReductionProcess'),
        ),
        migrations.AlterField(
            model_name='reductionprocess',
            name='experiments',
            field=models.ManyToManyField(to='reduction.Experiment'),
        ),
        migrations.AlterField(
            model_name='remotejob',
            name='plots',
            field=models.ManyToManyField(to='plotting.Plot1D', blank=True),
        ),
        migrations.AlterField(
            model_name='remotejob',
            name='plots2d',
            field=models.ManyToManyField(to='plotting.Plot2D', blank=True),
        ),
        migrations.AlterField(
            model_name='remotejobset',
            name='jobs',
            field=models.ManyToManyField(to='reduction.RemoteJob'),
        ),
    ]

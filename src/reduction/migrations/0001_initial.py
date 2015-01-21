# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Experiment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=24)),
                ('created_on', models.DateTimeField(auto_now_add=True, verbose_name=b'Timestamp')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Instrument',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=24)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ReductionConfiguration',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.TextField()),
                ('properties', models.TextField()),
                ('timestamp', models.DateTimeField(auto_now=True, verbose_name=b'timestamp')),
                ('experiments', models.ManyToManyField(related_name='_configuration_experiment+', to='reduction.Experiment')),
                ('instrument', models.ForeignKey(to='reduction.Instrument')),
                ('owner', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ReductionProcess',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.TextField()),
                ('data_file', models.TextField()),
                ('properties', models.TextField()),
                ('timestamp', models.DateTimeField(auto_now=True, verbose_name=b'timestamp')),
                ('experiments', models.ManyToManyField(related_name='_reduction_experiment+', to='reduction.Experiment')),
                ('instrument', models.ForeignKey(to='reduction.Instrument')),
                ('owner', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='reductionconfiguration',
            name='reductions',
            field=models.ManyToManyField(related_name='_configuration_reduction+', to='reduction.ReductionProcess'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='experiment',
            name='instruments',
            field=models.ManyToManyField(related_name='_ipts_instruments+', to='reduction.Instrument'),
            preserve_default=True,
        ),
    ]

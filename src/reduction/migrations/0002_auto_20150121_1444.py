# -*- coding: utf-8 -*-
"""
    Providing initial data to the models
    
    First generate the file with:
    $ python manage.py makemigrations --empty reduction
    
    Then add the data to be inserted into the model. A migration must be executed after:
    $ python manage.py makemigrations
    $ python manage.py migrate

    @author: R. Leal, Oak Ridge National Laboratory
    @copyright: 2015 Oak Ridge National Laboratory
"""



from __future__ import unicode_literals

from django.db import models, migrations
from reduction.models import Instrument

def insertEqsansInInstruments(apps, schema_editor):
    '''
    INSERT INTO eqsans_instrument(name) VALUES ('eqsans');
    '''
    inst = Instrument(name="eqsans")
    inst.save()
    inst = Instrument(name="seq")
    inst.save()

class Migration(migrations.Migration):

    dependencies = [
        ('reduction', '0001_initial'),
    ]

    operations = [
                  migrations.RunPython(insertEqsansInInstruments),
    ]

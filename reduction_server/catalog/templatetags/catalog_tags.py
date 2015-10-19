from django import template
from django.utils import dateformat
import datetime
from django.conf import settings
register = template.Library()

@register.filter(name='timeperiod')
def timeperiod(from_time, to_time):
    if isinstance(from_time, datetime.datetime) and isinstance(to_time, datetime.datetime):
        # Are both times on the same day?
        if from_time.year == to_time.year and from_time.month == to_time.month and from_time.day == to_time.day:
            return "%s - %s" % (from_time.strftime('%b %d, %H:%M:%S'), to_time.strftime('%H:%M:%S'))
        else:
            return "%s - %s" % (from_time.strftime('%b %d, %H:%M:%S'), to_time.strftime('%b %d, %H:%M:%S'))
    else:
        return ''


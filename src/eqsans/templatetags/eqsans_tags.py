"""
    Template tags for eqsans django app
    
    @author: M. Doucet, Oak Ridge National Laboratory
    @copyright: 2014 Oak Ridge National Laboratory
"""
from django import template
import re
register = template.Library()

@register.filter(name='ipts_suggestion')
def ipts_suggestion(value):
    """
        Filter used in the experiment view to suggest an IPTS name.
        Takes a string and parses it for a number. If a number is found,
        return IPTS-<nuumber>. IF not, return IPTS-1234.
        
        @param value: string used to generate the experiment name hint
    """
    try:
        number = re.search('([\d]+)', str(value)).group(0)
        return "IPTS-%s" % number
    except:
        return "IPTS-1234"

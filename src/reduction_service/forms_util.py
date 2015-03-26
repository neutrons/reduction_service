'''
Created on Mar 26, 2015

@author: rhf
'''
import os.path
from django.template import Template, Context
import logging
import pprint

logger = logging.getLogger('main')

def _get_default_values_from_form(form, suffix="_default"):
    """
    Iterates form.base_fields and returns a new dic
    with key_default = form.base_fields[key].initial
    """
    base_fields = form.base_fields
    out_dic = {}
    for k,v in base_fields.iteritems():
        out_dic[k+suffix] = v.initial
    return out_dic


def build_script(script_file_path, form, data):
    '''
    Build a script from a template file @script_file_path,
    the default values of a form @form,
    the dictionary @data
    '''
    if os.path.isfile(script_file_path):
        with open(script_file_path) as f:
            lines = f.readlines()
            text = '\n'.join(lines)
            template = Template(text)
            default_values = _get_default_values_from_form(form)
            data.update(default_values)
            logger.debug(pprint.pformat(data))
            context = Context(data)
            script = template.render(context)
            script_filtered = "\n".join([ll.rstrip() for ll in script.splitlines() if ll.strip()])
    return script_filtered
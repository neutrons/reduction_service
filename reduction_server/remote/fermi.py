import httplib
import json
import logging
import sys

# The following should be in settings
BASE_URL = 'https://fermi.ornl.gov/MantidRemote/'

def query(request):
    """
        Pull the legacy status information
    """
    try:
        conn = httplib.HTTPConnection(BASE_URL, timeout=0.5)
        conn.request('GET', 'query')
        r = conn.getresponse()
        
        # Check to see whether we need authentication
        if r.status == 401:
            pass
        
        
        data = json.loads(r.read())
        organized_data = []
        groups = data.keys()
        groups.sort()
        for group in groups:
            key_value_pairs = []
            keys = data[group].keys()
            keys.sort()
            for item in keys:
                key_value_pairs.append({'key':item.replace(' ', '_').replace('(%)','[pct]').replace('(', '[').replace(')', ']').replace('#',''),
                                        'value': data[group][item]})
            organized_data.append({'group':group,
                                   'data':key_value_pairs})
        return organized_data
    except:
        logging.error("Could not connect to status page: %s" % sys.exc_value)
        return []
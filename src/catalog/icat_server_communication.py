import httplib
import urllib
import xml.dom.minidom
import sys
import time
import datetime
from django.conf import settings
from catalog.view_util import get_webmon_url, get_new_reduction_url, get_new_batch_url
import logging

logger = logging.getLogger('catalog.icat')

if hasattr(settings, 'ICAT_DOMAIN'):
    ICAT_DOMAIN = settings.ICAT_DOMAIN
    ICAT_PORT = settings.ICAT_PORT
else:
    logger.error("App settings does not contain ICAT server info: using icat.sns.gov:2080")
    ICAT_DOMAIN = 'icat.sns.gov'
    ICAT_PORT = 2080

def get_text_from_xml(nodelist):
    rc = []
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc.append(node.data)
    return ''.join(rc)

def decode_time(timestamp):
    """
        Decode timestamp and return a datetime object
    """
    try:
        tz_location = timestamp.rfind('+')
        if tz_location<0:
            tz_location = timestamp.rfind('-')
        if tz_location>0:
            date_time_str = timestamp[:tz_location]
            try:
                return datetime.datetime.strptime(date_time_str, "%Y-%m-%dT%H:%M:%S.%f")
            except:
                return datetime.datetime.strptime(date_time_str, "%Y-%m-%dT%H:%M:%S")
    except:
        logger.error("Could not parse timestamp '%s': %s" % (timestamp, sys.exc_value))
        return None

def get_ipts_info(instrument, ipts):
    run_info = {}
    
    # Get basic run info
    try:
        t0 = time.time()
        conn = httplib.HTTPConnection(ICAT_DOMAIN, 
                                      ICAT_PORT, timeout=0.5)
        conn.request('GET', '/icat-rest-ws/experiment/SNS/%s/%s/meta' % (instrument.upper(),
                                                                         ipts.upper()))
        r = conn.getresponse()
        dom = xml.dom.minidom.parseString(r.read())
        metadata = dom.getElementsByTagName('proposal')
        if len(metadata)>0:
            for n in metadata[0].childNodes:
                # Run title
                if n.nodeName=='title' and n.hasChildNodes():
                    run_info['title'] = urllib.unquote(get_text_from_xml(n.childNodes))
                # Run range
                if n.nodeName=='runRange' and n.hasChildNodes():
                    run_info['run_range'] = get_text_from_xml(n.childNodes)
                # Time
                if n.nodeName=='createTime' and n.hasChildNodes():
                    timestr = get_text_from_xml(n.childNodes)
                    run_info['createTime'] = decode_time(timestr)
        conn.close()
        logger.debug("ICAT HTTP request took %g sec" % (time.time()-t0))
    except Exception as e:
        logger.exception(e)
        run_info['icat_error'] = 'Could not communicate with catalog server'
        logger.error("Communication with ICAT server failed: %s" % sys.exc_value)
    return run_info
    
def get_instruments():
    """
    http://icat-testing.sns.gov:2080/icat-rest-ws/experiment/SNS
    """
    instruments = []
    try:
        t0 = time.time()
        conn = httplib.HTTPConnection(ICAT_DOMAIN, 
                                      ICAT_PORT, timeout=0.5)
        conn.request('GET', '/icat-rest-ws/experiment/SNS/')
        r = conn.getresponse()
        dom = xml.dom.minidom.parseString(r.read())
        elements = dom.getElementsByTagName('instrument')
        for element in elements:
            instr = get_text_from_xml(element.childNodes)
            if not instr.upper().endswith('A'):
                if not instr.upper() in ['NSE', 'FNPB']:
                    instruments.append(instr)
        conn.close()
        logger.debug("ICAT HTTP request %s:%s took %g sec" % (ICAT_DOMAIN, ICAT_PORT, (time.time()-t0)))
    except Exception as e:
        logger.exception(e)
        logger.error("Could not get list of instruments from ICAT: %s" % sys.exc_value)
    return instruments
    

def get_experiments(instrument):
    """
    http://icat-testing.sns.gov:2080/icat-rest-ws/experiment/SNS/NOM/meta

    <proposal id="IPTS-8109">
      <collection>0</collection>
      <title>dummy</title>
      <createTime>2013-12-02T17:28:01.874-05:00</createTime>
    </proposal>

    """
    experiments = []
    try:
        t0 = time.time()
        url = '/icat-rest-ws/experiment/SNS/%s/meta' % instrument.upper()
        conn = httplib.HTTPConnection(ICAT_DOMAIN, 
                                      ICAT_PORT, timeout=20)
        conn.request('GET', url)
        r = conn.getresponse()
        dom = xml.dom.minidom.parseString(r.read())
        for e in  dom.getElementsByTagName('proposal'):
            expt = {'id': e.attributes['id'].value}
            for n in e.childNodes:
                if n.hasChildNodes():
                    if n.nodeName == 'title':
                        expt[n.nodeName] = urllib.unquote(get_text_from_xml(n.childNodes))
                    elif n.nodeName == 'createTime':
                        timestr = get_text_from_xml(n.childNodes)
                        expt[n.nodeName] = decode_time(timestr)
                        
            experiments.append(expt)
        conn.close()
        logger.debug("ICAT HTTP request %s:%s%s took %g sec" % (ICAT_DOMAIN, ICAT_PORT, url, (time.time()-t0)))
    except Exception as e:
        logger.exception(e)
        logger.error("Could not get list of experiments from ICAT: %s" % sys.exc_value)
    return experiments
    
    
def get_ipts_runs(instrument, ipts):
    """
        Get the list of runs and basic meta data for
        a given experiment
        @param instrument name [string]
        @param ipts: experiment name [string]
        
        <run id="12801">
            <title>Blank scanRT</title>
            <startTime>2013-04-05T16:17:56.246-04:00</startTime>
            <endTime>2013-04-05T16:40:12.938-04:00</endTime>
            <duration>1336.6914</duration>
            <protonCharge>1.20244649808e+12</protonCharge>
            <totalCounts>1.3197872E7</totalCounts>
        </run>
    """
    run_data = []
    try:
        t0 = time.time()
        url = '/icat-rest-ws/experiment/SNS/%s/%s/all' % (instrument.upper(), ipts.upper())
        conn = httplib.HTTPConnection(ICAT_DOMAIN, 
                                      ICAT_PORT, timeout=10)
        conn.request('GET', url)
        r = conn.getresponse()
        dom = xml.dom.minidom.parseString(r.read())
        for r in dom.getElementsByTagName('run'):
            run_info = {'id': r.attributes['id'].value,
                        'webmon_url': get_webmon_url(instrument, r.attributes['id'].value, ipts),
                        'reduce_url': get_new_reduction_url(instrument, r.attributes['id'].value, ipts),
                        'batch_url':  get_new_batch_url(instrument, r.attributes['id'].value, ipts)}
            for n in r.childNodes:
                if n.hasChildNodes():
                    if n.nodeName in ['title']:
                        run_info[n.nodeName] = urllib.unquote(get_text_from_xml(n.childNodes))
                    elif n.nodeName in ['duration', 'protonCharge', 'totalCounts']:
                        text_value = get_text_from_xml(n.childNodes)
                        try:
                            run_info[n.nodeName] = "%.4G" % float(text_value)
                        except:
                            run_info[n.nodeName] = text_value
                    elif n.nodeName in ['startTime', 'endTime']:
                        text_value = get_text_from_xml(n.childNodes)
                        run_info[n.nodeName] = decode_time(text_value)
            run_data.append(run_info)
        conn.close()
        logger.debug("ICAT HTTP request %s:%s%s took %g sec" % (ICAT_DOMAIN, ICAT_PORT, url, (time.time()-t0)))
    except Exception as e:
        logger.exception(e)
        logger.error("Communication with ICAT server failed: %s" % sys.exc_value)
    return run_data

# def _string_to_range(range_str):
#     """
#     Converts a string in the format of:
#     '1,2,5-7,10'
#     to python range:
#     [1, 2, 5, 6, 7, 10]
#     """
#     result = []
#     for part in range_str.split(','):
#         if '-' in part:
#             a, b = part.split('-')
#             a, b = int(a), int(b)
#             result.extend(range(a, b + 1))
#         else:
#             a = int(part)
#             result.append(a)
#     return result
#  
# def get_ipts_run_range(instrument, ipts):
#     """
#         Get the list of runs range a given experiment
#         @param instrument name [string]
#         @param ipts: experiment name [string]
#         @return a list of run numbers
#         $ curl -s http://icat.sns.gov:2080/icat-rest-ws/experiment/SNS/EQSANS/IPTS-13502 |  tidy -xml -iq -
#         <?xml version="1.0" encoding="utf-8" standalone="yes"?>
#         <runs>
#           <runRange>46477-46581, 46586-46628</runRange>
#         </runs>
#     """
#     run_range = []
#     try:
#         t0 = time.time()
#         url = '/icat-rest-ws/experiment/SNS/%s/%s' % (instrument.upper(), ipts.upper())
#         conn = httplib.HTTPConnection(ICAT_DOMAIN, 
#                                       ICAT_PORT, timeout=5)
#         conn.request('GET', url)
#         r = conn.getresponse()
#         dom = xml.dom.minidom.parseString(r.read())
#         run_range_node_list = dom.getElementsByTagName('runRange')
#         
#         if run_range_node_list.length != 1:
#             return None
#         else:
#             run_range_str = run_range_node_list.item(0).firstChild.data
#             run_range = _string_to_range(run_range_str)
#             
#         ret = []
#         for i in run_range:
#             #ret.append({"value" : i})
#             ret.append('%d'%i)
#         run_range = ret
# 
#         conn.close()
#         logger.debug("ICAT HTTP request %s:%s%s took %g sec" % (ICAT_DOMAIN, ICAT_PORT, url, (time.time()-t0)))
#     except Exception as e:
#         logger.exception(e)
#         logger.error("Communication with ICAT server failed: %s" % sys.exc_value)
#     return run_range

def get_ipts_runs_as_json(instrument, ipts):
    """
        Get the list of runs and basic meta data for
        a given experiment
        @param instrument name [string]
        @param ipts: experiment name [string]
        @return a list of run numbers and labels as json
        <run id="12801">
            <title>Blank scanRT</title>
            <startTime>2013-04-05T16:17:56.246-04:00</startTime>
            <endTime>2013-04-05T16:40:12.938-04:00</endTime>
            <duration>1336.6914</duration>
            <protonCharge>1.20244649808e+12</protonCharge>
            <totalCounts>1.3197872E7</totalCounts>
        </run>
    """
    run_data = []
    try:
        t0 = time.time()
        url = '/icat-rest-ws/experiment/SNS/%s/%s/all' % (instrument.upper(), ipts.upper())
        conn = httplib.HTTPConnection(ICAT_DOMAIN, 
                                      ICAT_PORT, timeout=10)
        conn.request('GET', url)
        r = conn.getresponse()
        dom = xml.dom.minidom.parseString(r.read())
        for r in dom.getElementsByTagName('run'):
            run_id = r.attributes['id'].value
            for n in r.childNodes:
                if n.hasChildNodes():
                    if n.nodeName in ['title']:
                        run_title = urllib.unquote(get_text_from_xml(n.childNodes))
            run_data.append({"label": "%s - %s"%(run_id,run_title), "value": run_id})
        conn.close()
        logger.debug("ICAT HTTP request as JSON %s:%s%s took %g sec" % (ICAT_DOMAIN, ICAT_PORT, url, (time.time()-t0)))
    except Exception as e:
        logger.exception(e)
        logger.error("Communication with ICAT server failed: %s" % sys.exc_value)
    return run_data


def get_experiments_as_json(instrument):
    """
    http://icat-testing.sns.gov:2080/icat-rest-ws/experiment/SNS/NOM/meta

    <proposal id="IPTS-8109">
      <collection>0</collection>
      <title>dummy</title>
      <createTime>2013-12-02T17:28:01.874-05:00</createTime>
    </proposal>

    """
    experiments = []
    try:
        t0 = time.time()
        url = '/icat-rest-ws/experiment/SNS/%s/meta' % instrument.upper()
        conn = httplib.HTTPConnection(ICAT_DOMAIN, 
                                      ICAT_PORT, timeout=20)
        conn.request('GET', url)
        r = conn.getresponse()
        dom = xml.dom.minidom.parseString(r.read())
        for e in  dom.getElementsByTagName('proposal'):
            exp_id = e.attributes['id'].value
            for n in e.childNodes:
                if n.hasChildNodes():
                    if n.nodeName == 'title':
                        exp_title = urllib.unquote(get_text_from_xml(n.childNodes))
            experiments.append({"label": "%s - %s"%(exp_id,exp_title), "value": exp_id})
        conn.close()
        logger.debug("ICAT HTTP request %s:%s%s took %g sec" % (ICAT_DOMAIN, ICAT_PORT, url, (time.time()-t0)))
    except Exception as e:
        logger.exception(e)
        logger.error("Could not get list of experiments from ICAT: %s" % sys.exc_value)
    return experiments

def get_run_info(instrument, run_number):
    """
        Get ICAT info for the specified run
        @param instrument: instrument name
        @param run_number: run_number
    """
    run_info = {}
    try:
        logger.debug("Getting information for %s and run number = %s."%(instrument,run_number))
        t0 = time.time()
        conn = httplib.HTTPConnection(ICAT_DOMAIN,
                                      ICAT_PORT, timeout=20.0)
        url = '/icat-rest-ws/dataset/SNS/%s/%s' % (instrument.upper(), run_number)
        
        logger.debug("Connecting %s:%s%s..."%(ICAT_DOMAIN,ICAT_PORT,url))
        conn.request('GET', url)
        r = conn.getresponse()
        dom = xml.dom.minidom.parseString(r.read())
        metadata = dom.getElementsByTagName('metadata')
        if len(metadata)>0:
            for n in metadata[0].childNodes:
                for tag in ['title', 'duration', 'protonCharge', 'totalCounts']:
                    if n.nodeName==tag and n.hasChildNodes():
                        run_info[tag] = urllib.unquote(get_text_from_xml(n.childNodes))
        conn.close()
        logger.debug("ICAT HTTP request %s:%s%s took %g sec" % (ICAT_DOMAIN, ICAT_PORT, url, (time.time()-t0)))
    except Exception as e:
        logger.exception(e)
        run_info['icat_error'] = 'Could not communicate with catalog server'
        logger.error("Communication with ICAT server failed: %s" % sys.exc_value)
        
    return run_info


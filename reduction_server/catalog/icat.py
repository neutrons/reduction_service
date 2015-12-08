'''
Created on Dec 8, 2015

@author: rhf
'''

import httplib
import json
import logging

from django.conf import settings
from django.contrib import messages

logger = logging.getLogger('catalog.icat')

# Defaults:
DEFAULT_ICAT_DOMAIN = "icat.sns.gov"
DEFAULT_ICAT_PORT = 2080

TIMEOUT = 1
URL_PATH_PREFIX = "icat-rest-ws"
HEADERS = {"Accept": "application/json"}

class ICat(object):
    '''
    ICAT rest interface
    '''


    def __init__(self,django_request, facility="SNS"):
        '''
        Constructor
        '''
        try:
            self.conn = httplib.HTTPConnection(
                                    settings.ICAT_DOMAIN,
                                    settings.ICAT_PORT,
                                    timeout=TIMEOUT)
        except Exception as e:
            logger.exception(e)
            logger.warning("Using default icat configuration. Is there ICAT_DOMAIN/ICAT_PORT in the settings?")
            self.conn = httplib.HTTPConnection(
                                    DEFAULT_ICAT_DOMAIN,
                                    DEFAULT_ICAT_PORT,
                                    timeout=TIMEOUT)
        self.facility = facility
        self.django_request = django_request
        
    def __del__(self):
        if self.conn is not None:
            self.conn.close()
        
    
    def _dump_error(self,exception,message):
        """
        @param exception: Must be a valid python exception
        @param message: Must be a string
        """
        logger.exception(exception)
        logger.error(message)
        messages.error(self.django_request, message)
        messages.error(self.django_request, str(exception))
        return None
    
    def _parse_json(self,json_as_string):
        '''
        Makes sure we have a proper json string
        @param json_as_string: must be a string
        @return: python json dictionary in unicode
        '''
        try:
            logger.debug(json_as_string)
            return json.loads(json_as_string)
        except Exception as e:
            self._dump_error(self,e,"It looks like ICAT did not return a valid JSON!")

            
    
    def get_instruments(self):
        '''
        @return: 
        {
            "instrument": [
                "ARCS",
                "BSS",
                "CNCS",
                "CORELLI",
                "EQSANS",
                "FNPB",
                "HYS",
                "HYSA",
                "MANDI",
                "NOM",
                "NSE",
                "PG3",
                "REF_L",
                "REF_M",
                "SEQ",
                "SNAP",
                "TOPAZ",
                "USANS",
                "VIS",
                "VULCAN"
            ]
        }
        '''
        logger.debug("get_instruments")
        try:
            self.conn.request('GET',
                              '/%s/experiment/%s'%(URL_PATH_PREFIX,self.facility),
                              headers = HEADERS)
            response = self.conn.getresponse()
            return self._parse_json(response.read())
        except Exception as e:
            self._dump_error(e,"Communication with ICAT server failed.")
            return None

    def get_experiments(self,instrument):
        '''
        @param instrument: Valid instrument as string
        @return: 
        {
            "proposal": [
                "2012_2_11b_SCI",
                "2013_2_11B_SCI",
                "2014_1_11B_SCI",
                "IPTS-10136",
                "IPTS-10138",
                "IPTS-10663",
                "IPTS-10943",
                "IPTS-11063",
                "IPTS-11091",
                "IPTS-11215",
                "IPTS-11464",
                "IPTS-11482",
                "IPTS-11543",
                "IPTS-11817",
                "IPTS-11862",
                "IPTS-11932",
                "IPTS-11940",
                "IPTS-12152",
                "IPTS-12402",
                "IPTS-12438",
                "IPTS-12697",
                "IPTS-12864",
                "IPTS-12874",
                "IPTS-12924",
                "IPTS-13243",
                "IPTS-13288",
                "IPTS-13552",
                "IPTS-13643",
                "IPTS-13653",
                "IPTS-13722",
                "IPTS-13904",
                "IPTS-14069",
                "IPTS-14562",
                "IPTS-14586",
                "IPTS-15880",
                "IPTS-8776"
            ]
        }
        '''
        
        try:
            self.conn.request('GET',
                              '/%s/experiment/%s/%s'%(URL_PATH_PREFIX, self.facility, instrument),
                              headers = HEADERS)
            response = self.conn.getresponse()
            return self._parse_json(response.read())
        except Exception as e:
            self._dump_error(e,"Communication with ICAT server failed.")
            return None            
        

#!/usr/bin/env python

#DGS_REDUCTION_PATH = "/SNS/SEQ/shared/mantid/matts_scripts"
DGS_REDUCTION_PATH = "/SNS/ARCS/shared/mantidscripts/dgsreduction/V6p0/newdgs"

import sys
sys.path.append(DGS_REDUCTION_PATH)

"""

DGS Reduction

The XML content must be assigned below!


"""

XML_CONTENT = '''{{ xml_content|safe }}'''

import dgsreductionmantid
import tempfile

f = tempfile.NamedTemporaryFile()
try:
    f.write(XML_CONTENT)    
    dgsreduction(XMLfile=f)
    
finally:
    # Automatically cleans up the file
    f.close()


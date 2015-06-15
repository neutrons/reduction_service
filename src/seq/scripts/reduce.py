#!/usr/bin/env python
"""

SEQ Reduction script

"""

#DGS_REDUCTION_PATH = "/SNS/SEQ/shared/mantid/matts_scripts"
DGS_REDUCTION_PATH = "/SNS/ARCS/shared/mantidscripts/dgsreduction/V6p0/newdgs"

import sys
sys.path.append(DGS_REDUCTION_PATH)

"""

DGS Reduction

The XML content must be assigned below!


"""

XML_CONTENT = '''{{ xml_content|safe }}'''

from dgsreductionmantid import dgsreduction
import tempfile

f = tempfile.NamedTemporaryFile()
try:
    f.write(XML_CONTENT)  
    f.flush()  
    dgsreduction(XMLfile=f.name)
    
finally:
    # Automatically cleans up the file
    f.close()


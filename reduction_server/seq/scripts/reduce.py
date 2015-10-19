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


## DGS reduction create folders which are not downloadable!
# Copy these folder contents to root
import os
import shutil
current_directory = os.getcwd()
directories_in_current_directory = [ name for name in os.listdir(current_directory) 
                                    if os.path.isdir(os.path.join(current_directory, name)) ]

for directory in directories_in_current_directory:
    directory_contents = os.listdir(directory)
    for content in directory_contents:
        file_path = os.path.join(directory,content)
        print file_path
        file_abspath = os.path.abspath(file_path)        
        shutil.move(file_abspath, current_directory)
    os.rmdir(directory)
        
import os
import sys

testdir = os.path.dirname(__file__)
srcdir = "../"
sys.path.insert(0, os.path.abspath(os.path.join(testdir, srcdir)))

from dcm_parser import DCMParser , DCMObject

parser_object = DCMParser('tests/sample.dcm')
dcm_object = parser_object.parse_dcm()

print(dcm_object)
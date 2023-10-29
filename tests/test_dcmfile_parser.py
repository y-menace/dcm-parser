import os
import sys
testdir = os.path.dirname(__file__)
module_dir = "../"
sys.path.insert(0, os.path.abspath(os.path.join(testdir, module_dir)))


import pytest
from dcmfile_parser import DCMParser, DCMObject


# Assuming the parse_dcm function is available and can parse a DCM file to produce instances of the provided attribute classes.

@pytest.fixture
def sample_dcm_file(tmp_path):
    dcmfile_parser = DCMParser('tests/sample1.dcm')
    dcm_obj = dcmfile_parser.create_dcm_object()
    return dcm_obj

@pytest.mark.parametrize("export_file", ["test.dcm"])
def test_export(sample_dcm_file, export_file):
    dcm_obj = sample_dcm_file
    dcm_obj.write(export_file)


@pytest.mark.parametrize("attribute_type,attribute_name,expected_wert", [
    # For FESTWERT
    ("FESTWERT", "parameter", [30.0]),

    # For FESTWERTEBLOCK
    ("FESTWERTEBLOCK", "matrix", [1.0, 0.0, 0.5, 2.0]),

    # For KENNLINIE
    ("KENNLINIE", "line_curve", [5.0, 85.0, 125.0, 185.0, 225.0, 265.0, 305.0, 345.0]),

    # For FESTKENNLINIE
    ("FESTKENNLINIE", "fixed_line_curve", [50.0 ,95.0, 140.0 ,185.0, 230.0, 275.0]),

    # For FESTKENNLINIE
    ("GRUPPENKENNLINIE", "group_line_curve", [-50.0, -95.0, -140.0]),

    # For FESTKENNLINIE
    ("KENNFELD", "map", [0.5, 0.9, 0.7 ,1.5 ,1.9, 2.3, 1.5, 2.5, 3.5 ,2.5, 3.5, 4.5 ]),
    
    # For FESTKENNLINIE
    ("FESTKENNFELD", "static_map", [0.5, 0.9, 0.7, 1.5, 1.9, 2.3, 1.5, 2.5, 3.5, 2.5, 3.5, 4.5]),

    # For FESTKENNLINIE
    ("GRUPPENKENNFELD", "group_map", [1.5 ,2.5 ,3.5 ,2.5 ,3.5 ,4.5 ,2.5 ,4.5 ,6.5 ,3.5 ,4.5 ,5.5 ,3.5 ,6.5 ,9.5 ,7.5 ,8.5 ,9.5]),

    # ... and so on for each attribute type and its values
])
def test_attribute_wert_read(sample_dcm_file, attribute_type, attribute_name, expected_wert):
    dcm_obj = sample_dcm_file
    attribute_object, type_of = dcm_obj._param_name_dict[attribute_name]
    
    # Depending on attribute_type, access the relevant WERT value or values
    assert attribute_object.wert == expected_wert


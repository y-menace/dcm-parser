## Introduction

Parser for DCM files [Data Conversion Format](https://www.etas.com/download-center-files/products_ASCET_Software_Products/TechNote_DCM_File_Formats.pdf ). The package has two main classes `DCMParser` and `DCMObject`, which provide a  toolkit to deal with DCM  files used in automotive software development. While the `DCMParser` is designed to read and interpret DCM files, the `DCMObject` allows for structured representation and manipulation of the parsed data.

## DCMParser

### Features

- **File Reading**: Efficiently read and parse DCM files.
- **DCM Interpretation**: Translate raw DCM file content into structured data.
- **Data Extraction**: Extract specific data sections or parameters from the DCM file.
- **Error Handling**: Gracefully handle potential parsing errors.

### Usage

1. **Parsing the DCM file**:
    ```python
    dcm_parser = DCMParser("path/to/dcm/file")
    ```

2. **Creating a DCM object**:
    ```python
    dcm_obj = dcm_parser.create_dcm_object()
    ```

## DCMObject

### Features

- **Initialization and Attribute Sorting**: Auto-sorts parameters alphabetically by name upon initialization.
- **Parameter Management**: Remove, update (from another DcMObject), or add parameters.
- **Exporter**: Write the `DCMObject` back to a dcm file .

### Usage


1. **Write to a File**:
    ```python
    dcm_obj.write()
    ```
2. **Update Parameters from Another DCMObject**:
    ```python
    updated_names, missing_names = dcm_obj.update_from(other_dcm)
    ```
3. **Add New Parameters from Another DCMObject**:
    ```python
    dcm_obj.add_new_parameters_from(other_dcm)
    ```

4. **Remove a Parameter**:
    ```python
    result = dcm_obj.remove_parameter_by_name("parameter_name")
    ```

5. **Cleanup All Parameters**:
    ```python
    dcm_obj.cleanup_parameters()
    ```

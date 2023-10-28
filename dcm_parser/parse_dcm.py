from dataclasses import dataclass
from typing import List, Union, Optional
from .attribute_classes import FUNKTIONEN, FESTWERT, FESTWERTEBLOCK, KENNLINIE, FESTKENNLINIE, GRUPPENKENNLINIE
from .attribute_classes import KENNFELD,FESTKENNFELD, GRUPPENKENNFELD, STUETZSTELLENVERTEILUNG 
from .dcm_object import DCMObject
import re

class DCMParser():    
    format_spec_string = 'KONSERVIERUNG_FORMAT'
    all_param_classes = [ FESTWERT, FESTWERTEBLOCK, KENNLINIE, FESTKENNLINIE, GRUPPENKENNLINIE,
                            KENNFELD,FESTKENNFELD, GRUPPENKENNFELD, STUETZSTELLENVERTEILUNG]

    single_line_attrs = {
        'LANGNAME': 'langname',
        'FUNKTION':'funktion',
        'DISPLAYNAME' : 'displayname',      
        'VAR': 'var',
        'SIZE': 'size',
        'EINHEIT_W' : 'einheit_w',
        'EINHEIT_X': 'einheit_x',
        'EINHEIT_Y': 'einheit_y',
        'TEXT': 'text'
    }
    single_line_attrs_keywords = '|'.join(single_line_attrs.keys())
    single_line_attrs_keywords_pattern = re.compile(rf'({single_line_attrs_keywords})\s+("?[^"\n]*"?)\s*$')

    possible_multi_line_attrs= {        
        'WERT': 'wert',
        'ST/X': 'st_x',
        'ST/Y': 'st_y',
        'SIZE_X': 'size_x',
        'SIZE_Y': 'size_y',
    }
    multi_line_attrs_keywords = '|'.join(possible_multi_line_attrs.keys())
    multi_line_attrs_keywords_pattern = re.compile(rf'({multi_line_attrs_keywords})\s+(.*?)\s*$', re.IGNORECASE)


    def __init__(self,dcm_file,):
        self.file = dcm_file

        with open(self.file, "r", encoding="ISO-8859-1") as f:
            content = f.read()
        self.file_raw_content = content

    def create_dcm_object(self):
        ## get comments , format_spec
        comments,format_spec, rest_data = self.get_comments_and_spec_version()    
        function_chunk = self.chunks_for_type(rest_data,FUNKTIONEN.token_string)
        self.all_functions = self.create_functions(function_chunk)
        ## make the chunks based on END
        self.raw_data_chunks_dict = self.create_chunks(rest_data)
        self.processed_data = {}        
        for key,value in self.raw_data_chunks_dict.items():
            self.processed_data[key] = self.process_param_chunk(value,key)
        

        return DCMObject(
            filePath = self.file,
            comments = comments,
            format_spec_version = format_spec,    # KONSERVIERUNG_FORMAT,
            functions = self.all_functions,
            parameters = self.processed_data['FESTWERT'],
            parameter_block = self.processed_data['FESTWERTEBLOCK'],
            characteristic_curve = self.processed_data['KENNLINIE'],
            characteristic_curve_fixed = self.processed_data['FESTKENNLINIE'],
            characteristic_curve_group = self.processed_data['GRUPPENKENNLINIE'],
            characteristic_map = self.processed_data['KENNFELD'],
            characteristic_map_fixed = self.processed_data['FESTKENNFELD'],
            characteristic_map_group = self.processed_data['GRUPPENKENNFELD'],
            distribution = self.processed_data['STUETZSTELLENVERTEILUNG']
         )
            
    def get_comments_and_spec_version(self):
        dcm_content = self.file_raw_content
        # Finding the line that starts with "KONSERVIERUNG_FORMAT" using regex
        match = re.search(f'^{self.format_spec_string}.*', dcm_content, re.MULTILINE)
        
        if not match:
            raise ValueError(f"{self.format_spec_string} line not found")
        
        # Splitting the content into comments and data based on the matched line
        split_index = match.start()
        comments = dcm_content[:split_index].strip()
        data_and_format = dcm_content[split_index:].strip()

        # Extracting the format value
        format_line = data_and_format.split('\n', 1)[0].strip()
        format_value = format_line.split()[1] if len(format_line.split()) > 1 else None
        
        # Extracting the data below the format spec line
        data = data_and_format[len(format_line):].strip()

        return comments, format_value, data

    def create_chunks(self,data):
        all_dict = {}
        for item_class in self.all_param_classes:
            all_dict[item_class.token_string.strip()] = self.chunks_for_type(data,item_class.token_string)
        return all_dict

    def chunks_for_type(self,data,type):        
        # This pattern matches the starting keyword, followed by any content (including newline),
        # up until the next 'END' that's at the start of a line.
        
        pattern = re.compile(rf'^(({type}).*?^END)', re.DOTALL | re.MULTILINE)
        chunks = pattern.findall(data)
        # Removing duplicates by converting the list to a set and then back to a list
        chunks = [match[0] for match in chunks]
        return chunks

    def create_functions (self,in_str):
        '''
        each line can be parsed as seperate objects
        '''
        all_objects = []
        if len(in_str) > 0:
            content = in_str[0].splitlines()
            for line in content[1:-1]: # 1st and last line are KEYWORDS
                match  = FUNKTIONEN.extract_regex.match(line)
                if match:
                    function_type = match.group(1)
                    version = match.group(2)
                    description = match.group(3)
                    # print(f'Function Type: {function_type}, Version: {version}, Description: {description}')
                    curr_obj = FUNKTIONEN(function = function_type,
                                            version = version,
                                            description = description
                                    )
                    all_objects.append(curr_obj)        
                else :
                    raise Exception(f'Malformed inupt for FUNKTIONEN :{line}')
        return all_objects
    
    def process_param_chunk(self, chunk_liststr, type):
        processed_chunks = []  # List to store processed data chunks
        
        for ele in chunk_liststr:
            lines = ele.splitlines()
            name, size = self.get_name_size_from_first_line(lines[0], type)  

            extracted_values, extracted_multi_line_values = self.give_param_attributes(lines[1:-1])

            # Combine single line and multi-line attributes
            combined_attributes = {**extracted_values}
            for key, value in extracted_multi_line_values.items():
                # Convert the lists to appropriate types if needed (for example, float)
                if value:
                    if key == 'text':  # Handle the text attribute differently
                        combined_attributes[key] = value[0]  # Assuming there's only one text value
                    else:
                        try:
                            combined_attributes[key] = list(map(float, value))
                        except ValueError:  # Handle non-numeric values
                            combined_attributes[key] = value  

            # Adding name and size if present
            combined_attributes['name'] = name
            if size:
                combined_attributes['size'] = [int(x) for x in size]  # Convert to int or other type as required

            # Dynamically create an object based on the type
            param_class = next((cls for cls in self.all_param_classes if cls.token_string.strip() == type), None)
            if param_class:
                obj = param_class(**combined_attributes)
                processed_chunks.append(obj)
            
        return processed_chunks

    def give_param_attributes(self, lines):
        # Dictionaries to hold the extracted values
        extracted_single_line_values = {}
        extracted_multi_line_values = {key: [] for key in self.possible_multi_line_attrs.values()}

        # Processing each line
        for line in lines:  # Skip the first line as it contains the name and size

            single_match = self.single_line_attrs_keywords_pattern.search(line)
            multi_match = self.multi_line_attrs_keywords_pattern.search(line)

            if single_match:
                key = single_match.group(1).upper()  
                value = single_match.group(2)
                var_name = self.single_line_attrs[key]
                extracted_single_line_values[var_name] = value

            elif multi_match:
                key = multi_match.group(1).upper()
                value = multi_match.group(2).split()  
                var_name = self.possible_multi_line_attrs[key]
                extracted_multi_line_values[var_name].extend(value)  

        return extracted_single_line_values, extracted_multi_line_values

    def get_name_size_from_first_line (self,line,type):
        name_and_size_pattern= re.compile(rf'^{re.escape(type)}\s+([a-zA-Z0-9_\.]+)(?:\s+(\d+)(?:\s+(\d+))?)?')
        match = name_and_size_pattern.match(line)
        size = None
        if match:
            name = match.group(1)
            size1 = match.group(2)
            size2 = match.group(3)
        if not(size2 is None):
            size = [size1, size2]
        else:
            if size1:
                size = [size1]  ## this can be None for things that are size 1
        return name,size       

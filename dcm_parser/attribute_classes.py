from dataclasses import dataclass, field
from typing import List, Optional, Union, Dict, Tuple
import re
from pathlib import Path as path
from jinja2 import Environment, FileSystemLoader
from jinja2.exceptions import TemplateNotFound
import logging



# Load Jinja2 templates from a directory named 'templates'
class Tempaltes():
    env = Environment(
        loader=FileSystemLoader('./dcm_parser/templates'),
    )

def format_value(value):
    if int(value) == value:
        return '{:.0f}'.format(value)
    else:
        return '{:.4f}'.format(value)


@dataclass
class FUNKTIONEN:
    function: str
    version: str
    description: str
    token_string: str = 'FUNKTIONEN'
    extract_regex = re.compile(r'\s*FKT\s+(\w+)\s+"([^"]*)"\s+"([^"]*)"')

    def __str__(self):
        func_str = f'  FKT {self.function} "{self.version}" "{self.description}"'
        return func_str
    
@dataclass
class BaseParam(Tempaltes):
    name: str
    langname: str = ''
    funktion: str = ''
    displayname: str = ''
    einheit_w: str = ''
    values_per_line : int = 6   
    
    def __str__(self):
        try:
            # Try to get the template based on the class name
            template_name = self.__class__.__name__ + '.jinja2'
            template = self.env.get_template(template_name)
        except TemplateNotFound:
            # If not found, try to get the parent class's template
            template_name = self.__class__.__bases__[0].__name__ + '.jinja2'
            template = self.env.get_template(template_name)       
        return template.render(param=self,enumerate=enumerate,format_value=format_value)

    def _relative_difference(self,a, b):
        if a == b == 0:
            return 0
        return abs(a - b) / max(abs(a), abs(b))

    def update_from_and_report_changes(self, other: "BaseParam"):
        attributes = ['wert', 'size', 'st_x', 'st_y']
        changes = {}

        for attr in attributes:
            if hasattr(self, attr) and hasattr(other, attr):
                current_list = getattr(self, attr)
                other_list = getattr(other, attr)
                
                # Ensure both lists have the same length, else there might be structural changes.
                if len(current_list) != len(other_list):
                    changes[attr] = (current_list, other_list)
                    setattr(self, attr, other_list)
                    continue
                
                updated_list = []
                for current_value, other_value in zip(current_list, other_list):
                    # If the values are within the acceptable difference range, use the current value.
                    if self._relative_difference(current_value, other_value) < 0.01 or abs(current_value - other_value) < 0.001:
                        updated_list.append(current_value)
                    else:  # Else, use the other's value and log the change
                        updated_list.append(other_value)
                        if attr not in changes:
                            changes[attr] = ([], [])  # Initialize with empty lists
                        changes[attr][0].append(current_value)
                        changes[attr][1].append(other_value)

                setattr(self, attr, updated_list)

        return changes



    def process_wert(self,arary_values):
        '''
        Make wert into the required format
        Consider Numpy array in future
        '''
        new_wert = []
        for x in arary_values:
            try:
                value = float(x)
                new_wert.append(int(value) if value.is_integer() else round(value, 5))
            except ValueError:
                # If the conversion fails, append the original string element 
                new_wert.append(x)  # add to log later
        return new_wert
    
@dataclass 
class ParamsWithWert(BaseParam):
    wert: List[Union[str, float, int]] = field(default_factory=list)

    def __post_init__(self):
        self.wert = self.process_wert(self.wert)

@dataclass
class FESTWERT(ParamsWithWert):
    text: str = ''
    var: Optional[str] = None
    token_string: str = 'FESTWERT '

@dataclass
class FESTWERTEBLOCK(ParamsWithWert):
    size: List[int] = field(default_factory=list)
    wert: List[float] = field(default_factory=list)
    token_string: str = 'FESTWERTEBLOCK '

@dataclass
class ParamWithSTX(ParamsWithWert):
    st_x: List[Union[str, float, int]] = field(default_factory=list)

    def __post_init__(self):
        self.st_x = self.process_wert(self.st_x)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

@dataclass
class KENNLINIE(ParamWithSTX):
    size:  List[int] = field(default_factory=list)
    einheit_x: str = ''
    token_string: str = 'KENNLINIE '

@dataclass
class FESTKENNLINIE(KENNLINIE):
    token_string: str = 'FESTKENNLINIE '

@dataclass
class GRUPPENKENNLINIE(KENNLINIE):
    token_string: str = 'GRUPPENKENNLINIE '

@dataclass
class KENNFELD(ParamWithSTX):
    size : List[int] = field(default_factory=list)
    einheit_x: str = ''
    einheit_y: str = ''
    st_y: List[Union[str, float, int]] = field(default_factory=list)
    wert: List[Union[str, float, int]] = field(default_factory=lambda: [[0.]])
    token_string: str = 'KENNFELD '
    zipped_y_wert: List[tuple] = field(init=False)  # Add this line
    
    def __post_init__(self):
        self.st_y = self.process_wert(self.st_y)

@dataclass
class FESTKENNFELD(KENNFELD):
    token_string: str = 'FESTKENNFELD '

@dataclass
class GRUPPENKENNFELD(KENNFELD):
    token_string: str = 'GRUPPENKENNFELD '

@dataclass
class STUETZSTELLENVERTEILUNG(BaseParam):
    size:  List[int] = field(default_factory=list)
    einheit_x: str = ''
    st_x: List[float] = field(default_factory=list)
    token_string: str = 'STUETZSTELLENVERTEILUNG '


@dataclass
class DCMObject():
    filePath : str
    comments : str
    format_spec_version : str    # KONSERVIERUNG_FORMAT
    functions :  List[FUNKTIONEN]
    parameters: List[FESTWERT]
    parameter_block : List[FESTWERTEBLOCK]
    characteristic_curve : List[KENNLINIE]
    characteristic_curve_fixed : List[FESTKENNLINIE]
    characteristic_curve_group : List[GRUPPENKENNLINIE]
    characteristic_map : List[KENNFELD]
    characteristic_map_fixed : List[FESTKENNFELD]
    characteristic_map_group : List[GRUPPENKENNFELD]
    distribution : List[STUETZSTELLENVERTEILUNG]

    def __str__(self):
        str_repr = [
            f"* File Path: {self.filePath}",
            f"* Comments: {self.comments}",
            f"\n"
            f"KONSERVIERUNG_FORMAT {self.format_spec_version}"
            f"\n"
        ] 
        if len (self.functions)>0:
            str_repr += ['FUNKTIONEN']
            str_repr += [str(func)  for func in self.functions]        
            str_repr += ['END\n']
        str_repr += [str(param) + '\n' for param in self.parameters]
        str_repr += [str(block) + '\n' for block in self.parameter_block]
        str_repr += [str(curve) + '\n' for curve in self.characteristic_curve]
        str_repr += [str(curve) + '\n'  for curve in self.characteristic_curve_fixed]
        str_repr += [str(curve) + '\n'  for curve in self.characteristic_curve_group]
        str_repr += [str(map) + '\n'  for map in self.characteristic_map]
        str_repr += [str(map) + '\n' for map in self.characteristic_map_fixed]
        str_repr += [str(map) + '\n' for map in self.characteristic_map_group]
        str_repr += [str(dist) + '\n' for dist in self.distribution]

        return "\n".join(str_repr)
        
    def update_from(self, other: "DCMObject", ignore_list=[], logger=None):
        updated_names = []
        missing_names = []
        attributes_to_update = ['parameters', 'parameter_block', 'characteristic_curve', 'characteristic_curve_fixed',
                                'characteristic_curve_group', 'characteristic_map', 'characteristic_map_fixed',
                                'characteristic_map_group', 'distribution']

        for attr in attributes_to_update:
            self_attr = getattr(self, attr)
            other_attr = getattr(other, attr)

            # Create a dictionary for quick name-based lookup for both self and other objects
            self_name_to_obj = {obj.name: obj for obj in self_attr}
            other_name_to_obj = {obj.name: obj for obj in other_attr}

            for other_name, other_param in other_name_to_obj.items():
                # Skip the names present in the ignore list
                if other_name in ignore_list:
                    continue

                # If the parameter is found in self, then update it
                if other_name in self_name_to_obj:
                    self_param = self_name_to_obj[other_name]
                    attributes_changed = self_param.update_from_and_report_changes(other_param)
                    if attributes_changed and logger:  
                        for attribute, (original_value, updated_value) in attributes_changed.items():
                            logger.info(f"Name: {other_name}, Attribute: {attribute}, Old : {original_value}, New : {updated_value}")
                            updated_names.append(other_name)
                else:
                    missing_names.append(other_name)           

        return updated_names, missing_names


    def write(self):
        with open (self.filePath, 'w') as fdcm:
            fdcm.write(self.__str__())


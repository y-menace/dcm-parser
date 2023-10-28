import os
import re
from typing import List, Optional, Union
from pathlib import Path as path
from dataclasses import dataclass, field
from jinja2 import Environment, FileSystemLoader
from jinja2.exceptions import TemplateNotFound
from copy import deepcopy
import logging

# Load Jinja2 templates from a directory named 'templates'
class Tempaltes():
    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    TEMPLATE_DIR = os.path.join(CURRENT_DIR, 'templates')
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))

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
        attributes = ['wert', 'size', 'st_x', 'st_y']   ## only these attributes are updated
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

    def __post_init__(self):
        self._param_attributes = ['parameters', 'parameter_block', 
                        'characteristic_curve', 'characteristic_curve_fixed','characteristic_curve_group',
                        'characteristic_map', 'characteristic_map_fixed','characteristic_map_group',
                        'distribution']
        self._param_name_dict = {}
        for attr in self._param_attributes:
            items = getattr(self, attr, [])
            for item in items:
                if hasattr(item, "name"):
                    self._param_name_dict[item.name] = (item, attr)
        self.sort_parameters_by_name()

    def sort_parameters_by_name(self):
        """Sorts all parameter lists alphabetically by name."""
        for attr in self._param_attributes:
            items = getattr(self, attr, [])
            items.sort(key=lambda item: getattr(item, "name", ""))


    def remove_parameter_by_name(self, name):
        if name in self._param_name_dict:
            item, attr_name = self._param_name_dict[name]
            
            # Remove the item from the appropriate list
            attr_list = getattr(self, attr_name)
            attr_list.remove(item)

            # Delete the entry from the dictionary
            del self._param_name_dict[name]
            return True
        else:
            return False

    def __str__(self):
        str_repr = [
            f"{self.comments}\n"
            f"\nKONSERVIERUNG_FORMAT {self.format_spec_version}\n"
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


    def update_from(self, other: "DCMObject",  delete_list=[], logger=None):
        updated_names = []
        
        # Determine the set of names from the current (self) object and the other object
        self_names = set(self._param_name_dict.keys())
        other_names = set(other._param_name_dict.keys())

        # Find out what's common, missing or extra
        common_names = self_names.intersection(other_names)
        missing_names = self_names - other_names 

        # Update the attributes that are common
        for name in common_names:
            self_param, _ = self._param_name_dict[name]
            other_param, _ = other._param_name_dict[name]
            if hasattr(self_param, 'update_from_and_report_changes') and hasattr(other_param, 'update_from_and_report_changes'):
                attributes_changed = self_param.update_from_and_report_changes(other_param)
                if attributes_changed:
                    for attribute, (original_value, updated_value) in attributes_changed.items():
                        if logger:
                            logger.info(f"Name: {name}, Attribute: {attribute}, Old: {original_value}, New: {updated_value}")
                    updated_names.append(name)

        # Handle missing names (parameters that are in self but not in other)
        self._delete_elements_if_in_list(missing_names,logger)
        self._delete_elements_if_in_list(delete_list,logger,'becuase it was from a higher prio DCM.')

        return updated_names, list(missing_names)
    

    def add_new_parameters_from(self, other: "DCMObject", logger=None):
        added_names = []
        # Identify the new parameters that are in the other object but not in self
        new_names = set(other._param_name_dict.keys()) - set(self._param_name_dict.keys())
        # Add those new parameters to self
        for name in new_names:
            if name in other._param_name_dict:
                item, attr_name = other._param_name_dict[name]
                
                # Copy the item to the appropriate list in self
                attr_list = getattr(self, attr_name)

                copied_item = deepcopy(item)
                attr_list.append(copied_item)

                # Add the entry to the dictionary
                self._param_name_dict[name] = (copied_item, attr_name)
                added_names.append(name)

                # Optionally, log the additions
                if logger:
                    logger.info(f"Added parameter with Name: {name}")

        return added_names  # Return the names of the parameters that wer

    def _delete_elements_if_in_list(self,list_of_names,logger,extra_messag=''):
        for name in list_of_names:
            if self.remove_parameter_by_name(name):     
                if logger:
                    logger.info(f"Name: {name} was deleted {extra_messag}")

    def write(self):
        with open (self.filePath, 'w') as fdcm:
            fdcm.write(self.__str__())

    def cleanup_parameters(self):
        """Removes all parameters from the DCMObject."""
        for attr in self._param_attributes:
            setattr(self, attr, [])  # Set the attribute list to an empty list
        self._param_name_dict.clear()  # Clear the dictionary
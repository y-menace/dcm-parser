import os
import re
from typing import List, Optional, Union
from pathlib import Path as path
from dataclasses import dataclass, field
from jinja2 import Environment, FileSystemLoader
from jinja2.exceptions import TemplateNotFound
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

    def update_from_and_report_changes(self, other: "BaseParam",diff_mode=False):
        attributes = ['wert', 'size', 'st_x', 'st_y']   ## only these attributes are updated
        changes = {}

        for attr in attributes:
            if hasattr(self, attr) and hasattr(other, attr):
                current_list = getattr(self, attr)
                other_list = getattr(other, attr)
                
                # Ensure both lists have the same length, else there might be structural changes.
                if len(current_list) != len(other_list):                    
                    changes[attr] = (current_list, other_list)
                    if diff_mode == False:
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
                if diff_mode == False:
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

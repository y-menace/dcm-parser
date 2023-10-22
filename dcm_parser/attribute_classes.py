from dataclasses import dataclass, field
from typing import List, Optional, Union
import re
from pathlib import Path as path
from jinja2 import Environment, FileSystemLoader
from jinja2.exceptions import TemplateNotFound

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
    size: int = 1
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
    size: int = 1
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
    size: int = 1 
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
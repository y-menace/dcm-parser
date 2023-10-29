from dataclasses import dataclass
from typing import List, Union, Optional
from .attribute_classes import FUNKTIONEN, FESTWERT, FESTWERTEBLOCK, KENNLINIE, FESTKENNLINIE, GRUPPENKENNLINIE
from .attribute_classes import KENNFELD,FESTKENNFELD, GRUPPENKENNFELD, STUETZSTELLENVERTEILUNG 
from copy import deepcopy


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

    def write(self,new_pathname_for_file=None):
        if not(new_pathname_for_file):
            new_pathname_for_file = self.filePath
            
        with open (new_pathname_for_file, 'w') as fdcm:
            fdcm.write(self.__str__())

    def cleanup_parameters(self):
        """Removes all parameters from the DCMObject."""
        for attr in self._param_attributes:
            setattr(self, attr, [])  # Set the attribute list to an empty list
        self._param_name_dict.clear()  # Clear the dictionary

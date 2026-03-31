from typing import Self,Dict
from unaceba.utils.variables import VarRange

class State:
    '''
    Abstract interface for task states
    '''

    def __init__(self,state_vars:list[str],var_ranges:Dict[str,VarRange],semantic_dict:dict[str,str],values:dict=None):
        '''
        Construct a new State

        Parameters
        --------------
        values : dict (default: None)
            a dict of initial values to populate the state with, or None
        '''
        # Define variables
        self.state_vars = state_vars
        self.var_ranges = var_ranges
        self.semantic_dict = semantic_dict

        # Set values
        self.values = values
        if values is not None:
            self.set_values(values)

    '''
    VARIABLES
    '''
    def inject_variable(self,var:str,var_range:VarRange,semantic_info:str,value=None):
        if var in self.state_vars:
            raise ValueError(f"Variable {var} already in the list of state variables")
        
        self.state_vars.append(var)
        self.var_ranges[var] = var_range
        self.semantic_dict[var] = semantic_info
        self.set_value(var,value)
   
    '''
    VALUES
    '''
    def get_value(self,node:str):
        '''
        Get the value of a particular variable

        Parameters
        ----------
        node : str
            the variable we want the value of

        Output
        ---------
        value
            the value of node in the state
        '''
        return self.values[node]
    
    def set_value(self,node:str,value):
        '''
        Sets the value of a particular state variable

        Parameters
        ----------
        node : str
            the variable to set
        value
            the value to set
        '''
        if not self.var_ranges[node].is_valid(value):
            raise ValueError(f"Cannot set {node} to {value}")
        
        self.values[node] = value

    def set_values(self,values:Dict):
        '''
        Uses a dictionary to populate the values of the state

        Parameters
        ----------
        values : Dict[str,___]
            a dictionary mapping variable names to valid values
        '''
        if self.valid_state_assignment(values):
            self.values = values
        else:
            raise ValueError("Invalid values: doesn't match defined ranges")
        
    '''
    VALIDATION
    '''
    def valid_state_assignment(self,values: Dict) -> bool:
        # First, check if all keys in values match keys in self.values
        for key in values.keys():
            if key not in self.var_ranges:
                print(f"Key {key} not in range")
                return False
            
        
        # Check values for each key        
        for var in values:
            valid = self.var_ranges[var].is_valid(values[var])
            if not valid:
                print(f"Invalid value for {var}: {values[var]}")
                return False
            
        return True

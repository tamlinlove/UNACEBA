from typing import Self,Dict
from unaceba.utils.variables import VarRange

class State:
    '''
    Abstract interface for task states
    '''
    def __init__(self,values:dict=None):
        '''
        Construct a new State

        Parameters
        --------------
        values : dict (default: None)
            a dict of initial values to populate the state with, or None
        '''
        self.values = values
        if values is not None:
            self.set_values(values)

    '''
    SETUP
    '''
    @staticmethod
    def get_ranges() -> Dict[str,VarRange]:
        '''
        Return a dict mapping every variable name to a VarRange object describing the possible values

        Output
        --------
        range_dict : Dict[str,VarRange]
            dict mapping variable names to VarRange objects describing possible values of each variable
        '''
        raise NotImplementedError
    
    @staticmethod
    def state_vars() -> list[str]:
        '''
        Return a list of state vars

        Output
        --------
        vars : list[str]
            list of state vars
        '''
        raise NotImplementedError
    
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
        if not self.get_ranges()[node].is_valid(value):
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
            if key not in self.get_ranges():
                return False
            
        
        # Check values for each key        
        for var in values:
            valid = self.get_ranges()[var].is_valid(values[var])
            if not valid:
                print(f"Invalid value for {var}: {values[var]}")
                return False
            
        return True

    '''
    SEMANTIC DESCRIPTION
    '''
    def semantic_dict(self) -> dict[str,str]:
        return {var:"A state variable" for var in self.vars()}

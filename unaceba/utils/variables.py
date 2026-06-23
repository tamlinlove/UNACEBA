import typing

class VarRange:
    '''
    A class used to define the range of possible values of a variable
    '''
    def __init__(self,allow_none:bool=False):
        '''
        Constructs a VarRange object

        Parameters
        ------------
        allow_none : bool (default: False)
            if True, None will be valid
        '''
        self.range_type = "Parent Range Class"
        self.values = None
        self.allow_none = allow_none

    def __str__(self):
        return str(self.values)

    def is_valid(self,value):
        '''
        Checks if value is valid for the defined range

        Parameters
        ----------
        value : any
            the value to check

        Output:
        ----------
        valid : boolean
            True if value is valid, False otherwise
        '''
        raise NotImplementedError
    
    def is_continuous(self):
        return False
    
    def add_value(self,value):
        '''
        Adds a value to the list of allowed variable values, if possible

        Parameters
        ----------
        value : any
            the value to add
        '''
        if self.values is None:
            raise TypeError("Variable range does not allow adding values")
        self.values.append(value)



class CategoricalRange(VarRange):
    '''
    Defines the range of a variable as a finite set of elements
    '''
    def __init__(self,values:list,**kwargs):
        '''
        Constructs a CategoricalRange object

        Parameters
        -----------
        values : list
            the set of allowed elements for this range
        **kwargs
            remaining kwargs, see superclass
        '''
        super().__init__(**kwargs)
        self.range_type = "Categorical"
        if isinstance(values,list):
            self.values = values
        else:
            raise TypeError(f"{values} is not a list")
        
    def is_valid(self,value):
        '''
        Checks if value is valid for the defined range

        Parameters
        ----------
        value : any
            the value to check

        Output:
        ----------
        valid : boolean
            True if value is valid, False otherwise
        '''
        # If None is allowed, check that
        if self.allow_none and value is None:
            return True
        
        if value in self.values:
            return True
        return False



class ContinuousRange(VarRange):
    '''
    Defines the range of a variable as continuous set of values with a defined minimum and maximum
    '''
    def __init__(self,min:float,max:float,min_inclusive:bool=True,max_inclusive:bool=True,**kwargs):
        '''
        Constructs a ContinuousRange object

        Parameters
        -----------
        min : float
            the minimum value of the range
        max : float
            the maximum value of the range
        min_inclusive : bool (default: True)
            if True, the range includes min. Otherwise, the range excludes min
        max_inclusive : bool (default: True)
            if True, the range includes max. Otherwise, the range excludes max
        **kwargs
            remaining kwargs, see superclass
        '''
        super().__init__(**kwargs)
        self.range_type = "Continuous"
        try:
            min = float(min)
        except ValueError:
            raise ValueError(f"{min} is not a float")
        try:
            max = float(max)
        except ValueError:
            raise ValueError(f"{max} is not a float")
        if min >= max:
            raise ValueError(f"Minimum {min} must be strictly less than maximum {max}")
        self.min = min
        self.max = max
        self.min_inclusive = min_inclusive
        self.max_inclusive = max_inclusive

    def __str__(self):
        start_bracket = "[" if self.min_inclusive else "("
        end_bracket = "]" if self.max_inclusive else ")"
        return f"{start_bracket}{self.min}:{self.max}{end_bracket}"

    def is_valid(self,value):
        '''
        Checks if value is valid for the defined range

        Parameters
        ----------
        value : any
            the value to check

        Output
        ----------
        valid : boolean
            True if value is valid, False otherwise
        '''
        # If None is allowed, check that
        if self.allow_none and value is None:
            return True
        
        # First, check if type makes sense
        if not (isinstance(value,float) or isinstance(value,int)):
            return False
        
        # Then check if in range
        if value < self.min or value > self.max:
            return False
        
        # Check for exclusive boundaries
        if not self.min_inclusive and value == self.min:
            return False
        if not self.max_inclusive and value == self.max:
            return False
        
        # Otherwise, we're fine
        return True
    
    def is_continuous(self):
        return True
    
    def discretise(self,size:int,dec_places:int=10):
        '''
        Create a DiscretisedRange object based on this continuous range
        '''
        return DiscretisedRange(
            min=self.min,
            max=self.max,
            size=size,
            min_inclusive=self.min_inclusive,
            max_inclusive=self.max_inclusive,
            dec_places=dec_places,
            allow_none=self.allow_none
        )

class DiscretisedRange(ContinuousRange):
    '''
    Defines the range of a variable as a finite set of elements derived from regular intervals of a bounded continuous set
    '''
    def __init__(self, min:float, max:float, size:int, min_inclusive:bool=True, max_inclusive:bool=True, dec_places:int=10, **kwargs):
        '''
        Constructs a DiscretisedRange object

        Parameters
        -----------
        min : float
            the minimum value of the range
        max : float
            the maximum value of the range
        size : int
            the number of elements in the discretised list
        min_inclusive : bool (default: True)
            if True, the range includes min. Otherwise, the range excludes min
        max_inclusive : bool (default: True)
            if True, the range includes max. Otherwise, the range excludes max
        dec_places : int (default: 10)
            the number of decimal places used in rounding the discretised values
        **kwargs
            remaining kwargs, see superclass
        '''
        super().__init__(min,max,min_inclusive=min_inclusive,max_inclusive=max_inclusive,**kwargs)
        self.range_type = "DiscretisedContinuous"
        self.is_continuous = False

        if not isinstance(size,int) or size < 2:
            raise TypeError(f"{size} is not a positive integer >=2")

        self.values = self.get_values(size,dec_places=dec_places)


    def get_values(self, size:int, dec_places:int=10):
        '''
        Defines the discretised set of possible values

        Parameters
        -----------
        size : int
            the number of elements in the discretised list
        dec_places : int (default: 10)
            the number of decimal places used in rounding the discretised values

        Output
        ----------
        values : list
            a list of values representing the discretised continuous range
        '''
        gaps = size - 1
        if not self.min_inclusive:
            gaps += 1
        if not self.max_inclusive:
            gaps += 1
        step = (self.max - self.min) / gaps

        if self.min_inclusive:
            start = self.min
        else:
            start = self.min + step

        values = []
        for i in range(size):
            v = start + i * step
            values.append(round(v, dec_places))

        return values

    def is_continuous(self):
        return False

class BooleanRange(VarRange):
    '''
    Defines the range of a variable as either true or false
    '''
    def __init__(self,**kwargs):
        '''
        Constructs a BooleanRange object

        Parameters
        --------------
        **kwargs
            remaining kwargs, see superclass
        '''
        super().__init__(**kwargs)
        self.range_type = "Boolean"
        self.values = [True,False]

    def is_valid(self,value):
        '''
        Checks if value is valid for the defined range

        Parameters
        ----------
        value : any
            the value to check

        Output:
        ----------
        valid : boolean
            True if value is valid, False otherwise
        '''
        # If None is allowed, check that
        if self.allow_none and value is None:
            return True
        
        if isinstance(value,bool):
            return True
        return False



class AnyRange(VarRange):
    '''
    Defines the range of a variable as any value, possibly constrained to a particular type
    '''
    def __init__(self,var_type:typing.Type=None,allow_none:bool=True,**kwargs):
        '''
        Constructs an AnyRange object

        Parameters
        ----------
        var_type : Type (default: None) 
            if None, any type is allowed. Otherwise, a specific type like int, str, etc.
        allow_none : bool (default: True)
            if True, None will be valid
        **kwargs
            remaining kwargs, see superclass
        '''
        super().__init__(allow_none=allow_none)
        self.range_type = "Any"
        self.var_type = var_type

    def __str__(self):
        return f"Any {self.var_type}"

    def is_valid(self,value):
        '''
        Checks if value is valid for the defined range

        Parameters
        ----------
        value : any
            the value to check

        Output:
        ----------
        valid : boolean
            True if value is valid, False otherwise
        '''
        
        # If None is allowed, check that
        if self.allow_none and value is None:
            return True
        
        # Allow anything if no vartype specified
        if self.var_type is None:
            return True
        
        # If vartype specified, only allow variables of that type
        if isinstance(value,self.var_type):
            return True
        
        # If None is allowed, we make an exception for that
        if self.allow_none and value is None:
            return True

        return False
    
class IntRange(VarRange):
    '''
    Defines the range of a variable as a range of integers between min and max
    '''
    def __init__(self,min:int,max:int,min_inclusive:bool=True,max_inclusive:bool=True,**kwargs):
        '''
        Constructs an IntRange object

        Parameters
        -----------
        min : int
            the minimum value of the range
        max : int
            the maximum value of the range
        min_inclusive : bool (default: True)
            if True, the range includes min. Otherwise, the range excludes min
        max_inclusive : bool (default: True)
            if True, the range includes max. Otherwise, the range excludes max
        **kwargs
            remaining kwargs, see superclass
        '''
        super().__init__(**kwargs)
        self.range_type = "IntegerInterval"

        if not isinstance(min,int):
            raise ValueError(f"{min} is not an int")
        if not isinstance(max,int):
            raise ValueError(f"{max} is not an int")
        if min >= max:
            raise ValueError(f"Minimum {min} must be strictly less than maximum {max}")
        
        # Exclude rare edge case
        if max - min == 1 and not min_inclusive and not max_inclusive:
            raise ValueError(f"Range is an empty set")

        self.min = min
        self.max = max
        self.min_inclusive = min_inclusive
        self.max_inclusive = max_inclusive

        # Create values
        min_val = self.min
        max_val = self.max
        if not self.min_inclusive:
            min_val += 1
        if not self.max_inclusive:
            max_val -= min_inclusive
        self.values = list(range(min_val, max_val + 1))

    def __str__(self):
        start_bracket = "[" if self.min_inclusive else "("
        end_bracket = "]" if self.max_inclusive else ")"
        return f"Integer {start_bracket}{self.min}:{self.max}{end_bracket}"

    def is_valid(self,value):
        '''
        Checks if value is valid for the defined range

        Parameters
        ----------
        value : any
            the value to check

        Output
        ----------
        valid : boolean
            True if value is valid, False otherwise
        '''
        # If None is allowed, check that
        if self.allow_none and value is None:
            return True

        # First, check if type makes sense
        if not isinstance(value,int):
            return False
        
        # Then check if in range
        if value < self.min or value > self.max:
            return False
        
        # Check for exclusive boundaries
        if not self.min_inclusive and value == self.min:
            return False
        if not self.max_inclusive and value == self.max:
            return False
        
        # Otherwise, we're fine
        return True
    
class NormalisedFloatRange(ContinuousRange):
    '''
    Defines the range of a variable as continuous set of values between and including 0 and 1
    '''
    def __init__(self,**kwargs):
        '''
        Constructs a NormalisedFloatRange object

        Parameters
        ------------
        **kwargs
            remaining kwargs, see superclass
        '''
        super().__init__(0, 1, **kwargs)
        self.range_type = "NormalisedFloat"
import py_trees

class LogNode:
    '''
    Class for a LogNode that mimics a behaviour tree node, in order to create a parallel log tree
    '''
    def __init__(self,behaviour:py_trees.behaviour.Behaviour,category:str):
        '''
        Creates a LogNode

        Parameters
        -----------
        behaviour : py_trees.behaviour.Behaviour
            the behaviour to log
        category : str
            the type of BT node e.g. Action, Condition, Sequence, Fallback
        '''
        self.name = behaviour.name
        self.category = category
        self.status = py_trees.common.Status.INVALID
        self.behaviour_class = behaviour.__class__.__name__
        self.behaviour_module = behaviour.__class__.__module__
        self.description = self.get_semantic_info(behaviour)

        if not self.is_leaf():
            self.memory = behaviour.memory

        self.tick = 0
        self.time = 0

    def to_dict(self) -> dict:
        return {
            "name":self.name,
            "category":self.category,
            "status":str(self.status),
        }
    
    def info_dict(self) -> dict:
        if self.is_leaf():
            return {
                "name":self.name,
                "category":self.category,
                "description":self.description,
                "class":self.behaviour_class,
                "module":self.behaviour_module
            }
        else:
            return {
                "name":self.name,
                "category":self.category,
                "memory":self.memory,
                "children":[]
            }
        
    def status_dict(self) -> dict:
        return {
                "name":self.name,
                "status":str(self.status)
            }
    
    def is_leaf(self):
        return self.category in ["Action","Condition"]
    
    def update_time(self,tick:int,time:int):
        self.tick = tick
        self.time = time

    def get_semantic_info(self,behaviour:py_trees.behaviour.Behaviour) -> str:
        if self.is_leaf():
            return behaviour.semantic_description()
        elif self.category == "Sequence":
            return "A sequence node"
        elif self.category == "Fallback":
            return "A fallback node"
        else:
            raise TypeError(f"Unrecognised type of behaviour: {type(behaviour)}")
            
from unaceba.explainer.explainer import Explainer
from unaceba.explainer.explanation_model import EXECUTION_CATEGORY,STATE_CATEGORY,RETURN_CATEGORY
from unaceba.explainer.query import Query

import copy
from rclpy.node import Node

class QueryManager:
    def __init__(self,explainer:Explainer,ros_node:Node=None):
        self.explainer = explainer
        self.ros_node = ros_node
        self.query_class = Query

    '''
    DEBUGGING
    '''
    def log(self,text:str):
        if self.ros_node is None:
            print(text)
        else:
            self.ros_node.get_logger().info(str(text))

    '''
    QUERIES
    '''
    def make_single_var_query(
            self,
            name:str,
            category:str,
            tick:int,
            time:int,
            foils:list=None,
    ) -> Query:
        # Get the state of the model at the timestep
        model_state = self.explainer.explanation_model.model_state_at_timestep(timestep_tick=tick,timestep_time=time)

        # Get the right variable name
        if category == EXECUTION_CATEGORY:
            node = self.explainer.explanation_model.executions[name]
        elif category == RETURN_CATEGORY:
            node = self.explainer.explanation_model.returns[name]
        elif category == STATE_CATEGORY:
            var_timestep = self.explainer.explanation_model.get_temporal_index_at_timestep(tick,time)
            node = self.explainer.explanation_model.temporal_state_vars[name][var_timestep]
        else:
            # Oops, shouldn't be here
            raise ValueError(f"No category {category}, must be one of {EXECUTION_CATEGORY}, {RETURN_CATEGORY} or {STATE_CATEGORY}")
        
        query_foils = {node:foils}

        # Create the query object
        query = self.create_query(query_foils,model_state)
        return query

    def create_query(self,foils:dict[str,list],model_state:dict) -> Query:
        proper_foil:dict[str,list] = {}

        for foil_var in foils:
            # First of all, validate the variables
            if foil_var not in self.explainer.explanation_model.explanation_graph.nodes:
                raise ValueError(f"Unrecognised foil variable {foil_var} in query")
            
            var_range = self.explainer.explanation_model.var_ranges[foil_var]

            if foils[foil_var] is not None:
                # Specific values have been provided
                for foil_var_val in foils[foil_var]:
                    if not var_range.is_valid(foil_var_val):
                        raise ValueError(f"Invalid value {foil_var_val} for foil variable {foil_var}")
                    if foil_var_val == model_state[foil_var]:
                        raise ValueError(f"Cannot use value {foil_var_val} for foil variable {foil_var} as it is the real value")
                    proper_foil[foil_var] = foils[foil_var]
                    
            else:
                # No foil values provided, will use all except real value
                proper_foil[foil_var] = copy.deepcopy(var_range.values)

            # Make sure the real value is not a valid foil
            real_var_val = model_state[foil_var]
            if real_var_val in proper_foil[foil_var]:
                proper_foil[foil_var].remove(real_var_val)

        return self.query_class(proper_foil,self.explainer.explanation_model,model_state=model_state)
import networkx as nx
from networkx.drawing.nx_pydot import graphviz_layout
import matplotlib.pyplot as plt
import copy

from collections.abc import Callable
from typing import List,Dict,Self

from unaceba.task.state import State
from unaceba.explainer.task_model import StateModel

CATEGORIES = ["Execution","Return","State"]

class CausalNode:
    def __init__(
            self,
            name:str,
            values:list,
            value,
            func:Callable,
            category:str
    ):
        '''
        Creates a CausalNode

        Parameters
        ----------
        name : str
            the name of the node
        values : list
            the possible values the node can take
        value
            the specific value of the node
        func : Callable
            the function associated with the node in the causal model
            valid functions must take only a State object as argument
        category : str
            the type of node, from the BTCM formalism - see CATEGORIES list
        '''
        self.name = name
        self.values = values
        self.func = func
        self.value = value
        self.category = category

    def run(self,state:State):
        return self.func(state=state)
    
class CausalModel:
    '''
    Class for a causal Explanation Model that represents a BT and Environment
    '''
    def __init__(self,state_model:StateModel):
        self.nodes:Dict[str,CausalNode] = {}
        self.graph = nx.DiGraph()
        self.state_model = state_model

    '''
    GRAPH OPERATIONS
    '''

    def add_node(self,node:CausalNode):
        self.nodes[node.name] = node
        self.graph.add_node(node.name)

    def add_nodes(self,nodes:List[CausalNode]):
        for node in nodes:
            self.add_node(node)

    def add_edge(self,edge:tuple[str,str]):
        if edge[0] in self.nodes and edge[1] in self.nodes:
            if not (edge in self.graph.edges):
                self.graph.add_edge(edge[0],edge[1])
        else:
            raise ValueError("Nodes described by edge must be added to causal model before edge")
        
    def add_edges(self,edges:list[tuple[str,str]]):
        for edge in edges:
            self.add_edge(edge)

    def parents(self,node:str):
        return list(self.graph.predecessors(node))
    
    '''
    CAUSAL OPERATIONS
    '''
    def value_dict(self) -> dict:
        '''
        Returns a dict that maps node names to values
        '''
        val_dict = {}
        for node in self.nodes:
            val_dict[node] = self.nodes[node].value
        return val_dict
    
    def propagation_order(self,nodes:list[str],graph:nx.DiGraph) -> list[str]:
        '''
        Get order for propagation, ignoring nodes that do not descend from intervened nodes

        Parameters
        ---------
        nodes : list[str]
            the nodes being intervened on
        graph : nx.DiGraph
            the graph over which we propagate interventions
        '''
        order = nx.topological_sort(graph)
        reduced_order = []
        for node in order:
            ancestors = nx.ancestors(graph,node)
            for inode in nodes:
                if inode in ancestors:
                    reduced_order.append(node)
                    break
        return reduced_order
    
    def propagate_interventions(self,order:list[str],state:State) -> None:
        '''
        Propagate interventions throughout the causal model, given an order of effects

        Parameters
        -----------
        order : list[str]
            the order in which functions are run
        state : State
            the counterfactual state that is affected by the interventions
        '''
        for node in order:
            new_val = self.state_model.run(node,state)
            state.set_value(node,new_val)

    def intervene(self,state:State,interventions:dict,search_graph:nx.DiGraph) -> tuple[nx.DiGraph,State]:
        '''
        Perform interventions on a causal model

        Parameters
        -------------
        state : State
            the state to be intervened on
        interventions : dict
            dict mapping node names to intervention values - these are the nodes being intervened on
        search_graph : nx.DiGraph
            the graph over which interventions are being performed

        Output
        ------------
        new_graph : nx.DiGraph
            the edited graph after the Do operator has been performed on the nodes in interventions
        new_state : State
            the updated state (a copy) reflecting the performed interventions
        '''
        # Validate
        for node in interventions:
            if node not in self.nodes:
                raise ValueError(f"Unrecognised node {node}")
            
            if interventions[node] not in self.nodes[node].values:
                raise ValueError(f"Invalid value {interventions[node]} for node {node}")
            
        
        # Copy
        new_graph = nx.DiGraph(search_graph)
        new_state = self.state_model.copy_state(state)
        
        for node in interventions:
            # Remove parents
            for parent in self.parents(node):
                # Check if parent has already been removed e.g. for variables that are not allowed to be intervened on
                if parent in new_graph.nodes:
                    new_graph.remove_edge(parent,node)

            # Set new values
            new_state.set_value(node,interventions[node])

        # Propagate changes throughout model
        order = self.propagation_order(list(interventions.keys()),new_graph)
        self.propagate_interventions(order,new_state)

        return new_graph,new_state
    
    '''
    VISUALISE
    '''
    def visualise(
            self,
            state:State,
            graph:nx.DiGraph=None,
            nodes:dict=None,
            node_names:Dict[str,str]=None,
            label_dict:dict=None,
            colours:dict=None
        ):
        if graph is None:
            graph = self.graph

        if nodes is None:
            nodes = self.nodes
        else:
            # Replace graph with only nodes from nodes
            graph = copy.deepcopy(graph)
            graph.remove_nodes_from(graph.nodes()-list(nodes.keys()))
        
        if label_dict is None:
            if node_names is None:
                label_dict = {nodes[node].name: f"{nodes[node].name} = {state.get_value(nodes[node].name)}" for node in nodes}
            else:
                label_dict = {nodes[node].name: f"{node_names[node]} = {state.get_value(nodes[node].name)}" for node in nodes}

        if colours is None:
            colour_list = ["cyan" for node in nodes]
        else:
            colour_list = []
            for node in graph.nodes:
                if node in colours:
                    colour_list.append(colours[node])
                else:
                    colour_list.append("cyan")        

        pos = graphviz_layout(graph, prog="dot")
        nx.draw_networkx_nodes(graph, pos, node_size = 500, node_color=colour_list)
        nx.draw_networkx_labels(graph, pos, labels=label_dict)
        nx.draw_networkx_edges(graph, pos, edgelist= graph.edges, arrows=True)
        plt.show()
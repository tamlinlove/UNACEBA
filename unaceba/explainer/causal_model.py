import networkx as nx
from networkx.drawing.nx_pydot import graphviz_layout
import matplotlib.pyplot as plt
import copy

from collections.abc import Callable
from typing import TYPE_CHECKING, List, Dict
if TYPE_CHECKING:
    from typing import Self
else:
    try:
        from typing import Self
    except ImportError:
        from typing_extensions import Self
from rclpy.node import Node

from unaceba.task.state import State
from unaceba.explainer.task_model import TaskModel

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

    def __str__(self):
        return f"CausalNode: {self.name}"

    def run(self,state:State,model_state:dict):
        return self.func(state=state,model_state=model_state)
    
class CausalModel:
    '''
    Class for a causal Explanation Model that represents a BT and Environment
    '''
    def __init__(self,state_model:TaskModel,ros_node:Node=None):
        self.nodes:Dict[str,CausalNode] = {}
        self.state_model = state_model
        self.ros_node = ros_node
        self.graph = nx.DiGraph()
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
            if edge[0] not in self.nodes:
                raise ValueError(f"Node {edge[0]} must be added to graph before edge {edge[0]}->{edge[1]} can be added")
            else:
                raise ValueError(f"Node {edge[1]} must be added to graph before edge {edge[0]}->{edge[1]} can be added")
        
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
    
    def propagate_interventions(
            self,
            order:list[str],
            model_state:dict[str],
            state_var_names:dict[str,str]
    ) -> None:
        for node in order:
            # First of all, make a state at the relevant time of the variable function being run
            node_parents = self.parents(node)
            state_vals = {
                state_var_names[parent]:model_state[parent] for parent in node_parents if parent in state_var_names
            }
            state = self.state_model.make_state(state_vals)

            # # DEBUGGING
            # self.log("======================")
            # self.log(f"Propagating to {node}")
            # self.log(f"Node {node} has parents {node_parents}")
            # for par in node_parents:
            #     self.log(f"Model_state[{par}] = {model_state[par]}")
            # self.log(f"CM State: {state.values}")

            # Run the relevant function for the node
            new_val = self.nodes[node].run(state,model_state)

            # self.log(f"New value for {node} is {new_val}")

            # Update model state
            model_state[node] = new_val

    def intervene(
            self,
            interventions:dict[str],
            search_graph:nx.DiGraph,
            model_state:dict[str],
            state_var_names:dict[str,str]
    ) -> tuple[nx.DiGraph,dict[str]]:
        # Copy before intervening
        new_graph = nx.DiGraph(search_graph)
        new_model_state = copy.deepcopy(model_state)

        # Do operator - cut incoming edges
        for ivar in interventions:
            for parent in self.parents(ivar):
                if parent in new_graph.nodes:
                    new_graph.remove_edge(parent,ivar)

            # Apply values
            new_model_state[ivar] = interventions[ivar]
        

        # Propagate changes through the graph
        order = self.propagation_order(list(interventions.keys()),new_graph)
        self.propagate_interventions(order,new_model_state,state_var_names)

        return new_graph,new_model_state
    
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

    '''
    DEBUGGING
    '''
    def log(self,text:str):
        if self.ros_node is None:
            print(text)
        else:
            self.ros_node.get_logger().info(str(text))

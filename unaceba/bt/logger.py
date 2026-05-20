import py_trees
import networkx as nx
import json
import copy
from pathlib import Path
from typing import Dict

from unaceba.bt.nodes import ActionNode,ConditionNode
from unaceba.bt.rosnodes import RosActionNode, RosConditionNode
from unaceba.bt.log_node import LogNode


class Logger(py_trees.visitors.VisitorBase):
    def __init__(self, tree:py_trees.trees.BehaviourTree, filename:str="log", log_env:bool=True, full:bool=False):
        '''
        Logger visitor for UNACEBA BT framework

        Parameters
        ------------
        tree : py_trees.trees.BehaviourTree
            the BT to log
        filename : str (default: "log")
            the name of the file to log to -> will save to <filename>.json
        log_env : bool (default: True)
            if True, logs environment information as well
        full : bool (default: False)
            py_trees parameter, if True logs the whole tree, if False only logs visited nodes
        '''
        super().__init__(full)

        self.tick = 0 # The current tick iteration
        self.time = 0 # The current timestep which increments after each leaf execution

        self.root = None # The root of the tree, for visualisation
        self.tree = tree # Points to the tree itself
        self.node_name_counts = {} # Counts the number of nodes with the same name

        self.log_env = log_env # Whether to register the environment in the log

        # Create dict of tree nodes and types
        self.make_tree(tree)

        # Setup board
        self.board = py_trees.blackboard.Client(name="LoggerBoard")
        self.board.register_key("state", access=py_trees.common.Access.READ)
        if self.log_env:
            self.board.register_key("environment", access=py_trees.common.Access.READ)

        # Log Dictionary to be saved
        self.log_dict = {}

        # Log file
        self.logfile = f"{filename}.json"

        # Initialise log
        self.log_structure()
        self.log(None)

    '''
    TREE STATE FUNCTIONS
    '''
    def make_tree(self,tree:py_trees.trees.BehaviourTree):
        self.nodes: Dict[str,LogNode] = {}
        self.graph = nx.DiGraph()
        self.ranges = {}
        self.var_funcs = {}

        self.add_to_tree(tree.root)

    def add_to_tree(self,btnode:py_trees.behaviour.Behaviour):
        # Get node category
        if isinstance(btnode,ActionNode) or isinstance(btnode,RosActionNode):
            category = "Action"
        elif isinstance(btnode,ConditionNode) or isinstance(btnode,RosConditionNode):
            category = "Condition"
        elif isinstance(btnode,py_trees.composites.Sequence):
            category = "Sequence"
        elif isinstance(btnode,py_trees.composites.Selector):
            category = "Fallback"
        else:
            raise TypeError(f"Unsuported behaviour of type {type(btnode)}")
        
        # Count number of nodes with the same name
        if btnode.name in self.node_name_counts:
            self.node_name_counts[btnode.name] += 1
            btnode.name = f"{btnode.name}{self.node_name_counts[btnode.name]}"
        else:
            self.node_name_counts[btnode.name] = 1

        # Add node to structure
        self.nodes[btnode.id] = LogNode(behaviour=btnode,category=category)

        # Link BT node with LogNode
        if self.nodes[btnode.id].is_leaf():
            btnode.add_log_node(self.nodes[btnode.id])

        # Add node to graph
        self.graph.add_node(btnode.id)

        # Recursively add children
        for child in btnode.children:
            self.add_to_tree(child)
            # Add child edge to structure
            self.graph.add_edge(btnode.id,child.id)

    '''
    VISITOR FUNCTIONS
    '''
    def initialise(self) -> None:
        self.root = None

    def run(self, behaviour: py_trees.behaviour.Behaviour):
        # Runs as each behaviour is ticked
        self.root = behaviour

        # Update stored behaviours
        self.nodes[behaviour.id].status = behaviour.status

        
        # Update time
        self.time += 1
        if self.nodes[behaviour.id].is_leaf():
            # Leaf node, update time
            self.nodes[behaviour.id].update_time(self.tick,self.time)

        # Log
        self.log(behaviour)
        
    def log_structure(self):
        # Log Tree Structure
        self.log_dict["tree"] = {}
        for node in self.nodes:
            self.log_dict["tree"][str(node)] = self.nodes[node].info_dict()

        for edge in self.graph.edges:
            self.log_dict["tree"][str(edge[0])]["children"].append(str(edge[1]))

        # Log State Information
        self.log_dict["state"] = {
            "variables":self.board.state.semantic_dict,
            "class":self.board.state.__class__.__name__,
            "module":self.board.state.__class__.__module__,
        }

        # Log Environment Information
        if self.log_env:
            self.log_dict["environment"] = {
                "class":self.board.environment.__class__.__name__,
                "module":self.board.environment.__class__.__module__,
            }

    def log(self,behaviour:py_trees.behaviour.Behaviour):
        if str(self.tick) in self.log_dict:
            self.log_dict[str(self.tick)][str(self.time)] = {}
        else:
            self.log_dict[str(self.tick)] = {
                str(self.time):{}
            }

        # Log node status and action
        if behaviour is not None:
            self.log_behaviour(behaviour=behaviour)

        # Log new state
        self.log_dict[str(self.tick)][str(self.time)]["state"] = copy.deepcopy(self.board.state.values)

        # Save log to file
        self.save_log()

    def log_behaviour(self,behaviour: py_trees.behaviour.Behaviour):
        self.log_dict[str(self.tick)][str(self.time)]["update"] = {
            str(behaviour.id):copy.deepcopy(self.nodes[behaviour.id].status_dict())
        }

    def save_log(self):
        Path(self.logfile).parent.mkdir(exist_ok=True, parents=True)
        with open(self.logfile, 'w') as f:
            json.dump(self.log_dict, f, indent=4)

    def reconstruct_tree_state(self):
        # Given the known states of all terminated nodes, reconstruct the full state of the tree
        self.print_behaviour_status(self.tree.root)

    def print_behaviour_status(self,behaviour: py_trees.behaviour.Behaviour):
        print(behaviour.name,behaviour.status.value)
        for child in behaviour.children:
            self.print_behaviour_status(child)

    def finalise(self) -> None:
        # Runs after each tick of the tree
        self.tick += 1
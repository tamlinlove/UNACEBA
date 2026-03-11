# Class for loading episodic memory used to construct and populate explanation model
import json
import networkx as nx
import matplotlib.pyplot as plt
import py_trees
import importlib
from typing import Self

class MemoryNode:
    def __init__(self,id:str,name:str,category:str,behaviour:py_trees.behaviour.Behaviour=None,memory:bool=None):
        self.id = id
        self.name = name
        self.parent = None
        self.category = category
        if self.category in ["Action","Condition"]:
            if behaviour is None:
                raise ValueError("Behaviour must be specified for a leaf node")
            self.behaviour = behaviour
            self.children = None
        elif self.category in ["Sequence","Fallback"]:
            if memory is None:
                raise ValueError("Memory must be specified for a composite node")
            self.memory = memory
            self.children = []
        else:
            raise ValueError(f"Unrecognised category {category}")
        
    def __str__(self):
        if self.category in self.category in ["Sequence","Fallback"]:
            return f"{self.name}:{self.category} ({[child.name for child in self.children]})"
        return f"{self.name}:{self.category}"
    
    def add_child(self,child:Self):
        self.children.append(child)
        child.parent = self

class EpisodicMemory:
    def __init__(
            self,
            filepath:str
    ):
        '''
        Creates the episodic memory from the specified file
        '''
        # Read file
        with open(filepath, 'r') as file:
            self.data = json.load(file)

        # Reconstruct tree
        self.tree_graph,self.bt_nodes = self.reconstruct_tree_graph(self.data["tree"])


    '''
    RECONSTRUCTION
    '''
    def reconstruct_tree_graph(self,tree_data:dict) -> tuple[nx.DiGraph,dict]:
        graph = nx.DiGraph()
        btnodes = {}
        name_counts = {}

        # Create Nodes
        for node in tree_data:
            graph.add_node(node)
            node_data = tree_data[node]

            name = node_data["name"]
            if name not in name_counts:
                name_counts[name] = 0
            else:
                name_counts[name] += 1
            name = f"{name}_{name_counts[name]}" 

            category = node_data["category"]

            if category in ["Action","Condition"]:
                module = importlib.import_module(node_data["module"])
                cls = getattr(module, node_data["class"])
                behaviour = cls()

                btnodes[node] = MemoryNode(node,name,category,behaviour=behaviour)
            elif category in ["Sequence","Fallback"]:
                memory = node_data["memory"]

                btnodes[node] = MemoryNode(node,name,category,memory=memory)

        # Create edges
        edges = []
        for node in tree_data:
            graph.add_node(node)
            if "children" in tree_data[node]:
                for child in tree_data[node]["children"]:
                    edges.append((node,child))
                    btnodes[node].add_child(btnodes[child])
        graph.add_edges_from(edges)

        return graph,btnodes



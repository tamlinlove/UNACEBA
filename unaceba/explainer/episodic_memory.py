# Class for loading episodic memory used to construct and populate explanation model
import json
import networkx as nx
import matplotlib.pyplot as plt
import py_trees
import importlib
from typing import Self,List,Dict

class MemoryNode:
    def __init__(self,id:str,name:str,category:str,behaviour:py_trees.behaviour.Behaviour=None,memory:bool=None):
        self.id = id
        self.name = name
        self.parent:Self = None
        self.category = category
        if self.is_leaf():
            if behaviour is None:
                raise ValueError("Behaviour must be specified for a leaf node")
            self.behaviour = behaviour
            self.children = None
        elif self.is_composite():
            if memory is None:
                raise ValueError("Memory must be specified for a composite node")
            self.memory = memory
            self.children:List[Self] = []
        else:
            raise ValueError(f"Unrecognised category {category}")
        
    def __str__(self):
        if self.category in self.category in ["Sequence","Fallback"]:
            return f"{self.name}:{self.category} ({[child.name for child in self.children]})"
        return f"{self.name}:{self.category}"
    
    def add_child(self,child:Self):
        self.children.append(child)
        child.parent = self

    '''
    UTILITY
    '''
    def is_root(self):
        return self.parent is None

    def is_leaf(self):
        return self.category in ["Action","Condition"]
    
    def is_action_node(self):
        return self.category == "Action"
    
    def is_condition_node(self):
        return self.category == "Condition"
    
    def is_composite(self):
        return self.category in ["Sequence","Fallback"]
    
    def is_sequence(self):
        return self.category == "Sequence"
    
    def is_fallback(self):
        return self.category == "Fallback"
    
    def child_index(self):
        '''
        Return the index of this node in the list of its parent's children
        '''
        return self.parent.children.index(self)
    
    def is_leftmost_child(self):
        return self.child_index() == 0
    
    def left_sibling(self):
        '''
        Returns the left sibling of the current node, or None if the node is the leftmost child of its parents
        '''
        index = self.child_index()
        if index > 0:
            return self.parent.children[index-1]
        return None


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
        self.root,self.btnodes,self.node_name_to_ids = self.reconstruct_tree_graph(self.data["tree"])

        # Leaf nodes
        self.ordered_nodes = self.calculate_node_order()
        self.ordered_leaf_nodes = [node_id for node_id in self.btnodes if self.btnodes[node_id].is_leaf()]


    '''
    RECONSTRUCTION
    '''
    def reconstruct_tree_graph(self,tree_data:dict) -> tuple[str,Dict[str,MemoryNode],Dict[str,int]]:
        btnodes = {}
        node_names = {}

        # Create Nodes
        for node in tree_data:
            node_data = tree_data[node]

            name = node_data["name"]
            if name not in node_names:
                node_names[name] = []
            name_num = f"{name}_{len(node_names[name])}"
            node_names[name].append(node)

            category = node_data["category"]

            if category in ["Action","Condition"]:
                module = importlib.import_module(node_data["module"])
                cls = getattr(module, node_data["class"])
                behaviour = cls()

                btnodes[node] = MemoryNode(node,name_num,category,behaviour=behaviour)
            elif category in ["Sequence","Fallback"]:
                memory = node_data["memory"]

                btnodes[node] = MemoryNode(node,name_num,category,memory=memory)

        # Create edges
        for node in tree_data:
            if "children" in tree_data[node]:
                for child in tree_data[node]["children"]:
                    btnodes[node].add_child(btnodes[child])

        # Find root
        root = None
        for node_id in btnodes:
            if btnodes[node_id].is_root():
                root = node_id
                break

        return root,btnodes,node_names

    '''
    GRAPH OPERATIONS
    '''
    def calculate_node_order(self) -> list[str]:
        ordered_ids = []

        def traverse(current_id):
            ordered_ids.append(current_id)
            
            node_obj = self.btnodes[current_id]
            
            if node_obj and node_obj.children:
                for child in node_obj.children:
                    traverse(child.id)

        traverse(self.root)
        return ordered_ids



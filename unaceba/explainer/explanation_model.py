from unaceba.explainer.episodic_memory import EpisodicMemory,MemoryNode
from unaceba.explainer.task_model import TaskModel
from unaceba.bt.nodes import LeafNode

import networkx as nx
import matplotlib.pyplot as plt
from typing import Dict

EXECUTION_CATEGORY = "Execution"
RETURN_CATEGORY = "Return"
STATE_CATEGORY = "State"

class ExplanationModelNode:
    def __init__(self,node_id:str,node_name:str,category:str):
        self.id = node_id
        self.name = node_name
        self.category = category

    @classmethod
    def node_from_bt(cls,btnode:MemoryNode,category:str):
        node_id = f"{category}_{btnode.id}"
        node_name = f"{category}_{btnode.name}"

        if category not in [EXECUTION_CATEGORY,RETURN_CATEGORY]:
            raise ValueError(f"Invalid category {category} for node {btnode}")

        return cls(node_id,node_name,category)

    @classmethod
    def node_from_state(cls,var:str,index:int):
        node_id = f"{var}_t{index}"
        node_name = f"{var}_t{index}"

        return cls(node_id,node_name,STATE_CATEGORY)

class ExplanationModel:
    def __init__(
            self,
            episodic_memory:EpisodicMemory,
            task_model:TaskModel
    ):
        '''
        Creates the explanation model combining BT structure and the task model
        '''
        self.em = episodic_memory
        self.tm = task_model

        # Create explanation model structure
        self.nodes:Dict[str,ExplanationModelNode] = {}
        self.executions:Dict[str,str] = {}
        self.returns:Dict[str,str] = {}
        self.explanation_graph = self.create_graph_from_bt(
            nodes=self.nodes,
            executions=self.executions,
            returns=self.returns
        )

        self.btnode_times = self.assign_times_to_bt_nodes()

        self.temporal_state_vars:Dict[str,str] = {}
        self.explanation_graph = self.add_states_to_graph(
            graph=self.explanation_graph,
            nodes=self.nodes,
            executions=self.executions,
            returns=self.returns,
            temporal_state_vars=self.temporal_state_vars
        )

        self.visualise_explanation_graph()

    '''
    EXPLANATION GRAPH
    '''
    def create_graph_from_bt(
            self,
            nodes:Dict[str,ExplanationModelNode],
            executions:dict[str,str],
            returns:dict[str,str],
        ) -> nx.DiGraph:
        graph = nx.DiGraph()

        # Start by creating nodes for every bt node
        for btnode_id in self.em.btnodes:
            btnode:MemoryNode = self.em.btnodes[btnode_id]

            execution_node = ExplanationModelNode.node_from_bt(btnode=btnode,category=EXECUTION_CATEGORY)
            nodes[execution_node.id] = execution_node
            executions[btnode_id] = execution_node.id
            graph.add_node(execution_node.id)

            return_node = ExplanationModelNode.node_from_bt(btnode=btnode,category=RETURN_CATEGORY)
            nodes[return_node.id] = return_node
            returns[btnode_id] = return_node.id
            graph.add_node(return_node.id)

        # Add edges
        for btnode_id in self.em.btnodes:
            btnode:MemoryNode = self.em.btnodes[btnode_id]

            # Add return edge
            graph.add_edge(executions[btnode.id],returns[btnode.id])
            if btnode.is_composite():
                for child in btnode.children:
                    graph.add_edge(returns[child.id],returns[btnode.id])

            # Add execution edge
            if not btnode.is_root():
                if btnode.is_leftmost_child():
                    graph.add_edge(executions[btnode.parent.id],executions[btnode.id])
                else:
                    left_sibling = btnode.left_sibling()
                    graph.add_edge(returns[left_sibling.id],executions[btnode.id])

        return graph
    
    def assign_times_to_bt_nodes(self) -> dict[str,int]:
        temporalities = {}
        i = 0
        for node_id in self.em.ordered_nodes:
            if self.em.btnodes[node_id].is_leaf():
                temporalities[node_id] = i
                i += 1
        return temporalities


    
    def add_states_to_graph(
        self,
        graph:nx.DiGraph,
        nodes:Dict[str,ExplanationModelNode],
        executions:dict[str,str],
        returns:dict[str,str],
        temporal_state_vars:dict[str,str]
    ) -> nx.DiGraph:
        
        # Create a temporal state at each timestep
        num_timesteps = len(self.em.ordered_leaf_nodes)+1
        for var in self.tm.state_vars():
            temporal_state_vars[var] = []
            for t in range(num_timesteps):
                temporal_state_var = ExplanationModelNode.node_from_state(var,t)
                temporal_state_vars[var].append(temporal_state_var.id)
                nodes[temporal_state_var.id] = temporal_state_var

        # Add edges
        for t in range(num_timesteps):
            # Create causal links within a single timestep
            for edge in self.tm.cm_edges():
                e0 = temporal_state_vars[edge[0]][t]
                e1 = temporal_state_vars[edge[1]][t]
                graph.add_edge(e0,e1)

        for leaf_id in self.em.ordered_leaf_nodes:
            behaviour:LeafNode = self.em.btnodes[leaf_id].behaviour

            '''
            TODO: Instead of using input_variables and output_variables, use a combined list that includes the environmental dynamics included in the task model
            '''

            # Leaf input nodes
            for input_var in behaviour.input_variables():
                temporal_input_var = temporal_state_vars[input_var][self.btnode_times[leaf_id]]
                graph.add_edge(temporal_input_var,returns[leaf_id])

            # Leaf output nodes
            for output_var in behaviour.output_variables():
                temporal_output_var = temporal_state_vars[output_var][self.btnode_times[leaf_id]+1]
                graph.add_edge(executions[leaf_id],temporal_output_var)

            # The effect of executing a node on the output state variables
            for input_var in behaviour.input_variables():
                temporal_input_var = temporal_state_vars[input_var][self.btnode_times[leaf_id]]
                for output_var in behaviour.output_variables():
                    temporal_output_var = temporal_state_vars[output_var][self.btnode_times[leaf_id]+1]
                    graph.add_edge(temporal_input_var,temporal_output_var)


        # Link all temporal versions together
        for var in self.tm.state_vars():
            for t in range(num_timesteps-1):
                graph.add_edge(temporal_state_vars[var][t],temporal_state_vars[var][t+1])

        return graph
    
    '''
    VISUALISATION
    '''
    def visualise_explanation_graph(self):
        labels = {node_id: self.nodes[node_id].name for node_id in self.explanation_graph.nodes()}

        categories = [self.nodes[node_id].category for node_id in self.explanation_graph.nodes()]
        unique_cats = list(set(categories))
        
        color_palette = plt.cm.get_cmap('tab10', len(unique_cats))
        cat_to_color = {cat: color_palette(i) for i, cat in enumerate(unique_cats)}
        
        node_colors = [cat_to_color[cat] for cat in categories]

        plt.figure(figsize=(10, 8))
        pos = nx.spring_layout(self.explanation_graph, seed=42)  # Consistent layout
        
        nx.draw(
            self.explanation_graph, pos, 
            labels=labels, 
            node_color=node_colors, 
            with_labels=True, 
            node_size=2000, 
            font_size=10, 
            font_weight="bold", 
            arrowsize=20,
            edge_color="gray"
        )

        for cat, color in cat_to_color.items():
            plt.scatter([], [], c=[color], label=cat)
        plt.legend(title="Categories")

        plt.show()







            

        

        


        
            

        



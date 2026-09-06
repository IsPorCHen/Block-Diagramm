from typing import List, Dict, Any, Optional, Union, Tuple
from app.models.flowchart import Flowchart, Node, Edge


class FlowchartBuilder:
    """Builder for creating flowchart from parsed code."""
    
    def __init__(self):
        self._flowchart = Flowchart()
        self._node_id = 0
    
    @property
    def flowchart(self) -> Flowchart:
        """Get the built flowchart."""
        return self._flowchart
    
    def add_node(self, node_type: str, text: str) -> int:
        """Add a node to the flowchart."""
        node = Node(id=self._node_id, type=node_type, text=text)
        self._flowchart.nodes.append(node)
        self._node_id += 1
        return node.id
    
    def add_edge(
        self, 
        from_id: int, 
        to_id: int, 
        label: str = '', 
        branch: str = ''
    ) -> Edge:
        """Add an edge between nodes."""
        # Check for duplicate
        for edge in self._flowchart.edges:
            if edge.from_id == from_id and edge.to_id == to_id:
                if label and not edge.label:
                    edge.label = label
                    edge.branch = branch
                return edge
        
        edge = Edge(from_id=from_id, to_id=to_id, label=label, branch=branch)
        self._flowchart.edges.append(edge)
        return edge
    
    def add_nodes_from_graph(self, graph_data: List[Dict[str, Any]]):
        """Add multiple nodes from graph data."""
        for node_data in graph_data:
            self.add_node(node_data['type'], node_data['text'])
    
    def add_edges_from_graph(self, graph_data: List[Dict[str, Any]]):
        """Add multiple edges from graph data."""
        for edge_data in graph_data:
            self.add_edge(
                edge_data['from'],
                edge_data['to'],
                edge_data.get('label', ''),
                edge_data.get('branch', '')
            )
    
    def get_flowchart_data(self) -> Dict[str, Any]:
        """Get flowchart data as dictionary."""
        return self._flowchart.to_dict()
    
    def reset(self):
        """Reset the builder."""
        self._flowchart = Flowchart()
        self._node_id = 0
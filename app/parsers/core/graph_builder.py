"""Builds flowchart graphs from nodes and edges."""

from typing import List, Dict, Any, Optional
from app.models.flowchart import Flowchart, Node, Edge
from app.parsers.core.node_factory import NodeFactory
from app.parsers.core.edge_factory import EdgeFactory


class GraphBuilder:
    """Builds a complete flowchart graph."""
    
    def __init__(self):
        self.node_factory = NodeFactory()
        self.edge_factory = EdgeFactory()
        self._nodes: List[Node] = []
    
    def add_node(self, node_type: str, text: str) -> int:
        """Add a node and return its ID."""
        node = self.node_factory.create_node(node_type, text)
        self._nodes.append(node)
        return node.id
    
    def add_edge(self, from_id: int, to_id: int, label: str = '', branch: str = '') -> Edge:
        """Add an edge."""
        return self.edge_factory.add_edge(from_id, to_id, label, branch)
    
    def build(self) -> Flowchart:
        """Build the flowchart."""
        return Flowchart(nodes=self._nodes, edges=self.edge_factory.get_edges())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'nodes': [{'id': n.id, 'type': n.type, 'text': n.text} for n in self._nodes],
            'edges': [{'from': e.from_id, 'to': e.to_id, 'label': e.label, 'branch': e.branch} 
                     for e in self.edge_factory.get_edges()]
        }
    
    def reset(self):
        """Reset the builder."""
        self.node_factory.reset()
        self.edge_factory.reset()
        self._nodes = []
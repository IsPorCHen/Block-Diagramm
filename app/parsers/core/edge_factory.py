"""Factory for creating flowchart edges."""

from typing import List, Optional
from app.models.flowchart import Edge


class EdgeFactory:
    """Creates edges for flowcharts."""
    
    def __init__(self):
        self._edges: List[Edge] = []
    
    def add_edge(self, from_id: int, to_id: int, label: str = '', branch: str = '') -> Edge:
        """Add an edge between nodes."""
        # Check for duplicate
        for edge in self._edges:
            if edge.from_id == from_id and edge.to_id == to_id:
                if label and not edge.label:
                    edge.label = label
                    edge.branch = branch
                return edge
        
        edge = Edge(from_id=from_id, to_id=to_id, label=label, branch=branch)
        self._edges.append(edge)
        return edge
    
    def get_edges(self) -> List[Edge]:
        """Get all edges."""
        return self._edges
    
    def reset(self):
        """Reset edges."""
        self._edges = []
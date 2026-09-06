from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class Node:
    """Flowchart node."""
    
    id: int
    type: str
    text: str


@dataclass
class Edge:
    """Flowchart edge (connection between nodes)."""
    
    from_id: int
    to_id: int
    label: str = ''
    branch: str = ''


@dataclass
class Flowchart:
    """Complete flowchart data."""
    
    nodes: List[Node] = field(default_factory=list)
    edges: List[Edge] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'nodes': [{'id': n.id, 'type': n.type, 'text': n.text} for n in self.nodes],
            'edges': [{'from': e.from_id, 'to': e.to_id, 'label': e.label, 'branch': e.branch} for e in self.edges]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Flowchart':
        """Create Flowchart from dictionary."""
        flowchart = cls()
        for node_data in data.get('nodes', []):
            flowchart.nodes.append(Node(**node_data))
        for edge_data in data.get('edges', []):
            flowchart.edges.append(Edge(
                from_id=edge_data['from'],
                to_id=edge_data['to'],
                label=edge_data.get('label', ''),
                branch=edge_data.get('branch', '')
            ))
        return flowchart
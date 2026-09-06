"""Factory for creating flowchart nodes."""

from typing import Dict, Any
from app.models.flowchart import Node


class NodeFactory:
    """Creates nodes for flowcharts."""
    
    NODE_TYPES = {
        'start': {'shape': 'rounded_rect', 'color': '#dbeafe'},
        'end': {'shape': 'circle', 'color': '#dbeafe'},
        'process': {'shape': 'rect', 'color': '#dbeafe'},
        'input': {'shape': 'parallelogram', 'color': '#dbeafe'},
        'output': {'shape': 'parallelogram', 'color': '#dbeafe'},
        'condition': {'shape': 'diamond', 'color': '#dbeafe'},
        'loop': {'shape': 'hexagon', 'color': '#dbeafe'},
        'method': {'shape': 'rounded_rect', 'color': '#dbeafe'},
        'class_start': {'shape': 'rounded_rect', 'color': '#dbeafe'},
        'try_start': {'shape': 'rect', 'color': '#dbeafe', 'dashed': True},
        'except': {'shape': 'rect', 'color': '#dbeafe', 'dashed': True},
        'finally': {'shape': 'rect', 'color': '#dbeafe', 'dashed': True},
    }
    
    def __init__(self):
        self._node_id = 0
    
    def create_node(self, node_type: str, text: str) -> Node:
        """Create a new node."""
        node = Node(
            id=self._node_id,
            type=node_type,
            text=text
        )
        self._node_id += 1
        return node
    
    def reset(self):
        """Reset node counter."""
        self._node_id = 0
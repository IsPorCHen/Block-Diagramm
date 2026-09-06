"""Base parser with common functionality."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Tuple, Optional, Union
from app.parsers.core.graph_builder import GraphBuilder


class BaseParser(ABC):
    """Abstract base class for language parsers."""
    
    def __init__(self):
        self.graph = GraphBuilder()
        self._return_marker = 'return'
        self._no_empty_marker = 'no_empty'
        self._from_no_marker = 'from_no_branch'
        self._loop_exit_marker = 'loop_exit'
    
    @abstractmethod
    def parse(self, code: str) -> Dict[str, Any]:
        """Parse source code and return flowchart data."""
        pass
    
    @abstractmethod
    def get_language(self) -> str:
        """Get the language name."""
        pass
    
    @abstractmethod
    def get_extension(self) -> str:
        """Get the file extension."""
        pass
    
    def _connect_to_end(self, last_ids: List[Union[int, Tuple]], end_id: int):
        """Connect nodes to the end node."""
        for lid in last_ids:
            if lid is None:
                continue
            if isinstance(lid, tuple):
                marker, node_id = lid
                if marker == self._return_marker:
                    self.graph.add_edge(node_id, end_id)
                elif marker == self._no_empty_marker:
                    self.graph.add_edge(node_id, end_id, 'нет', 'no')
                elif marker == self._from_no_marker:
                    self.graph.add_edge(node_id, end_id, '', 'from_no')
                elif marker == self._loop_exit_marker:
                    self.graph.add_edge(node_id, end_id, '', 'loop_exit')
            else:
                self.graph.add_edge(lid, end_id)
    
    def _is_return(self, value) -> bool:
        """Check if value is a return marker."""
        return isinstance(value, tuple) and value[0] == self._return_marker
    
    def _is_no_empty(self, value) -> bool:
        """Check if value is a no_empty marker."""
        return isinstance(value, tuple) and value[0] == self._no_empty_marker
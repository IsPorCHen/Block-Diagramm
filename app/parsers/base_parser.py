from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BaseParser(ABC):
    """Abstract base class for language parsers."""
    
    @abstractmethod
    def parse(self, code: str) -> Dict[str, Any]:
        """
        Parse source code and return flowchart data.
        
        Args:
            code: Source code string
            
        Returns:
            Dictionary with 'success' flag and flowchart data
        """
        pass
    
    @abstractmethod
    def get_language(self) -> str:
        """Get the language name."""
        pass
    
    @abstractmethod
    def get_extension(self) -> str:
        """Get the file extension."""
        pass
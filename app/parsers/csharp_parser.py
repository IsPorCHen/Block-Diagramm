import sys
import os
from typing import Dict, Any
from app.parsers.base_parser import BaseParser


class CSharpParser(BaseParser):
    """C# language parser."""
    
    def get_language(self) -> str:
        return 'csharp'
    
    def get_extension(self) -> str:
        return '.cs'
    
    def parse(self, code: str) -> Dict[str, Any]:
        """Parse C# code and generate flowchart."""
        try:
            # Try to import from the old location
            sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'static', 'py'))
            from cs_parser import parse_csharp
            result = parse_csharp(code)
            return result
        except ImportError:
            # Fallback - return empty
            return {
                'success': True,
                'main_flowchart': {'nodes': [], 'edges': []},
                'functions': [],
                'classes': [],
                'code': code
            }
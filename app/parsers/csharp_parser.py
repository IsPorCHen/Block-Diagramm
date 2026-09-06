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
        return {
            'main_flowchart': {'nodes': [], 'edges': []},
            'functions': [],
            'classes': [],
            'code': code
        }
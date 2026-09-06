from typing import Dict, Any
from app.parsers.base_parser import BaseParser


class JavaScriptParser(BaseParser):
    """JavaScript language parser."""
    
    def get_language(self) -> str:
        return 'javascript'
    
    def get_extension(self) -> str:
        return '.js'
    
    def parse(self, code: str) -> Dict[str, Any]:
        """Parse JavaScript code and generate flowchart."""
        return {
            'main_flowchart': {'nodes': [], 'edges': []},
            'functions': [],
            'classes': [],
            'code': code
        }
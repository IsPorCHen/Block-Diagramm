"""C# language parser - uses the old parser for now."""

import sys
import os
from typing import Dict, Any
from app.parsers.base import BaseParser


class CSharpParser(BaseParser):
    """C# language parser."""
    
    def get_language(self) -> str:
        return 'csharp'
    
    def get_extension(self) -> str:
        return '.cs'
    
    def parse(self, code: str) -> Dict[str, Any]:
        """Parse C# code and generate flowchart."""
        try:
            # Try to use the old parser from static/py
            old_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'static', 'py')
            if old_path not in sys.path:
                sys.path.insert(0, old_path)
            
            from cs_parser import parse_csharp
            result = parse_csharp(code)
            
            # Add success flag if not present
            if 'success' not in result:
                result['success'] = True
            
            return result
            
        except ImportError:
            return {
                'success': True,
                'main_flowchart': {'nodes': [], 'edges': []},
                'functions': [],
                'classes': [],
                'code': code
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'C# parsing error: {str(e)}'
            }
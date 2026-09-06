import sys
import os
from typing import Dict, Any

# Add the old static/py directory to path to import the old parser
# But we'll use a better approach - copy the logic

from app.parsers.base_parser import BaseParser


class JavaScriptParser(BaseParser):
    """JavaScript language parser."""
    
    def get_language(self) -> str:
        return 'javascript'
    
    def get_extension(self) -> str:
        return '.js'
    
    def parse(self, code: str) -> Dict[str, Any]:
        """Parse JavaScript code and generate flowchart."""
        # Import the old parser dynamically
        try:
            # Try to import from the old location
            sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'static', 'py'))
            from js_parser import parse_javascript
            result = parse_javascript(code)
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
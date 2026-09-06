"""C# language parser - uses the new clean parser."""

import logging
from typing import Dict, Any
from app.parsers.base import BaseParser
from app.parsers.csharp import CSharpParser as NewCSharpParser

logger = logging.getLogger(__name__)


class CSharpParser(BaseParser):
    """C# language parser."""
    
    def __init__(self):
        super().__init__()
        self._parser = NewCSharpParser()
    
    def get_language(self) -> str:
        return 'csharp'
    
    def get_extension(self) -> str:
        return '.cs'
    
    def parse(self, code: str) -> Dict[str, Any]:
        """Parse C# code and generate flowchart."""
        try:
            result = self._parser.parse(code)
            
            if 'success' not in result:
                result['success'] = True
            
            return result
            
        except Exception as e:
            logger.error(f"C# parsing error: {e}", exc_info=True)
            return {
                'success': False,
                'error': f'C# parsing error: {str(e)}',
                'main_flowchart': {'nodes': [], 'edges': []},
                'functions': [],
                'classes': [],
                'code': code
            }
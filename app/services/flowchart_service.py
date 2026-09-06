from typing import Dict, Any, Optional
from app.services.parser_factory import ParserFactory


class FlowchartService:
    """Service for generating flowcharts from source code."""
    
    def __init__(self):
        self._builder = None
    
    def generate(self, code: str, extension: str) -> Dict[str, Any]:
        """
        Generate flowchart from source code.
        
        Args:
            code: Source code string
            extension: File extension
            
        Returns:
            Dictionary with flowchart data
        """
        parser = ParserFactory.get_parser(extension)
        if not parser:
            return {
                'success': False,
                'error': f'Unsupported file extension: {extension}'
            }
        
        try:
            result = parser.parse(code)
            result['success'] = True
            return result
        except SyntaxError as e:
            return {
                'success': False,
                'error': f'Syntax error: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Parsing error: {str(e)}'
            }
    
    def get_supported_extensions(self) -> tuple:
        """Get supported file extensions."""
        return ParserFactory.get_supported_extensions()
from typing import Optional
from app.parsers import BaseParser, PythonParser, JavaScriptParser, CSharpParser


class ParserFactory:
    """Factory for creating language-specific parsers."""
    
    _parsers = {
        '.py': PythonParser,
        '.js': JavaScriptParser,
        '.cs': CSharpParser,
    }
    
    @classmethod
    def get_parser(cls, extension: str) -> Optional[BaseParser]:
        """
        Get parser for the given file extension.
        
        Args:
            extension: File extension (e.g., '.py')
            
        Returns:
            Parser instance or None if not supported
        """
        parser_class = cls._parsers.get(extension.lower())
        if parser_class:
            return parser_class()
        return None
    
    @classmethod
    def get_supported_extensions(cls) -> tuple:
        """Get supported file extensions."""
        return tuple(cls._parsers.keys())
    
    @classmethod
    def is_supported(cls, extension: str) -> bool:
        """Check if extension is supported."""
        return extension.lower() in cls._parsers
"""Python tokenizer - uses ast module."""

import ast
from typing import List, Dict, Any


class PythonTokenizer:
    """Tokenizer for Python code using ast."""
    
    def tokenize(self, code: str) -> ast.AST:
        """Parse Python code into AST."""
        try:
            return ast.parse(code)
        except SyntaxError as e:
            raise SyntaxError(f'Синтаксическая ошибка: строка {e.lineno}')
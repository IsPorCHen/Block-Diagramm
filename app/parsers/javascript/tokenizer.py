"""JavaScript tokenizer for parsing."""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class Token:
    """JavaScript token."""
    type: str
    value: str
    line: int
    column: int


class JavaScriptTokenizer:
    """Tokenizes JavaScript code."""
    
    KEYWORDS = {
        'function', 'return', 'if', 'else', 'for', 'while', 'do',
        'switch', 'case', 'break', 'continue', 'try', 'catch',
        'finally', 'throw', 'class', 'extends', 'new', 'this',
        'var', 'let', 'const', 'async', 'await', 'export',
        'import', 'default', 'from', 'of', 'in', 'typeof',
        'instanceof', 'void', 'delete', 'yield', 'true', 'false',
        'null', 'undefined', 'NaN', 'Infinity'
    }
    
    def __init__(self):
        self._tokens: List[Token] = []
        self._pos = 0
        self._line = 1
        self._column = 1
        self._code = ''
    
    def tokenize(self, code: str) -> List[Token]:
        """Tokenize JavaScript code."""
        self._tokens = []
        self._pos = 0
        self._line = 1
        self._column = 1
        self._code = code
        
        while self._pos < len(self._code):
            char = self._code[self._pos]
            
            # Skip whitespace
            if char in ' \t':
                self._advance()
                continue
            
            # Newline
            if char == '\n':
                self._line += 1
                self._column = 1
                self._pos += 1
                continue
            
            # Comments
            if char == '/' and self._pos + 1 < len(self._code):
                if self._code[self._pos + 1] == '/':
                    self._skip_line_comment()
                    continue
                elif self._code[self._pos + 1] == '*':
                    self._skip_block_comment()
                    continue
            
            # Strings
            if char in '"\'`':
                self._tokenize_string(char)
                continue
            
            # Numbers
            if char.isdigit() or (char == '.' and self._pos + 1 < len(self._code) and self._code[self._pos + 1].isdigit()):
                self._tokenize_number()
                continue
            
            # Identifiers and keywords
            if char.isalpha() or char == '_' or char == '$':
                self._tokenize_identifier()
                continue
            
            # Operators and punctuation
            self._tokenize_operator()
        
        return self._tokens
    
    def _advance(self):
        """Advance position."""
        self._pos += 1
        self._column += 1
    
    def _skip_line_comment(self):
        """Skip single-line comment."""
        self._pos += 2
        while self._pos < len(self._code) and self._code[self._pos] != '\n':
            self._pos += 1
    
    def _skip_block_comment(self):
        """Skip multi-line comment."""
        self._pos += 2
        while self._pos + 1 < len(self._code):
            if self._code[self._pos] == '*' and self._code[self._pos + 1] == '/':
                self._pos += 2
                return
            if self._code[self._pos] == '\n':
                self._line += 1
            self._pos += 1
    
    def _tokenize_string(self, quote: str):
        """Tokenize string literal."""
        start_line = self._line
        start_col = self._column
        self._pos += 1
        escaped = False
        value = quote
        
        while self._pos < len(self._code):
            char = self._code[self._pos]
            value += char
            
            if escaped:
                escaped = False
                self._pos += 1
                continue
            
            if char == '\\':
                escaped = True
                self._pos += 1
                continue
            
            if char == quote:
                self._pos += 1
                break
            
            if char == '\n':
                self._line += 1
            self._pos += 1
        
        self._tokens.append(Token('STRING', value, start_line, start_col))
        self._column += len(value)
    
    def _tokenize_number(self):
        """Tokenize number literal."""
        start_line = self._line
        start_col = self._column
        is_float = False
        value = ''
        
        while self._pos < len(self._code):
            char = self._code[self._pos]
            if char.isdigit():
                value += char
                self._pos += 1
            elif char == '.' and not is_float:
                is_float = True
                value += char
                self._pos += 1
            else:
                break
        
        token_type = 'FLOAT' if is_float else 'INTEGER'
        self._tokens.append(Token(token_type, value, start_line, start_col))
        self._column += len(value)
    
    def _tokenize_identifier(self):
        """Tokenize identifier or keyword."""
        start_line = self._line
        start_col = self._column
        value = ''
        
        while self._pos < len(self._code):
            char = self._code[self._pos]
            if char.isalnum() or char == '_' or char == '$':
                value += char
                self._pos += 1
            else:
                break
        
        token_type = 'KEYWORD' if value in self.KEYWORDS else 'IDENTIFIER'
        self._tokens.append(Token(token_type, value, start_line, start_col))
        self._column += len(value)
    
    def _tokenize_operator(self):
        """Tokenize operator or punctuation."""
        start_line = self._line
        start_col = self._column
        char = self._code[self._pos]
        
        # Multi-character operators
        multi_ops = ['===', '!==', '>=', '<=', '&&', '||', '++', '--', '=>', '!=', '==', '+=', '-=', '*=', '/=', '%=']
        for op in multi_ops:
            if self._code[self._pos:self._pos + len(op)] == op:
                self._tokens.append(Token('OPERATOR', op, start_line, start_col))
                self._pos += len(op)
                self._column += len(op)
                return
        
        # Single character
        self._pos += 1
        
        if char in '(){}[];,.':
            self._tokens.append(Token('PUNCTUATION', char, start_line, start_col))
        else:
            self._tokens.append(Token('OPERATOR', char, start_line, start_col))
        self._column += 1
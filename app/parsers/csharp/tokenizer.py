"""C# tokenizer for parsing."""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class Token:
    """C# token."""
    type: str
    value: str
    line: int
    column: int


class CSharpTokenizer:
    """Tokenizes C# code."""
    
    KEYWORDS = {
        'class', 'struct', 'interface', 'enum', 'delegate', 'event',
        'public', 'private', 'protected', 'internal', 'static', 'readonly',
        'const', 'volatile', 'abstract', 'sealed', 'virtual', 'override',
        'new', 'this', 'base', 'null', 'true', 'false', 'default',
        'if', 'else', 'for', 'foreach', 'while', 'do', 'switch',
        'case', 'break', 'continue', 'return', 'throw', 'try',
        'catch', 'finally', 'using', 'namespace', 'var', 'dynamic',
        'object', 'string', 'int', 'long', 'float', 'double', 'decimal',
        'bool', 'char', 'byte', 'sbyte', 'short', 'ushort', 'uint', 'ulong',
        'void', 'async', 'await', 'yield', 'where', 'from', 'select',
        'in', 'join', 'on', 'equals', 'orderby', 'group', 'into',
        'let', 'ascending', 'descending', 'get', 'set', 'value', 'partial'
    }
    
    def __init__(self):
        self._tokens: List[Token] = []
        self._pos = 0
        self._line = 1
        self._column = 1
        self._code = ''
    
    def tokenize(self, code: str) -> List[Token]:
        """Tokenize C# code."""
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
            if char == '"' or char == '\'':
                self._tokenize_string(char)
                continue
            
            # Verbatim strings
            if char == '@' and self._pos + 1 < len(self._code) and self._code[self._pos + 1] == '"':
                self._tokenize_verbatim_string()
                continue
            
            # Numbers
            if char.isdigit() or (char == '.' and self._pos + 1 < len(self._code) and self._code[self._pos + 1].isdigit()):
                self._tokenize_number()
                continue
            
            # Identifiers and keywords
            if char.isalpha() or char == '_':
                self._tokenize_identifier()
                continue
            
            # Preprocessor directives
            if char == '#':
                self._skip_preprocessor()
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
    
    def _skip_preprocessor(self):
        """Skip preprocessor directive."""
        while self._pos < len(self._code) and self._code[self._pos] != '\n':
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
    
    def _tokenize_verbatim_string(self):
        """Tokenize verbatim string (@\"...\")."""
        start_line = self._line
        start_col = self._column
        self._pos += 2  # Skip @"
        value = '@"'
        
        while self._pos < len(self._code):
            char = self._code[self._pos]
            value += char
            
            if char == '"' and self._pos + 1 < len(self._code) and self._code[self._pos + 1] == '"':
                # Double quote escape
                value += self._code[self._pos + 1]
                self._pos += 2
                continue
            
            if char == '"':
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
            elif char in 'fFdDmM':
                value += char
                self._pos += 1
                break
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
            if char.isalnum() or char == '_':
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
        multi_ops = ['>=', '<=', '==', '!=', '&&', '||', '++', '--', '=>', 
                     '+=', '-=', '*=', '/=', '%=', '&=', '|=', '^=',
                     '<<', '>>', '??', '?.', '?[', '::', '->']
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
        elif char in '<>':
            self._tokens.append(Token('OPERATOR', char, start_line, start_col))
        else:
            self._tokens.append(Token('OPERATOR', char, start_line, start_col))
        self._column += 1
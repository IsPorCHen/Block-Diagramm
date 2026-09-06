"""Tokenizer for Go source code."""

import re
from typing import List, Dict, Any, Optional, Tuple


class GoTokenizer:
    """Tokenizes Go source code."""
    
    def __init__(self):
        self.tokens = []
        self.pos = 0
    
    def tokenize(self, code: str) -> List[Dict[str, Any]]:
        """Tokenize Go source code."""
        self.tokens = []
        self.pos = 0
        
        # Remove multi-line comments /* ... */
        code = self._remove_multiline_comments(code)
        
        lines = code.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            # Remove single-line comments
            line = self._remove_comments(line)
            if not line.strip():
                continue
            
            # Tokenize line
            tokens = self._tokenize_line(line, line_num)
            self.tokens.extend(tokens)
        
        return self.tokens
    
    def _remove_multiline_comments(self, code: str) -> str:
        """Remove /* */ comments."""
        result = []
        i = 0
        in_comment = False
        
        while i < len(code):
            if not in_comment and i + 1 < len(code) and code[i:i+2] == '/*':
                in_comment = True
                i += 2
                continue
            if in_comment and i + 1 < len(code) and code[i:i+2] == '*/':
                in_comment = False
                i += 2
                continue
            if not in_comment:
                result.append(code[i])
            i += 1
        
        return ''.join(result)
    
    def _remove_comments(self, line: str) -> str:
        """Remove // comments."""
        # Remove // comments
        if '//' in line:
            # Check if // is inside a string
            in_string = False
            in_char = False
            for i, char in enumerate(line):
                if char == '"' and not in_char and (i == 0 or line[i-1] != '\\'):
                    in_string = not in_string
                elif char == "'" and not in_string and (i == 0 or line[i-1] != '\\'):
                    in_char = not in_char
                elif char == '/' and i + 1 < len(line) and line[i+1] == '/' and not in_string and not in_char:
                    return line[:i]
            return line
        return line
    
    def _tokenize_line(self, line: str, line_num: int) -> List[Dict[str, Any]]:
        """Tokenize a single line."""
        tokens = []
        pos = 0
        
        while pos < len(line):
            char = line[pos]
            
            # Skip whitespace
            if char.isspace():
                pos += 1
                continue
            
            # Handle strings (double quotes)
            if char == '"':
                start = pos
                pos += 1
                while pos < len(line) and line[pos] != '"':
                    if line[pos] == '\\' and pos + 1 < len(line):
                        pos += 2
                    else:
                        pos += 1
                if pos < len(line):
                    pos += 1
                token_text = line[start:pos]
                tokens.append({
                    'type': 'string',
                    'value': token_text,
                    'line': line_num
                })
                continue
            
            # Handle raw strings (backticks)
            if char == '`':
                start = pos
                pos += 1
                while pos < len(line) and line[pos] != '`':
                    pos += 1
                if pos < len(line):
                    pos += 1
                token_text = line[start:pos]
                tokens.append({
                    'type': 'string',
                    'value': token_text,
                    'line': line_num
                })
                continue
            
            # Handle character literals
            if char == "'":
                start = pos
                pos += 1
                if pos < len(line) and line[pos] == '\\':
                    pos += 2
                elif pos < len(line):
                    pos += 1
                if pos < len(line) and line[pos] == "'":
                    pos += 1
                token_text = line[start:pos]
                tokens.append({
                    'type': 'string',
                    'value': token_text,
                    'line': line_num
                })
                continue
            
            # Handle numbers
            if char.isdigit() or (char == '.' and pos + 1 < len(line) and line[pos+1].isdigit()):
                start = pos
                if char == '0' and pos + 1 < len(line) and line[pos+1] in 'xXbBoO':
                    pos += 2
                    while pos < len(line) and (line[pos].isdigit() or line[pos] in 'abcdefABCDEF'):
                        pos += 1
                else:
                    while pos < len(line) and (line[pos].isdigit() or line[pos] == '.'):
                        pos += 1
                tokens.append({
                    'type': 'number',
                    'value': line[start:pos],
                    'line': line_num
                })
                continue
            
            # Handle identifiers and keywords
            if char.isalpha() or char == '_':
                start = pos
                while pos < len(line) and (line[pos].isalnum() or line[pos] == '_'):
                    pos += 1
                word = line[start:pos]
                
                keywords = {
                    'break', 'default', 'func', 'interface', 'select',
                    'case', 'defer', 'go', 'map', 'struct',
                    'chan', 'else', 'goto', 'package', 'switch',
                    'const', 'fallthrough', 'if', 'range', 'type',
                    'continue', 'for', 'import', 'return', 'var',
                    'true', 'false', 'nil', 'iota'
                }
                
                tokens.append({
                    'type': 'keyword' if word in keywords else 'identifier',
                    'value': word,
                    'line': line_num
                })
                continue
            
            # Handle operators and punctuation
            # Multi-character operators
            if pos + 1 < len(line):
                two_chars = line[pos:pos+2]
                if two_chars in ['==', '!=', '<=', '>=', '&&', '||', '++', '--', ':=', '->']:
                    tokens.append({
                        'type': 'operator',
                        'value': two_chars,
                        'line': line_num
                    })
                    pos += 2
                    continue
                if two_chars in ['+=', '-=', '*=', '/=', '%=', '&=', '|=', '^=', '<<=', '>>=']:
                    tokens.append({
                        'type': 'operator',
                        'value': two_chars,
                        'line': line_num
                    })
                    pos += 2
                    continue
            
            # Single character operators
            if char in '+-*/%&|^!<>=.,;:(){}[]':
                tokens.append({
                    'type': 'operator' if char in '+-*/%&|^!<>=.' else 'punctuation',
                    'value': char,
                    'line': line_num
                })
                pos += 1
                continue
            
            # Handle unknown
            tokens.append({
                'type': 'unknown',
                'value': char,
                'line': line_num
            })
            pos += 1
        
        return tokens
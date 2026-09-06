"""Builds AST from JavaScript tokens."""

from typing import List, Dict, Any, Optional
from app.parsers.javascript.tokenizer import Token


class JavaScriptASTBuilder:
    """Builds AST from tokens."""
    
    def __init__(self):
        self.tokens = []
        self.pos = 0
    
    def build(self, tokens: List[Token]) -> List[Dict[str, Any]]:
        """Build AST from tokens."""
        self.tokens = tokens
        self.pos = 0
        nodes = []
        
        while self.pos < len(self.tokens):
            node = self._parse_statement()
            if node:
                nodes.append(node)
        
        return nodes
    
    def _peek(self) -> Optional[Token]:
        """Peek at current token."""
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None
    
    def _next(self) -> Optional[Token]:
        """Get next token and advance."""
        if self.pos < len(self.tokens):
            token = self.tokens[self.pos]
            self.pos += 1
            return token
        return None
    
    def _expect(self, value: str) -> bool:
        """Check if current token matches value."""
        token = self._peek()
        return token is not None and token.value == value
    
    def _parse_statement(self) -> Optional[Dict[str, Any]]:
        """Parse a single statement."""
        token = self._peek()
        if token is None:
            return None
        
        # Skip semicolons
        if token.value == ';':
            self._next()
            return None
        
        # Function declaration
        if token.value == 'function':
            return self._parse_function()
        
        # Class declaration
        if token.value == 'class':
            return self._parse_class()
        
        # If statement
        if token.value == 'if':
            return self._parse_if()
        
        # For loop
        if token.value == 'for':
            return self._parse_for()
        
        # While loop
        if token.value == 'while':
            return self._parse_while()
        
        # Do-while loop
        if token.value == 'do':
            return self._parse_do_while()
        
        # Switch statement
        if token.value == 'switch':
            return self._parse_switch()
        
        # Try statement
        if token.value == 'try':
            return self._parse_try()
        
        # Return statement
        if token.value == 'return':
            return self._parse_return()
        
        # Throw statement
        if token.value == 'throw':
            return self._parse_throw()
        
        # Break/Continue
        if token.value in ('break', 'continue'):
            self._next()
            if self._expect(';'):
                self._next()
            return {'type': token.value}
        
        # Variable declaration
        if token.value in ('var', 'let', 'const'):
            return self._parse_declaration()
        
        # Expression statement
        return self._parse_expression_statement()
    
    def _parse_function(self) -> Dict[str, Any]:
        """Parse function declaration."""
        self._next()  # Skip 'function'
        
        # Get name
        name = ''
        token = self._peek()
        if token and token.type == 'IDENTIFIER':
            name = token.value
            self._next()
        
        # Parse parameters
        params = []
        if self._expect('('):
            self._next()
            while not self._expect(')') and self.pos < len(self.tokens):
                token = self._peek()
                if token and token.type == 'IDENTIFIER':
                    params.append(token.value)
                    self._next()
                else:
                    self._next()
            if self._expect(')'):
                self._next()
        
        # Parse body
        body = self._parse_block_or_statement()
        
        return {
            'type': 'function',
            'name': name,
            'params': params,
            'body': body
        }
    
    def _parse_class(self) -> Dict[str, Any]:
        """Parse class declaration."""
        self._next()  # Skip 'class'
        
        name = ''
        token = self._peek()
        if token and token.type == 'IDENTIFIER':
            name = token.value
            self._next()
        
        methods = []
        method_nodes = []
        
        if self._expect('{'):
            self._next()
            while not self._expect('}') and self.pos < len(self.tokens):
                token = self._peek()
                if token and token.type == 'IDENTIFIER':
                    method_name = token.value
                    self._next()
                    
                    # Check if it's a method (has parentheses)
                    if self._expect('('):
                        # It's a method
                        self._next()  # Skip '('
                        params = []
                        while not self._expect(')') and self.pos < len(self.tokens):
                            token = self._peek()
                            if token and token.type == 'IDENTIFIER':
                                params.append(token.value)
                                self._next()
                            else:
                                self._next()
                        if self._expect(')'):
                            self._next()
                        
                        body = self._parse_block_or_statement()
                        
                        method_node = {
                            'type': 'function',
                            'name': method_name,
                            'params': params,
                            'body': body
                        }
                        methods.append(method_name)
                        method_nodes.append(method_node)
                    else:
                        # Property - skip
                        while not self._expect(';') and not self._expect('}') and self.pos < len(self.tokens):
                            self._next()
                        if self._expect(';'):
                            self._next()
                else:
                    self._next()
            if self._expect('}'):
                self._next()
        
        return {
            'type': 'class',
            'name': name,
            'methods': methods,
            'method_nodes': method_nodes
        }
    
    def _parse_if(self) -> Dict[str, Any]:
        """Parse if statement."""
        self._next()  # Skip 'if'
        
        condition = ''
        if self._expect('('):
            self._next()
            while not self._expect(')') and self.pos < len(self.tokens):
                token = self._peek()
                if token:
                    condition += token.value
                    self._next()
            if self._expect(')'):
                self._next()
        
        body = self._parse_block_or_statement()
        
        else_body = []
        if self._expect('else'):
            self._next()
            if self._expect('if'):
                else_node = self._parse_if()
                else_body = [else_node]
            else:
                else_body = self._parse_block_or_statement()
        
        return {
            'type': 'if',
            'condition': condition.strip(),
            'body': body,
            'else_body': else_body
        }
    
    def _parse_for(self) -> Dict[str, Any]:
        """Parse for loop."""
        self._next()  # Skip 'for'
        
        header = ''
        if self._expect('('):
            self._next()
            while not self._expect(')') and self.pos < len(self.tokens):
                token = self._peek()
                if token:
                    header += token.value
                    self._next()
            if self._expect(')'):
                self._next()
        
        body = self._parse_block_or_statement()
        
        return {
            'type': 'for',
            'header': header.strip(),
            'body': body
        }
    
    def _parse_while(self) -> Dict[str, Any]:
        """Parse while loop."""
        self._next()  # Skip 'while'
        
        condition = ''
        if self._expect('('):
            self._next()
            while not self._expect(')') and self.pos < len(self.tokens):
                token = self._peek()
                if token:
                    condition += token.value
                    self._next()
            if self._expect(')'):
                self._next()
        
        body = self._parse_block_or_statement()
        
        return {
            'type': 'while',
            'condition': condition.strip(),
            'body': body
        }
    
    def _parse_do_while(self) -> Dict[str, Any]:
        """Parse do-while loop."""
        self._next()  # Skip 'do'
        
        body = self._parse_block_or_statement()
        
        condition = ''
        if self._expect('while'):
            self._next()
            if self._expect('('):
                self._next()
                while not self._expect(')') and self.pos < len(self.tokens):
                    token = self._peek()
                    if token:
                        condition += token.value
                        self._next()
                if self._expect(')'):
                    self._next()
        
        return {
            'type': 'do_while',
            'condition': condition.strip(),
            'body': body
        }
    
    def _parse_switch(self) -> Dict[str, Any]:
        """Parse switch statement."""
        self._next()  # Skip 'switch'
        
        expression = ''
        if self._expect('('):
            self._next()
            while not self._expect(')') and self.pos < len(self.tokens):
                token = self._peek()
                if token:
                    expression += token.value
                    self._next()
            if self._expect(')'):
                self._next()
        
        cases = []
        if self._expect('{'):
            self._next()
            while not self._expect('}') and self.pos < len(self.tokens):
                token = self._peek()
                if token and token.value == 'case':
                    self._next()
                    case_value = ''
                    while not self._expect(':') and self.pos < len(self.tokens):
                        token = self._peek()
                        if token:
                            case_value += token.value
                            self._next()
                    if self._expect(':'):
                        self._next()
                    
                    case_body = self._parse_block_or_statement()
                    cases.append({
                        'type': 'case',
                        'value': case_value.strip(),
                        'body': case_body
                    })
                elif token and token.value == 'default':
                    self._next()
                    if self._expect(':'):
                        self._next()
                    
                    default_body = self._parse_block_or_statement()
                    cases.append({
                        'type': 'default',
                        'body': default_body
                    })
                else:
                    self._next()
            if self._expect('}'):
                self._next()
        
        return {
            'type': 'switch',
            'expression': expression.strip(),
            'cases': cases
        }
    
    def _parse_try(self) -> Dict[str, Any]:
        """Parse try-catch-finally."""
        self._next()  # Skip 'try'
        
        body = self._parse_block_or_statement()
        
        catches = []
        while self._expect('catch'):
            self._next()
            catch_param = ''
            if self._expect('('):
                self._next()
                while not self._expect(')') and self.pos < len(self.tokens):
                    token = self._peek()
                    if token:
                        catch_param += token.value
                        self._next()
                if self._expect(')'):
                    self._next()
            
            catch_body = self._parse_block_or_statement()
            catches.append({
                'type': 'catch',
                'param': catch_param.strip(),
                'body': catch_body
            })
        
        finally_body = []
        if self._expect('finally'):
            self._next()
            finally_body = self._parse_block_or_statement()
        
        return {
            'type': 'try',
            'body': body,
            'catches': catches,
            'finally_body': finally_body
        }
    
    def _parse_return(self) -> Dict[str, Any]:
        """Parse return statement."""
        self._next()  # Skip 'return'
        
        value = ''
        while not self._expect(';') and self.pos < len(self.tokens):
            token = self._peek()
            if token:
                value += token.value
                self._next()
        
        if self._expect(';'):
            self._next()
        
        return {
            'type': 'return',
            'value': value.strip()
        }
    
    def _parse_throw(self) -> Dict[str, Any]:
        """Parse throw statement."""
        self._next()  # Skip 'throw'
        
        value = ''
        while not self._expect(';') and self.pos < len(self.tokens):
            token = self._peek()
            if token:
                value += token.value
                self._next()
        
        if self._expect(';'):
            self._next()
        
        return {
            'type': 'throw',
            'value': value.strip()
        }
    
    def _parse_declaration(self) -> Dict[str, Any]:
        """Parse variable declaration."""
        var_type = self._next().value
        
        names = []
        while not self._expect(';') and self.pos < len(self.tokens):
            token = self._peek()
            if token and token.type == 'IDENTIFIER':
                names.append(token.value)
                self._next()
            else:
                self._next()
        
        if self._expect(';'):
            self._next()
        
        return {
            'type': 'declaration',
            'var_type': var_type,
            'names': names
        }
    
    def _parse_expression_statement(self) -> Dict[str, Any]:
        """Parse expression statement."""
        value = ''
        while not self._expect(';') and self.pos < len(self.tokens):
            token = self._peek()
            if token:
                value += token.value
                self._next()
        
        if self._expect(';'):
            self._next()
        
        return {
            'type': 'expression',
            'value': value.strip()
        }
    
    def _parse_block_or_statement(self) -> List[Dict[str, Any]]:
        """Parse a block or single statement."""
        result = []
        
        if self._expect('{'):
            self._next()
            while not self._expect('}') and self.pos < len(self.tokens):
                stmt = self._parse_statement()
                if stmt:
                    result.append(stmt)
            if self._expect('}'):
                self._next()
        else:
            stmt = self._parse_statement()
            if stmt:
                result.append(stmt)
        
        return result
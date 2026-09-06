"""Builds AST from C# tokens."""

from typing import List, Dict, Any, Optional
from app.parsers.csharp.tokenizer import Token


class CSharpASTBuilder:
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
        
        # Class/Struct/Interface
        if token.value in ('class', 'struct', 'interface'):
            return self._parse_class()
        
        # Enum
        if token.value == 'enum':
            return self._parse_enum()
        
        # If
        if token.value == 'if':
            return self._parse_if()
        
        # For
        if token.value == 'for':
            return self._parse_for()
        
        # Foreach
        if token.value == 'foreach':
            return self._parse_foreach()
        
        # While
        if token.value == 'while':
            return self._parse_while()
        
        # Do
        if token.value == 'do':
            return self._parse_do()
        
        # Switch
        if token.value == 'switch':
            return self._parse_switch()
        
        # Try
        if token.value == 'try':
            return self._parse_try()
        
        # Return
        if token.value == 'return':
            return self._parse_return()
        
        # Throw
        if token.value == 'throw':
            return self._parse_throw()
        
        # Break/Continue
        if token.value in ('break', 'continue'):
            self._next()
            if self._expect(';'):
                self._next()
            return {'type': token.value}
        
        # Using
        if token.value == 'using':
            return self._parse_using()
        
        # Public/private/etc - skip modifiers and parse next
        if token.value in ('public', 'private', 'protected', 'internal', 'static', 
                          'readonly', 'const', 'virtual', 'override', 'abstract',
                          'sealed', 'async', 'unsafe'):
            self._next()
            return self._parse_statement()
        
        # Variable declaration - check if next token is identifier
        if token.type == 'IDENTIFIER':
            return self._parse_declaration_or_expression()
        
        # Skip unknown
        self._next()
        return None
    
    def _parse_class(self) -> Dict[str, Any]:
        """Parse class/struct/interface declaration."""
        class_type = self._next().value
        
        # Get name
        name = ''
        token = self._peek()
        if token and token.type == 'IDENTIFIER':
            name = token.value
            self._next()
        
        # Skip generic parameters and inheritance
        while not self._expect('{') and self.pos < len(self.tokens):
            self._next()
        
        # Parse body
        fields = []
        properties = []
        methods = []
        method_nodes = []
        
        if self._expect('{'):
            self._next()
            while not self._expect('}') and self.pos < len(self.tokens):
                # Skip attributes
                if self._expect('['):
                    while not self._expect(']') and self.pos < len(self.tokens):
                        self._next()
                    if self._expect(']'):
                        self._next()
                    continue
                
                # Skip modifiers
                modifiers = []
                while self._peek() and self._peek().value in ('public', 'private', 'protected', 
                                                              'internal', 'static', 'readonly',
                                                              'const', 'virtual', 'override',
                                                              'abstract', 'sealed', 'async'):
                    modifiers.append(self._peek().value)
                    self._next()
                
                token = self._peek()
                if token is None:
                    break
                
                # Check if it's a method (has parentheses after name)
                if token.type == 'IDENTIFIER':
                    name_token = token.value
                    self._next()
                    
                    # Method
                    if self._expect('('):
                        method_node = self._parse_method_body(name_token)
                        if method_node:
                            methods.append(name_token)
                            method_nodes.append(method_node)
                    # Property
                    elif self._expect('{'):
                        properties.append(name_token)
                        # Skip property body
                        while not self._expect('}') and self.pos < len(self.tokens):
                            self._next()
                        if self._expect('}'):
                            self._next()
                    # Field
                    else:
                        fields.append(name_token)
                        while not self._expect(';') and self.pos < len(self.tokens):
                            self._next()
                        if self._expect(';'):
                            self._next()
                else:
                    self._next()
            
            if self._expect('}'):
                self._next()
        
        return {
            'type': class_type,
            'name': name,
            'fields': fields,
            'properties': properties,
            'methods': methods,
            'method_nodes': method_nodes
        }
    
    def _parse_method_body(self, name: str) -> Dict[str, Any]:
        """Parse method body."""
        # Skip parameters
        params = []
        if self._expect('('):
            self._next()
            while not self._expect(')') and self.pos < len(self.tokens):
                token = self._peek()
                if token and token.type in ('IDENTIFIER', 'KEYWORD'):
                    # Skip type
                    self._next()
                    token = self._peek()
                    if token and token.type == 'IDENTIFIER':
                        params.append(token.value)
                        self._next()
                else:
                    self._next()
            if self._expect(')'):
                self._next()
        
        # Parse body
        body = []
        if self._expect('{'):
            self._next()
            while not self._expect('}') and self.pos < len(self.tokens):
                stmt = self._parse_statement()
                if stmt:
                    body.append(stmt)
            if self._expect('}'):
                self._next()
        
        return {
            'type': 'function',
            'name': name,
            'params': params,
            'body': body
        }
    
    def _parse_enum(self) -> Dict[str, Any]:
        """Parse enum declaration."""
        self._next()
        
        name = ''
        token = self._peek()
        if token and token.type == 'IDENTIFIER':
            name = token.value
            self._next()
        
        values = []
        if self._expect('{'):
            self._next()
            while not self._expect('}') and self.pos < len(self.tokens):
                token = self._peek()
                if token and token.type == 'IDENTIFIER':
                    values.append(token.value)
                    self._next()
                else:
                    self._next()
            if self._expect('}'):
                self._next()
        
        return {
            'type': 'enum',
            'name': name,
            'values': values
        }
    
    def _parse_if(self) -> Dict[str, Any]:
        """Parse if statement."""
        self._next()
        
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
        self._next()
        
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
    
    def _parse_foreach(self) -> Dict[str, Any]:
        """Parse foreach loop."""
        self._next()
        
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
            'type': 'foreach',
            'header': header.strip(),
            'body': body
        }
    
    def _parse_while(self) -> Dict[str, Any]:
        """Parse while loop."""
        self._next()
        
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
    
    def _parse_do(self) -> Dict[str, Any]:
        """Parse do-while loop."""
        self._next()
        
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
        self._next()
        
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
        self._next()
        
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
        self._next()
        
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
        self._next()
        
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
    
    def _parse_using(self) -> Dict[str, Any]:
        """Parse using statement or directive."""
        self._next()
        
        value = ''
        while not self._expect(';') and not self._expect('{') and self.pos < len(self.tokens):
            token = self._peek()
            if token:
                value += token.value
                self._next()
        
        if self._expect(';'):
            self._next()
            return {
                'type': 'using_directive',
                'value': value.strip()
            }
        elif self._expect('{'):
            body = self._parse_block_or_statement()
            return {
                'type': 'using_statement',
                'value': value.strip(),
                'body': body
            }
        
        return {
            'type': 'using',
            'value': value.strip()
        }
    
    def _parse_declaration_or_expression(self) -> Dict[str, Any]:
        """Parse declaration or expression."""
        # Try to detect if it's a declaration
        token = self._peek()
        if token and token.type == 'IDENTIFIER':
            # Check if next token is identifier (var name) or operator
            var_type = token.value
            self._next()
            
            token = self._peek()
            if token and token.type == 'IDENTIFIER':
                # It's a declaration
                names = [token.value]
                self._next()
                
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
            else:
                # It's an expression
                value = var_type
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
        
        # Expression
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
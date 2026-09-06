"""Builds AST from JavaScript tokens."""

from typing import List, Dict, Any, Optional


class JavaScriptASTBuilder:
    """Builds AST from tokens."""
    
    def __init__(self):
        self.tokens = []
        self.pos = 0
    
    def build(self, tokens: List) -> List[Dict[str, Any]]:
        """Build AST from tokens."""
        self.tokens = tokens
        self.pos = 0
        nodes = []
        
        while self.pos < len(self.tokens):
            node = self._parse_statement()
            if node:
                nodes.append(node)
        
        return nodes
    
    def _parse_statement(self) -> Optional[Dict[str, Any]]:
        """Parse a single statement."""
        if self.pos >= len(self.tokens):
            return None
        
        token = self.tokens[self.pos]
        
        if token.value == 'function':
            return self._parse_function()
        elif token.value == 'class':
            return self._parse_class()
        elif token.value == 'if':
            return self._parse_if()
        elif token.value == 'for':
            return self._parse_for()
        elif token.value == 'while':
            return self._parse_while()
        elif token.value == 'do':
            return self._parse_do_while()
        elif token.value == 'switch':
            return self._parse_switch()
        elif token.value == 'try':
            return self._parse_try()
        elif token.value == 'return':
            return self._parse_return()
        elif token.value == 'throw':
            return self._parse_throw()
        elif token.value == 'break' or token.value == 'continue':
            self.pos += 1
            if self.pos < len(self.tokens) and self.tokens[self.pos].value == ';':
                self.pos += 1
            return {'type': token.value}
        elif token.value == 'var' or token.value == 'let' or token.value == 'const':
            return self._parse_declaration()
        elif token.value == ';':
            self.pos += 1
            return None
        else:
            return self._parse_expression_statement()
    
    def _parse_function(self) -> Dict[str, Any]:
        """Parse function declaration."""
        self.pos += 1  # Skip 'function'
        
        # Get name
        name = ''
        if self.pos < len(self.tokens) and self.tokens[self.pos].type == 'IDENTIFIER':
            name = self.tokens[self.pos].value
            self.pos += 1
        
        # Parse parameters
        params = []
        if self.pos < len(self.tokens) and self.tokens[self.pos].value == '(':
            self.pos += 1
            while self.pos < len(self.tokens) and self.tokens[self.pos].value != ')':
                if self.tokens[self.pos].type == 'IDENTIFIER':
                    params.append(self.tokens[self.pos].value)
                self.pos += 1
            if self.pos < len(self.tokens) and self.tokens[self.pos].value == ')':
                self.pos += 1
        
        # Parse body
        body = []
        if self.pos < len(self.tokens) and self.tokens[self.pos].value == '{':
            self.pos += 1
            while self.pos < len(self.tokens) and self.tokens[self.pos].value != '}':
                stmt = self._parse_statement()
                if stmt:
                    body.append(stmt)
            if self.pos < len(self.tokens) and self.tokens[self.pos].value == '}':
                self.pos += 1
        
        return {
            'type': 'function',
            'name': name,
            'params': params,
            'body': body
        }
    
    def _parse_class(self) -> Dict[str, Any]:
        """Parse class declaration."""
        self.pos += 1  # Skip 'class'
        
        name = ''
        if self.pos < len(self.tokens) and self.tokens[self.pos].type == 'IDENTIFIER':
            name = self.tokens[self.pos].value
            self.pos += 1
        
        methods = []
        method_nodes = []
        
        if self.pos < len(self.tokens) and self.tokens[self.pos].value == '{':
            self.pos += 1
            while self.pos < len(self.tokens) and self.tokens[self.pos].value != '}':
                # Parse method
                if self.pos < len(self.tokens) and self.tokens[self.pos].type == 'IDENTIFIER':
                    method_name = self.tokens[self.pos].value
                    self.pos += 1
                    
                    if self.pos < len(self.tokens) and self.tokens[self.pos].value == '(':
                        # It's a method
                        method_node = self._parse_function()
                        if method_node:
                            method_node['name'] = method_name
                            methods.append(method_name)
                            method_nodes.append(method_node)
                    else:
                        # Property - skip for now
                        while self.pos < len(self.tokens) and self.tokens[self.pos].value != ';':
                            self.pos += 1
                        if self.pos < len(self.tokens):
                            self.pos += 1
                else:
                    self.pos += 1
            if self.pos < len(self.tokens) and self.tokens[self.pos].value == '}':
                self.pos += 1
        
        return {
            'type': 'class',
            'name': name,
            'methods': methods,
            'method_nodes': method_nodes
        }
    
    def _parse_if(self) -> Dict[str, Any]:
        """Parse if statement."""
        self.pos += 1  # Skip 'if'
        
        condition = ''
        if self.pos < len(self.tokens) and self.tokens[self.pos].value == '(':
            self.pos += 1
            while self.pos < len(self.tokens) and self.tokens[self.pos].value != ')':
                condition += self.tokens[self.pos].value
                self.pos += 1
            if self.pos < len(self.tokens) and self.tokens[self.pos].value == ')':
                self.pos += 1
        
        # Parse body
        body = []
        if self.pos < len(self.tokens) and self.tokens[self.pos].value == '{':
            self.pos += 1
            while self.pos < len(self.tokens) and self.tokens[self.pos].value != '}':
                stmt = self._parse_statement()
                if stmt:
                    body.append(stmt)
            if self.pos < len(self.tokens) and self.tokens[self.pos].value == '}':
                self.pos += 1
        else:
            # Single statement
            stmt = self._parse_statement()
            if stmt:
                body.append(stmt)
        
        # Parse else
        else_body = []
        if self.pos < len(self.tokens) and self.tokens[self.pos].value == 'else':
            self.pos += 1
            if self.pos < len(self.tokens) and self.tokens[self.pos].value == 'if':
                # else if
                else_node = self._parse_if()
                else_body = [else_node]
            else:
                if self.pos < len(self.tokens) and self.tokens[self.pos].value == '{':
                    self.pos += 1
                    while self.pos < len(self.tokens) and self.tokens[self.pos].value != '}':
                        stmt = self._parse_statement()
                        if stmt:
                            else_body.append(stmt)
                    if self.pos < len(self.tokens) and self.tokens[self.pos].value == '}':
                        self.pos += 1
                else:
                    stmt = self._parse_statement()
                    if stmt:
                        else_body.append(stmt)
        
        return {
            'type': 'if',
            'condition': condition,
            'body': body,
            'else_body': else_body
        }
    
    def _parse_for(self) -> Dict[str, Any]:
        """Parse for/for-of/for-in loop."""
        self.pos += 1  # Skip 'for'
        
        header = ''
        if self.pos < len(self.tokens) and self.tokens[self.pos].value == '(':
            self.pos += 1
            while self.pos < len(self.tokens) and self.tokens[self.pos].value != ')':
                header += self.tokens[self.pos].value
                self.pos += 1
            if self.pos < len(self.tokens) and self.tokens[self.pos].value == ')':
                self.pos += 1
        
        body = []
        if self.pos < len(self.tokens) and self.tokens[self.pos].value == '{':
            self.pos += 1
            while self.pos < len(self.tokens) and self.tokens[self.pos].value != '}':
                stmt = self._parse_statement()
                if stmt:
                    body.append(stmt)
            if self.pos < len(self.tokens) and self.tokens[self.pos].value == '}':
                self.pos += 1
        else:
            stmt = self._parse_statement()
            if stmt:
                body.append(stmt)
        
        return {
            'type': 'for',
            'header': header,
            'body': body
        }
    
    def _parse_while(self) -> Dict[str, Any]:
        """Parse while loop."""
        self.pos += 1  # Skip 'while'
        
        condition = ''
        if self.pos < len(self.tokens) and self.tokens[self.pos].value == '(':
            self.pos += 1
            while self.pos < len(self.tokens) and self.tokens[self.pos].value != ')':
                condition += self.tokens[self.pos].value
                self.pos += 1
            if self.pos < len(self.tokens) and self.tokens[self.pos].value == ')':
                self.pos += 1
        
        body = []
        if self.pos < len(self.tokens) and self.tokens[self.pos].value == '{':
            self.pos += 1
            while self.pos < len(self.tokens) and self.tokens[self.pos].value != '}':
                stmt = self._parse_statement()
                if stmt:
                    body.append(stmt)
            if self.pos < len(self.tokens) and self.tokens[self.pos].value == '}':
                self.pos += 1
        else:
            stmt = self._parse_statement()
            if stmt:
                body.append(stmt)
        
        return {
            'type': 'while',
            'condition': condition,
            'body': body
        }
    
    def _parse_do_while(self) -> Dict[str, Any]:
        """Parse do-while loop."""
        self.pos += 1  # Skip 'do'
        
        body = []
        if self.pos < len(self.tokens) and self.tokens[self.pos].value == '{':
            self.pos += 1
            while self.pos < len(self.tokens) and self.tokens[self.pos].value != '}':
                stmt = self._parse_statement()
                if stmt:
                    body.append(stmt)
            if self.pos < len(self.tokens) and self.tokens[self.pos].value == '}':
                self.pos += 1
        
        condition = ''
        if self.pos < len(self.tokens) and self.tokens[self.pos].value == 'while':
            self.pos += 1
            if self.pos < len(self.tokens) and self.tokens[self.pos].value == '(':
                self.pos += 1
                while self.pos < len(self.tokens) and self.tokens[self.pos].value != ')':
                    condition += self.tokens[self.pos].value
                    self.pos += 1
                if self.pos < len(self.tokens) and self.tokens[self.pos].value == ')':
                    self.pos += 1
        
        return {
            'type': 'do_while',
            'condition': condition,
            'body': body
        }
    
    def _parse_switch(self) -> Dict[str, Any]:
        """Parse switch statement."""
        self.pos += 1  # Skip 'switch'
        
        expression = ''
        if self.pos < len(self.tokens) and self.tokens[self.pos].value == '(':
            self.pos += 1
            while self.pos < len(self.tokens) and self.tokens[self.pos].value != ')':
                expression += self.tokens[self.pos].value
                self.pos += 1
            if self.pos < len(self.tokens) and self.tokens[self.pos].value == ')':
                self.pos += 1
        
        cases = []
        if self.pos < len(self.tokens) and self.tokens[self.pos].value == '{':
            self.pos += 1
            while self.pos < len(self.tokens) and self.tokens[self.pos].value != '}':
                if self.tokens[self.pos].value == 'case':
                    self.pos += 1
                    case_value = ''
                    while self.pos < len(self.tokens) and self.tokens[self.pos].value != ':':
                        case_value += self.tokens[self.pos].value
                        self.pos += 1
                    if self.pos < len(self.tokens) and self.tokens[self.pos].value == ':':
                        self.pos += 1
                    
                    case_body = []
                    while self.pos < len(self.tokens) and self.tokens[self.pos].value not in ['case', 'default', '}']:
                        stmt = self._parse_statement()
                        if stmt:
                            case_body.append(stmt)
                    
                    cases.append({
                        'type': 'case',
                        'value': case_value,
                        'body': case_body
                    })
                elif self.tokens[self.pos].value == 'default':
                    self.pos += 1
                    if self.pos < len(self.tokens) and self.tokens[self.pos].value == ':':
                        self.pos += 1
                    
                    default_body = []
                    while self.pos < len(self.tokens) and self.tokens[self.pos].value != '}':
                        stmt = self._parse_statement()
                        if stmt:
                            default_body.append(stmt)
                    
                    cases.append({
                        'type': 'default',
                        'body': default_body
                    })
                else:
                    self.pos += 1
            if self.pos < len(self.tokens) and self.tokens[self.pos].value == '}':
                self.pos += 1
        
        return {
            'type': 'switch',
            'expression': expression,
            'cases': cases
        }
    
    def _parse_try(self) -> Dict[str, Any]:
        """Parse try-catch-finally."""
        self.pos += 1  # Skip 'try'
        
        body = []
        if self.pos < len(self.tokens) and self.tokens[self.pos].value == '{':
            self.pos += 1
            while self.pos < len(self.tokens) and self.tokens[self.pos].value != '}':
                stmt = self._parse_statement()
                if stmt:
                    body.append(stmt)
            if self.pos < len(self.tokens) and self.tokens[self.pos].value == '}':
                self.pos += 1
        
        catches = []
        while self.pos < len(self.tokens) and self.tokens[self.pos].value == 'catch':
            self.pos += 1
            catch_param = ''
            if self.pos < len(self.tokens) and self.tokens[self.pos].value == '(':
                self.pos += 1
                while self.pos < len(self.tokens) and self.tokens[self.pos].value != ')':
                    catch_param += self.tokens[self.pos].value
                    self.pos += 1
                if self.pos < len(self.tokens) and self.tokens[self.pos].value == ')':
                    self.pos += 1
            
            catch_body = []
            if self.pos < len(self.tokens) and self.tokens[self.pos].value == '{':
                self.pos += 1
                while self.pos < len(self.tokens) and self.tokens[self.pos].value != '}':
                    stmt = self._parse_statement()
                    if stmt:
                        catch_body.append(stmt)
                if self.pos < len(self.tokens) and self.tokens[self.pos].value == '}':
                    self.pos += 1
            
            catches.append({
                'type': 'catch',
                'param': catch_param,
                'body': catch_body
            })
        
        finally_body = []
        if self.pos < len(self.tokens) and self.tokens[self.pos].value == 'finally':
            self.pos += 1
            if self.pos < len(self.tokens) and self.tokens[self.pos].value == '{':
                self.pos += 1
                while self.pos < len(self.tokens) and self.tokens[self.pos].value != '}':
                    stmt = self._parse_statement()
                    if stmt:
                        finally_body.append(stmt)
                if self.pos < len(self.tokens) and self.tokens[self.pos].value == '}':
                    self.pos += 1
        
        return {
            'type': 'try',
            'body': body,
            'catches': catches,
            'finally_body': finally_body
        }
    
    def _parse_return(self) -> Dict[str, Any]:
        """Parse return statement."""
        self.pos += 1  # Skip 'return'
        
        value = ''
        while self.pos < len(self.tokens) and self.tokens[self.pos].value != ';':
            value += self.tokens[self.pos].value
            self.pos += 1
        
        if self.pos < len(self.tokens) and self.tokens[self.pos].value == ';':
            self.pos += 1
        
        return {
            'type': 'return',
            'value': value
        }
    
    def _parse_throw(self) -> Dict[str, Any]:
        """Parse throw statement."""
        self.pos += 1  # Skip 'throw'
        
        value = ''
        while self.pos < len(self.tokens) and self.tokens[self.pos].value != ';':
            value += self.tokens[self.pos].value
            self.pos += 1
        
        if self.pos < len(self.tokens) and self.tokens[self.pos].value == ';':
            self.pos += 1
        
        return {
            'type': 'throw',
            'value': value
        }
    
    def _parse_declaration(self) -> Dict[str, Any]:
        """Parse variable declaration."""
        var_type = self.tokens[self.pos].value
        self.pos += 1
        
        names = []
        while self.pos < len(self.tokens) and self.tokens[self.pos].value != ';':
            if self.tokens[self.pos].type == 'IDENTIFIER':
                names.append(self.tokens[self.pos].value)
            self.pos += 1
        
        if self.pos < len(self.tokens) and self.tokens[self.pos].value == ';':
            self.pos += 1
        
        return {
            'type': 'declaration',
            'var_type': var_type,
            'names': names
        }
    
    def _parse_expression_statement(self) -> Dict[str, Any]:
        """Parse expression statement."""
        expr = ''
        while self.pos < len(self.tokens) and self.tokens[self.pos].value != ';':
            expr += self.tokens[self.pos].value
            self.pos += 1
        
        if self.pos < len(self.tokens) and self.tokens[self.pos].value == ';':
            self.pos += 1
        
        return {
            'type': 'expression',
            'value': expr
        }
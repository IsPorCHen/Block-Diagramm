"""AST builder for Go source code."""

from typing import List, Dict, Any, Optional, Union
import re


class GoASTBuilder:
    """Builds AST from Go tokens."""
    
    def __init__(self, max_depth: int = 100):
        self.pos = 0
        self.tokens = []
        self.max_depth = max_depth
        self.depth = 0
    
    def build(self, tokens: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build AST from tokens."""
        self.tokens = tokens
        self.pos = 0
        self.depth = 0
        
        ast = {
            'type': 'program',
            'body': [],
            'imports': [],
            'package': None
        }
        
        # Parse package declaration
        if self._peek('keyword', 'package'):
            pkg = self._consume()
            if self._peek('identifier'):
                name = self._consume()
                ast['package'] = name['value']
        
        # Parse imports
        if self._peek('keyword', 'import'):
            self.pos += 1
            imports = self._parse_imports()
            ast['imports'] = imports
        
        # Parse functions, types, vars, constants
        while self.pos < len(self.tokens) and self.depth < self.max_depth:
            token = self.tokens[self.pos]
            
            if token['type'] == 'keyword':
                if token['value'] == 'func':
                    func = self._parse_function()
                    if func:
                        ast['body'].append(func)
                elif token['value'] == 'type':
                    type_def = self._parse_type_declaration()
                    if type_def:
                        ast['body'].append(type_def)
                elif token['value'] == 'var':
                    var_def = self._parse_variable()
                    if var_def:
                        ast['body'].append(var_def)
                elif token['value'] == 'const':
                    const_def = self._parse_constant()
                    if const_def:
                        ast['body'].append(const_def)
                else:
                    self.pos += 1
            else:
                self.pos += 1
        
        return ast
    
    def _parse_imports(self) -> List[str]:
        """Parse import statements."""
        imports = []
        
        if self._peek('punctuation', '('):
            self.pos += 1  # Consume (
            while self.pos < len(self.tokens) and not self._peek('punctuation', ')'):
                if self._peek('string'):
                    token = self._consume()
                    imports.append(token['value'].strip('"'))
                elif self._peek('identifier'):
                    # Alias import
                    self.pos += 1
                    if self._peek('string'):
                        token = self._consume()
                        imports.append(token['value'].strip('"'))
                else:
                    self.pos += 1
            if self._peek('punctuation', ')'):
                self.pos += 1
        else:
            if self._peek('string'):
                token = self._consume()
                imports.append(token['value'].strip('"'))
        
        return imports
    
    def _parse_function(self) -> Optional[Dict[str, Any]]:
        """Parse a function declaration."""
        self.depth += 1
        if self.depth > self.max_depth:
            self.depth -= 1
            return None
        
        func = {
            'type': 'function',
            'name': None,
            'params': [],
            'returns': [],
            'body': [],
            'is_method': False,
            'receiver': None
        }
        
        self.pos += 1  # Consume 'func'
        
        # Check for receiver (method)
        if self._peek('punctuation', '('):
            self.pos += 1  # Consume (
            if self._peek('identifier'):
                receiver = self._consume()
                if self._peek('identifier') or self._peek('operator', '*'):
                    # Type name
                    type_name = self._consume() if self._peek('identifier') else None
                    if type_name:
                        func['is_method'] = True
                        func['receiver'] = {
                            'name': receiver['value'],
                            'type': type_name['value']
                        }
                    else:
                        # Pointer receiver
                        self.pos += 1  # Skip *
                        if self._peek('identifier'):
                            type_name = self._consume()
                            func['is_method'] = True
                            func['receiver'] = {
                                'name': receiver['value'],
                                'type': '*' + type_name['value']
                            }
            if self._peek('punctuation', ')'):
                self.pos += 1
        
        # Function name
        if self._peek('identifier'):
            name = self._consume()
            func['name'] = name['value']
        else:
            self.depth -= 1
            return None
        
        # Parameters
        if self._peek('punctuation', '('):
            self.pos += 1
            params = []
            while self.pos < len(self.tokens) and not self._peek('punctuation', ')'):
                if self._peek('identifier') or self._peek('operator', '...'):
                    if self._peek('operator', '...'):
                        self.pos += 1  # Skip ...
                    name = self._consume()
                    if self._peek('identifier') or self._peek('operator', '*'):
                        type_name = self._consume() if self._peek('identifier') else None
                        if type_name:
                            params.append({
                                'name': name['value'],
                                'type': type_name['value']
                            })
                        else:
                            # Pointer type
                            self.pos += 1  # Skip *
                            if self._peek('identifier'):
                                type_name = self._consume()
                                params.append({
                                    'name': name['value'],
                                    'type': '*' + type_name['value']
                                })
                    else:
                        # Type-only parameter (e.g., int, string)
                        params.append({
                            'name': name['value'],
                            'type': None
                        })
                else:
                    # Just type
                    type_name = self._consume() if self._peek('identifier') else None
                    if type_name:
                        params.append({
                            'name': '',
                            'type': type_name['value']
                        })
                    else:
                        self.pos += 1
                
                if self._peek('punctuation', ','):
                    self.pos += 1
            if self._peek('punctuation', ')'):
                self.pos += 1
            func['params'] = params
        
        # Return values
        if self._peek('identifier') or self._peek('punctuation', '('):
            returns = self._parse_type()
            if isinstance(returns, list):
                func['returns'] = returns
            elif returns:
                func['returns'] = [returns]
        
        # Function body
        if self._peek('punctuation', '{'):
            self.pos += 1
            body = self._parse_block()
            func['body'] = body
            if self._peek('punctuation', '}'):
                self.pos += 1
        
        self.depth -= 1
        return func
    
    def _parse_type(self) -> Union[str, List[str], None]:
        """Parse a type declaration."""
        if self._peek('punctuation', '('):
            self.pos += 1
            types = []
            while self.pos < len(self.tokens) and not self._peek('punctuation', ')'):
                if self._peek('identifier'):
                    types.append(self._consume()['value'])
                else:
                    self.pos += 1
            if self._peek('punctuation', ')'):
                self.pos += 1
            return types
        elif self._peek('identifier'):
            return self._consume()['value']
        elif self._peek('operator', '*'):
            self.pos += 1
            if self._peek('identifier'):
                return '*' + self._consume()['value']
        elif self._peek('operator', '...'):
            self.pos += 1
            if self._peek('identifier'):
                return '...' + self._consume()['value']
        return None
    
    def _parse_block(self) -> List[Dict[str, Any]]:
        """Parse a block of statements."""
        self.depth += 1
        if self.depth > self.max_depth:
            self.depth -= 1
            return []
        
        statements = []
        max_iter = 1000
        iter_count = 0
        
        while self.pos < len(self.tokens) and not self._peek('punctuation', '}') and iter_count < max_iter:
            iter_count += 1
            # Skip semicolons
            if self._peek('punctuation', ';'):
                self.pos += 1
                continue
            
            stmt = self._parse_statement()
            if stmt:
                statements.append(stmt)
        
        self.depth -= 1
        return statements
    
    def _parse_statement(self) -> Optional[Dict[str, Any]]:
        """Parse a single statement."""
        if self.pos >= len(self.tokens):
            return None
        
        token = self.tokens[self.pos]
        
        if token['type'] == 'keyword':
            if token['value'] == 'if':
                return self._parse_if()
            elif token['value'] == 'for':
                return self._parse_for()
            elif token['value'] == 'switch':
                return self._parse_switch()
            elif token['value'] == 'return':
                return self._parse_return()
            elif token['value'] == 'break':
                self.pos += 1
                return {'type': 'break'}
            elif token['value'] == 'continue':
                self.pos += 1
                return {'type': 'continue'}
            elif token['value'] == 'defer':
                return self._parse_defer()
            elif token['value'] == 'go':
                return self._parse_go()
            elif token['value'] == 'var':
                return self._parse_var_declaration()
            elif token['value'] == 'const':
                return self._parse_const_declaration()
            elif token['value'] == 'goto':
                self.pos += 1
                if self._peek('identifier'):
                    label = self._consume()
                    return {'type': 'goto', 'label': label['value']}
                return {'type': 'goto'}
        
        # Assignment or expression
        if token['type'] == 'identifier' or token['type'] == 'operator':
            return self._parse_assignment_or_call()
        
        # Skip unknown tokens
        self.pos += 1
        return None
    
    def _parse_if(self) -> Dict[str, Any]:
        """Parse an if statement."""
        if_stmt = {
            'type': 'if',
            'condition': None,
            'body': [],
            'else_body': None
        }
        
        self.pos += 1  # Consume 'if'
        
        # Check for initialization (e.g., if x := 1; x > 0)
        init = None
        if self._peek('identifier'):
            # Try to parse init
            temp_pos = self.pos
            if self._parse_assignment_or_call():
                init = self._parse_assignment_or_call()
                if self._peek('punctuation', ';'):
                    self.pos += 1
        
        # Parse condition
        condition = self._parse_condition()
        if condition:
            if_stmt['condition'] = condition
        elif init:
            if_stmt['condition'] = init
        
        # Parse body
        if self._peek('punctuation', '{'):
            self.pos += 1
            body = self._parse_block()
            if_stmt['body'] = body
            if self._peek('punctuation', '}'):
                self.pos += 1
        
        # Parse else
        if self._peek('keyword', 'else'):
            self.pos += 1
            if self._peek('keyword', 'if'):
                else_if = self._parse_if()
                if_stmt['else_body'] = [else_if]
            elif self._peek('punctuation', '{'):
                self.pos += 1
                else_body = self._parse_block()
                if_stmt['else_body'] = else_body
                if self._peek('punctuation', '}'):
                    self.pos += 1
        
        return if_stmt
    
    def _parse_for(self) -> Dict[str, Any]:
        """Parse a for loop."""
        for_stmt = {
            'type': 'for',
            'init': None,
            'condition': None,
            'post': None,
            'body': [],
            'is_range': False
        }
        
        self.pos += 1  # Consume 'for'
        
        # Check for range
        if self._peek_identifier_or_underscore():
            # Parse init part
            init = self._parse_assignment_or_call()
            if init:
                for_stmt['init'] = init
            
            # Check for range
            if self._peek('keyword', 'range'):
                self.pos += 1
                for_stmt['is_range'] = True
                if self._peek('identifier'):
                    range_expr = self._consume()
                    for_stmt['range_expr'] = range_expr['value']
                elif self._peek('operator'):
                    range_expr = self._consume()
                    if self._peek('identifier'):
                        range_expr = range_expr['value'] + self._consume()['value']
                        for_stmt['range_expr'] = range_expr
        
        # If not range, parse condition
        if not for_stmt['is_range'] and not self._peek('punctuation', '{'):
            condition = self._parse_condition()
            if condition:
                for_stmt['condition'] = condition
        
        # Parse body
        if self._peek('punctuation', '{'):
            self.pos += 1
            body = self._parse_block()
            for_stmt['body'] = body
            if self._peek('punctuation', '}'):
                self.pos += 1
        
        return for_stmt
    
    def _parse_switch(self) -> Dict[str, Any]:
        """Parse a switch statement."""
        switch_stmt = {
            'type': 'switch',
            'expression': None,
            'cases': []
        }
        
        self.pos += 1  # Consume 'switch'
        
        # Parse expression
        expr = self._parse_condition()
        if expr:
            switch_stmt['expression'] = expr
        
        # Parse body
        if self._peek('punctuation', '{'):
            self.pos += 1
            while self.pos < len(self.tokens) and not self._peek('punctuation', '}'):
                if self._peek('keyword', 'case'):
                    self.pos += 1
                    case_expr = self._parse_condition()
                    body = []
                    # Parse case body until next case or default or }
                    while self.pos < len(self.tokens) and not self._peek('keyword', 'case') and not self._peek('keyword', 'default') and not self._peek('punctuation', '}'):
                        if self._peek('punctuation', ';'):
                            self.pos += 1
                            continue
                        stmt = self._parse_statement()
                        if stmt:
                            body.append(stmt)
                    switch_stmt['cases'].append({
                        'type': 'case',
                        'expression': case_expr,
                        'body': body
                    })
                elif self._peek('keyword', 'default'):
                    self.pos += 1
                    body = []
                    while self.pos < len(self.tokens) and not self._peek('keyword', 'case') and not self._peek('keyword', 'default') and not self._peek('punctuation', '}'):
                        if self._peek('punctuation', ';'):
                            self.pos += 1
                            continue
                        stmt = self._parse_statement()
                        if stmt:
                            body.append(stmt)
                    switch_stmt['cases'].append({
                        'type': 'default',
                        'body': body
                    })
                else:
                    # Skip unknown tokens
                    self.pos += 1
            if self._peek('punctuation', '}'):
                self.pos += 1
        
        return switch_stmt
    
    def _parse_return(self) -> Dict[str, Any]:
        """Parse a return statement."""
        self.pos += 1  # Consume 'return'
        expr = self._parse_condition()
        return {
            'type': 'return',
            'value': expr
        }
    
    def _parse_defer(self) -> Dict[str, Any]:
        """Parse a defer statement."""
        self.pos += 1  # Consume 'defer'
        call = self._parse_function_call()
        return {
            'type': 'defer',
            'call': call
        }
    
    def _parse_go(self) -> Dict[str, Any]:
        """Parse a go statement."""
        self.pos += 1  # Consume 'go'
        call = self._parse_function_call()
        return {
            'type': 'go',
            'call': call
        }
    
    def _parse_var_declaration(self) -> Dict[str, Any]:
        """Parse a variable declaration."""
        self.pos += 1  # Consume 'var'
        return self._parse_declaration('var')
    
    def _parse_const_declaration(self) -> Dict[str, Any]:
        """Parse a constant declaration."""
        self.pos += 1  # Consume 'const'
        return self._parse_declaration('const')
    
    def _parse_declaration(self, kind: str) -> Dict[str, Any]:
        """Parse variable or constant declaration."""
        decl = {
            'type': kind,
            'name': None,
            'type': None,
            'value': None
        }
        
        if self._peek('identifier'):
            name = self._consume()
            decl['name'] = name['value']
            
            if self._peek('identifier') or self._peek('operator', '*'):
                if self._peek('operator', '*'):
                    self.pos += 1
                    if self._peek('identifier'):
                        type_name = self._consume()
                        decl['type'] = '*' + type_name['value']
                else:
                    type_name = self._consume()
                    decl['type'] = type_name['value']
            
            if self._peek('operator', '='):
                self.pos += 1
                value = self._parse_condition()
                decl['value'] = value
        
        # Handle multiple declarations
        if self._peek('punctuation', ','):
            self.pos += 1
            if self._peek('identifier'):
                decl2 = self._parse_declaration(kind)
                if decl2:
                    decl['name'] = decl['name'] + ', ' + decl2['name']
                    decl['value'] = decl['value']
        
        return decl
    
    def _parse_assignment_or_call(self) -> Optional[Dict[str, Any]]:
        """Parse an assignment or function call."""
        if self._peek('identifier'):
            name = self._consume()
            
            # Check if it's a function call
            if self._peek('punctuation', '('):
                return self._parse_function_call_with_name(name['value'])
            
            # Check for chained access (e.g., person.Name)
            if self._peek('punctuation', '.'):
                self.pos += 1
                if self._peek('identifier'):
                    field = self._consume()
                    # Check if it's a method call
                    if self._peek('punctuation', '('):
                        return self._parse_function_call_with_name(f"{name['value']}.{field['value']}")
                    # Assignment to field
                    if self._peek('operator', '=') or self._peek('operator', ':='):
                        op = self._consume()
                        value = self._parse_condition()
                        return {
                            'type': 'assignment',
                            'target': f"{name['value']}.{field['value']}",
                            'operator': op['value'],
                            'value': value
                        }
            
            # Check for assignment
            if self._peek('operator', '=') or self._peek('operator', ':='):
                op = self._consume()
                value = self._parse_condition()
                return {
                    'type': 'assignment',
                    'target': name['value'],
                    'operator': op['value'],
                    'value': value
                }
            
            # Simple expression
            return {
                'type': 'expr',
                'value': name['value']
            }
        
        return None
    
    def _parse_function_call(self) -> Dict[str, Any]:
        """Parse a function call."""
        if self._peek('identifier'):
            name = self._consume()
            return self._parse_function_call_with_name(name['value'])
        return {'type': 'call', 'name': 'unknown'}
    
    def _parse_function_call_with_name(self, name: str) -> Dict[str, Any]:
        """Parse a function call with known name."""
        call = {
            'type': 'call',
            'name': name,
            'args': []
        }
        
        if self._peek('punctuation', '('):
            self.pos += 1
            while self.pos < len(self.tokens) and not self._peek('punctuation', ')'):
                arg = self._parse_condition()
                if arg:
                    call['args'].append(arg)
                if self._peek('punctuation', ','):
                    self.pos += 1
            if self._peek('punctuation', ')'):
                self.pos += 1
        
        return call
    
    def _parse_condition(self) -> Any:
        """Parse a condition or expression."""
        if self._peek('identifier'):
            return self._consume()['value']
        elif self._peek('number'):
            return self._consume()['value']
        elif self._peek('string'):
            return self._consume()['value']
        elif self._peek('operator'):
            # Parse operator chain
            op = self._consume()['value']
            right = None
            if self._peek('identifier') or self._peek('number') or self._peek('string'):
                right = self._parse_condition()
            if right:
                return f"{op} {right}"
            return op
        elif self._peek('punctuation', '('):
            self.pos += 1
            expr = self._parse_condition()
            if self._peek('punctuation', ')'):
                self.pos += 1
            return expr
        elif self._peek('punctuation', '-'):
            self.pos += 1
            if self._peek('number'):
                num = self._consume()
                return f"-{num['value']}"
        return None
    
    def _parse_type_declaration(self) -> Optional[Dict[str, Any]]:
        """Parse a type declaration."""
        self.depth += 1
        if self.depth > self.max_depth:
            self.depth -= 1
            return None
        
        self.pos += 1  # Consume 'type'
        
        type_def = {
            'type': 'type',
            'name': None,
            'kind': None,
            'fields': []
        }
        
        if self._peek('identifier'):
            name = self._consume()
            type_def['name'] = name['value']
            
            if self._peek('keyword', 'struct'):
                self.pos += 1
                type_def['kind'] = 'struct'
                if self._peek('punctuation', '{'):
                    self.pos += 1
                    while self.pos < len(self.tokens) and not self._peek('punctuation', '}') and self.depth < self.max_depth:
                        if self._peek('identifier'):
                            field = self._consume()
                            if self._peek('identifier') or self._peek('operator', '*'):
                                if self._peek('operator', '*'):
                                    self.pos += 1
                                    if self._peek('identifier'):
                                        field_type = self._consume()
                                        type_def['fields'].append({
                                            'name': field['value'],
                                            'type': '*' + field_type['value']
                                        })
                                else:
                                    field_type = self._consume()
                                    type_def['fields'].append({
                                        'name': field['value'],
                                        'type': field_type['value']
                                    })
                            else:
                                # Field without type (maybe error)
                                pass
                        elif self._peek('identifier'):
                            # Embedded field
                            embedded = self._consume()
                            type_def['fields'].append({
                                'name': '',
                                'type': embedded['value']
                            })
                        else:
                            self.pos += 1
                    if self._peek('punctuation', '}'):
                        self.pos += 1
            elif self._peek('keyword', 'interface'):
                self.pos += 1
                type_def['kind'] = 'interface'
                if self._peek('punctuation', '{'):
                    self.pos += 1
                    while self.pos < len(self.tokens) and not self._peek('punctuation', '}'):
                        if self._peek('identifier'):
                            method = self._consume()
                            if self._peek('punctuation', '('):
                                self.pos += 1
                                params = []
                                while self.pos < len(self.tokens) and not self._peek('punctuation', ')'):
                                    if self._peek('identifier'):
                                        param = self._consume()
                                        if self._peek('identifier'):
                                            param_type = self._consume()
                                            params.append({
                                                'name': param['value'],
                                                'type': param_type['value']
                                            })
                                        else:
                                            params.append({'name': param['value'], 'type': None})
                                    else:
                                        self.pos += 1
                                if self._peek('punctuation', ')'):
                                    self.pos += 1
                                returns = None
                                if self._peek('identifier') or self._peek('operator', '*'):
                                    returns = self._parse_type()
                                type_def['fields'].append({
                                    'name': method['value'],
                                    'type': 'method',
                                    'params': params,
                                    'returns': returns
                                })
                        else:
                            self.pos += 1
                    if self._peek('punctuation', '}'):
                        self.pos += 1
        
        self.depth -= 1
        return type_def
    
    def _parse_variable(self) -> Dict[str, Any]:
        """Parse a variable declaration."""
        # Simplified: just consume var declaration
        self.pos += 1  # Consume 'var'
        return {'type': 'var'}
    
    def _parse_constant(self) -> Dict[str, Any]:
        """Parse a constant declaration."""
        # Simplified: just consume const declaration
        self.pos += 1  # Consume 'const'
        return {'type': 'const'}
    
    def _peek(self, token_type: str, value: Optional[str] = None) -> bool:
        """Peek at the next token."""
        if self.pos >= len(self.tokens):
            return False
        token = self.tokens[self.pos]
        if token['type'] != token_type:
            return False
        if value is not None and token['value'] != value:
            return False
        return True
    
    def _peek_identifier_or_underscore(self) -> bool:
        """Check if the next token is an identifier or underscore."""
        if self.pos >= len(self.tokens):
            return False
        token = self.tokens[self.pos]
        return token['type'] == 'identifier' or token['value'] == '_'
    
    def _consume(self) -> Dict[str, Any]:
        """Consume and return the next token."""
        if self.pos >= len(self.tokens):
            return {'type': 'eof', 'value': ''}
        token = self.tokens[self.pos]
        self.pos += 1
        return token
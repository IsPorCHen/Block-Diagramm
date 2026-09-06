"""Statement handlers for Go AST."""

from typing import List, Dict, Any, Tuple, Union, Optional
from app.parsers.core.graph_builder import GraphBuilder


class GoHandlers:
    """Handles Go statements and builds flowchart nodes."""
    
    def __init__(self, graph: GraphBuilder):
        self.graph = graph
        self._return_marker = 'return'
        self._no_empty_marker = 'no_empty'
    
    def process_body(self, statements: List[Dict[str, Any]], prev_ids: List[Union[int, Tuple]]) -> List[Union[int, Tuple]]:
        """Process a list of statements."""
        current_prev = prev_ids
        returns = []
        
        for stmt in statements:
            # Skip function/type definitions inside body
            if stmt.get('type') in ['function', 'type', 'interface']:
                continue
            
            # Filter out returns
            non_returns = [p for p in current_prev if not self._is_return(p)]
            new_returns = [p for p in current_prev if self._is_return(p)]
            returns.extend(new_returns)
            
            if not non_returns:
                break
            
            result = self._handle_statement(stmt, non_returns)
            current_prev = result
        
        return current_prev + returns
    
    def _handle_statement(self, stmt: Dict[str, Any], prev_ids: List[Union[int, Tuple]]) -> List[Union[int, Tuple]]:
        """Handle a single statement."""
        stmt_type = stmt.get('type')
        
        if stmt_type == 'assignment' or stmt_type == 'var' or stmt_type == 'const':
            return self._handle_assignment(stmt, prev_ids)
        elif stmt_type == 'call':
            return self._handle_call(stmt, prev_ids)
        elif stmt_type == 'if':
            return self._handle_if(stmt, prev_ids)
        elif stmt_type == 'for':
            return self._handle_for(stmt, prev_ids)
        elif stmt_type == 'switch':
            return self._handle_switch(stmt, prev_ids)
        elif stmt_type == 'return':
            return self._handle_return(stmt, prev_ids)
        elif stmt_type == 'break':
            return self._handle_break(prev_ids)
        elif stmt_type == 'continue':
            return self._handle_continue(prev_ids)
        elif stmt_type == 'defer':
            return self._handle_defer(stmt, prev_ids)
        elif stmt_type == 'go':
            return self._handle_go(stmt, prev_ids)
        
        return prev_ids
    
    def _handle_assignment(self, stmt: Dict[str, Any], prev_ids: List[Union[int, Tuple]]) -> List[Union[int, Tuple]]:
        """Handle an assignment statement."""
        target = stmt.get('target', '')
        operator = stmt.get('operator', '=')
        value = self._format_expression(stmt.get('value'))
        
        if target:
            text = f'{target} {operator} {value}'
        else:
            text = value if value else 'assignment'
        
        node_id = self._add_node('process', text, prev_ids)
        return [node_id]
    
    def _handle_call(self, stmt: Dict[str, Any], prev_ids: List[Union[int, Tuple]]) -> List[Union[int, Tuple]]:
        """Handle a function call."""
        name = stmt.get('name', '')
        args = stmt.get('args', [])
        
        # Check for print/output functions
        if name in ['fmt.Println', 'fmt.Printf', 'fmt.Print', 'println', 'print']:
            text = f'{name}({", ".join(self._format_expression(arg) for arg in args)})'
            node_id = self._add_node('output', text, prev_ids)
        elif name in ['fmt.Scan', 'fmt.Scanln', 'input', 'scanf']:
            node_id = self._add_node('input', f'{name}()', prev_ids)
        else:
            text = f'{name}({", ".join(self._format_expression(arg) for arg in args)})'
            node_id = self._add_node('process', text, prev_ids)
        
        return [node_id]
    
    def _handle_if(self, stmt: Dict[str, Any], prev_ids: List[Union[int, Tuple]]) -> List[Union[int, Tuple]]:
        """Handle an if statement."""
        condition = self._format_expression(stmt.get('condition'))
        cond_id = self._add_node('condition', f'{condition}?', prev_ids)
        
        # Yes branch
        if stmt.get('body'):
            yes_ids = self.process_body(stmt['body'], [cond_id])
            self._mark_edge(cond_id, 'да', 'yes')
        else:
            yes_ids = []
        
        exit_ids = list(yes_ids) if yes_ids else []
        
        # No branch (else)
        if stmt.get('else_body'):
            no_ids = self.process_body(stmt['else_body'], [cond_id])
            self._mark_edge(cond_id, 'нет', 'no')
            exit_ids.extend(no_ids)
        else:
            exit_ids.append((self._no_empty_marker, cond_id))
        
        return [e for e in exit_ids if e is not None] or [None]
    
    def _handle_for(self, stmt: Dict[str, Any], prev_ids: List[Union[int, Tuple]]) -> List[Union[int, Tuple]]:
        """Handle a for loop."""
        if stmt.get('is_range'):
            # Range loop
            range_expr = stmt.get('range_expr', '')
            loop_id = self._add_node('loop', f'for range {range_expr}', prev_ids)
        else:
            # Regular for loop
            condition = self._format_expression(stmt.get('condition'))
            if condition:
                loop_id = self._add_node('loop', f'for {condition}', prev_ids)
            else:
                # Infinite loop
                loop_id = self._add_node('loop', 'for (бесконечный)', prev_ids)
        
        if stmt.get('body'):
            body_ids = self.process_body(stmt['body'], [loop_id])
            self._mark_edge(loop_id, '', 'loop_body')
            
            for bid in body_ids:
                if bid is not None and not isinstance(bid, tuple):
                    self.graph.add_edge(bid, loop_id, '', 'loop_back')
        
        return [loop_id]
    
    def _handle_switch(self, stmt: Dict[str, Any], prev_ids: List[Union[int, Tuple]]) -> List[Union[int, Tuple]]:
        """Handle a switch statement."""
        expr = self._format_expression(stmt.get('expression'))
        
        if expr:
            switch_id = self._add_node('condition', f'switch {expr}', prev_ids)
        else:
            switch_id = self._add_node('condition', 'switch', prev_ids)
        
        exit_ids = []
        
        cases = stmt.get('cases', [])
        for i, case in enumerate(cases):
            if case.get('type') == 'default':
                case_id = self._add_node('process', 'default:', [switch_id])
                label = 'default'
                branch = f'case_{i}'
            else:
                case_expr = self._format_expression(case.get('expression'))
                case_id = self._add_node('process', f'case {case_expr}:', [switch_id])
                label = case_expr if case_expr else f'case {i}'
                branch = f'case_{i}'
            
            self.graph.add_edge(switch_id, case_id, label, branch)
            
            if case.get('body'):
                body_ids = self.process_body(case['body'], [case_id])
                exit_ids.extend(body_ids)
            else:
                exit_ids.append(case_id)
        
        return [e for e in exit_ids if e is not None] or [None]
    
    def _handle_return(self, stmt: Dict[str, Any], prev_ids: List[Union[int, Tuple]]) -> List[Union[int, Tuple]]:
        """Handle a return statement."""
        value = self._format_expression(stmt.get('value'))
        if value:
            node_id = self._add_node('output', f'return {value}', prev_ids)
        else:
            node_id = self._add_node('output', 'return', prev_ids)
        return [(self._return_marker, node_id)]
    
    def _handle_break(self, prev_ids: List[Union[int, Tuple]]) -> List[Union[int, Tuple]]:
        """Handle a break statement."""
        self._add_node('process', 'break', prev_ids)
        return [None]
    
    def _handle_continue(self, prev_ids: List[Union[int, Tuple]]) -> List[Union[int, Tuple]]:
        """Handle a continue statement."""
        self._add_node('process', 'continue', prev_ids)
        return [None]
    
    def _handle_defer(self, stmt: Dict[str, Any], prev_ids: List[Union[int, Tuple]]) -> List[Union[int, Tuple]]:
        """Handle a defer statement."""
        call = stmt.get('call', {})
        name = call.get('name', '')
        args = call.get('args', [])
        text = f'defer {name}({", ".join(self._format_expression(arg) for arg in args)})'
        node_id = self._add_node('process', text, prev_ids)
        return [node_id]
    
    def _handle_go(self, stmt: Dict[str, Any], prev_ids: List[Union[int, Tuple]]) -> List[Union[int, Tuple]]:
        """Handle a go statement."""
        call = stmt.get('call', {})
        name = call.get('name', '')
        args = call.get('args', [])
        text = f'go {name}({", ".join(self._format_expression(arg) for arg in args)})'
        node_id = self._add_node('process', text, prev_ids)
        return [node_id]
    
    def _add_node(self, node_type: str, text: str, prev_ids: List[Union[int, Tuple]]) -> int:
        """Add a node and connect from prev_ids."""
        node_id = self.graph.add_node(node_type, text)
        for pid in prev_ids:
            if pid is None:
                continue
            if isinstance(pid, tuple):
                marker, node_id_from = pid
                if marker == self._no_empty_marker:
                    self.graph.add_edge(node_id_from, node_id, 'нет', 'no')
                elif marker == self._return_marker:
                    # Return marker: don't connect from return
                    pass
            else:
                self.graph.add_edge(pid, node_id)
        return node_id
    
    def _mark_edge(self, from_id: int, label: str, branch: str):
        """Mark the first edge from a node with label and branch."""
        for edge in reversed(self.graph.edge_factory.get_edges()):
            if edge.from_id == from_id and not edge.branch:
                edge.label = label
                edge.branch = branch
                break
    
    def _format_expression(self, expr) -> str:
        """Format an expression to string."""
        if expr is None:
            return ''
        if isinstance(expr, (int, float, bool)):
            return str(expr)
        if isinstance(expr, list):
            return ', '.join(self._format_expression(e) for e in expr)
        if isinstance(expr, dict):
            return expr.get('value', str(expr))
        return str(expr)
    
    def _is_return(self, value) -> bool:
        """Check if value is a return marker."""
        return isinstance(value, tuple) and value[0] == self._return_marker
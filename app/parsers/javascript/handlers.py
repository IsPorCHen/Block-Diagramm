"""Statement handlers for JavaScript AST."""

from typing import List, Dict, Any, Tuple, Union
from app.parsers.core.graph_builder import GraphBuilder


class JavaScriptHandlers:
    """Handles JavaScript statements and builds flowchart nodes."""
    
    def __init__(self, graph: GraphBuilder):
        self.graph = graph
    
    def process_body(self, statements: List[Dict[str, Any]], 
                     prev_ids: List[Union[int, Tuple]]) -> List[Union[int, Tuple]]:
        """Process a list of statements."""
        current_prev = prev_ids
        returns = []
        
        for stmt in statements:
            if not stmt:
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
    
    def _handle_statement(self, stmt: Dict[str, Any], 
                          prev_ids: List[Union[int, Tuple]]) -> List[Union[int, Tuple]]:
        """Handle a single statement."""
        stmt_type = stmt.get('type', '')
        
        if stmt_type == 'function':
            return prev_ids  # Skip function declarations inside body
        elif stmt_type == 'if':
            return self._handle_if(stmt, prev_ids)
        elif stmt_type == 'for':
            return self._handle_for(stmt, prev_ids)
        elif stmt_type == 'while':
            return self._handle_while(stmt, prev_ids)
        elif stmt_type == 'do_while':
            return self._handle_do_while(stmt, prev_ids)
        elif stmt_type == 'switch':
            return self._handle_switch(stmt, prev_ids)
        elif stmt_type == 'try':
            return self._handle_try(stmt, prev_ids)
        elif stmt_type == 'return':
            return self._handle_return(stmt, prev_ids)
        elif stmt_type == 'throw':
            return self._handle_throw(stmt, prev_ids)
        elif stmt_type == 'break':
            return self._handle_break(prev_ids)
        elif stmt_type == 'continue':
            return self._handle_continue(prev_ids)
        elif stmt_type == 'declaration':
            return self._handle_declaration(stmt, prev_ids)
        else:
            return self._handle_expression(stmt, prev_ids)
    
    def _handle_if(self, stmt: Dict[str, Any], 
                   prev_ids: List[Union[int, Tuple]]) -> List[Union[int, Tuple]]:
        """Handle if statement."""
        condition = stmt.get('condition', '?')
        cond_id = self._add_node('condition', f'{condition}?', prev_ids)
        
        # Yes branch
        body = stmt.get('body', [])
        yes_ids = self.process_body(body, [cond_id]) if body else []
        self._mark_edge(cond_id, 'да', 'yes')
        
        exit_ids = list(yes_ids) if yes_ids else []
        
        # No branch
        else_body = stmt.get('else_body', [])
        if else_body:
            no_ids = self.process_body(else_body, [cond_id])
            self._mark_edge(cond_id, 'нет', 'no')
            exit_ids.extend(no_ids)
        else:
            exit_ids.append(('no_empty', cond_id))
        
        return [e for e in exit_ids if e is not None] or [None]
    
    def _handle_for(self, stmt: Dict[str, Any], 
                    prev_ids: List[Union[int, Tuple]]) -> List[Union[int, Tuple]]:
        """Handle for loop."""
        header = stmt.get('header', '...')
        loop_id = self._add_node('loop', f'for ({header})', prev_ids)
        
        body = stmt.get('body', [])
        if body:
            body_ids = self.process_body(body, [loop_id])
            self._mark_edge(loop_id, '', 'loop_body')
            
            for bid in body_ids:
                if bid is not None and not isinstance(bid, tuple):
                    self.graph.add_edge(bid, loop_id, '', 'loop_back')
        
        return [loop_id]
    
    def _handle_while(self, stmt: Dict[str, Any], 
                      prev_ids: List[Union[int, Tuple]]) -> List[Union[int, Tuple]]:
        """Handle while loop."""
        condition = stmt.get('condition', '?')
        loop_id = self._add_node('loop', f'while ({condition})', prev_ids)
        
        body = stmt.get('body', [])
        if body:
            body_ids = self.process_body(body, [loop_id])
            self._mark_edge(loop_id, '', 'loop_body')
            
            for bid in body_ids:
                if bid is not None and not isinstance(bid, tuple):
                    self.graph.add_edge(bid, loop_id, '', 'loop_back')
        
        return [loop_id]
    
    def _handle_do_while(self, stmt: Dict[str, Any], 
                         prev_ids: List[Union[int, Tuple]]) -> List[Union[int, Tuple]]:
        """Handle do-while loop."""
        body = stmt.get('body', [])
        condition = stmt.get('condition', '?')
        
        # Process body first
        body_ids = self.process_body(body, prev_ids)
        
        # Add condition after body
        cond_id = self.graph.add_node('condition', f'{condition}?')
        for bid in body_ids:
            if bid is not None and not isinstance(bid, tuple):
                self.graph.add_edge(bid, cond_id)
        
        # Connect back to first body node
        first_body_id = None
        for node in self.graph._nodes:
            if node.type == 'process' or node.type == 'input' or node.type == 'output':
                first_body_id = node.id
                break
        
        if first_body_id is not None:
            self.graph.add_edge(cond_id, first_body_id, 'да', 'yes')
        
        return [('no_empty', cond_id)]
    
    def _handle_switch(self, stmt: Dict[str, Any], 
                       prev_ids: List[Union[int, Tuple]]) -> List[Union[int, Tuple]]:
        """Handle switch statement."""
        expr = stmt.get('expression', '?')
        cases = stmt.get('cases', [])
        exit_ids = []
        current_prev = prev_ids
        
        for case in cases:
            if case.get('type') == 'case':
                case_value = case.get('value', '')
                cond_id = self._add_node('condition', f'{expr} == {case_value}?', current_prev)
                
                case_body = case.get('body', [])
                if case_body:
                    case_ids = self.process_body(case_body, [cond_id])
                    self._mark_edge(cond_id, 'да', 'yes')
                    exit_ids.extend(case_ids)
                else:
                    exit_ids.append(cond_id)
                
                current_prev = [('no_empty', cond_id)]
            else:  # default
                default_body = case.get('body', [])
                if default_body:
                    default_ids = self.process_body(default_body, current_prev)
                    exit_ids.extend(default_ids)
                else:
                    exit_ids.extend(current_prev)
                current_prev = []
        
        if current_prev:
            exit_ids.extend(current_prev)
        
        return [e for e in exit_ids if e is not None] or [None]
    
    def _handle_try(self, stmt: Dict[str, Any], 
                    prev_ids: List[Union[int, Tuple]]) -> List[Union[int, Tuple]]:
        """Handle try-catch-finally."""
        try_id = self._add_node('try_start', 'try', prev_ids)
        exit_ids = []
        
        body = stmt.get('body', [])
        if body:
            body_ids = self.process_body(body, [try_id])
            exit_ids.extend(body_ids)
        
        catches = stmt.get('catches', [])
        for catch in catches:
            catch_param = catch.get('param', '')
            catch_text = f'catch ({catch_param})' if catch_param else 'catch'
            catch_id = self._add_node('except', catch_text, [try_id])
            self.graph.add_edge(try_id, catch_id, 'ошибка', 'exception')
            
            catch_body = catch.get('body', [])
            if catch_body:
                catch_ids = self.process_body(catch_body, [catch_id])
                exit_ids.extend(catch_ids)
        
        finally_body = stmt.get('finally_body', [])
        if finally_body:
            finally_id = self._add_node('finally', 'finally', exit_ids)
            exit_ids = self.process_body(finally_body, [finally_id])
        
        return [e for e in exit_ids if e is not None] or [None]
    
    def _handle_return(self, stmt: Dict[str, Any], 
                       prev_ids: List[Union[int, Tuple]]) -> List[Union[int, Tuple]]:
        """Handle return statement."""
        value = stmt.get('value', '')
        text = f'return {value}' if value else 'return'
        ret_id = self._add_node('output', text, prev_ids)
        return [('return', ret_id)]
    
    def _handle_throw(self, stmt: Dict[str, Any], 
                      prev_ids: List[Union[int, Tuple]]) -> List[Union[int, Tuple]]:
        """Handle throw statement."""
        value = stmt.get('value', '')
        text = f'throw {value}' if value else 'throw'
        self._add_node('process', text, prev_ids)
        return [None]
    
    def _handle_break(self, prev_ids: List[Union[int, Tuple]]) -> List[Union[int, Tuple]]:
        """Handle break statement."""
        self._add_node('process', 'break', prev_ids)
        return [None]
    
    def _handle_continue(self, prev_ids: List[Union[int, Tuple]]) -> List[Union[int, Tuple]]:
        """Handle continue statement."""
        self._add_node('process', 'continue', prev_ids)
        return [None]
    
    def _handle_declaration(self, stmt: Dict[str, Any], 
                            prev_ids: List[Union[int, Tuple]]) -> List[Union[int, Tuple]]:
        """Handle variable declaration."""
        var_type = stmt.get('var_type', '')
        names = stmt.get('names', [])
        text = f'{var_type} {", ".join(names)}'
        node_id = self._add_node('process', text, prev_ids)
        return [node_id]
    
    def _handle_expression(self, stmt: Dict[str, Any], 
                           prev_ids: List[Union[int, Tuple]]) -> List[Union[int, Tuple]]:
        """Handle expression statement."""
        value = stmt.get('value', '')
        if value:
            # Check for console.log
            if 'console.log' in value or 'console.error' in value:
                node_id = self._add_node('output', value, prev_ids)
            else:
                node_id = self._add_node('process', value, prev_ids)
            return [node_id]
        return prev_ids
    
    def _add_node(self, node_type: str, text: str, 
                  prev_ids: List[Union[int, Tuple]]) -> int:
        """Add a node and connect from prev_ids."""
        node_id = self.graph.add_node(node_type, text)
        for pid in prev_ids:
            if pid is None:
                continue
            if isinstance(pid, tuple):
                marker, node_id_from = pid
                if marker == 'no_empty':
                    self.graph.add_edge(node_id_from, node_id, 'нет', 'no')
                elif marker == 'from_no_branch':
                    self.graph.add_edge(node_id_from, node_id, '', 'from_no')
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
    
    def _is_return(self, value) -> bool:
        return isinstance(value, tuple) and value[0] == 'return'
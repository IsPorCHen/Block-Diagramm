"""Statement handlers for Python AST."""

import ast
from typing import List, Dict, Any, Tuple, Union
from app.parsers.core.graph_builder import GraphBuilder
from app.parsers.python.formatter import PythonFormatter


class PythonHandlers:
    """Handles Python statements and builds flowchart nodes."""
    
    def __init__(self, graph: GraphBuilder):
        self.graph = graph
        self.formatter = PythonFormatter()
    
    def process_body(self, statements: List[ast.stmt], prev_ids: List[Union[int, Tuple]]) -> List[Union[int, Tuple]]:
        """Process a list of statements."""
        current_prev = prev_ids
        returns = []
        
        for stmt in statements:
            # Skip function/class definitions inside body
            if isinstance(stmt, (ast.FunctionDef, ast.ClassDef)):
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
    
    def _handle_statement(self, stmt: ast.stmt, prev_ids: List[Union[int, Tuple]]) -> List[Union[int, Tuple]]:
        """Handle a single statement."""
        if isinstance(stmt, ast.Assign):
            return self._handle_assign(stmt, prev_ids)
        elif isinstance(stmt, ast.AugAssign):
            return self._handle_aug_assign(stmt, prev_ids)
        elif isinstance(stmt, ast.Expr):
            return self._handle_expr(stmt, prev_ids)
        elif isinstance(stmt, ast.If):
            return self._handle_if(stmt, prev_ids)
        elif isinstance(stmt, ast.While):
            return self._handle_while(stmt, prev_ids)
        elif isinstance(stmt, ast.For):
            return self._handle_for(stmt, prev_ids)
        elif isinstance(stmt, ast.Try):
            return self._handle_try(stmt, prev_ids)
        elif isinstance(stmt, ast.Return):
            return self._handle_return(stmt, prev_ids)
        elif isinstance(stmt, ast.Raise):
            return self._handle_raise(stmt, prev_ids)
        elif isinstance(stmt, ast.Break):
            return self._handle_break(prev_ids)
        elif isinstance(stmt, ast.Continue):
            return self._handle_continue(prev_ids)
        elif isinstance(stmt, ast.Pass):
            return prev_ids
        return prev_ids
    
    def _handle_assign(self, stmt: ast.Assign, prev_ids: List[Union[int, Tuple]]) -> List[Union[int, Tuple]]:
        targets = ', '.join(self.formatter.format(t) for t in stmt.targets)
        value = self.formatter.format(stmt.value)
        node_id = self._add_node('process', f'{targets} = {value}', prev_ids)
        return [node_id]
    
    def _handle_aug_assign(self, stmt: ast.AugAssign, prev_ids: List[Union[int, Tuple]]) -> List[Union[int, Tuple]]:
        target = self.formatter.format(stmt.target)
        op = self.formatter._get_op(stmt.op)
        value = self.formatter.format(stmt.value)
        node_id = self._add_node('process', f'{target} {op}= {value}', prev_ids)
        return [node_id]
    
    def _handle_expr(self, stmt: ast.Expr, prev_ids: List[Union[int, Tuple]]) -> List[Union[int, Tuple]]:
        if isinstance(stmt.value, ast.Call):
            func_name = self.formatter.format(stmt.value.func)
            args = ', '.join(self.formatter.format(arg) for arg in stmt.value.args)
            
            if func_name in ['print', 'output']:
                node_id = self._add_node('output', f'{func_name}({args})', prev_ids)
            elif func_name == 'input':
                node_id = self._add_node('input', 'Ввод данных', prev_ids)
            else:
                node_id = self._add_node('process', f'{func_name}({args})', prev_ids)
            return [node_id]
        return prev_ids
    
    def _handle_if(self, stmt: ast.If, prev_ids: List[Union[int, Tuple]]) -> List[Union[int, Tuple]]:
        condition = self.formatter.format(stmt.test)
        cond_id = self._add_node('condition', f'{condition}?', prev_ids)
        
        # Yes branch
        if stmt.body:
            yes_ids = self.process_body(stmt.body, [cond_id])
            self._mark_edge(cond_id, 'да', 'yes')
        else:
            yes_ids = []
        
        exit_ids = list(yes_ids) if yes_ids else []
        
        # No branch
        if stmt.orelse:
            no_ids = self.process_body(stmt.orelse, [cond_id])
            self._mark_edge(cond_id, 'нет', 'no')
            exit_ids.extend(no_ids)
        else:
            exit_ids.append(('no_empty', cond_id))
        
        return [e for e in exit_ids if e is not None] or [None]
    
    def _handle_while(self, stmt: ast.While, prev_ids: List[Union[int, Tuple]]) -> List[Union[int, Tuple]]:
        condition = self.formatter.format(stmt.test)
        loop_id = self._add_node('loop', condition, prev_ids)
        
        if stmt.body:
            body_ids = self.process_body(stmt.body, [loop_id])
            self._mark_edge(loop_id, '', 'loop_body')
            
            for bid in body_ids:
                if bid is not None and not isinstance(bid, tuple):
                    self.graph.add_edge(bid, loop_id, '', 'loop_back')
        
        return [loop_id]
    
    def _handle_for(self, stmt: ast.For, prev_ids: List[Union[int, Tuple]]) -> List[Union[int, Tuple]]:
        target = self.formatter.format(stmt.target)
        iter_val = self.formatter.format(stmt.iter)
        loop_id = self._add_node('loop', f'для {target} в {iter_val}', prev_ids)
        
        if stmt.body:
            body_ids = self.process_body(stmt.body, [loop_id])
            self._mark_edge(loop_id, '', 'loop_body')
            
            for bid in body_ids:
                if bid is not None and not isinstance(bid, tuple):
                    self.graph.add_edge(bid, loop_id, '', 'loop_back')
        
        return [loop_id]
    
    def _handle_try(self, stmt: ast.Try, prev_ids: List[Union[int, Tuple]]) -> List[Union[int, Tuple]]:
        try_id = self._add_node('try_start', 'try', prev_ids)
        exit_ids = []
        
        if stmt.body:
            body_ids = self.process_body(stmt.body, [try_id])
            exit_ids.extend(body_ids)
        
        for handler in stmt.handlers:
            exc_name = self.formatter.format(handler.type) if handler.type else ''
            if handler.name:
                exc_text = f'except {exc_name} as {handler.name}'
            else:
                exc_text = f'except {exc_name}' if exc_name else 'except'
            
            except_id = self._add_node('except', exc_text, [try_id])
            self.graph.add_edge(try_id, except_id, 'ошибка', 'exception')
            
            if handler.body:
                body_ids = self.process_body(handler.body, [except_id])
                exit_ids.extend(body_ids)
        
        return [e for e in exit_ids if e is not None] or [None]
    
    def _handle_return(self, stmt: ast.Return, prev_ids: List[Union[int, Tuple]]) -> List[Union[int, Tuple]]:
        if stmt.value:
            value = self.formatter.format(stmt.value)
            node_id = self._add_node('output', f'return {value}', prev_ids)
        else:
            node_id = self._add_node('output', 'return', prev_ids)
        return [('return', node_id)]
    
    def _handle_raise(self, stmt: ast.Raise, prev_ids: List[Union[int, Tuple]]) -> List[Union[int, Tuple]]:
        if stmt.exc:
            exc_text = self.formatter.format(stmt.exc)
            node_id = self._add_node('process', f'raise {exc_text}', prev_ids)
        else:
            node_id = self._add_node('process', 'raise', prev_ids)
        return [None]
    
    def _handle_break(self, prev_ids: List[Union[int, Tuple]]) -> List[Union[int, Tuple]]:
        self._add_node('process', 'break', prev_ids)
        return [None]
    
    def _handle_continue(self, prev_ids: List[Union[int, Tuple]]) -> List[Union[int, Tuple]]:
        self._add_node('process', 'continue', prev_ids)
        return [None]
    
    def _add_node(self, node_type: str, text: str, prev_ids: List[Union[int, Tuple]]) -> int:
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
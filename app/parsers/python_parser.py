import ast
from typing import Dict, Any, List, Optional, Tuple, Union
from app.parsers.base_parser import BaseParser
from app.builders.flowchart_builder import FlowchartBuilder
from app.utils.code_cleaner import CodeCleaner


class PythonParser(BaseParser):
    """Python language parser."""
    
    def get_language(self) -> str:
        return 'python'
    
    def get_extension(self) -> str:
        return '.py'
    
    def parse(self, code: str) -> Dict[str, Any]:
        """Parse Python code and generate flowchart."""
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return {'error': f'Синтаксическая ошибка: строка {e.lineno}'}
        
        functions = []
        classes = []
        
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                builder = FlowchartBuilder()
                self._build_function(node, builder)
                functions.append({
                    'name': node.name,
                    'type': 'function',
                    'flowchart': builder.get_flowchart_data()
                })
            elif isinstance(node, ast.ClassDef):
                class_builder = FlowchartBuilder()
                self._build_class(node, class_builder)
                classes.append({
                    'name': node.name,
                    'type': 'class',
                    'flowchart': class_builder.get_flowchart_data()
                })
                
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        method_builder = FlowchartBuilder()
                        self._build_function(item, method_builder)
                        functions.append({
                            'name': f'{node.name}.{item.name}',
                            'type': 'method',
                            'flowchart': method_builder.get_flowchart_data()
                        })
        
        # Main body
        main_builder = FlowchartBuilder()
        main_body = [stmt for stmt in tree.body 
                     if not isinstance(stmt, (ast.FunctionDef, ast.ClassDef))]
        
        main_flowchart = {'nodes': [], 'edges': []}
        if main_body:
            start_id = main_builder.add_node('start', 'начало main()')
            last_ids = self._process_body(main_body, main_builder, [start_id])
            end_id = main_builder.add_node('end', '')
            for lid in last_ids:
                if lid is None:
                    continue
                if isinstance(lid, tuple) and lid[0] == 'no_empty':
                    main_builder.add_edge(lid[1], end_id, 'нет', 'no')
                elif isinstance(lid, tuple) and lid[0] == 'from_no_branch':
                    main_builder.add_edge(lid[1], end_id, '', 'from_no')
                else:
                    main_builder.add_edge(lid, end_id)
            main_flowchart = main_builder.get_flowchart_data()
        
        return {
            'success': True,
            'main_flowchart': main_flowchart,
            'functions': functions,
            'classes': classes,
            'code': code
        }
    
    def _build_function(self, node: ast.FunctionDef, builder: FlowchartBuilder):
        """Build flowchart for a function."""
        start_id = builder.add_node('start', f'начало {node.name}()')
        prev_ids = [start_id]
        
        if node.args.args:
            params = ', '.join([arg.arg for arg in node.args.args])
            param_id = builder.add_node('input', f'Параметры: {params}')
            builder.add_edge(start_id, param_id)
            prev_ids = [param_id]
        
        body = [stmt for stmt in node.body 
                if not (isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant))]
        
        last_ids = self._process_body(body, builder, prev_ids)
        
        end_id = builder.add_node('end', '')
        for lid in last_ids:
            if lid is None:
                continue
            if isinstance(lid, tuple) and lid[0] == 'no_empty':
                builder.add_edge(lid[1], end_id, 'нет', 'no')
            elif isinstance(lid, tuple) and lid[0] == 'from_no_branch':
                builder.add_edge(lid[1], end_id, '', 'from_no')
            elif isinstance(lid, tuple) and lid[0] == 'return':
                builder.add_edge(lid[1], end_id)
            else:
                builder.add_edge(lid, end_id)
    
    def _build_class(self, node: ast.ClassDef, builder: FlowchartBuilder):
        """Build flowchart for a class."""
        class_id = builder.add_node('class_start', node.name)
        
        fields = []
        methods = []
        
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                methods.append(item.name)
                if item.name == '__init__':
                    for stmt in item.body:
                        if isinstance(stmt, ast.Assign):
                            for target in stmt.targets:
                                if isinstance(target, ast.Attribute) and \
                                   isinstance(target.value, ast.Name) and \
                                   target.value.id == 'self':
                                    fields.append(target.attr)
            elif isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        fields.append(target.id)
        
        if fields:
            fields_text = ', '.join(fields)
            fields_id = builder.add_node('input', f'Поля: {fields_text}')
            builder.add_edge(class_id, fields_id)
            source_id = fields_id
        else:
            source_id = class_id
        
        for i, method_name in enumerate(methods):
            method_id = builder.add_node('method', method_name + '()')
            builder.add_edge(source_id, method_id, '', f'fan_{i}')
    
    def _process_body(self, statements: List[ast.stmt], builder: FlowchartBuilder, 
                      prev_ids: List[Union[int, Tuple]]) -> List[Union[int, Tuple]]:
        """Process a list of statements."""
        current_prev_ids = prev_ids
        return_ids = []
        
        for stmt in statements:
            if isinstance(stmt, (ast.FunctionDef, ast.ClassDef)):
                continue
            
            non_return_ids = [p for p in current_prev_ids if not (isinstance(p, tuple) and p[0] == 'return')]
            new_return_ids = [p for p in current_prev_ids if isinstance(p, tuple) and p[0] == 'return']
            return_ids.extend(new_return_ids)
            
            if non_return_ids:
                new_prev_ids = self._process_statement(stmt, builder, non_return_ids)
                current_prev_ids = new_prev_ids
            else:
                break
        
        return current_prev_ids + return_ids
    
    def _process_statement(self, stmt: ast.stmt, builder: FlowchartBuilder, 
                          prev_ids: List[Union[int, Tuple]]) -> List[Union[int, Tuple]]:
        """Process a single statement."""
        
        def add_edges_from_prev(target_id: int):
            for pid in prev_ids:
                if pid is None:
                    continue
                if isinstance(pid, tuple) and pid[0] == 'no_empty':
                    builder.add_edge(pid[1], target_id, 'нет', 'no')
                elif isinstance(pid, tuple) and pid[0] == 'from_no_branch':
                    builder.add_edge(pid[1], target_id, '', 'from_no')
                else:
                    builder.add_edge(pid, target_id)
        
        if isinstance(stmt, ast.Assign):
            targets = ', '.join([self._get_name(t) for t in stmt.targets])
            value = self._get_expr_text(stmt.value)
            node_id = builder.add_node('process', f'{targets} = {value}')
            add_edges_from_prev(node_id)
            return [node_id]
        
        elif isinstance(stmt, ast.AugAssign):
            target = self._get_name(stmt.target)
            op = self._get_op(stmt.op)
            value = self._get_expr_text(stmt.value)
            node_id = builder.add_node('process', f'{target} {op}= {value}')
            add_edges_from_prev(node_id)
            return [node_id]
        
        elif isinstance(stmt, ast.Expr):
            if isinstance(stmt.value, ast.Call):
                func_name = self._get_name(stmt.value.func)
                args = ', '.join([self._get_expr_text(arg) for arg in stmt.value.args])
                
                if func_name in ['print', 'output']:
                    node_id = builder.add_node('output', f'{func_name}({args})')
                elif func_name == 'input':
                    node_id = builder.add_node('input', 'Ввод данных')
                else:
                    node_id = builder.add_node('process', f'{func_name}({args})')
                    
                add_edges_from_prev(node_id)
                return [node_id]
            return prev_ids
        
        elif isinstance(stmt, ast.If):
            return self._process_if(stmt, builder, prev_ids)
        
        elif isinstance(stmt, ast.While):
            return self._process_while(stmt, builder, prev_ids)
        
        elif isinstance(stmt, ast.For):
            return self._process_for(stmt, builder, prev_ids)
        
        elif isinstance(stmt, ast.Try):
            return self._process_try(stmt, builder, prev_ids)
        
        elif isinstance(stmt, ast.Return):
            if stmt.value:
                value = self._get_expr_text(stmt.value)
                node_id = builder.add_node('output', f'return {value}')
            else:
                node_id = builder.add_node('output', 'return')
            add_edges_from_prev(node_id)
            return [('return', node_id)]
        
        elif isinstance(stmt, ast.Raise):
            if stmt.exc:
                exc_text = self._get_expr_text(stmt.exc)
                node_id = builder.add_node('process', f'raise {exc_text}')
            else:
                node_id = builder.add_node('process', 'raise')
            add_edges_from_prev(node_id)
            return [None]
        
        elif isinstance(stmt, ast.Break):
            node_id = builder.add_node('process', 'break')
            add_edges_from_prev(node_id)
            return [None]
        
        elif isinstance(stmt, ast.Continue):
            node_id = builder.add_node('process', 'continue')
            add_edges_from_prev(node_id)
            return [None]
        
        elif isinstance(stmt, ast.Pass):
            return prev_ids
        
        return prev_ids
    
    def _process_if(self, stmt: ast.If, builder: FlowchartBuilder,
                   prev_ids: List[Union[int, Tuple]]) -> List[Union[int, Tuple]]:
        """Process if statement."""
        condition = self._get_expr_text(stmt.test)
        cond_id = builder.add_node('condition', condition + '?')
        
        for pid in prev_ids:
            if pid is None:
                continue
            if isinstance(pid, tuple) and pid[0] == 'no_empty':
                builder.add_edge(pid[1], cond_id, 'нет', 'no')
            elif isinstance(pid, tuple) and pid[0] == 'from_no_branch':
                builder.add_edge(pid[1], cond_id, '', 'from_no')
            elif isinstance(pid, tuple) and pid[0] == 'return':
                pass
            else:
                builder.add_edge(pid, cond_id)
        
        exit_ids = []
        
        # Yes branch
        if stmt.body:
            edge_idx = len(builder._flowchart.edges)
            yes_ids = self._process_body(stmt.body, builder, [cond_id])
            
            for i in range(edge_idx, len(builder._flowchart.edges)):
                if builder._flowchart.edges[i].from_id == cond_id and not builder._flowchart.edges[i].label:
                    builder._flowchart.edges[i].label = 'да'
                    builder._flowchart.edges[i].branch = 'yes'
                    break
            
            for yid in yes_ids:
                if yid is not None:
                    exit_ids.append(yid)
        
        # No branch
        if stmt.orelse:
            edge_idx = len(builder._flowchart.edges)
            
            if len(stmt.orelse) == 1 and isinstance(stmt.orelse[0], ast.If):
                no_ids = self._process_if(stmt.orelse[0], builder, [cond_id])
            else:
                no_ids = self._process_body(stmt.orelse, builder, [cond_id])
            
            for i in range(edge_idx, len(builder._flowchart.edges)):
                if builder._flowchart.edges[i].from_id == cond_id and not builder._flowchart.edges[i].label:
                    builder._flowchart.edges[i].label = 'нет'
                    builder._flowchart.edges[i].branch = 'no'
                    break
            
            for nid in no_ids:
                if nid is not None:
                    if isinstance(nid, tuple) and nid[0] == 'return':
                        exit_ids.append(nid)
                    elif isinstance(nid, tuple):
                        exit_ids.append(nid)
                    else:
                        exit_ids.append(nid)
        else:
            exit_ids.append(('no_empty', cond_id))
        
        exit_ids = [eid for eid in exit_ids if eid is not None]
        return exit_ids if exit_ids else [None]
    
    def _process_while(self, stmt: ast.While, builder: FlowchartBuilder,
                      prev_ids: List[Union[int, Tuple]]) -> List[Union[int, Tuple]]:
        """Process while loop."""
        condition = self._get_expr_text(stmt.test)
        loop_id = builder.add_node('loop', condition)
        
        for pid in prev_ids:
            if pid is None:
                continue
            if isinstance(pid, tuple) and pid[0] == 'no_empty':
                builder.add_edge(pid[1], loop_id, 'нет', 'no')
            elif isinstance(pid, tuple) and pid[0] == 'from_no_branch':
                builder.add_edge(pid[1], loop_id, '', 'from_no')
            else:
                builder.add_edge(pid, loop_id)
        
        if stmt.body:
            edge_idx = len(builder._flowchart.edges)
            body_ids = self._process_body(stmt.body, builder, [loop_id])
            
            for i in range(edge_idx, len(builder._flowchart.edges)):
                if builder._flowchart.edges[i].from_id == loop_id and not builder._flowchart.edges[i].label:
                    builder._flowchart.edges[i].branch = 'loop_body'
                    break
            
            for bid in body_ids:
                if bid is None:
                    continue
                if isinstance(bid, tuple) and bid[0] == 'no_empty':
                    builder.add_edge(bid[1], loop_id, '', 'loop_back')
                elif isinstance(bid, tuple) and bid[0] == 'from_no_branch':
                    builder.add_edge(bid[1], loop_id, '', 'loop_back')
                elif isinstance(bid, tuple) and bid[0] == 'return':
                    pass
                else:
                    builder.add_edge(bid, loop_id, '', 'loop_back')
        
        return [loop_id]
    
    def _process_for(self, stmt: ast.For, builder: FlowchartBuilder,
                    prev_ids: List[Union[int, Tuple]]) -> List[Union[int, Tuple]]:
        """Process for loop."""
        target = self._get_name(stmt.target)
        iter_val = self._get_expr_text(stmt.iter)
        
        loop_id = builder.add_node('loop', f'для {target} в {iter_val}')
        
        for pid in prev_ids:
            if pid is None:
                continue
            if isinstance(pid, tuple) and pid[0] == 'no_empty':
                builder.add_edge(pid[1], loop_id, 'нет', 'no')
            elif isinstance(pid, tuple) and pid[0] == 'from_no_branch':
                builder.add_edge(pid[1], loop_id, '', 'from_no')
            else:
                builder.add_edge(pid, loop_id)
        
        if stmt.body:
            edge_idx = len(builder._flowchart.edges)
            body_ids = self._process_body(stmt.body, builder, [loop_id])
            
            for i in range(edge_idx, len(builder._flowchart.edges)):
                if builder._flowchart.edges[i].from_id == loop_id and not builder._flowchart.edges[i].label:
                    builder._flowchart.edges[i].branch = 'loop_body'
                    break
            
            for bid in body_ids:
                if bid is None:
                    continue
                if isinstance(bid, tuple) and bid[0] == 'no_empty':
                    builder.add_edge(bid[1], loop_id, '', 'loop_back')
                elif isinstance(bid, tuple) and bid[0] == 'from_no_branch':
                    builder.add_edge(bid[1], loop_id, '', 'loop_back')
                elif isinstance(bid, tuple) and bid[0] == 'return':
                    pass
                else:
                    builder.add_edge(bid, loop_id, '', 'loop_back')
        
        return [loop_id]
    
    def _process_try(self, stmt: ast.Try, builder: FlowchartBuilder,
                    prev_ids: List[Union[int, Tuple]]) -> List[Union[int, Tuple]]:
        """Process try/except."""
        try_id = builder.add_node('try_start', 'try')
        
        for pid in prev_ids:
            if pid is None:
                continue
            if isinstance(pid, tuple) and pid[0] == 'no_empty':
                builder.add_edge(pid[1], try_id, 'нет', 'no')
            elif isinstance(pid, tuple) and pid[0] == 'from_no_branch':
                builder.add_edge(pid[1], try_id, '', 'from_no')
            else:
                builder.add_edge(pid, try_id)
        
        exit_ids = []
        
        if stmt.body:
            try_body_ids = self._process_body(stmt.body, builder, [try_id])
            exit_ids.extend(try_body_ids)
        
        for handler in stmt.handlers:
            if handler.type:
                exc_name = self._get_name(handler.type)
                if handler.name:
                    exc_text = f'except {exc_name} as {handler.name}'
                else:
                    exc_text = f'except {exc_name}'
            else:
                exc_text = 'except'
            
            except_id = builder.add_node('except', exc_text)
            builder.add_edge(try_id, except_id, 'ошибка', 'exception')
            
            if handler.body:
                except_body_ids = self._process_body(handler.body, builder, [except_id])
                exit_ids.extend(except_body_ids)
        
        if stmt.finalbody:
            finally_id = builder.add_node('finally', 'finally')
            
            return_markers = []
            for eid in exit_ids:
                if eid is None:
                    continue
                if isinstance(eid, tuple) and eid[0] == 'return':
                    builder.add_edge(eid[1], finally_id)
                    return_markers.append(eid)
                elif isinstance(eid, tuple):
                    builder.add_edge(eid[1], finally_id)
                else:
                    builder.add_edge(eid, finally_id)
            
            finally_body_ids = self._process_body(stmt.finalbody, builder, [finally_id])
            
            result = []
            for fid in finally_body_ids:
                if fid is not None:
                    result.append(fid)
            
            result.extend(return_markers)
            return result if result else [None]
        
        exit_ids = [eid for eid in exit_ids if eid is not None]
        return exit_ids if exit_ids else [None]
    
    def _get_name(self, node) -> str:
        """Get name from AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f'{self._get_name(node.value)}.{node.attr}'
        elif isinstance(node, ast.Subscript):
            return f'{self._get_name(node.value)}[{self._get_expr_text(node.slice)}]'
        elif isinstance(node, ast.Tuple):
            return ', '.join([self._get_name(e) for e in node.elts])
        return 'var'
    
    def _get_expr_text(self, node) -> str:
        """Get expression text from AST node."""
        if isinstance(node, ast.Constant):
            if isinstance(node.value, str):
                s = node.value
                if len(s) > 20:
                    s = s[:17] + '...'
                return f'"{s}"'
            return str(node.value)
        elif isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.BinOp):
            left = self._get_expr_text(node.left)
            right = self._get_expr_text(node.right)
            op = self._get_op(node.op)
            return f'{left} {op} {right}'
        elif isinstance(node, ast.UnaryOp):
            operand = self._get_expr_text(node.operand)
            op = self._get_unary_op(node.op)
            return f'{op}{operand}'
        elif isinstance(node, ast.Compare):
            left = self._get_expr_text(node.left)
            parts = [left]
            for op, comp in zip(node.ops, node.comparators):
                parts.append(self._get_op(op))
                parts.append(self._get_expr_text(comp))
            return ' '.join(parts)
        elif isinstance(node, ast.BoolOp):
            op = ' and ' if isinstance(node.op, ast.And) else ' or '
            values = [self._get_expr_text(v) for v in node.values]
            return op.join(values)
        elif isinstance(node, ast.Call):
            func = self._get_name(node.func)
            args = ', '.join([self._get_expr_text(arg) for arg in node.args])
            return f'{func}({args})'
        elif isinstance(node, ast.List):
            elements = ', '.join([self._get_expr_text(e) for e in node.elts])
            return f'[{elements}]'
        elif isinstance(node, ast.Tuple):
            elements = ', '.join([self._get_expr_text(e) for e in node.elts])
            return f'({elements})'
        elif isinstance(node, ast.Dict):
            items = []
            for k, v in zip(node.keys, node.values):
                if k is not None:
                    items.append(f'{self._get_expr_text(k)}: {self._get_expr_text(v)}')
            return '{' + ', '.join(items) + '}'
        elif isinstance(node, ast.Subscript):
            return f'{self._get_expr_text(node.value)}[{self._get_expr_text(node.slice)}]'
        elif isinstance(node, ast.Attribute):
            return f'{self._get_expr_text(node.value)}.{node.attr}'
        elif isinstance(node, ast.IfExp):
            return f'{self._get_expr_text(node.body)} if {self._get_expr_text(node.test)} else {self._get_expr_text(node.orelse)}'
        elif isinstance(node, ast.ListComp):
            return '[...]'
        elif isinstance(node, ast.Slice):
            lower = self._get_expr_text(node.lower) if node.lower else ''
            upper = self._get_expr_text(node.upper) if node.upper else ''
            return f'{lower}:{upper}'
        elif isinstance(node, ast.JoinedStr):
            parts = []
            for val in node.values:
                if isinstance(val, ast.Constant):
                    parts.append(str(val.value))
                elif isinstance(val, ast.FormattedValue):
                    parts.append('{' + self._get_expr_text(val.value) + '}')
                else:
                    parts.append(self._get_expr_text(val))
            result = ''.join(parts)
            if len(result) > 25:
                result = result[:22] + '...'
            return f'f"{result}"'
        return 'expr'
    
    def _get_op(self, op):
        """Get operator string."""
        ops = {
            ast.Add: '+', ast.Sub: '-', ast.Mult: '*', ast.Div: '/',
            ast.Mod: '%', ast.Pow: '**', ast.FloorDiv: '//',
            ast.Eq: '==', ast.NotEq: '!=', ast.Lt: '<', ast.LtE: '<=',
            ast.Gt: '>', ast.GtE: '>=', 
            ast.And: 'and', ast.Or: 'or',
            ast.In: 'in', ast.NotIn: 'not in',
            ast.Is: 'is', ast.IsNot: 'is not',
        }
        return ops.get(type(op), '?')
    
    def _get_unary_op(self, op):
        """Get unary operator string."""
        ops = {
            ast.Not: 'not ',
            ast.UAdd: '+',
            ast.USub: '-',
        }
        return ops.get(type(op), '?')
"""Main Python parser."""

import ast
from typing import Dict, Any, List
from app.parsers.base import BaseParser
from app.parsers.python.handlers import PythonHandlers


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
            return {'success': False, 'error': f'Синтаксическая ошибка: строка {e.lineno}'}
        
        handlers = PythonHandlers(self.graph)
        
        functions = []
        classes = []
        
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                flowchart = self._build_function(node, handlers)
                functions.append({
                    'name': node.name,
                    'type': 'function',
                    'flowchart': flowchart
                })
            elif isinstance(node, ast.ClassDef):
                flowchart, methods = self._build_class(node, handlers)
                classes.append({
                    'name': node.name,
                    'type': 'class',
                    'flowchart': flowchart
                })
                functions.extend(methods)
        
        # Main body
        main_body = [stmt for stmt in tree.body 
                     if not isinstance(stmt, (ast.FunctionDef, ast.ClassDef))]
        
        main_flowchart = self._build_main(main_body, handlers)
        
        return {
            'success': True,
            'main_flowchart': main_flowchart,
            'functions': functions,
            'classes': classes,
            'code': code
        }
    
    def _build_function(self, node: ast.FunctionDef, handlers: PythonHandlers) -> Dict[str, Any]:
        """Build flowchart for a function."""
        self.graph.reset()
        
        start_id = self.graph.add_node('start', f'начало {node.name}()')
        prev_ids = [start_id]
        
        if node.args.args:
            params = ', '.join([arg.arg for arg in node.args.args])
            param_id = self.graph.add_node('input', f'Параметры: {params}')
            self.graph.add_edge(start_id, param_id)
            prev_ids = [param_id]
        
        body = [stmt for stmt in node.body 
                if not (isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant))]
        
        last_ids = handlers.process_body(body, prev_ids)
        end_id = self.graph.add_node('end', '')
        self._connect_to_end(last_ids, end_id)
        
        return self.graph.to_dict()
    
    def _build_class(self, node: ast.ClassDef, handlers: PythonHandlers) -> tuple:
        """Build flowchart for a class."""
        self.graph.reset()
        
        class_id = self.graph.add_node('class_start', node.name)
        
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
            fields_id = self.graph.add_node('input', f'Поля: {", ".join(fields)}')
            self.graph.add_edge(class_id, fields_id)
            source_id = fields_id
        else:
            source_id = class_id
        
        for i, method_name in enumerate(methods):
            method_id = self.graph.add_node('method', f'{method_name}()')
            self.graph.add_edge(source_id, method_id, '', f'fan_{i}')
        
        flowchart = self.graph.to_dict()
        
        # Build method flowcharts
        method_flowcharts = []
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                method_flow = self._build_function(item, handlers)
                method_flowcharts.append({
                    'name': f'{node.name}.{item.name}',
                    'type': 'method',
                    'flowchart': method_flow
                })
        
        return flowchart, method_flowcharts
    
    def _build_main(self, body: List[ast.stmt], handlers: PythonHandlers) -> Dict[str, Any]:
        """Build flowchart for main code."""
        if not body:
            return {'nodes': [], 'edges': []}
        
        self.graph.reset()
        
        start_id = self.graph.add_node('start', 'начало main()')
        last_ids = handlers.process_body(body, [start_id])
        end_id = self.graph.add_node('end', '')
        self._connect_to_end(last_ids, end_id)
        
        return self.graph.to_dict()
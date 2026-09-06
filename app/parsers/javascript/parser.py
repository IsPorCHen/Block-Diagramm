"""Main JavaScript parser."""

from typing import Dict, Any, List, Optional, Tuple
from app.parsers.base import BaseParser
from app.parsers.javascript.handlers import JavaScriptHandlers
from app.parsers.javascript.tokenizer import JavaScriptTokenizer
from app.parsers.javascript.ast_builder import JavaScriptASTBuilder


class JavaScriptParser(BaseParser):
    """JavaScript language parser."""
    
    def __init__(self):
        super().__init__()
        self.tokenizer = JavaScriptTokenizer()
        self.ast_builder = JavaScriptASTBuilder()
    
    def get_language(self) -> str:
        return 'javascript'
    
    def get_extension(self) -> str:
        return '.js'
    
    def parse(self, code: str) -> Dict[str, Any]:
        """Parse JavaScript code and generate flowchart."""
        try:
            # Tokenize
            tokens = self.tokenizer.tokenize(code)
            
            # Build AST
            ast_nodes = self.ast_builder.build(tokens)
            
            # Generate flowchart
            handlers = JavaScriptHandlers(self.graph)
            
            functions = []
            classes = []
            
            for node in ast_nodes:
                if node['type'] == 'function':
                    flowchart = self._build_function(node, handlers)
                    functions.append({
                        'name': node.get('name', 'anonymous'),
                        'type': 'function',
                        'flowchart': flowchart
                    })
                elif node['type'] == 'class':
                    flowchart, methods = self._build_class(node, handlers)
                    classes.append({
                        'name': node.get('name', ''),
                        'type': 'class',
                        'flowchart': flowchart
                    })
                    functions.extend(methods)
            
            return {
                'success': True,
                'main_flowchart': {'nodes': [], 'edges': []},
                'functions': functions,
                'classes': classes,
                'code': code
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Parsing error: {str(e)}'
            }
    
    def _build_function(self, node: Dict[str, Any], handlers: JavaScriptHandlers) -> Dict[str, Any]:
        """Build flowchart for a function."""
        self.graph.reset()
        
        name = node.get('name', 'anonymous')
        params = node.get('params', [])
        body = node.get('body', [])
        
        start_id = self.graph.add_node('start', f'начало {name}()')
        prev_ids = [start_id]
        
        if params:
            param_id = self.graph.add_node('input', f'Параметры: {", ".join(params)}')
            self.graph.add_edge(start_id, param_id)
            prev_ids = [param_id]
        
        last_ids = handlers.process_body(body, prev_ids)
        end_id = self.graph.add_node('end', '')
        self._connect_to_end(last_ids, end_id)
        
        return self.graph.to_dict()
    
    def _build_class(self, node: Dict[str, Any], handlers: JavaScriptHandlers) -> tuple:
        """Build flowchart for a class."""
        self.graph.reset()
        
        name = node.get('name', '')
        methods = node.get('methods', [])
        
        class_id = self.graph.add_node('class_start', name)
        
        for i, method_name in enumerate(methods):
            method_id = self.graph.add_node('method', f'{method_name}()')
            self.graph.add_edge(class_id, method_id, '', f'fan_{i}')
        
        flowchart = self.graph.to_dict()
        
        # Build method flowcharts
        method_flowcharts = []
        for method in methods:
            # Find method body from methods list
            method_node = next((m for m in node.get('method_nodes', []) if m.get('name') == method), None)
            if method_node:
                method_flow = self._build_function(method_node, handlers)
                method_flowcharts.append({
                    'name': f'{name}.{method}',
                    'type': 'method',
                    'flowchart': method_flow
                })
        
        return flowchart, method_flowcharts
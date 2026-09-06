"""Main JavaScript parser."""

from typing import Dict, Any, List, Optional, Tuple
import logging
from app.parsers.base import BaseParser
from app.parsers.javascript.handlers import JavaScriptHandlers
from app.parsers.javascript.tokenizer import JavaScriptTokenizer
from app.parsers.javascript.ast_builder import JavaScriptASTBuilder

logger = logging.getLogger(__name__)


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
            logger.info(f"Parsing JavaScript code, length: {len(code)}")
            
            # Tokenize
            tokens = self.tokenizer.tokenize(code)
            logger.info(f"Tokenized into {len(tokens)} tokens")
            
            # Build AST
            ast_nodes = self.ast_builder.build(tokens)
            logger.info(f"Built AST with {len(ast_nodes)} nodes")
            
            # Generate flowchart
            handlers = JavaScriptHandlers(self.graph)
            
            functions = []
            classes = []
            
            for node in ast_nodes:
                logger.debug(f"Processing node: {node.get('type', 'unknown')}")
                
                if node.get('type') == 'function':
                    flowchart = self._build_function(node, handlers)
                    functions.append({
                        'name': node.get('name', 'anonymous'),
                        'type': 'function',
                        'flowchart': flowchart
                    })
                elif node.get('type') == 'class':
                    flowchart, methods = self._build_class(node, handlers)
                    classes.append({
                        'name': node.get('name', ''),
                        'type': 'class',
                        'flowchart': flowchart
                    })
                    functions.extend(methods)
            
            result = {
                'success': True,
                'main_flowchart': {'nodes': [], 'edges': []},
                'functions': functions,
                'classes': classes,
                'code': code
            }
            
            logger.info(f"Parse complete: {len(functions)} functions, {len(classes)} classes")
            return result
            
        except Exception as e:
            logger.error(f"JavaScript parsing error: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': f'JavaScript parsing error: {str(e)}',
                'main_flowchart': {'nodes': [], 'edges': []},
                'functions': [],
                'classes': [],
                'code': code
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
        
        if body:
            last_ids = handlers.process_body(body, prev_ids)
        else:
            last_ids = prev_ids
        
        end_id = self.graph.add_node('end', '')
        self._connect_to_end(last_ids, end_id)
        
        return self.graph.to_dict()
    
    def _build_class(self, node: Dict[str, Any], handlers: JavaScriptHandlers) -> tuple:
        """Build flowchart for a class."""
        self.graph.reset()
        
        name = node.get('name', '')
        methods = node.get('methods', [])
        
        class_id = self.graph.add_node('class_start', name)
        
        if methods:
            for i, method_name in enumerate(methods):
                method_id = self.graph.add_node('method', f'{method_name}()')
                self.graph.add_edge(class_id, method_id, '', f'fan_{i}')
        
        flowchart = self.graph.to_dict()
        
        # Build method flowcharts
        method_flowcharts = []
        for method in methods:
            # Find method body from method_nodes
            method_node = next((m for m in node.get('method_nodes', []) if m.get('name') == method), None)
            if method_node:
                method_flow = self._build_function(method_node, handlers)
                method_flowcharts.append({
                    'name': f'{name}.{method}',
                    'type': 'method',
                    'flowchart': method_flow
                })
        
        return flowchart, method_flowcharts
"""Main C# parser."""

from typing import Dict, Any, List, Optional
import logging
from app.parsers.base import BaseParser
from app.parsers.csharp.tokenizer import CSharpTokenizer
from app.parsers.csharp.ast_builder import CSharpASTBuilder
from app.parsers.csharp.handlers import CSharpHandlers

logger = logging.getLogger(__name__)


class CSharpParser(BaseParser):
    """C# language parser."""
    
    def __init__(self):
        super().__init__()
        self.tokenizer = CSharpTokenizer()
        self.ast_builder = CSharpASTBuilder()
    
    def get_language(self) -> str:
        return 'csharp'
    
    def get_extension(self) -> str:
        return '.cs'
    
    def parse(self, code: str) -> Dict[str, Any]:
        """Parse C# code and generate flowchart."""
        try:
            logger.info(f"Parsing C# code, length: {len(code)}")
            
            # Tokenize
            tokens = self.tokenizer.tokenize(code)
            logger.info(f"Tokenized into {len(tokens)} tokens")
            
            # Build AST
            ast_nodes = self.ast_builder.build(tokens)
            logger.info(f"Built AST with {len(ast_nodes)} nodes")
            
            # Generate flowchart
            handlers = CSharpHandlers(self.graph)
            
            functions = []
            classes = []
            
            for node in ast_nodes:
                logger.debug(f"Processing node: {node.get('type', 'unknown')}")
                
                if node.get('type') in ('class', 'struct', 'interface'):
                    flowchart, methods = self._build_class(node, handlers)
                    classes.append({
                        'name': node.get('name', ''),
                        'type': node.get('type', 'class'),
                        'flowchart': flowchart
                    })
                    functions.extend(methods)
                elif node.get('type') == 'enum':
                    flowchart = self._build_enum(node)
                    classes.append({
                        'name': node.get('name', ''),
                        'type': 'enum',
                        'flowchart': flowchart
                    })
                elif node.get('type') == 'function':
                    flowchart = self._build_function(node, handlers)
                    functions.append({
                        'name': node.get('name', 'anonymous'),
                        'type': 'function',
                        'flowchart': flowchart
                    })
            
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
            logger.error(f"C# parsing error: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': f'C# parsing error: {str(e)}',
                'main_flowchart': {'nodes': [], 'edges': []},
                'functions': [],
                'classes': [],
                'code': code
            }
    
    def _build_function(self, node: Dict[str, Any], handlers: CSharpHandlers) -> Dict[str, Any]:
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
    
    def _build_class(self, node: Dict[str, Any], handlers: CSharpHandlers) -> tuple:
        """Build flowchart for a class."""
        self.graph.reset()
        
        class_type = node.get('type', 'class')
        name = node.get('name', '')
        fields = node.get('fields', [])
        properties = node.get('properties', [])
        methods = node.get('methods', [])
        
        class_id = self.graph.add_node('class_start', name)
        source_id = class_id
        
        # Show fields
        if fields:
            fields_id = self.graph.add_node('input', f'Поля: {", ".join(fields)}')
            self.graph.add_edge(source_id, fields_id)
            source_id = fields_id
        
        # Show properties
        if properties:
            props_id = self.graph.add_node('process', f'Свойства: {", ".join(properties)}')
            self.graph.add_edge(source_id, props_id)
            source_id = props_id
        
        # Show methods
        if methods:
            for i, method_name in enumerate(methods):
                method_id = self.graph.add_node('method', f'{method_name}()')
                self.graph.add_edge(source_id, method_id, '', f'fan_{i}')
        
        flowchart = self.graph.to_dict()
        
        # Build method flowcharts
        method_flowcharts = []
        method_nodes = node.get('method_nodes', [])
        
        for method_node in method_nodes:
            method_name = method_node.get('name', 'unknown')
            method_flow = self._build_function(method_node, handlers)
            method_flowcharts.append({
                'name': f'{name}.{method_name}',
                'type': 'method',
                'flowchart': method_flow
            })
        
        return flowchart, method_flowcharts
    
    def _build_enum(self, node: Dict[str, Any]) -> Dict[str, Any]:
        """Build flowchart for an enum."""
        self.graph.reset()
        
        name = node.get('name', '')
        values = node.get('values', [])
        
        class_id = self.graph.add_node('class_start', name)
        values_id = self.graph.add_node('input', f'Значения: {", ".join(values)}')
        self.graph.add_edge(class_id, values_id)
        
        return self.graph.to_dict()
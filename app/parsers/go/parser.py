"""Main Go parser."""

from typing import Dict, Any, List, Optional
import logging
from app.parsers.base import BaseParser
from app.parsers.go.tokenizer import GoTokenizer
from app.parsers.go.ast_builder import GoASTBuilder
from app.parsers.go.handlers import GoHandlers

logger = logging.getLogger(__name__)


class GoParser(BaseParser):
    """Go language parser."""
    
    def __init__(self):
        super().__init__()
        self.tokenizer = GoTokenizer()
        self.ast_builder = GoASTBuilder()
    
    def get_language(self) -> str:
        return 'go'
    
    def get_extension(self) -> str:
        return '.go'
    
    def parse(self, code: str) -> Dict[str, Any]:
        """Parse Go code and generate flowchart."""
        try:
            logger.info(f"Parsing Go code, length: {len(code)}")
            
            # Tokenize
            tokens = self.tokenizer.tokenize(code)
            logger.info(f"Tokenized into {len(tokens)} tokens")
            
            # Build AST
            ast = self.ast_builder.build(tokens)
            logger.info(f"AST built: {len(ast.get('body', []))} top-level nodes")
            
            handlers = GoHandlers(self.graph)
            
            functions = []
            structs = []
            interfaces = []
            
            # Process top-level declarations
            for node in ast.get('body', []):
                if node.get('type') == 'function':
                    flowchart = self._build_function(node, handlers)
                    functions.append({
                        'name': node.get('name', ''),
                        'type': 'function',
                        'flowchart': flowchart
                    })
                elif node.get('type') == 'type':
                    if node.get('kind') == 'struct':
                        structs.append({
                            'name': node.get('name', ''),
                            'type': 'struct',
                            'fields': node.get('fields', []),
                            'flowchart': self._build_struct(node, handlers)
                        })
                    elif node.get('kind') == 'interface':
                        interfaces.append({
                            'name': node.get('name', ''),
                            'type': 'interface',
                            'methods': node.get('methods', []),
                            'flowchart': self._build_interface(node, handlers)
                        })
                elif node.get('type') == 'var' or node.get('type') == 'const':
                    # Global variables/constants
                    pass
            
            # Main body
            main_body = [stmt for stmt in ast.get('body', []) 
                         if stmt.get('type') not in ['function', 'type', 'interface']]
            
            # Check for main function
            main_flowchart = None
            for func in functions:
                if func.get('name') == 'main':
                    main_flowchart = func.get('flowchart')
                    break
            
            if not main_flowchart:
                # If no main function, use top-level statements
                main_flowchart = self._build_main(main_body, handlers)
            
            result = {
                'success': True,
                'main_flowchart': main_flowchart or {'nodes': [], 'edges': []},
                'functions': functions,
                'classes': structs,  # Reuse classes field for structs
                'code': code
            }
            
            logger.info(f"Parse complete: {len(functions)} functions, {len(structs)} structs, {len(interfaces)} interfaces")
            return result
            
        except SyntaxError as e:
            logger.error(f"Go syntax error: {e}")
            return {
                'success': False,
                'error': f'Синтаксическая ошибка: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Go parsing error: {e}", exc_info=True)
            return {
                'success': False,
                'error': f'Go parsing error: {str(e)}'
            }
    
    def _build_function(self, node: Dict[str, Any], handlers: GoHandlers) -> Dict[str, Any]:
        """Build flowchart for a function."""
        self.graph.reset()
        
        name = node.get('name', '')
        is_method = node.get('is_method', False)
        receiver = node.get('receiver')
        
        if is_method and receiver:
            start_text = f'начало {receiver.get("type")}.{name}()'
        else:
            start_text = f'начало {name}()'
        
        start_id = self.graph.add_node('start', start_text)
        prev_ids = [start_id]
        
        # Parameters
        params = node.get('params', [])
        if params:
            param_texts = []
            for param in params:
                if param.get('type'):
                    param_texts.append(f'{param.get("name")} {param.get("type")}')
                else:
                    param_texts.append(param.get('name', ''))
            param_text = ', '.join(param_texts)
            param_id = self.graph.add_node('input', f'Параметры: {param_text}')
            self.graph.add_edge(start_id, param_id)
            prev_ids = [param_id]
        
        # Function body
        body = node.get('body', [])
        last_ids = handlers.process_body(body, prev_ids)
        end_id = self.graph.add_node('end', '')
        self._connect_to_end(last_ids, end_id)
        
        return self.graph.to_dict()
    
    def _build_struct(self, node: Dict[str, Any], handlers: GoHandlers) -> Dict[str, Any]:
        """Build flowchart for a struct."""
        self.graph.reset()
        
        struct_id = self.graph.add_node('class_start', f'struct {node.get("name", "")}')
        
        fields = node.get('fields', [])
        if fields:
            field_texts = []
            for field in fields:
                field_texts.append(f'{field.get("name")} {field.get("type")}')
            fields_text = ', '.join(field_texts)
            fields_id = self.graph.add_node('input', f'Поля: {fields_text}')
            self.graph.add_edge(struct_id, fields_id)
        
        flowchart = self.graph.to_dict()
        return flowchart
    
    def _build_interface(self, node: Dict[str, Any], handlers: GoHandlers) -> Dict[str, Any]:
        """Build flowchart for an interface."""
        self.graph.reset()
        
        interface_id = self.graph.add_node('class_start', f'interface {node.get("name", "")}')
        
        methods = node.get('methods', [])
        if methods:
            method_texts = []
            for method in methods:
                method_texts.append(f'{method.get("name")}()')
            methods_text = ', '.join(method_texts)
            methods_id = self.graph.add_node('process', f'Методы: {methods_text}')
            self.graph.add_edge(interface_id, methods_id)
        
        flowchart = self.graph.to_dict()
        return flowchart
    
    def _build_main(self, body: List[Dict[str, Any]], handlers: GoHandlers) -> Dict[str, Any]:
        """Build flowchart for main code."""
        if not body:
            return {'nodes': [], 'edges': []}
        
        self.graph.reset()
        
        start_id = self.graph.add_node('start', 'начало main()')
        last_ids = handlers.process_body(body, [start_id])
        end_id = self.graph.add_node('end', '')
        self._connect_to_end(last_ids, end_id)
        
        return self.graph.to_dict()
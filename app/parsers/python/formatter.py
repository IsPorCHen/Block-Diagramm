"""Expression formatter for Python AST."""

import ast
from typing import Any


class PythonFormatter:
    """Format Python AST nodes to readable text."""
    
    @staticmethod
    def format(node) -> str:
        """Format any AST node to string."""
        if node is None:
            return ''
        
        if isinstance(node, ast.Constant):
            return PythonFormatter._format_constant(node)
        elif isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f'{PythonFormatter.format(node.value)}.{node.attr}'
        elif isinstance(node, ast.BinOp):
            return PythonFormatter._format_binop(node)
        elif isinstance(node, ast.Compare):
            return PythonFormatter._format_compare(node)
        elif isinstance(node, ast.BoolOp):
            return PythonFormatter._format_boolop(node)
        elif isinstance(node, ast.Call):
            return PythonFormatter._format_call(node)
        elif isinstance(node, ast.Subscript):
            return f'{PythonFormatter.format(node.value)}[{PythonFormatter.format(node.slice)}]'
        elif isinstance(node, ast.Tuple):
            return f'({", ".join(PythonFormatter.format(e) for e in node.elts)})'
        elif isinstance(node, ast.List):
            return f'[{", ".join(PythonFormatter.format(e) for e in node.elts)}]'
        elif isinstance(node, ast.Dict):
            return PythonFormatter._format_dict(node)
        elif isinstance(node, ast.UnaryOp):
            return PythonFormatter._format_unary(node)
        elif isinstance(node, ast.IfExp):
            return f'{PythonFormatter.format(node.body)} if {PythonFormatter.format(node.test)} else {PythonFormatter.format(node.orelse)}'
        elif isinstance(node, ast.Slice):
            lower = PythonFormatter.format(node.lower) if node.lower else ''
            upper = PythonFormatter.format(node.upper) if node.upper else ''
            return f'{lower}:{upper}'
        else:
            return str(node)
    
    @staticmethod
    def _format_constant(node: ast.Constant) -> str:
        if isinstance(node.value, str):
            s = node.value
            if len(s) > 20:
                s = s[:17] + '...'
            return f'"{s}"'
        return str(node.value)
    
    @staticmethod
    def _format_binop(node: ast.BinOp) -> str:
        op = PythonFormatter._get_op(node.op)
        left = PythonFormatter.format(node.left)
        right = PythonFormatter.format(node.right)
        return f'{left} {op} {right}'
    
    @staticmethod
    def _format_compare(node: ast.Compare) -> str:
        parts = [PythonFormatter.format(node.left)]
        for op, comp in zip(node.ops, node.comparators):
            parts.append(PythonFormatter._get_op(op))
            parts.append(PythonFormatter.format(comp))
        return ' '.join(parts)
    
    @staticmethod
    def _format_boolop(node: ast.BoolOp) -> str:
        op = ' and ' if isinstance(node.op, ast.And) else ' or '
        return op.join(PythonFormatter.format(v) for v in node.values)
    
    @staticmethod
    def _format_call(node: ast.Call) -> str:
        func = PythonFormatter.format(node.func)
        args = ', '.join(PythonFormatter.format(arg) for arg in node.args)
        return f'{func}({args})'
    
    @staticmethod
    def _format_dict(node: ast.Dict) -> str:
        items = []
        for k, v in zip(node.keys, node.values):
            if k is not None:
                items.append(f'{PythonFormatter.format(k)}: {PythonFormatter.format(v)}')
        return '{' + ', '.join(items) + '}'
    
    @staticmethod
    def _format_unary(node: ast.UnaryOp) -> str:
        op = PythonFormatter._get_unary_op(node.op)
        operand = PythonFormatter.format(node.operand)
        return f'{op}{operand}'
    
    @staticmethod
    def _get_op(op) -> str:
        ops = {
            ast.Add: '+', ast.Sub: '-', ast.Mult: '*', ast.Div: '/',
            ast.Mod: '%', ast.Pow: '**', ast.FloorDiv: '//',
            ast.Eq: '==', ast.NotEq: '!=', ast.Lt: '<', ast.LtE: '<=',
            ast.Gt: '>', ast.GtE: '>=', 
            ast.In: 'in', ast.NotIn: 'not in',
            ast.Is: 'is', ast.IsNot: 'is not',
        }
        return ops.get(type(op), '?')
    
    @staticmethod
    def _get_unary_op(op) -> str:
        ops = {
            ast.Not: 'not ',
            ast.UAdd: '+',
            ast.USub: '-',
        }
        return ops.get(type(op), '?')
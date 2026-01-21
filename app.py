from flask import Flask, render_template, request, jsonify
import ast
import re

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024

class FlowchartBuilder:
    def __init__(self):
        self.blocks = []
        self.block_id = 0
        
    def add_block(self, block_type, text, branches=None):
        """Добавить блок в блок-схему"""
        block = {
            'id': self.block_id,
            'type': block_type,
            'text': text,
            'branches': branches or {}
        }
        self.blocks.append(block)
        self.block_id += 1
        return block['id']
    
    def build_from_ast(self, node, indent=0):
        """Рекурсивно строим блок-схему из AST"""
        if isinstance(node, ast.Module):
            for stmt in node.body:
                self.build_from_ast(stmt, indent)
        
        elif isinstance(node, ast.FunctionDef):
            # начало
            self.add_block('start', f'НАЧАЛО: {node.name}')
            
            # параметры
            if node.args.args:
                params = ', '.join([arg.arg for arg in node.args.args])
                self.add_block('input', f'Параметры: {params}')
            
            # код функции
            for stmt in node.body:
                if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant):
                    continue
                self.build_from_ast(stmt, indent)
            
            # конец
            self.add_block('end', 'КОНЕЦ')
        
        elif isinstance(node, ast.Assign):
            # присваивание
            targets = ', '.join([self.get_name(t) for t in node.targets])
            value = self.get_expr_text(node.value)
            self.add_block('operation', f'{targets} = {value}')
        
        elif isinstance(node, ast.AugAssign):
            # присваивание с операцией (+=, -=, и тд)
            target = self.get_name(node.target)
            op = self.get_op(node.op)
            value = self.get_expr_text(node.value)
            self.add_block('operation', f'{target} {op}= {value}')
        
        elif isinstance(node, ast.Expr):
            # Выражение (например, вызов функции)
            if isinstance(node.value, ast.Call):
                func_name = self.get_name(node.value.func)
                if func_name in ['print', 'output']:
                    # Вывод
                    args = ', '.join([self.get_expr_text(arg) for arg in node.value.args])
                    self.add_block('output', f'Вывод: {args}')
                else:
                    # Обычный вызов функции
                    args = ', '.join([self.get_expr_text(arg) for arg in node.value.args])
                    self.add_block('operation', f'{func_name}({args})')
        
        elif isinstance(node, ast.If):
            # Условие
            condition = self.get_expr_text(node.test)
            cond_id = self.add_block('condition', condition)
            
            # if
            for stmt in node.body:
                self.build_from_ast(stmt, indent + 1)
            
            # else
            if node.orelse:
                for stmt in node.orelse:
                    self.build_from_ast(stmt, indent + 1)
        
        elif isinstance(node, ast.While):
            # цикл while
            condition = self.get_expr_text(node.test)
            self.add_block('loop', f'ПОКА {condition}')
            
            for stmt in node.body:
                self.build_from_ast(stmt, indent + 1)
        
        elif isinstance(node, ast.For):
            # цикл for
            target = self.get_name(node.target)
            iter_val = self.get_expr_text(node.iter)
            self.add_block('loop', f'ДЛЯ {target} В {iter_val}')
            
            for stmt in node.body:
                self.build_from_ast(stmt, indent + 1)
        
        elif isinstance(node, ast.Return):
            # возврат значения
            if node.value:
                value = self.get_expr_text(node.value)
                self.add_block('operation', f'ВЕРНУТЬ {value}')
            else:
                self.add_block('operation', 'ВЕРНУТЬ')
        
        elif isinstance(node, ast.Call):
            # вызов функции
            func_name = self.get_name(node.func)
            if func_name in ['input', 'int', 'float', 'str']:
                # ввод
                self.add_block('input', f'Ввод данных')
            else:
                args = ', '.join([self.get_expr_text(arg) for arg in node.args])
                self.add_block('operation', f'{func_name}({args})')
    
    def get_name(self, node):
        """Получить имя переменной/функции"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f'{self.get_name(node.value)}.{node.attr}'
        elif isinstance(node, ast.Subscript):
            return f'{self.get_name(node.value)}[{self.get_expr_text(node.slice)}]'
        return 'unknown'
    
    def get_expr_text(self, node):
        """Получить текстовое представление выражения"""
        if isinstance(node, ast.Constant):
            return repr(node.value)
        elif isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.BinOp):
            left = self.get_expr_text(node.left)
            right = self.get_expr_text(node.right)
            op = self.get_op(node.op)
            return f'{left} {op} {right}'
        elif isinstance(node, ast.Compare):
            left = self.get_expr_text(node.left)
            ops = ' '.join([self.get_op(op) for op in node.ops])
            comparators = ' '.join([self.get_expr_text(c) for c in node.comparators])
            return f'{left} {ops} {comparators}'
        elif isinstance(node, ast.Call):
            func = self.get_name(node.func)
            args = ', '.join([self.get_expr_text(arg) for arg in node.args])
            return f'{func}({args})'
        elif isinstance(node, ast.List):
            elements = ', '.join([self.get_expr_text(e) for e in node.elts])
            return f'[{elements}]'
        elif isinstance(node, ast.Subscript):
            return f'{self.get_expr_text(node.value)}[{self.get_expr_text(node.slice)}]'
        elif isinstance(node, ast.Attribute):
            return f'{self.get_expr_text(node.value)}.{node.attr}'
        return 'expr'
    
    def get_op(self, op):
        """Получить символ операции"""
        ops = {
            ast.Add: '+', ast.Sub: '-', ast.Mult: '*', ast.Div: '/',
            ast.Mod: '%', ast.Pow: '**', ast.FloorDiv: '//',
            ast.Eq: '==', ast.NotEq: '!=', ast.Lt: '<', ast.LtE: '<=',
            ast.Gt: '>', ast.GtE: '>=', ast.And: 'И', ast.Or: 'ИЛИ',
        }
        return ops.get(type(op), '?')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Файл не найден'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'Файл не выбран'}), 400
        
        if not file.filename.endswith('.py'):
            return jsonify({'error': 'Разрешены только файлы с расширением .py'}), 400

        code = file.read().decode('utf-8')
        
        if len(code) > 1024 * 1024:
            return jsonify({'error': 'Файл слишком большой (максимум 1 МБ)'}), 400

        # парсинг кода
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return jsonify({'error': f'Синтаксическая ошибка в строке {e.lineno}: {e.msg}'}), 400

        functions = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                builder = FlowchartBuilder()
                builder.build_from_ast(node)
                
                functions.append({
                    'name': node.name,
                    'blocks': builder.blocks
                })
        
        # основная блок-схема
        main_builder = FlowchartBuilder()
        main_builder.add_block('start', 'НАЧАЛО ПРОГРАММЫ')
        
        for stmt in tree.body:
            if not isinstance(stmt, ast.FunctionDef):
                main_builder.build_from_ast(stmt)
        
        if len(main_builder.blocks) > 1:
            main_builder.add_block('end', 'КОНЕЦ ПРОГРАММЫ')

        return jsonify({
            'success': True,
            'main_flowchart': main_builder.blocks,
            'functions': functions,
            'code': code
        })
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error: {error_details}")
        return jsonify({'error': f'Непредвиденная ошибка: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
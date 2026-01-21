from flask import Flask, render_template, request, jsonify
import ast

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024


class FlowchartBuilder:
    """Строитель блок-схем с поддержкой ветвлений, циклов, try/except и классов"""
    
    def __init__(self):
        self.nodes = []
        self.edges = []
        self.node_id = 0
        
    def add_node(self, node_type, text, extra=None):
        """Добавить узел"""
        node = {
            'id': self.node_id,
            'type': node_type,
            'text': text
        }
        if extra:
            node.update(extra)
        self.nodes.append(node)
        self.node_id += 1
        return node['id']
    
    def add_edge(self, from_id, to_id, label='', branch=''):
        """Добавить связь (branch: 'yes', 'no', '' для обычной)"""
        for edge in self.edges:
            if edge['from'] == from_id and edge['to'] == to_id:
                if label and not edge['label']:
                    edge['label'] = label
                return edge
        
        edge = {
            'from': from_id,
            'to': to_id,
            'label': label,
            'branch': branch
        }
        self.edges.append(edge)
        return edge
    
    def build_function(self, node):
        """Построить блок-схему функции"""
        start_id = self.add_node('start', f'начало {node.name}()')
        prev_ids = [start_id]
        
        if node.args.args:
            params = ', '.join([arg.arg for arg in node.args.args])
            param_id = self.add_node('input', f'Параметры: {params}')
            self.add_edge(start_id, param_id)
            prev_ids = [param_id]
        
        body = [stmt for stmt in node.body 
                if not (isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant))]
        
        last_ids = self.process_body(body, prev_ids)
        
        end_id = self.add_node('end', '')
        for lid in last_ids:
            if lid is not None:
                self.add_edge(lid, end_id)
    
    def build_class(self, node):
        """Построить блок-схему класса"""
        # Терминатор с именем класса
        class_id = self.add_node('class_start', node.name)
        
        # Собираем поля класса (из __init__ или атрибуты уровня класса)
        fields = []
        methods = []
        
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                methods.append(item.name)
                # Ищем self.x = ... в __init__
                if item.name == '__init__':
                    for stmt in item.body:
                        if isinstance(stmt, ast.Assign):
                            for target in stmt.targets:
                                if isinstance(target, ast.Attribute) and \
                                   isinstance(target.value, ast.Name) and \
                                   target.value.id == 'self':
                                    fields.append(target.attr)
            elif isinstance(item, ast.Assign):
                # Атрибуты класса
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        fields.append(target.id)
        
        # Блок полей класса
        if fields:
            fields_text = ', '.join(fields)
            fields_id = self.add_node('input', f'Поля: {fields_text}')
            self.add_edge(class_id, fields_id)
            source_id = fields_id
        else:
            source_id = class_id
        
        # Терминаторы методов (все соединены от полей)
        for method_name in methods:
            method_id = self.add_node('method', method_name + '()')
            self.add_edge(source_id, method_id)
    
    def process_body(self, statements, prev_ids):
        """Обработать список операторов"""
        current_prev_ids = prev_ids
        
        for stmt in statements:
            if isinstance(stmt, (ast.FunctionDef, ast.ClassDef)):
                continue
            new_prev_ids = self.process_statement(stmt, current_prev_ids)
            current_prev_ids = new_prev_ids
            
        return current_prev_ids
    
    def process_statement(self, stmt, prev_ids):
        """Обработать один оператор"""
        
        if isinstance(stmt, ast.Assign):
            targets = ', '.join([self.get_name(t) for t in stmt.targets])
            value = self.get_expr_text(stmt.value)
            node_id = self.add_node('process', f'{targets} = {value}')
            for pid in prev_ids:
                if pid is not None:
                    self.add_edge(pid, node_id)
            return [node_id]
        
        elif isinstance(stmt, ast.AugAssign):
            target = self.get_name(stmt.target)
            op = self.get_op(stmt.op)
            value = self.get_expr_text(stmt.value)
            node_id = self.add_node('process', f'{target} {op}= {value}')
            for pid in prev_ids:
                if pid is not None:
                    self.add_edge(pid, node_id)
            return [node_id]
        
        elif isinstance(stmt, ast.Expr):
            if isinstance(stmt.value, ast.Call):
                func_name = self.get_name(stmt.value.func)
                args = ', '.join([self.get_expr_text(arg) for arg in stmt.value.args])
                
                if func_name in ['print', 'output']:
                    node_id = self.add_node('output', f'{func_name}({args})')
                elif func_name == 'input':
                    node_id = self.add_node('input', 'Ввод данных')
                else:
                    node_id = self.add_node('process', f'{func_name}({args})')
                    
                for pid in prev_ids:
                    if pid is not None:
                        self.add_edge(pid, node_id)
                return [node_id]
            return prev_ids
        
        elif isinstance(stmt, ast.If):
            return self.process_if(stmt, prev_ids)
        
        elif isinstance(stmt, ast.While):
            return self.process_while(stmt, prev_ids)
        
        elif isinstance(stmt, ast.For):
            return self.process_for(stmt, prev_ids)
        
        elif isinstance(stmt, ast.Try):
            return self.process_try(stmt, prev_ids)
        
        elif isinstance(stmt, ast.Return):
            if stmt.value:
                value = self.get_expr_text(stmt.value)
                node_id = self.add_node('process', f'return {value}')
            else:
                node_id = self.add_node('process', 'return')
            for pid in prev_ids:
                if pid is not None:
                    self.add_edge(pid, node_id)
            return [node_id]
        
        elif isinstance(stmt, ast.Raise):
            if stmt.exc:
                exc_text = self.get_expr_text(stmt.exc)
                node_id = self.add_node('process', f'raise {exc_text}')
            else:
                node_id = self.add_node('process', 'raise')
            for pid in prev_ids:
                if pid is not None:
                    self.add_edge(pid, node_id)
            return [None]
        
        elif isinstance(stmt, ast.Break):
            node_id = self.add_node('process', 'break')
            for pid in prev_ids:
                if pid is not None:
                    self.add_edge(pid, node_id)
            return [None]
        
        elif isinstance(stmt, ast.Continue):
            node_id = self.add_node('process', 'continue')
            for pid in prev_ids:
                if pid is not None:
                    self.add_edge(pid, node_id)
            return [None]
        
        elif isinstance(stmt, ast.Pass):
            return prev_ids
        
        return prev_ids
    
    def process_if(self, stmt, prev_ids):
        """Обработка IF с ветвлением влево/вправо"""
        condition = self.get_expr_text(stmt.test)
        cond_id = self.add_node('condition', condition + '?')
        
        for pid in prev_ids:
            if pid is not None:
                self.add_edge(pid, cond_id)
        
        exit_ids = []
        
        # Ветка "да"
        if stmt.body:
            edge_idx = len(self.edges)
            yes_ids = self.process_body(stmt.body, [cond_id])
            
            for i in range(edge_idx, len(self.edges)):
                if self.edges[i]['from'] == cond_id and not self.edges[i]['label']:
                    self.edges[i]['label'] = 'да'
                    self.edges[i]['branch'] = 'yes'
                    break
            
            exit_ids.extend(yes_ids)
        
        # Ветка "нет"
        if stmt.orelse:
            edge_idx = len(self.edges)
            
            if len(stmt.orelse) == 1 and isinstance(stmt.orelse[0], ast.If):
                no_ids = self.process_if(stmt.orelse[0], [cond_id])
            else:
                no_ids = self.process_body(stmt.orelse, [cond_id])
            
            for i in range(edge_idx, len(self.edges)):
                if self.edges[i]['from'] == cond_id and not self.edges[i]['label']:
                    self.edges[i]['label'] = 'нет'
                    self.edges[i]['branch'] = 'no'
                    break
            
            exit_ids.extend(no_ids)
        else:
            exit_ids.append(cond_id)
        
        exit_ids = [eid for eid in exit_ids if eid is not None]
        return exit_ids if exit_ids else [None]
    
    def process_while(self, stmt, prev_ids):
        """Обработка WHILE"""
        condition = self.get_expr_text(stmt.test)
        cond_id = self.add_node('condition', condition + '?')
        
        for pid in prev_ids:
            if pid is not None:
                self.add_edge(pid, cond_id)
        
        if stmt.body:
            edge_idx = len(self.edges)
            body_ids = self.process_body(stmt.body, [cond_id])
            
            for i in range(edge_idx, len(self.edges)):
                if self.edges[i]['from'] == cond_id and not self.edges[i]['label']:
                    self.edges[i]['label'] = 'да'
                    self.edges[i]['branch'] = 'yes'
                    break
            
            for bid in body_ids:
                if bid is not None and bid != cond_id:
                    self.add_edge(bid, cond_id, '', 'loop')
        
        return [cond_id]
    
    def process_for(self, stmt, prev_ids):
        """Обработка FOR"""
        target = self.get_name(stmt.target)
        iter_val = self.get_expr_text(stmt.iter)
        
        cond_id = self.add_node('condition', f'есть элементы в {iter_val}?')
        
        for pid in prev_ids:
            if pid is not None:
                self.add_edge(pid, cond_id)
        
        # Блок получения элемента
        get_id = self.add_node('process', f'взять следующий элемент {target}')
        self.add_edge(cond_id, get_id, 'да', 'yes')
        
        if stmt.body:
            body_ids = self.process_body(stmt.body, [get_id])
            
            for bid in body_ids:
                if bid is not None:
                    self.add_edge(bid, cond_id, '', 'loop')
        
        return [cond_id]
    
    def process_try(self, stmt, prev_ids):
        """Обработка TRY/EXCEPT"""
        # Блок try
        try_id = self.add_node('try_start', 'try')
        
        for pid in prev_ids:
            if pid is not None:
                self.add_edge(pid, try_id)
        
        exit_ids = []
        
        # Тело try
        if stmt.body:
            try_body_ids = self.process_body(stmt.body, [try_id])
            exit_ids.extend(try_body_ids)
        
        # Обработчики except
        for handler in stmt.handlers:
            if handler.type:
                exc_name = self.get_name(handler.type)
                if handler.name:
                    exc_text = f'except {exc_name} as {handler.name}'
                else:
                    exc_text = f'except {exc_name}'
            else:
                exc_text = 'except'
            
            except_id = self.add_node('except', exc_text)
            self.add_edge(try_id, except_id, 'исключение', 'exception')
            
            if handler.body:
                except_body_ids = self.process_body(handler.body, [except_id])
                exit_ids.extend(except_body_ids)
        
        # finally
        if stmt.finalbody:
            finally_id = self.add_node('finally', 'finally')
            
            # Соединяем все выходы с finally
            new_exit_ids = []
            for eid in exit_ids:
                if eid is not None:
                    self.add_edge(eid, finally_id)
            
            finally_body_ids = self.process_body(stmt.finalbody, [finally_id])
            return finally_body_ids
        
        exit_ids = [eid for eid in exit_ids if eid is not None]
        return exit_ids if exit_ids else [None]
    
    def get_name(self, node):
        """Получить имя"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f'{self.get_name(node.value)}.{node.attr}'
        elif isinstance(node, ast.Subscript):
            return f'{self.get_name(node.value)}[{self.get_expr_text(node.slice)}]'
        elif isinstance(node, ast.Tuple):
            return ', '.join([self.get_name(e) for e in node.elts])
        return 'var'
    
    def get_expr_text(self, node):
        """Получить текст выражения"""
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
            left = self.get_expr_text(node.left)
            right = self.get_expr_text(node.right)
            op = self.get_op(node.op)
            return f'{left} {op} {right}'
        elif isinstance(node, ast.UnaryOp):
            operand = self.get_expr_text(node.operand)
            op = self.get_unary_op(node.op)
            return f'{op}{operand}'
        elif isinstance(node, ast.Compare):
            left = self.get_expr_text(node.left)
            parts = [left]
            for op, comp in zip(node.ops, node.comparators):
                parts.append(self.get_op(op))
                parts.append(self.get_expr_text(comp))
            return ' '.join(parts)
        elif isinstance(node, ast.BoolOp):
            op = ' and ' if isinstance(node.op, ast.And) else ' or '
            values = [self.get_expr_text(v) for v in node.values]
            return op.join(values)
        elif isinstance(node, ast.Call):
            func = self.get_name(node.func)
            args = ', '.join([self.get_expr_text(arg) for arg in node.args])
            return f'{func}({args})'
        elif isinstance(node, ast.List):
            elements = ', '.join([self.get_expr_text(e) for e in node.elts])
            return f'[{elements}]'
        elif isinstance(node, ast.Tuple):
            elements = ', '.join([self.get_expr_text(e) for e in node.elts])
            return f'({elements})'
        elif isinstance(node, ast.Dict):
            items = []
            for k, v in zip(node.keys, node.values):
                if k is not None:
                    items.append(f'{self.get_expr_text(k)}: {self.get_expr_text(v)}')
            return '{' + ', '.join(items) + '}'
        elif isinstance(node, ast.Subscript):
            return f'{self.get_expr_text(node.value)}[{self.get_expr_text(node.slice)}]'
        elif isinstance(node, ast.Attribute):
            return f'{self.get_expr_text(node.value)}.{node.attr}'
        elif isinstance(node, ast.IfExp):
            return f'{self.get_expr_text(node.body)} if {self.get_expr_text(node.test)} else {self.get_expr_text(node.orelse)}'
        elif isinstance(node, ast.ListComp):
            return '[...]'
        elif isinstance(node, ast.Slice):
            lower = self.get_expr_text(node.lower) if node.lower else ''
            upper = self.get_expr_text(node.upper) if node.upper else ''
            return f'{lower}:{upper}'
        return 'expr'
    
    def get_op(self, op):
        """Получить символ операции"""
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
    
    def get_unary_op(self, op):
        """Получить унарную операцию"""
        ops = {
            ast.Not: 'not ',
            ast.UAdd: '+',
            ast.USub: '-',
        }
        return ops.get(type(op), '?')
    
    def get_flowchart_data(self):
        """Получить данные"""
        return {
            'nodes': self.nodes,
            'edges': self.edges
        }


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
            return jsonify({'error': 'Разрешены только файлы .py'}), 400

        code = file.read().decode('utf-8')
        
        if len(code) > 1024 * 1024:
            return jsonify({'error': 'Файл слишком большой'}), 400

        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return jsonify({'error': f'Синтаксическая ошибка: строка {e.lineno}'}), 400

        functions = []
        classes = []
        
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                builder = FlowchartBuilder()
                builder.build_function(node)
                functions.append({
                    'name': node.name,
                    'type': 'function',
                    'flowchart': builder.get_flowchart_data()
                })
            elif isinstance(node, ast.ClassDef):
                # Блок-схема класса
                class_builder = FlowchartBuilder()
                class_builder.build_class(node)
                classes.append({
                    'name': node.name,
                    'type': 'class',
                    'flowchart': class_builder.get_flowchart_data()
                })
                
                # Методы класса как отдельные блок-схемы
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        method_builder = FlowchartBuilder()
                        method_builder.build_function(item)
                        functions.append({
                            'name': f'{node.name}.{item.name}',
                            'type': 'method',
                            'flowchart': method_builder.get_flowchart_data()
                        })
        
        # Основной код
        main_builder = FlowchartBuilder()
        main_body = [stmt for stmt in tree.body 
                     if not isinstance(stmt, (ast.FunctionDef, ast.ClassDef))]
        
        main_flowchart = {'nodes': [], 'edges': []}
        if main_body:
            start_id = main_builder.add_node('start', 'начало main()')
            last_ids = main_builder.process_body(main_body, [start_id])
            end_id = main_builder.add_node('end', '')
            for lid in last_ids:
                if lid is not None:
                    main_builder.add_edge(lid, end_id)
            main_flowchart = main_builder.get_flowchart_data()

        return jsonify({
            'success': True,
            'main_flowchart': main_flowchart,
            'functions': functions,
            'classes': classes,
            'code': code
        })
        
    except Exception as e:
        import traceback
        print(f"Error: {traceback.format_exc()}")
        return jsonify({'error': f'Ошибка: {str(e)}'}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

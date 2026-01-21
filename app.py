from flask import Flask, render_template, request, jsonify
import ast

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024


class FlowchartBuilder:
    """Строитель блок-схем с поддержкой ветвлений и циклов"""
    
    def __init__(self):
        self.nodes = []
        self.edges = []
        self.node_id = 0
        
    def add_node(self, node_type, text):
        """Добавить узел в блок-схему"""
        node = {
            'id': self.node_id,
            'type': node_type,
            'text': text
        }
        self.nodes.append(node)
        self.node_id += 1
        return node['id']
    
    def add_edge(self, from_id, to_id, label=''):
        """Добавить связь между узлами"""
        # Избегаем дублирования связей
        for edge in self.edges:
            if edge['from'] == from_id and edge['to'] == to_id:
                if label and not edge['label']:
                    edge['label'] = label
                return edge
        
        edge = {
            'from': from_id,
            'to': to_id,
            'label': label
        }
        self.edges.append(edge)
        return edge
    
    def build_from_ast(self, node):
        """Построить блок-схему из AST"""
        if isinstance(node, ast.FunctionDef):
            # Функция
            start_id = self.add_node('start', f'НАЧАЛО: {node.name}')
            prev_ids = [start_id]
            
            # Параметры функции
            if node.args.args:
                params = ', '.join([arg.arg for arg in node.args.args])
                param_id = self.add_node('input', f'Параметры: {params}')
                self.add_edge(start_id, param_id)
                prev_ids = [param_id]
            
            # Тело функции (пропускаем docstring)
            body = [stmt for stmt in node.body 
                    if not (isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant))]
            
            last_ids = self.process_body(body, prev_ids)
            
            end_id = self.add_node('end', 'КОНЕЦ')
            for lid in last_ids:
                if lid is not None:
                    self.add_edge(lid, end_id)
    
    def process_body(self, statements, prev_ids):
        """Обработать список операторов"""
        current_prev_ids = prev_ids
        
        for stmt in statements:
            if isinstance(stmt, ast.FunctionDef):
                continue
            new_prev_ids = self.process_statement(stmt, current_prev_ids)
            current_prev_ids = new_prev_ids
            
        return current_prev_ids
    
    def process_statement(self, stmt, prev_ids):
        """Обработать один оператор"""
        
        if isinstance(stmt, ast.Assign):
            targets = ', '.join([self.get_name(t) for t in stmt.targets])
            value = self.get_expr_text(stmt.value)
            node_id = self.add_node('operation', f'{targets} = {value}')
            for pid in prev_ids:
                if pid is not None:
                    self.add_edge(pid, node_id)
            return [node_id]
        
        elif isinstance(stmt, ast.AugAssign):
            target = self.get_name(stmt.target)
            op = self.get_op(stmt.op)
            value = self.get_expr_text(stmt.value)
            node_id = self.add_node('operation', f'{target} {op}= {value}')
            for pid in prev_ids:
                if pid is not None:
                    self.add_edge(pid, node_id)
            return [node_id]
        
        elif isinstance(stmt, ast.Expr):
            if isinstance(stmt.value, ast.Call):
                func_name = self.get_name(stmt.value.func)
                args = ', '.join([self.get_expr_text(arg) for arg in stmt.value.args])
                
                if func_name in ['print', 'output']:
                    node_id = self.add_node('output', f'Вывод: {args}')
                elif func_name == 'input':
                    node_id = self.add_node('input', f'Ввод данных')
                else:
                    node_id = self.add_node('operation', f'{func_name}({args})')
                    
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
        
        elif isinstance(stmt, ast.Return):
            if stmt.value:
                value = self.get_expr_text(stmt.value)
                node_id = self.add_node('operation', f'ВЕРНУТЬ {value}')
            else:
                node_id = self.add_node('operation', 'ВЕРНУТЬ')
            for pid in prev_ids:
                if pid is not None:
                    self.add_edge(pid, node_id)
            return [node_id]
        
        elif isinstance(stmt, ast.Break):
            node_id = self.add_node('operation', 'ВЫХОД ИЗ ЦИКЛА')
            for pid in prev_ids:
                if pid is not None:
                    self.add_edge(pid, node_id)
            return [None]
        
        elif isinstance(stmt, ast.Continue):
            node_id = self.add_node('operation', 'ПРОДОЛЖИТЬ')
            for pid in prev_ids:
                if pid is not None:
                    self.add_edge(pid, node_id)
            return [None]
        
        elif isinstance(stmt, ast.Pass):
            return prev_ids
        
        return prev_ids
    
    def process_if(self, stmt, prev_ids):
        """Обработка условного оператора IF"""
        condition = self.get_expr_text(stmt.test)
        cond_id = self.add_node('condition', condition)
        
        # Связываем предыдущие узлы с условием
        for pid in prev_ids:
            if pid is not None:
                self.add_edge(pid, cond_id)
        
        exit_ids = []
        
        # Ветка "Да" (if body)
        if stmt.body:
            # Запоминаем индекс для маркировки
            edge_index_before = len(self.edges)
            if_body_ids = self.process_body(stmt.body, [cond_id])
            
            # Помечаем первую связь от условия как "Да"
            for i in range(edge_index_before, len(self.edges)):
                if self.edges[i]['from'] == cond_id and not self.edges[i]['label']:
                    self.edges[i]['label'] = 'Да'
                    break
            
            exit_ids.extend(if_body_ids)
        
        # Ветка "Нет" (else/elif)
        if stmt.orelse:
            edge_index_before = len(self.edges)
            
            if len(stmt.orelse) == 1 and isinstance(stmt.orelse[0], ast.If):
                # elif - рекурсивно обрабатываем
                elif_ids = self.process_if(stmt.orelse[0], [cond_id])
                exit_ids.extend(elif_ids)
            else:
                # else
                else_body_ids = self.process_body(stmt.orelse, [cond_id])
                exit_ids.extend(else_body_ids)
            
            # Помечаем связь как "Нет"
            for i in range(edge_index_before, len(self.edges)):
                if self.edges[i]['from'] == cond_id and not self.edges[i]['label']:
                    self.edges[i]['label'] = 'Нет'
                    break
        else:
            # Нет else - условие само является выходом для "Нет"
            exit_ids.append(cond_id)
        
        # Фильтруем None
        exit_ids = [eid for eid in exit_ids if eid is not None]
        return exit_ids if exit_ids else [None]
    
    def process_while(self, stmt, prev_ids):
        """Обработка цикла WHILE"""
        condition = self.get_expr_text(stmt.test)
        cond_id = self.add_node('loop_condition', f'{condition}')
        
        # Связываем предыдущие узлы с условием
        for pid in prev_ids:
            if pid is not None:
                self.add_edge(pid, cond_id)
        
        # Тело цикла
        if stmt.body:
            edge_index_before = len(self.edges)
            body_ids = self.process_body(stmt.body, [cond_id])
            
            # Помечаем вход в цикл как "Да"
            for i in range(edge_index_before, len(self.edges)):
                if self.edges[i]['from'] == cond_id and not self.edges[i]['label']:
                    self.edges[i]['label'] = 'Да'
                    break
            
            # Связываем конец тела обратно с условием
            for bid in body_ids:
                if bid is not None and bid != cond_id:
                    self.add_edge(bid, cond_id, '')
        
        # Выход из цикла (условие как точка выхода для "Нет")
        return [cond_id]
    
    def process_for(self, stmt, prev_ids):
        """Обработка цикла FOR"""
        target = self.get_name(stmt.target)
        iter_val = self.get_expr_text(stmt.iter)
        
        # Инициализация цикла
        init_id = self.add_node('loop_init', f'{target} в {iter_val}')
        for pid in prev_ids:
            if pid is not None:
                self.add_edge(pid, init_id)
        
        # Условие цикла
        cond_id = self.add_node('loop_condition', f'Ещё есть {target}?')
        self.add_edge(init_id, cond_id)
        
        # Тело цикла
        if stmt.body:
            edge_index_before = len(self.edges)
            body_ids = self.process_body(stmt.body, [cond_id])
            
            # Помечаем вход в тело как "Да"
            for i in range(edge_index_before, len(self.edges)):
                if self.edges[i]['from'] == cond_id and not self.edges[i]['label']:
                    self.edges[i]['label'] = 'Да'
                    break
            
            # Связываем конец тела обратно с условием
            for bid in body_ids:
                if bid is not None and bid != cond_id:
                    self.add_edge(bid, cond_id, '')
        
        return [cond_id]
    
    def get_name(self, node):
        """Получить имя переменной/функции"""
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
        """Получить текстовое представление выражения"""
        if isinstance(node, ast.Constant):
            if isinstance(node.value, str):
                return f'"{node.value}"'
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
            op = self.get_op(node.op)
            values = [self.get_expr_text(v) for v in node.values]
            return f' {op} '.join(values)
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
            test = self.get_expr_text(node.test)
            body = self.get_expr_text(node.body)
            orelse = self.get_expr_text(node.orelse)
            return f'{body} если {test} иначе {orelse}'
        elif isinstance(node, ast.ListComp):
            return '[генератор]'
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
            ast.And: 'И', ast.Or: 'ИЛИ',
            ast.In: 'в', ast.NotIn: 'не в',
            ast.Is: 'есть', ast.IsNot: 'не есть',
        }
        return ops.get(type(op), '?')
    
    def get_unary_op(self, op):
        """Получить символ унарной операции"""
        ops = {
            ast.Not: 'НЕ ',
            ast.UAdd: '+',
            ast.USub: '-',
        }
        return ops.get(type(op), '?')
    
    def get_flowchart_data(self):
        """Получить данные блок-схемы"""
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
            return jsonify({'error': 'Файл слишком большой (макс. 1 МБ)'}), 400

        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return jsonify({'error': f'Синтаксическая ошибка в строке {e.lineno}: {e.msg}'}), 400

        functions = []
        
        # Обрабатываем функции
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                builder = FlowchartBuilder()
                builder.build_from_ast(node)
                functions.append({
                    'name': node.name,
                    'flowchart': builder.get_flowchart_data()
                })
        
        # Основной код (вне функций)
        main_builder = FlowchartBuilder()
        main_body = [stmt for stmt in tree.body if not isinstance(stmt, ast.FunctionDef)]
        
        if main_body:
            start_id = main_builder.add_node('start', 'НАЧАЛО ПРОГРАММЫ')
            last_ids = main_builder.process_body(main_body, [start_id])
            end_id = main_builder.add_node('end', 'КОНЕЦ ПРОГРАММЫ')
            for lid in last_ids:
                if lid is not None:
                    main_builder.add_edge(lid, end_id)
                    
        main_flowchart = main_builder.get_flowchart_data()

        return jsonify({
            'success': True,
            'main_flowchart': main_flowchart,
            'functions': functions,
            'code': code
        })
        
    except Exception as e:
        import traceback
        print(f"Error: {traceback.format_exc()}")
        return jsonify({'error': f'Ошибка: {str(e)}'}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

"""
Парсер JavaScript для генерации блок-схем
Использует регулярные выражения для базового анализа
"""
import re


class JSFlowchartBuilder:
    """Строитель блок-схем для JavaScript"""
    
    def __init__(self):
        self.nodes = []
        self.edges = []
        self.node_id = 0
        
    def add_node(self, node_type, text):
        node = {
            'id': self.node_id,
            'type': node_type,
            'text': text
        }
        self.nodes.append(node)
        self.node_id += 1
        return node['id']
    
    def add_edge(self, from_id, to_id, label='', branch=''):
        for edge in self.edges:
            if edge['from'] == from_id and edge['to'] == to_id:
                if label and not edge['label']:
                    edge['label'] = label
                    edge['branch'] = branch
                return edge
        
        edge = {
            'from': from_id,
            'to': to_id,
            'label': label,
            'branch': branch
        }
        self.edges.append(edge)
        return edge
    
    def get_flowchart_data(self):
        return {'nodes': self.nodes, 'edges': self.edges}


def tokenize_js(code):
    """Разбить JS код на токены"""
    tokens = []
    i = 0
    while i < len(code):
        # Пропуск пробелов
        if code[i] in ' \t\n\r':
            i += 1
            continue
        
        # Однострочный комментарий
        if code[i:i+2] == '//':
            end = code.find('\n', i)
            if end == -1:
                end = len(code)
            i = end + 1
            continue
        
        # Многострочный комментарий
        if code[i:i+2] == '/*':
            end = code.find('*/', i)
            if end == -1:
                end = len(code)
            else:
                end += 2
            i = end
            continue
        
        # Строки
        if code[i] in '"\'`':
            quote = code[i]
            j = i + 1
            while j < len(code):
                if code[j] == '\\':
                    j += 2
                elif code[j] == quote:
                    j += 1
                    break
                else:
                    j += 1
            tokens.append(('STRING', code[i:j]))
            i = j
            continue
        
        # Ключевые слова и идентификаторы
        if code[i].isalpha() or code[i] == '_':
            j = i
            while j < len(code) and (code[j].isalnum() or code[j] == '_'):
                j += 1
            word = code[i:j]
            keywords = ['function', 'if', 'else', 'for', 'while', 'do', 'switch', 
                       'case', 'break', 'continue', 'return', 'var', 'let', 'const',
                       'class', 'constructor', 'try', 'catch', 'finally', 'throw',
                       'async', 'await', 'console']
            if word in keywords:
                tokens.append((word.upper(), word))
            else:
                tokens.append(('IDENT', word))
            i = j
            continue
        
        # Числа
        if code[i].isdigit():
            j = i
            while j < len(code) and (code[j].isdigit() or code[j] == '.'):
                j += 1
            tokens.append(('NUMBER', code[i:j]))
            i = j
            continue
        
        # Операторы и символы
        two_char = code[i:i+2]
        if two_char in ['==', '!=', '<=', '>=', '&&', '||', '++', '--', '+=', '-=', '=>', '===', '!==']:
            tokens.append(('OP', two_char))
            i += 2
            continue
        
        tokens.append((code[i], code[i]))
        i += 1
    
    return tokens


def parse_js_block(tokens, start, builder, prev_ids):
    """Парсить блок кода в фигурных скобках"""
    i = start
    depth = 0
    
    # Найти начало блока
    while i < len(tokens) and tokens[i][0] != '{':
        i += 1
    
    if i >= len(tokens):
        return start, prev_ids
    
    i += 1  # пропустить {
    depth = 1
    
    while i < len(tokens) and depth > 0:
        token = tokens[i]
        
        if token[0] == '{':
            depth += 1
            i += 1
        elif token[0] == '}':
            depth -= 1
            i += 1
        elif token[0] == 'IF':
            i, prev_ids = parse_js_if(tokens, i, builder, prev_ids)
        elif token[0] == 'FOR':
            i, prev_ids = parse_js_for(tokens, i, builder, prev_ids)
        elif token[0] == 'WHILE':
            i, prev_ids = parse_js_while(tokens, i, builder, prev_ids)
        elif token[0] == 'DO':
            i, prev_ids = parse_js_do_while(tokens, i, builder, prev_ids)
        elif token[0] == 'SWITCH':
            i, prev_ids = parse_js_switch(tokens, i, builder, prev_ids)
        elif token[0] == 'TRY':
            i, prev_ids = parse_js_try(tokens, i, builder, prev_ids)
        elif token[0] == 'RETURN':
            i, prev_ids = parse_js_return(tokens, i, builder, prev_ids)
        elif token[0] == 'CONSOLE':
            i, prev_ids = parse_js_console(tokens, i, builder, prev_ids)
        elif token[0] in ['VAR', 'LET', 'CONST']:
            i, prev_ids = parse_js_var(tokens, i, builder, prev_ids)
        elif token[0] == 'IDENT':
            i, prev_ids = parse_js_statement(tokens, i, builder, prev_ids)
        else:
            i += 1
    
    return i, prev_ids


def parse_js_if(tokens, start, builder, prev_ids):
    """Парсить if/else"""
    i = start + 1  # пропустить IF
    
    # Получить условие
    condition = ""
    if i < len(tokens) and tokens[i][0] == '(':
        depth = 1
        i += 1
        while i < len(tokens) and depth > 0:
            if tokens[i][0] == '(':
                depth += 1
            elif tokens[i][0] == ')':
                depth -= 1
            if depth > 0:
                condition += tokens[i][1] + " "
            i += 1
    
    condition = condition.strip() + "?"
    cond_id = builder.add_node('condition', condition)
    
    for pid in prev_ids:
        if pid is not None:
            builder.add_edge(pid, cond_id)
    
    # Ветка "да"
    edge_idx = len(builder.edges)
    i, yes_ids = parse_js_block(tokens, i, builder, [cond_id])
    
    for j in range(edge_idx, len(builder.edges)):
        if builder.edges[j]['from'] == cond_id and not builder.edges[j]['label']:
            builder.edges[j]['label'] = 'да'
            builder.edges[j]['branch'] = 'yes'
            break
    
    exit_ids = list(yes_ids) if yes_ids else []
    
    # Проверить else
    if i < len(tokens) and tokens[i][0] == 'ELSE':
        i += 1
        edge_idx = len(builder.edges)
        
        if i < len(tokens) and tokens[i][0] == 'IF':
            i, no_ids = parse_js_if(tokens, i, builder, [cond_id])
        else:
            i, no_ids = parse_js_block(tokens, i, builder, [cond_id])
        
        for j in range(edge_idx, len(builder.edges)):
            if builder.edges[j]['from'] == cond_id and not builder.edges[j]['label']:
                builder.edges[j]['label'] = 'нет'
                builder.edges[j]['branch'] = 'no'
                break
        
        for nid in no_ids:
            if nid is not None:
                exit_ids.append(('from_no_branch', nid))
    else:
        exit_ids.append(('no_empty', cond_id))
    
    return i, exit_ids if exit_ids else [None]


def parse_js_for(tokens, start, builder, prev_ids):
    """Парсить for"""
    i = start + 1
    
    # Получить заголовок цикла
    header = ""
    if i < len(tokens) and tokens[i][0] == '(':
        depth = 1
        i += 1
        while i < len(tokens) and depth > 0:
            if tokens[i][0] == '(':
                depth += 1
            elif tokens[i][0] == ')':
                depth -= 1
            if depth > 0:
                header += tokens[i][1] + " "
            i += 1
    
    header = header.strip()
    loop_id = builder.add_node('loop', f'for ({header})')
    
    for pid in prev_ids:
        if pid is not None:
            if isinstance(pid, tuple) and pid[0] == 'no_empty':
                builder.add_edge(pid[1], loop_id, 'нет', 'no')
            elif isinstance(pid, tuple) and pid[0] == 'from_no_branch':
                builder.add_edge(pid[1], loop_id, '', 'from_no')
            else:
                builder.add_edge(pid, loop_id)
    
    # Тело цикла
    i, body_ids = parse_js_block(tokens, i, builder, [loop_id])
    
    # Обратная связь
    for bid in body_ids:
        if bid is not None and not isinstance(bid, tuple):
            builder.add_edge(bid, loop_id, '', 'loop_back')
    
    return i, [('loop_exit', loop_id)]


def parse_js_while(tokens, start, builder, prev_ids):
    """Парсить while"""
    i = start + 1
    
    # Получить условие
    condition = ""
    if i < len(tokens) and tokens[i][0] == '(':
        depth = 1
        i += 1
        while i < len(tokens) and depth > 0:
            if tokens[i][0] == '(':
                depth += 1
            elif tokens[i][0] == ')':
                depth -= 1
            if depth > 0:
                condition += tokens[i][1] + " "
            i += 1
    
    condition = condition.strip() + "?"
    loop_id = builder.add_node('loop', f'while ({condition[:-1]})')
    
    for pid in prev_ids:
        if pid is not None:
            if isinstance(pid, tuple) and pid[0] == 'no_empty':
                builder.add_edge(pid[1], loop_id, 'нет', 'no')
            elif isinstance(pid, tuple) and pid[0] == 'from_no_branch':
                builder.add_edge(pid[1], loop_id, '', 'from_no')
            else:
                builder.add_edge(pid, loop_id)
    
    # Тело цикла
    i, body_ids = parse_js_block(tokens, i, builder, [loop_id])
    
    for bid in body_ids:
        if bid is not None and not isinstance(bid, tuple):
            builder.add_edge(bid, loop_id, '', 'loop_back')
    
    return i, [('loop_exit', loop_id)]


def parse_js_do_while(tokens, start, builder, prev_ids):
    """Парсить do-while"""
    i = start + 1
    
    do_id = builder.add_node('process', 'do')
    
    for pid in prev_ids:
        if pid is not None:
            builder.add_edge(pid, do_id)
    
    # Тело
    i, body_ids = parse_js_block(tokens, i, builder, [do_id])
    
    # while условие
    if i < len(tokens) and tokens[i][0] == 'WHILE':
        i += 1
        condition = ""
        if i < len(tokens) and tokens[i][0] == '(':
            depth = 1
            i += 1
            while i < len(tokens) and depth > 0:
                if tokens[i][0] == '(':
                    depth += 1
                elif tokens[i][0] == ')':
                    depth -= 1
                if depth > 0:
                    condition += tokens[i][1] + " "
                i += 1
        
        loop_id = builder.add_node('condition', condition.strip() + "?")
        
        for bid in body_ids:
            if bid is not None and not isinstance(bid, tuple):
                builder.add_edge(bid, loop_id)
        
        builder.add_edge(loop_id, do_id, 'да', 'yes')
        
        # Пропустить ;
        if i < len(tokens) and tokens[i][0] == ';':
            i += 1
        
        return i, [('no_empty', loop_id)]
    
    return i, body_ids


def parse_js_switch(tokens, start, builder, prev_ids):
    """Парсить switch"""
    i = start + 1
    
    # Получить выражение
    expr = ""
    if i < len(tokens) and tokens[i][0] == '(':
        depth = 1
        i += 1
        while i < len(tokens) and depth > 0:
            if tokens[i][0] == '(':
                depth += 1
            elif tokens[i][0] == ')':
                depth -= 1
            if depth > 0:
                expr += tokens[i][1] + " "
            i += 1
    
    switch_id = builder.add_node('condition', f'switch ({expr.strip()})')
    
    for pid in prev_ids:
        if pid is not None:
            builder.add_edge(pid, switch_id)
    
    exit_ids = []
    
    # Парсить case
    if i < len(tokens) and tokens[i][0] == '{':
        i += 1
        depth = 1
        
        while i < len(tokens) and depth > 0:
            if tokens[i][0] == '{':
                depth += 1
                i += 1
            elif tokens[i][0] == '}':
                depth -= 1
                i += 1
            elif tokens[i][0] == 'CASE':
                i += 1
                case_val = ""
                while i < len(tokens) and tokens[i][0] != ':':
                    case_val += tokens[i][1] + " "
                    i += 1
                i += 1  # пропустить :
                
                case_id = builder.add_node('process', f'case {case_val.strip()}')
                builder.add_edge(switch_id, case_id, case_val.strip(), 'yes')
                exit_ids.append(case_id)
            elif tokens[i][0] == 'BREAK':
                i += 1
                if i < len(tokens) and tokens[i][0] == ';':
                    i += 1
            else:
                i += 1
    
    return i, exit_ids if exit_ids else [switch_id]


def parse_js_try(tokens, start, builder, prev_ids):
    """Парсить try-catch"""
    i = start + 1
    
    try_id = builder.add_node('process', 'try')
    
    for pid in prev_ids:
        if pid is not None:
            builder.add_edge(pid, try_id)
    
    # try блок
    i, try_ids = parse_js_block(tokens, i, builder, [try_id])
    
    exit_ids = list(try_ids)
    
    # catch
    if i < len(tokens) and tokens[i][0] == 'CATCH':
        i += 1
        # Пропустить (error)
        if i < len(tokens) and tokens[i][0] == '(':
            depth = 1
            i += 1
            while i < len(tokens) and depth > 0:
                if tokens[i][0] == '(':
                    depth += 1
                elif tokens[i][0] == ')':
                    depth -= 1
                i += 1
        
        catch_id = builder.add_node('process', 'catch')
        builder.add_edge(try_id, catch_id, 'ошибка', 'no')
        
        i, catch_ids = parse_js_block(tokens, i, builder, [catch_id])
        exit_ids.extend(catch_ids)
    
    # finally
    if i < len(tokens) and tokens[i][0] == 'FINALLY':
        i += 1
        finally_id = builder.add_node('process', 'finally')
        
        for eid in exit_ids:
            if eid is not None and not isinstance(eid, tuple):
                builder.add_edge(eid, finally_id)
        
        i, finally_ids = parse_js_block(tokens, i, builder, [finally_id])
        exit_ids = finally_ids
    
    return i, exit_ids


def parse_js_return(tokens, start, builder, prev_ids):
    """Парсить return"""
    i = start + 1
    
    value = ""
    while i < len(tokens) and tokens[i][0] != ';' and tokens[i][0] != '}':
        value += tokens[i][1] + " "
        i += 1
    
    if i < len(tokens) and tokens[i][0] == ';':
        i += 1
    
    text = f'return {value.strip()}' if value.strip() else 'return'
    ret_id = builder.add_node('output', text)  # output вместо process
    
    for pid in prev_ids:
        if pid is not None:
            if isinstance(pid, tuple) and pid[0] == 'no_empty':
                builder.add_edge(pid[1], ret_id, 'нет', 'no')
            elif isinstance(pid, tuple) and pid[0] == 'from_no_branch':
                builder.add_edge(pid[1], ret_id, '', 'from_no')
            else:
                builder.add_edge(pid, ret_id)
    
    return i, [ret_id]


def parse_js_console(tokens, start, builder, prev_ids):
    """Парсить console.log"""
    i = start + 1
    
    # .log
    if i < len(tokens) and tokens[i][0] == '.':
        i += 1
    if i < len(tokens) and tokens[i][0] == 'IDENT':
        i += 1
    
    # Аргументы
    args = ""
    if i < len(tokens) and tokens[i][0] == '(':
        depth = 1
        i += 1
        while i < len(tokens) and depth > 0:
            if tokens[i][0] == '(':
                depth += 1
            elif tokens[i][0] == ')':
                depth -= 1
            if depth > 0:
                args += tokens[i][1] + " "
            i += 1
    
    if i < len(tokens) and tokens[i][0] == ';':
        i += 1
    
    out_id = builder.add_node('output', f'console.log({args.strip()})')
    
    for pid in prev_ids:
        if pid is not None:
            if isinstance(pid, tuple) and pid[0] == 'no_empty':
                builder.add_edge(pid[1], out_id, 'нет', 'no')
            elif isinstance(pid, tuple) and pid[0] == 'from_no_branch':
                builder.add_edge(pid[1], out_id, '', 'from_no')
            else:
                builder.add_edge(pid, out_id)
    
    return i, [out_id]


def parse_js_var(tokens, start, builder, prev_ids):
    """Парсить объявление переменной"""
    i = start + 1
    
    statement = tokens[start][1] + " "
    while i < len(tokens) and tokens[i][0] != ';' and tokens[i][0] != '}':
        statement += tokens[i][1] + " "
        i += 1
    
    if i < len(tokens) and tokens[i][0] == ';':
        i += 1
    
    proc_id = builder.add_node('process', statement.strip())
    
    for pid in prev_ids:
        if pid is not None:
            if isinstance(pid, tuple) and pid[0] == 'no_empty':
                builder.add_edge(pid[1], proc_id, 'нет', 'no')
            elif isinstance(pid, tuple) and pid[0] == 'from_no_branch':
                builder.add_edge(pid[1], proc_id, '', 'from_no')
            else:
                builder.add_edge(pid, proc_id)
    
    return i, [proc_id]


def parse_js_statement(tokens, start, builder, prev_ids):
    """Парсить обычный оператор"""
    i = start
    
    statement = ""
    while i < len(tokens) and tokens[i][0] != ';' and tokens[i][0] != '}':
        statement += tokens[i][1] + " "
        i += 1
    
    if i < len(tokens) and tokens[i][0] == ';':
        i += 1
    
    if statement.strip():
        proc_id = builder.add_node('process', statement.strip())
        
        for pid in prev_ids:
            if pid is not None:
                if isinstance(pid, tuple) and pid[0] == 'no_empty':
                    builder.add_edge(pid[1], proc_id, 'нет', 'no')
                elif isinstance(pid, tuple) and pid[0] == 'from_no_branch':
                    builder.add_edge(pid[1], proc_id, '', 'from_no')
                else:
                    builder.add_edge(pid, proc_id)
        
        return i, [proc_id]
    
    return i, prev_ids


def parse_js_function(tokens, start):
    """Парсить функцию"""
    i = start + 1
    
    # async function
    is_async = False
    if i > 0 and tokens[start][0] == 'ASYNC':
        is_async = True
        i += 1
    
    # Имя функции
    name = ""
    if i < len(tokens) and tokens[i][0] == 'IDENT':
        name = tokens[i][1]
        i += 1
    
    # Параметры
    params = []
    if i < len(tokens) and tokens[i][0] == '(':
        i += 1
        while i < len(tokens) and tokens[i][0] != ')':
            if tokens[i][0] == 'IDENT':
                params.append(tokens[i][1])
            i += 1
        i += 1  # пропустить )
    
    builder = JSFlowchartBuilder()
    prefix = 'async ' if is_async else ''
    start_id = builder.add_node('start', f'начало {prefix}{name}()')
    
    prev_ids = [start_id]
    
    if params:
        param_id = builder.add_node('input', f'Параметры: {", ".join(params)}')
        builder.add_edge(start_id, param_id)
        prev_ids = [param_id]
    
    # Тело функции
    i, last_ids = parse_js_block(tokens, i, builder, prev_ids)
    
    end_id = builder.add_node('end', '')
    for lid in last_ids:
        if lid is None:
            continue
        if isinstance(lid, tuple):
            if lid[0] == 'no_empty':
                builder.add_edge(lid[1], end_id, 'нет', 'no')
            elif lid[0] == 'from_no_branch':
                builder.add_edge(lid[1], end_id, '', 'from_no')
            elif lid[0] == 'loop_exit':
                builder.add_edge(lid[1], end_id, '', 'loop_exit')
        else:
            builder.add_edge(lid, end_id)
    
    return i, name, builder.get_flowchart_data()


def parse_js_class(tokens, start):
    """Парсить класс"""
    i = start + 1
    
    # Имя класса
    name = ""
    if i < len(tokens) and tokens[i][0] == 'IDENT':
        name = tokens[i][1]
        i += 1
    
    # extends
    if i < len(tokens) and tokens[i][0] == 'IDENT' and tokens[i][1] == 'extends':
        i += 2  # пропустить extends и имя
    
    builder = JSFlowchartBuilder()
    class_id = builder.add_node('class_start', name)
    
    methods = []
    
    # Тело класса
    if i < len(tokens) and tokens[i][0] == '{':
        i += 1
        depth = 1
        
        while i < len(tokens) and depth > 0:
            if tokens[i][0] == '{':
                depth += 1
                i += 1
            elif tokens[i][0] == '}':
                depth -= 1
                i += 1
            elif tokens[i][0] == 'CONSTRUCTOR' or (tokens[i][0] == 'IDENT' and i + 1 < len(tokens) and tokens[i+1][0] == '('):
                method_name = tokens[i][1]
                # Пропустить до конца метода
                j = i
                while j < len(tokens) and tokens[j][0] != '{':
                    j += 1
                if j < len(tokens):
                    j += 1
                    d = 1
                    while j < len(tokens) and d > 0:
                        if tokens[j][0] == '{':
                            d += 1
                        elif tokens[j][0] == '}':
                            d -= 1
                        j += 1
                methods.append(method_name)
                i = j
            elif tokens[i][0] == 'ASYNC':
                i += 1
            else:
                i += 1
    
    # Методы веером
    for idx, method_name in enumerate(methods):
        method_id = builder.add_node('method', method_name + '()')
        builder.add_edge(class_id, method_id, '', f'fan_{idx}')
    
    return i, name, builder.get_flowchart_data(), methods


def parse_javascript(code):
    """Главная функция парсинга JavaScript"""
    tokens = tokenize_js(code)
    
    functions = []
    classes = []
    main_statements = []
    
    i = 0
    while i < len(tokens):
        token = tokens[i]
        
        if token[0] == 'FUNCTION':
            end_i, name, flowchart = parse_js_function(tokens, i)
            functions.append({
                'name': name,
                'type': 'function',
                'flowchart': flowchart
            })
            i = end_i
        elif token[0] == 'ASYNC' and i + 1 < len(tokens) and tokens[i+1][0] == 'FUNCTION':
            end_i, name, flowchart = parse_js_function(tokens, i + 1)
            functions.append({
                'name': f'async {name}',
                'type': 'function',
                'flowchart': flowchart
            })
            i = end_i
        elif token[0] == 'CLASS':
            end_i, name, flowchart, methods = parse_js_class(tokens, i)
            classes.append({
                'name': name,
                'type': 'class',
                'flowchart': flowchart
            })
            i = end_i
        else:
            main_statements.append(token)
            i += 1
    
    # Основной код
    main_flowchart = {'nodes': [], 'edges': []}
    if main_statements:
        builder = JSFlowchartBuilder()
        start_id = builder.add_node('start', 'начало main()')
        prev_ids = [start_id]
        
        # Простой парсинг main
        j = 0
        while j < len(main_statements):
            tok = main_statements[j]
            if tok[0] in ['VAR', 'LET', 'CONST', 'IDENT']:
                stmt = ""
                while j < len(main_statements) and main_statements[j][0] != ';':
                    stmt += main_statements[j][1] + " "
                    j += 1
                if stmt.strip():
                    proc_id = builder.add_node('process', stmt.strip())
                    for pid in prev_ids:
                        if pid is not None and not isinstance(pid, tuple):
                            builder.add_edge(pid, proc_id)
                    prev_ids = [proc_id]
            j += 1
        
        end_id = builder.add_node('end', '')
        for pid in prev_ids:
            if pid is not None and not isinstance(pid, tuple):
                builder.add_edge(pid, end_id)
        
        main_flowchart = builder.get_flowchart_data()
    
    return {
        'success': True,
        'main_flowchart': main_flowchart,
        'functions': functions,
        'classes': classes,
        'code': code
    }

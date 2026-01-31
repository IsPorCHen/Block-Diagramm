"""
Парсер C# для генерации блок-схем
Улучшенная версия с поддержкой свойств, статических членов
"""
import re


class CSharpFlowchartBuilder:
    """Строитель блок-схем для C#"""
    
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


def remove_comments(code):
    """Удалить комментарии из кода"""
    result = []
    i = 0
    while i < len(code):
        if code[i:i+2] == '//':
            end = code.find('\n', i)
            if end == -1:
                break
            i = end + 1
        elif code[i:i+2] == '/*':
            end = code.find('*/', i)
            if end == -1:
                break
            i = end + 2
        else:
            result.append(code[i])
            i += 1
    return ''.join(result)


def find_matching_brace(code, start):
    """Найти закрывающую скобку"""
    depth = 0
    i = start
    in_string = False
    string_char = None
    
    while i < len(code):
        c = code[i]
        
        # Обработка строк
        if not in_string and c in '"\'':
            in_string = True
            string_char = c
            i += 1
            continue
        
        if in_string:
            if c == '\\' and i + 1 < len(code):
                i += 2
                continue
            if c == string_char:
                in_string = False
            i += 1
            continue
        
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return len(code)


def find_matching_paren(code, start):
    """Найти закрывающую круглую скобку"""
    depth = 0
    i = start
    in_string = False
    string_char = None
    
    while i < len(code):
        c = code[i]
        
        if not in_string and c in '"\'':
            in_string = True
            string_char = c
            i += 1
            continue
        
        if in_string:
            if c == '\\' and i + 1 < len(code):
                i += 2
                continue
            if c == string_char:
                in_string = False
            i += 1
            continue
        
        if c == '(':
            depth += 1
        elif c == ')':
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return len(code)


def extract_block(code, start):
    """Извлечь блок кода в фигурных скобках"""
    brace_start = code.find('{', start)
    if brace_start == -1:
        return "", len(code)
    
    brace_end = find_matching_brace(code, brace_start)
    return code[brace_start + 1:brace_end], brace_end + 1


def connect_nodes(builder, from_id, to_id, label='', branch=''):
    """Соединить узлы с учётом маркеров"""
    if isinstance(from_id, tuple):
        if from_id[0] == 'no_empty':
            builder.add_edge(from_id[1], to_id, 'нет', 'no')
        elif from_id[0] == 'from_no_branch':
            builder.add_edge(from_id[1], to_id, '', 'from_no')
        elif from_id[0] == 'loop_exit':
            builder.add_edge(from_id[1], to_id, '', 'loop_exit')
        elif from_id[0] == 'return':
            pass  # return не соединяется с следующим блоком
    else:
        builder.add_edge(from_id, to_id, label, branch)


def is_keyword(code, pos, keyword):
    """Проверить, что в позиции pos начинается ключевое слово"""
    if not code[pos:].startswith(keyword):
        return False
    end = pos + len(keyword)
    if end >= len(code):
        return True
    return not code[end].isalnum() and code[end] != '_'


def parse_method_body(code, builder, prev_ids):
    """Парсить тело метода"""
    code = code.strip()
    if not code:
        return prev_ids
    
    return_ids = []  # Собираем return маркеры
    
    i = 0
    while i < len(code):
        # Пропуск пробелов
        while i < len(code) and code[i] in ' \t\n\r':
            i += 1
        
        if i >= len(code):
            break
        
        # Фильтруем return из prev_ids
        non_return = [p for p in prev_ids if not (isinstance(p, tuple) and p[0] == 'return')]
        new_returns = [p for p in prev_ids if isinstance(p, tuple) and p[0] == 'return']
        return_ids.extend(new_returns)
        
        if not non_return:
            break  # Все пути закончились return
        
        prev_ids = non_return
        
        # IF
        if is_keyword(code, i, 'if'):
            i, prev_ids = parse_if(code, i, builder, prev_ids)
            continue
        
        # FOR
        if is_keyword(code, i, 'for'):
            i, prev_ids = parse_for(code, i, builder, prev_ids)
            continue
        
        # FOREACH
        if is_keyword(code, i, 'foreach'):
            i, prev_ids = parse_foreach(code, i, builder, prev_ids)
            continue
        
        # WHILE
        if is_keyword(code, i, 'while'):
            i, prev_ids = parse_while(code, i, builder, prev_ids)
            continue
        
        # DO
        if is_keyword(code, i, 'do'):
            i, prev_ids = parse_do_while(code, i, builder, prev_ids)
            continue
        
        # SWITCH
        if is_keyword(code, i, 'switch'):
            i, prev_ids = parse_switch(code, i, builder, prev_ids)
            continue
        
        # TRY
        if is_keyword(code, i, 'try'):
            i, prev_ids = parse_try(code, i, builder, prev_ids)
            continue
        
        # RETURN
        if is_keyword(code, i, 'return'):
            i, prev_ids = parse_return(code, i, builder, prev_ids)
            continue
        
        # THROW
        if is_keyword(code, i, 'throw'):
            i, prev_ids = parse_throw(code, i, builder, prev_ids)
            continue
        
        # BREAK / CONTINUE
        if is_keyword(code, i, 'break') or is_keyword(code, i, 'continue'):
            end = code.find(';', i)
            if end == -1:
                end = len(code)
            i = end + 1
            continue
        
        # Пропустить закрывающую скобку
        if code[i] == '}':
            i += 1
            continue
        
        # Обычный оператор (до ;)
        stmt_end = code.find(';', i)
        if stmt_end == -1:
            stmt_end = len(code)
        
        stmt = code[i:stmt_end].strip()
        if stmt:
            # Проверить - это вывод?
            if 'Console.Write' in stmt or 'MessageBox.Show' in stmt:
                node_id = builder.add_node('output', stmt)
            else:
                node_id = builder.add_node('process', stmt)
            
            for pid in prev_ids:
                if pid is not None:
                    connect_nodes(builder, pid, node_id)
            prev_ids = [node_id]
        
        i = stmt_end + 1
    
    # Возвращаем все return и текущие выходы
    return prev_ids + return_ids


def parse_if(code, start, builder, prev_ids):
    """Парсить if/else if/else"""
    i = start + 2
    
    while i < len(code) and code[i] in ' \t\n\r':
        i += 1
    
    if i < len(code) and code[i] == '(':
        paren_end = find_matching_paren(code, i)
        condition = code[i + 1:paren_end].strip()
        i = paren_end + 1
    else:
        condition = "?"
    
    cond_id = builder.add_node('condition', condition + '?')
    
    for pid in prev_ids:
        if pid is not None:
            connect_nodes(builder, pid, cond_id)
    
    while i < len(code) and code[i] in ' \t\n\r':
        i += 1
    
    edge_idx = len(builder.edges)
    
    if i < len(code) and code[i] == '{':
        body, i = extract_block(code, i)
        yes_ids = parse_method_body(body, builder, [cond_id])
    else:
        stmt_end = code.find(';', i)
        if stmt_end == -1:
            stmt_end = len(code)
        stmt = code[i:stmt_end].strip()
        if stmt:
            node_id = builder.add_node('process', stmt)
            builder.add_edge(cond_id, node_id)
            yes_ids = [node_id]
        else:
            yes_ids = [cond_id]
        i = stmt_end + 1
    
    for j in range(edge_idx, len(builder.edges)):
        if builder.edges[j]['from'] == cond_id and not builder.edges[j]['label']:
            builder.edges[j]['label'] = 'да'
            builder.edges[j]['branch'] = 'yes'
            break
    
    exit_ids = list(yes_ids) if yes_ids else []
    
    while i < len(code) and code[i] in ' \t\n\r':
        i += 1
    
    if is_keyword(code, i, 'else'):
        i += 4
        while i < len(code) and code[i] in ' \t\n\r':
            i += 1
        
        edge_idx = len(builder.edges)
        
        if is_keyword(code, i, 'if'):
            i, no_ids = parse_if(code, i, builder, [cond_id])
        elif i < len(code) and code[i] == '{':
            body, i = extract_block(code, i)
            no_ids = parse_method_body(body, builder, [cond_id])
        else:
            stmt_end = code.find(';', i)
            if stmt_end == -1:
                stmt_end = len(code)
            stmt = code[i:stmt_end].strip()
            if stmt:
                node_id = builder.add_node('process', stmt)
                builder.add_edge(cond_id, node_id)
                no_ids = [node_id]
            else:
                no_ids = [cond_id]
            i = stmt_end + 1
        
        for j in range(edge_idx, len(builder.edges)):
            if builder.edges[j]['from'] == cond_id and not builder.edges[j]['label']:
                builder.edges[j]['label'] = 'нет'
                builder.edges[j]['branch'] = 'no'
                break
        
        # Когда есть else, выходы без маркеров
        for nid in no_ids:
            if nid is not None:
                if isinstance(nid, tuple):
                    exit_ids.append(nid)
                else:
                    exit_ids.append(nid)  # Без маркера from_no_branch
    else:
        exit_ids.append(('no_empty', cond_id))
    
    return i, exit_ids if exit_ids else [None]


def parse_for(code, start, builder, prev_ids):
    """Парсить for"""
    i = start + 3
    
    while i < len(code) and code[i] in ' \t\n\r':
        i += 1
    
    if i < len(code) and code[i] == '(':
        paren_end = find_matching_paren(code, i)
        header = code[i + 1:paren_end].strip()
        i = paren_end + 1
    else:
        header = "..."
    
    loop_id = builder.add_node('loop', f'for ({header})')
    
    for pid in prev_ids:
        if pid is not None:
            connect_nodes(builder, pid, loop_id)
    
    while i < len(code) and code[i] in ' \t\n\r':
        i += 1
    
    if i < len(code) and code[i] == '{':
        body, i = extract_block(code, i)
        body_ids = parse_method_body(body, builder, [loop_id])
    else:
        stmt_end = code.find(';', i)
        if stmt_end == -1:
            stmt_end = len(code)
        i = stmt_end + 1
        body_ids = []
    
    for bid in body_ids:
        if bid is not None and not isinstance(bid, tuple):
            builder.add_edge(bid, loop_id, '', 'loop_back')
    
    return i, [('loop_exit', loop_id)]


def parse_foreach(code, start, builder, prev_ids):
    """Парсить foreach"""
    i = start + 7
    
    while i < len(code) and code[i] in ' \t\n\r':
        i += 1
    
    if i < len(code) and code[i] == '(':
        paren_end = find_matching_paren(code, i)
        header = code[i + 1:paren_end].strip()
        i = paren_end + 1
    else:
        header = "..."
    
    loop_id = builder.add_node('loop', f'foreach ({header})')
    
    for pid in prev_ids:
        if pid is not None:
            connect_nodes(builder, pid, loop_id)
    
    while i < len(code) and code[i] in ' \t\n\r':
        i += 1
    
    if i < len(code) and code[i] == '{':
        body, i = extract_block(code, i)
        body_ids = parse_method_body(body, builder, [loop_id])
    else:
        stmt_end = code.find(';', i)
        if stmt_end == -1:
            stmt_end = len(code)
        i = stmt_end + 1
        body_ids = []
    
    for bid in body_ids:
        if bid is not None and not isinstance(bid, tuple):
            builder.add_edge(bid, loop_id, '', 'loop_back')
    
    return i, [('loop_exit', loop_id)]


def parse_while(code, start, builder, prev_ids):
    """Парсить while"""
    i = start + 5
    
    while i < len(code) and code[i] in ' \t\n\r':
        i += 1
    
    if i < len(code) and code[i] == '(':
        paren_end = find_matching_paren(code, i)
        condition = code[i + 1:paren_end].strip()
        i = paren_end + 1
    else:
        condition = "?"
    
    loop_id = builder.add_node('loop', f'while ({condition})')
    
    for pid in prev_ids:
        if pid is not None:
            connect_nodes(builder, pid, loop_id)
    
    while i < len(code) and code[i] in ' \t\n\r':
        i += 1
    
    if i < len(code) and code[i] == '{':
        body, i = extract_block(code, i)
        body_ids = parse_method_body(body, builder, [loop_id])
    else:
        stmt_end = code.find(';', i)
        if stmt_end == -1:
            stmt_end = len(code)
        i = stmt_end + 1
        body_ids = []
    
    for bid in body_ids:
        if bid is not None and not isinstance(bid, tuple):
            builder.add_edge(bid, loop_id, '', 'loop_back')
    
    return i, [('loop_exit', loop_id)]


def parse_do_while(code, start, builder, prev_ids):
    """Парсить do-while: тело → условие (ромб) → да к началу тела, нет дальше"""
    i = start + 2
    
    while i < len(code) and code[i] in ' \t\n\r':
        i += 1
    
    # Парсим тело цикла
    if i < len(code) and code[i] == '{':
        body, i = extract_block(code, i)
        # Парсим тело, начиная от prev_ids
        body_ids = parse_method_body(body, builder, prev_ids)
    else:
        body_ids = prev_ids
    
    while i < len(code) and code[i] in ' \t\n\r':
        i += 1
    
    # Ищем while
    if is_keyword(code, i, 'while'):
        i += 5
        while i < len(code) and code[i] in ' \t\n\r':
            i += 1
        
        if i < len(code) and code[i] == '(':
            paren_end = find_matching_paren(code, i)
            condition = code[i + 1:paren_end].strip()
            i = paren_end + 1
        else:
            condition = "?"
        
        # Создаём условие (ромб)
        cond_id = builder.add_node('condition', condition + '?')
        
        # Связываем конец тела с условием
        for bid in body_ids:
            if bid is not None and not isinstance(bid, tuple):
                builder.add_edge(bid, cond_id)
            elif isinstance(bid, tuple) and bid[0] != 'return':
                builder.add_edge(bid[1], cond_id)
        
        # Находим первый блок тела (после prev_ids)
        # Это будет первый узел, добавленный после начала парсинга тела
        first_body_node = None
        for pid in prev_ids:
            if isinstance(pid, tuple):
                continue
            # Находим детей pid
            for edge in builder.edges:
                if edge['from'] == pid and edge['to'] != cond_id:
                    first_body_node = edge['to']
                    break
            if first_body_node:
                break
        
        # Если нашли первый блок тела - связь "да" к нему
        if first_body_node is not None:
            builder.add_edge(cond_id, first_body_node, 'да', 'yes')
        
        while i < len(code) and code[i] in ' \t\n\r;':
            i += 1
        
        # Выход - ветка "нет" от условия
        return i, [('no_empty', cond_id)]
    
    return i, body_ids


def parse_switch(code, start, builder, prev_ids):
    """Парсить switch"""
    i = start + 6
    
    while i < len(code) and code[i] in ' \t\n\r':
        i += 1
    
    if i < len(code) and code[i] == '(':
        paren_end = find_matching_paren(code, i)
        expr = code[i + 1:paren_end].strip()
        i = paren_end + 1
    else:
        expr = "?"
    
    switch_id = builder.add_node('condition', f'switch ({expr})')
    
    for pid in prev_ids:
        if pid is not None:
            connect_nodes(builder, pid, switch_id)
    
    while i < len(code) and code[i] in ' \t\n\r':
        i += 1
    
    exit_ids = []
    
    if i < len(code) and code[i] == '{':
        body, i = extract_block(code, i)
        
        cases = re.findall(r'case\s+([^:]+):', body)
        has_default = 'default:' in body
        
        for case_val in cases:
            case_id = builder.add_node('process', f'case {case_val.strip()}')
            builder.add_edge(switch_id, case_id, case_val.strip(), 'yes')
            exit_ids.append(case_id)
        
        if has_default:
            default_id = builder.add_node('process', 'default')
            builder.add_edge(switch_id, default_id, 'default', 'no')
            exit_ids.append(default_id)
    
    return i, exit_ids if exit_ids else [switch_id]


def parse_try(code, start, builder, prev_ids):
    """Парсить try-catch-finally"""
    i = start + 3
    
    while i < len(code) and code[i] in ' \t\n\r':
        i += 1
    
    try_id = builder.add_node('process', 'try')
    
    for pid in prev_ids:
        if pid is not None:
            connect_nodes(builder, pid, try_id)
    
    if i < len(code) and code[i] == '{':
        body, i = extract_block(code, i)
        try_ids = parse_method_body(body, builder, [try_id])
    else:
        try_ids = [try_id]
    
    exit_ids = list(try_ids)
    
    while True:
        while i < len(code) and code[i] in ' \t\n\r':
            i += 1
        
        if not is_keyword(code, i, 'catch'):
            break
        
        i += 5
        while i < len(code) and code[i] in ' \t\n\r':
            i += 1
        
        exception = ""
        if i < len(code) and code[i] == '(':
            paren_end = find_matching_paren(code, i)
            exception = code[i + 1:paren_end].strip()
            i = paren_end + 1
        
        catch_text = f'catch ({exception})' if exception else 'catch'
        catch_id = builder.add_node('process', catch_text)
        builder.add_edge(try_id, catch_id, 'ошибка', 'no')
        
        while i < len(code) and code[i] in ' \t\n\r':
            i += 1
        
        if i < len(code) and code[i] == '{':
            body, i = extract_block(code, i)
            catch_ids = parse_method_body(body, builder, [catch_id])
            exit_ids.extend(catch_ids)
        else:
            exit_ids.append(catch_id)
    
    while i < len(code) and code[i] in ' \t\n\r':
        i += 1
    
    if is_keyword(code, i, 'finally'):
        i += 7
        while i < len(code) and code[i] in ' \t\n\r':
            i += 1
        
        finally_id = builder.add_node('process', 'finally')
        
        for eid in exit_ids:
            if eid is not None and not isinstance(eid, tuple):
                builder.add_edge(eid, finally_id)
        
        if i < len(code) and code[i] == '{':
            body, i = extract_block(code, i)
            finally_ids = parse_method_body(body, builder, [finally_id])
            exit_ids = finally_ids
        else:
            exit_ids = [finally_id]
    
    return i, exit_ids


def parse_return(code, start, builder, prev_ids):
    """Парсить return - терминальный узел"""
    i = start + 6
    
    stmt_end = code.find(';', i)
    if stmt_end == -1:
        stmt_end = len(code)
    
    value = code[i:stmt_end].strip()
    text = f'return {value}' if value else 'return'
    
    ret_id = builder.add_node('output', text)
    
    for pid in prev_ids:
        if pid is not None:
            connect_nodes(builder, pid, ret_id)
    
    return stmt_end + 1, [('return', ret_id)]  # Маркер return


def parse_throw(code, start, builder, prev_ids):
    """Парсить throw"""
    i = start + 5
    
    stmt_end = code.find(';', i)
    if stmt_end == -1:
        stmt_end = len(code)
    
    value = code[i:stmt_end].strip()
    text = f'throw {value}' if value else 'throw'
    
    throw_id = builder.add_node('process', text)
    
    for pid in prev_ids:
        if pid is not None:
            connect_nodes(builder, pid, throw_id)
    
    return stmt_end + 1, [throw_id]


def parse_method(name, params, body, class_name=""):
    """Парсить метод и построить блок-схему"""
    builder = CSharpFlowchartBuilder()
    
    display_name = f'{class_name}.{name}' if class_name else name
    start_id = builder.add_node('start', f'начало {display_name}()')
    
    prev_ids = [start_id]
    
    if params:
        param_id = builder.add_node('input', f'Параметры: {params}')
        builder.add_edge(start_id, param_id)
        prev_ids = [param_id]
    
    last_ids = parse_method_body(body, builder, prev_ids)
    
    end_id = builder.add_node('end', '')
    for lid in last_ids:
        if lid is None:
            continue
        if isinstance(lid, tuple):
            if lid[0] == 'return':
                builder.add_edge(lid[1], end_id)  # return к end
            else:
                connect_nodes(builder, lid, end_id)
        else:
            builder.add_edge(lid, end_id)
    
    return builder.get_flowchart_data()


def parse_property_accessor(name, accessor_type, body, class_name=""):
    """Парсить get/set аксессор свойства"""
    builder = CSharpFlowchartBuilder()
    
    display_name = f'{class_name}.{name}.{accessor_type}'
    start_id = builder.add_node('start', f'начало {display_name}')
    
    prev_ids = [start_id]
    
    if accessor_type == 'set':
        param_id = builder.add_node('input', 'value')
        builder.add_edge(start_id, param_id)
        prev_ids = [param_id]
    
    last_ids = parse_method_body(body, builder, prev_ids)
    
    end_id = builder.add_node('end', '')
    for lid in last_ids:
        if lid is None:
            continue
        connect_nodes(builder, lid, end_id)
    
    return builder.get_flowchart_data()


def extract_class_members(class_body):
    """Извлечь члены класса"""
    fields = []
    properties = []
    methods = []
    
    body = class_body.strip()
    i = 0
    
    while i < len(body):
        while i < len(body) and body[i] in ' \t\n\r':
            i += 1
        
        if i >= len(body):
            break
        
        # Пропустить атрибуты [...]
        if body[i] == '[':
            depth = 1
            i += 1
            while i < len(body) and depth > 0:
                if body[i] == '[':
                    depth += 1
                elif body[i] == ']':
                    depth -= 1
                i += 1
            continue
        
        # Найти конец объявления
        line_start = i
        
        # Собрать модификаторы и тип
        decl_parts = []
        while i < len(body):
            while i < len(body) and body[i] in ' \t\n\r':
                i += 1
            
            if i >= len(body):
                break
            
            # Читаем слово
            if body[i].isalpha() or body[i] == '_':
                word_start = i
                while i < len(body) and (body[i].isalnum() or body[i] in '_<>[],.'):
                    if body[i] == '<':
                        # Generic
                        depth = 1
                        i += 1
                        while i < len(body) and depth > 0:
                            if body[i] == '<':
                                depth += 1
                            elif body[i] == '>':
                                depth -= 1
                            i += 1
                    else:
                        i += 1
                word = body[word_start:i]
                decl_parts.append(word)
            elif body[i] == '(':
                # Это метод
                paren_end = find_matching_paren(body, i)
                params = body[i + 1:paren_end].strip()
                i = paren_end + 1
                
                while i < len(body) and body[i] in ' \t\n\r':
                    i += 1
                
                if i < len(body) and body[i] == '{':
                    method_body, i = extract_block(body, i)
                    method_name = decl_parts[-1] if decl_parts else "unknown"
                    methods.append({
                        'name': method_name,
                        'params': params,
                        'body': method_body
                    })
                break
            elif body[i] == '{':
                # Это свойство или инициализатор
                prop_body, end_i = extract_block(body, i)
                
                if 'get' in prop_body or 'set' in prop_body:
                    # Свойство
                    prop_name = decl_parts[-1] if decl_parts else "unknown"
                    
                    # Найти get
                    get_match = re.search(r'\bget\s*\{', prop_body)
                    if get_match:
                        get_start = get_match.end() - 1
                        get_body, _ = extract_block(prop_body, get_start)
                        properties.append({
                            'name': prop_name,
                            'accessor': 'get',
                            'body': get_body
                        })
                    
                    # Найти set
                    set_match = re.search(r'\bset\s*\{', prop_body)
                    if set_match:
                        set_start = set_match.end() - 1
                        set_body, _ = extract_block(prop_body, set_start)
                        properties.append({
                            'name': prop_name,
                            'accessor': 'set',
                            'body': set_body
                        })
                
                i = end_i
                break
            elif body[i] == '=' or body[i] == ';':
                # Поле
                if decl_parts:
                    field_name = decl_parts[-1]
                    if field_name not in ['public', 'private', 'protected', 'internal', 
                                          'static', 'readonly', 'const', 'volatile']:
                        fields.append(field_name)
                
                # Пропустить до ;
                while i < len(body) and body[i] != ';':
                    i += 1
                i += 1
                break
            else:
                i += 1
                break
    
    return fields, properties, methods


def parse_class(code, start):
    """Парсить класс"""
    match = re.search(r'class\s+(\w+)', code[start:])
    if not match:
        return start, None, None, []
    
    class_name = match.group(1)
    
    brace_start = code.find('{', start + match.end())
    if brace_start == -1:
        return start, None, None, []
    
    class_body, end_pos = extract_block(code, brace_start)
    
    fields, properties, methods = extract_class_members(class_body)
    
    builder = CSharpFlowchartBuilder()
    class_id = builder.add_node('class_start', class_name)
    
    last_id = class_id
    
    if fields:
        fields_id = builder.add_node('input', f'Поля: {", ".join(fields)}')
        builder.add_edge(last_id, fields_id)
        last_id = fields_id
    
    prop_names = list(set(p['name'] for p in properties))
    if prop_names:
        props_id = builder.add_node('process', f'Свойства: {", ".join(prop_names)}')
        builder.add_edge(last_id, props_id)
        last_id = props_id
    
    # Методы веером от последнего блока
    method_names = [m['name'] for m in methods]
    for i, method_name in enumerate(method_names):
        method_id = builder.add_node('method', method_name + '()')
        builder.add_edge(last_id, method_id, '', f'fan_{i}')
    
    method_flowcharts = []
    
    for method in methods:
        flowchart = parse_method(method['name'], method['params'], method['body'], class_name)
        method_flowcharts.append({
            'name': f'{class_name}.{method["name"]}',
            'type': 'method',
            'flowchart': flowchart
        })
    
    for prop in properties:
        flowchart = parse_property_accessor(prop['name'], prop['accessor'], prop['body'], class_name)
        method_flowcharts.append({
            'name': f'{class_name}.{prop["name"]}.{prop["accessor"]}',
            'type': 'property',
            'flowchart': flowchart
        })
    
    return end_pos, class_name, builder.get_flowchart_data(), method_flowcharts


def parse_csharp(code):
    """Главная функция парсинга C#"""
    code = remove_comments(code)
    
    functions = []
    classes = []
    
    i = 0
    while i < len(code):
        while i < len(code) and code[i] in ' \t\n\r':
            i += 1
        
        if i >= len(code):
            break
        
        if code[i:].startswith('using '):
            semi = code.find(';', i)
            if semi != -1:
                i = semi + 1
            continue
        
        if code[i:].startswith('namespace '):
            brace = code.find('{', i)
            if brace != -1:
                i = brace + 1
            continue
        
        class_match = re.search(r'\bclass\s+\w+', code[i:])
        if class_match:
            class_start = i + class_match.start()
            end_pos, class_name, class_flowchart, method_flowcharts = parse_class(code, class_start)
            
            if class_name:
                classes.append({
                    'name': class_name,
                    'type': 'class',
                    'flowchart': class_flowchart
                })
                functions.extend(method_flowcharts)
            
            i = end_pos
            continue
        
        i += 1
    
    return {
        'success': True,
        'main_flowchart': {'nodes': [], 'edges': []},
        'functions': functions,
        'classes': classes,
        'code': code
    }

"""
Парсер JavaScript для генерации блок-схем
Исправленная версия
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
        # Не добавляем дубликаты
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
    """Удалить комментарии"""
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
    """Найти закрывающую фигурную скобку"""
    depth = 0
    i = start
    in_string = False
    string_char = None
    
    while i < len(code):
        c = code[i]
        
        if not in_string and c in '"\'`':
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
        
        if not in_string and c in '"\'`':
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
    """Извлечь блок в фигурных скобках"""
    brace_start = code.find('{', start)
    if brace_start == -1:
        return "", len(code)
    brace_end = find_matching_brace(code, brace_start)
    return code[brace_start + 1:brace_end], brace_end + 1


def is_keyword(code, pos, keyword):
    """Проверить ключевое слово"""
    if not code[pos:].startswith(keyword):
        return False
    end = pos + len(keyword)
    if end >= len(code):
        return True
    return not code[end].isalnum() and code[end] != '_'


def connect_nodes(builder, from_id, to_id, label='', branch=''):
    """Соединить узлы с учётом маркеров"""
    if from_id is None:
        return
    if isinstance(from_id, tuple):
        marker = from_id[0]
        node_id = from_id[1]
        if marker == 'no_empty':
            builder.add_edge(node_id, to_id, 'нет', 'no')
        elif marker == 'from_no_branch':
            builder.add_edge(node_id, to_id, '', 'from_no')
        elif marker == 'loop_exit':
            builder.add_edge(node_id, to_id, '', 'loop_exit')
        # return маркеры НЕ соединяем с обычными блоками
    else:
        builder.add_edge(from_id, to_id, label, branch)


def filter_returns(prev_ids):
    """Отфильтровать return маркеры"""
    non_returns = []
    returns = []
    for pid in prev_ids:
        if isinstance(pid, tuple) and pid[0] == 'return':
            returns.append(pid)
        else:
            non_returns.append(pid)
    return non_returns, returns


def parse_body(code, builder, prev_ids):
    """Парсить тело блока"""
    code = code.strip()
    if not code:
        return prev_ids
    
    i = 0
    while i < len(code):
        while i < len(code) and code[i] in ' \t\n\r':
            i += 1
        
        if i >= len(code):
            break
        
        # Отфильтровываем return - после return код недостижим
        non_returns, returns = filter_returns(prev_ids)
        if not non_returns and returns:
            # Весь предыдущий код - return, дальше ничего не выполнится
            break
        
        working_prev = non_returns if non_returns else prev_ids
        
        # IF
        if is_keyword(code, i, 'if'):
            i, new_ids = parse_if(code, i, builder, working_prev)
            prev_ids = new_ids + returns
            continue
        
        # FOR
        if is_keyword(code, i, 'for'):
            i, new_ids = parse_for(code, i, builder, working_prev)
            prev_ids = new_ids + returns
            continue
        
        # WHILE
        if is_keyword(code, i, 'while'):
            i, new_ids = parse_while(code, i, builder, working_prev)
            prev_ids = new_ids + returns
            continue
        
        # DO
        if is_keyword(code, i, 'do'):
            i, new_ids = parse_do_while(code, i, builder, working_prev)
            prev_ids = new_ids + returns
            continue
        
        # SWITCH
        if is_keyword(code, i, 'switch'):
            i, new_ids = parse_switch(code, i, builder, working_prev)
            prev_ids = new_ids + returns
            continue
        
        # TRY
        if is_keyword(code, i, 'try'):
            i, new_ids = parse_try(code, i, builder, working_prev)
            prev_ids = new_ids + returns
            continue
        
        # RETURN
        if is_keyword(code, i, 'return'):
            i, new_ids = parse_return(code, i, builder, working_prev)
            prev_ids = new_ids + returns
            continue
        
        # BREAK / CONTINUE
        if is_keyword(code, i, 'break') or is_keyword(code, i, 'continue'):
            end = code.find(';', i)
            if end == -1:
                end = len(code)
            i = end + 1
            continue
        
        # Закрывающая скобка
        if code[i] == '}':
            i += 1
            continue
        
        # Обычный оператор
        stmt_end = code.find(';', i)
        if stmt_end == -1:
            stmt_end = len(code)
        
        stmt = code[i:stmt_end].strip()
        if stmt:
            if 'console.log' in stmt or 'console.error' in stmt:
                node_id = builder.add_node('output', stmt)
            else:
                node_id = builder.add_node('process', stmt)
            
            for pid in working_prev:
                connect_nodes(builder, pid, node_id)
            
            prev_ids = [node_id] + returns
        
        i = stmt_end + 1
    
    return prev_ids


def parse_if(code, start, builder, prev_ids):
    """Парсить if/else if/else"""
    i = start + 2  # пропустить 'if'
    
    while i < len(code) and code[i] in ' \t\n\r':
        i += 1
    
    # Условие
    condition = ""
    if i < len(code) and code[i] == '(':
        paren_end = find_matching_paren(code, i)
        condition = code[i + 1:paren_end].strip()
        i = paren_end + 1
    
    cond_id = builder.add_node('condition', condition + '?')
    
    for pid in prev_ids:
        connect_nodes(builder, pid, cond_id)
    
    while i < len(code) and code[i] in ' \t\n\r':
        i += 1
    
    # Ветка "да"
    edge_idx = len(builder.edges)
    
    if i < len(code) and code[i] == '{':
        body, i = extract_block(code, i)
        yes_ids = parse_body(body, builder, [cond_id])
    else:
        # Однострочный if
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
    
    # Помечаем ребро "да"
    for j in range(edge_idx, len(builder.edges)):
        if builder.edges[j]['from'] == cond_id and not builder.edges[j]['label']:
            builder.edges[j]['label'] = 'да'
            builder.edges[j]['branch'] = 'yes'
            break
    
    exit_ids = []
    
    # Собираем выходы из "да"
    for yid in yes_ids:
        if yid is not None:
            exit_ids.append(yid)
    
    while i < len(code) and code[i] in ' \t\n\r':
        i += 1
    
    # Проверяем else
    if is_keyword(code, i, 'else'):
        i += 4
        while i < len(code) and code[i] in ' \t\n\r':
            i += 1
        
        edge_idx = len(builder.edges)
        
        # else if
        if is_keyword(code, i, 'if'):
            i, no_ids = parse_if(code, i, builder, [cond_id])
        elif code[i] == '{':
            body, i = extract_block(code, i)
            no_ids = parse_body(body, builder, [cond_id])
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
        
        # Помечаем ребро "нет"
        for j in range(edge_idx, len(builder.edges)):
            if builder.edges[j]['from'] == cond_id and not builder.edges[j]['label']:
                builder.edges[j]['label'] = 'нет'
                builder.edges[j]['branch'] = 'no'
                break
        
        # Когда есть else, выходы из ветки "нет" - обычные (без маркеров)
        for nid in no_ids:
            if nid is not None:
                if isinstance(nid, tuple):
                    # Сохраняем маркеры return и другие
                    exit_ids.append(nid)
                else:
                    # Обычный выход - без маркера
                    exit_ids.append(nid)
    else:
        # Нет else - добавляем маркер
        exit_ids.append(('no_empty', cond_id))
    
    return i, exit_ids if exit_ids else [None]


def parse_for(code, start, builder, prev_ids):
    """Парсить for"""
    i = start + 3
    
    while i < len(code) and code[i] in ' \t\n\r':
        i += 1
    
    header = ""
    if i < len(code) and code[i] == '(':
        paren_end = find_matching_paren(code, i)
        header = code[i + 1:paren_end].strip()
        i = paren_end + 1
    
    loop_id = builder.add_node('loop', f'for ({header})')
    
    for pid in prev_ids:
        connect_nodes(builder, pid, loop_id)
    
    while i < len(code) and code[i] in ' \t\n\r':
        i += 1
    
    # Запоминаем индекс рёбер чтобы пометить связь к телу
    edge_idx = len(builder.edges)
    
    if i < len(code) and code[i] == '{':
        body, i = extract_block(code, i)
        body_ids = parse_body(body, builder, [loop_id])
    else:
        stmt_end = code.find(';', i)
        if stmt_end == -1:
            stmt_end = len(code)
        i = stmt_end + 1
        body_ids = [loop_id]
    
    # Помечаем первое ребро от цикла как loop_body
    for j in range(edge_idx, len(builder.edges)):
        if builder.edges[j]['from'] == loop_id and not builder.edges[j]['branch']:
            builder.edges[j]['branch'] = 'loop_body'
            break
    
    # Обратная связь цикла (кроме return)
    for bid in body_ids:
        if bid is not None and not isinstance(bid, tuple):
            builder.add_edge(bid, loop_id, '', 'loop_back')
        elif isinstance(bid, tuple) and bid[0] not in ['return']:
            builder.add_edge(bid[1], loop_id, '', 'loop_back')
    
    # Возвращаем выход из цикла + return маркеры
    exits = [('loop_exit', loop_id)]
    for bid in body_ids:
        if isinstance(bid, tuple) and bid[0] == 'return':
            exits.append(bid)
    
    return i, exits


def parse_while(code, start, builder, prev_ids):
    """Парсить while"""
    i = start + 5
    
    while i < len(code) and code[i] in ' \t\n\r':
        i += 1
    
    condition = ""
    if i < len(code) and code[i] == '(':
        paren_end = find_matching_paren(code, i)
        condition = code[i + 1:paren_end].strip()
        i = paren_end + 1
    
    loop_id = builder.add_node('loop', f'while ({condition})')
    
    for pid in prev_ids:
        connect_nodes(builder, pid, loop_id)
    
    while i < len(code) and code[i] in ' \t\n\r':
        i += 1
    
    # Запоминаем индекс рёбер
    edge_idx = len(builder.edges)
    
    if i < len(code) and code[i] == '{':
        body, i = extract_block(code, i)
        body_ids = parse_body(body, builder, [loop_id])
    else:
        stmt_end = code.find(';', i)
        if stmt_end == -1:
            stmt_end = len(code)
        i = stmt_end + 1
        body_ids = [loop_id]
    
    # Помечаем первое ребро от цикла как loop_body
    for j in range(edge_idx, len(builder.edges)):
        if builder.edges[j]['from'] == loop_id and not builder.edges[j]['branch']:
            builder.edges[j]['branch'] = 'loop_body'
            break
    
    for bid in body_ids:
        if bid is not None and not isinstance(bid, tuple):
            builder.add_edge(bid, loop_id, '', 'loop_back')
        elif isinstance(bid, tuple) and bid[0] not in ['return']:
            builder.add_edge(bid[1], loop_id, '', 'loop_back')
    
    exits = [('loop_exit', loop_id)]
    for bid in body_ids:
        if isinstance(bid, tuple) and bid[0] == 'return':
            exits.append(bid)
    
    return i, exits


def parse_do_while(code, start, builder, prev_ids):
    """Парсить do-while: тело → условие (ромб) → да к началу тела, нет дальше"""
    i = start + 2
    
    while i < len(code) and code[i] in ' \t\n\r':
        i += 1
    
    # Запоминаем количество узлов до парсинга тела
    nodes_before = len(builder.nodes)
    
    # Парсим тело цикла напрямую от prev_ids
    if i < len(code) and code[i] == '{':
        body, i = extract_block(code, i)
        body_ids = parse_body(body, builder, prev_ids)
    else:
        body_ids = prev_ids
    
    while i < len(code) and code[i] in ' \t\n\r':
        i += 1
    
    if is_keyword(code, i, 'while'):
        i += 5
        while i < len(code) and code[i] in ' \t\n\r':
            i += 1
        
        condition = ""
        if i < len(code) and code[i] == '(':
            paren_end = find_matching_paren(code, i)
            condition = code[i + 1:paren_end].strip()
            i = paren_end + 1
        
        # Создаём условие (ромб)
        cond_id = builder.add_node('condition', condition + '?')
        
        # Связываем конец тела с условием
        for bid in body_ids:
            if bid is not None and not isinstance(bid, tuple):
                builder.add_edge(bid, cond_id)
            elif isinstance(bid, tuple) and bid[0] != 'return':
                builder.add_edge(bid[1], cond_id)
        
        # Первый блок тела - это первый узел добавленный после nodes_before
        if nodes_before < len(builder.nodes) - 1:  # -1 для cond_id
            first_body_node = builder.nodes[nodes_before]['id']
            builder.add_edge(cond_id, first_body_node, 'да', 'yes')
        
        while i < len(code) and code[i] in ' \t\n\r;':
            i += 1
        
        exits = [('no_empty', cond_id)]
        for bid in body_ids:
            if isinstance(bid, tuple) and bid[0] == 'return':
                exits.append(bid)
        
        return i, exits
    
    return i, body_ids


def find_colon_outside_strings(text, start=0):
    """Найти : вне строк"""
    i = start
    while i < len(text):
        c = text[i]
        if c in '"\'`':
            quote = c
            i += 1
            while i < len(text):
                if text[i] == '\\' and i + 1 < len(text):
                    i += 2
                elif text[i] == quote:
                    i += 1
                    break
                else:
                    i += 1
        elif c == ':':
            return i
        else:
            i += 1
    return -1


def parse_switch(code, start, builder, prev_ids):
    """Парсить switch как цепочку if-else"""
    i = start + 6
    
    while i < len(code) and code[i] in ' \t\n\r':
        i += 1
    
    # Получаем выражение switch
    expr = ""
    if i < len(code) and code[i] == '(':
        paren_end = find_matching_paren(code, i)
        expr = code[i + 1:paren_end].strip()
        i = paren_end + 1
    
    while i < len(code) and code[i] in ' \t\n\r':
        i += 1
    
    exit_ids = []
    
    if i < len(code) and code[i] == '{':
        body, i = extract_block(code, i)
        
        # Парсим case блоки
        j = 0
        cases = []
        
        while j < len(body):
            while j < len(body) and body[j] in ' \t\n\r':
                j += 1
            
            if j >= len(body):
                break
            
            # case
            if is_keyword(body, j, 'case'):
                j += 4
                while j < len(body) and body[j] in ' \t\n\r':
                    j += 1
                
                val_start = j
                colon_pos = find_colon_outside_strings(body, j)
                if colon_pos == -1:
                    break
                
                case_val = body[val_start:colon_pos].strip()
                j = colon_pos + 1
                
                body_start = j
                depth = 0
                while j < len(body):
                    c = body[j]
                    if c in '"\'`':
                        quote = c
                        j += 1
                        while j < len(body):
                            if body[j] == '\\' and j + 1 < len(body):
                                j += 2
                            elif body[j] == quote:
                                j += 1
                                break
                            else:
                                j += 1
                        continue
                    
                    if c == '{':
                        depth += 1
                        j += 1
                    elif c == '}':
                        if depth == 0:
                            break
                        depth -= 1
                        j += 1
                    elif depth == 0 and (is_keyword(body, j, 'case') or is_keyword(body, j, 'default')):
                        break
                    else:
                        j += 1
                
                case_body = body[body_start:j].strip()
                case_body = re.sub(r'\bbreak\s*;', '', case_body).strip()
                cases.append(('case', case_val, case_body))
                
            # default
            elif is_keyword(body, j, 'default'):
                j += 7
                colon_pos = find_colon_outside_strings(body, j)
                if colon_pos == -1:
                    break
                j = colon_pos + 1
                
                default_body = body[j:].strip()
                default_body = re.sub(r'\bbreak\s*;', '', default_body).strip()
                cases.append(('default', None, default_body))
                break
            else:
                j += 1
        
        # Строим цепочку if-else if-else
        current_prev = prev_ids
        
        for idx, (part_type, case_val, case_body) in enumerate(cases):
            if part_type == 'case':
                # Создаём условие: expr == case_val
                cond_id = builder.add_node('condition', f'{expr} == {case_val}?')
                
                for pid in current_prev:
                    connect_nodes(builder, pid, cond_id)
                
                # Ветка "да" - тело case
                if case_body:
                    edge_idx = len(builder.edges)
                    case_exits = parse_body(case_body, builder, [cond_id])
                    
                    # Помечаем ребро "да"
                    for k in range(edge_idx, len(builder.edges)):
                        if builder.edges[k]['from'] == cond_id and not builder.edges[k]['label']:
                            builder.edges[k]['label'] = 'да'
                            builder.edges[k]['branch'] = 'yes'
                            break
                    
                    exit_ids.extend(case_exits)
                else:
                    exit_ids.append(cond_id)
                
                # Следующий case будет в ветке "нет"
                current_prev = [('no_empty', cond_id)]
                
            else:  # default - это else
                if case_body:
                    # Если есть предыдущее условие - это его ветка "нет"
                    edge_idx = len(builder.edges)
                    default_exits = parse_body(case_body, builder, current_prev)
                    
                    # Помечаем ребро "нет"
                    for k in range(edge_idx, len(builder.edges)):
                        if builder.edges[k]['branch'] == '' and builder.edges[k]['label'] == '':
                            # Это первое ребро от последнего условия
                            pass
                    
                    exit_ids.extend(default_exits)
                else:
                    exit_ids.extend(current_prev)
                
                current_prev = []
        
        # Если не было default, добавляем пустой выход из последнего условия
        if current_prev:
            exit_ids.extend(current_prev)
    
    return i, exit_ids if exit_ids else prev_ids


def parse_try(code, start, builder, prev_ids):
    """Парсить try-catch-finally"""
    i = start + 3
    
    while i < len(code) and code[i] in ' \t\n\r':
        i += 1
    
    try_id = builder.add_node('process', 'try')
    
    for pid in prev_ids:
        connect_nodes(builder, pid, try_id)
    
    if i < len(code) and code[i] == '{':
        body, i = extract_block(code, i)
        try_ids = parse_body(body, builder, [try_id])
    else:
        try_ids = [try_id]
    
    exit_ids = list(try_ids)
    
    # catch
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
            catch_ids = parse_body(body, builder, [catch_id])
            exit_ids.extend(catch_ids)
        else:
            exit_ids.append(catch_id)
    
    # finally
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
            finally_ids = parse_body(body, builder, [finally_id])
            exit_ids = finally_ids
        else:
            exit_ids = [finally_id]
    
    return i, exit_ids


def parse_return(code, start, builder, prev_ids):
    """Парсить return"""
    i = start + 6
    
    stmt_end = code.find(';', i)
    if stmt_end == -1:
        stmt_end = len(code)
    
    value = code[i:stmt_end].strip()
    text = f'return {value}' if value else 'return'
    
    ret_id = builder.add_node('output', text)
    
    for pid in prev_ids:
        connect_nodes(builder, pid, ret_id)
    
    # Возвращаем маркер return - этот блок ведёт к end
    return stmt_end + 1, [('return', ret_id)]


def parse_function(code, start):
    """Парсить функцию"""
    i = start
    
    # Пропустить async
    is_async = False
    if is_keyword(code, i, 'async'):
        is_async = True
        i += 5
        while i < len(code) and code[i] in ' \t\n\r':
            i += 1
    
    # function
    if is_keyword(code, i, 'function'):
        i += 8
    
    while i < len(code) and code[i] in ' \t\n\r':
        i += 1
    
    # Имя
    name = ""
    while i < len(code) and (code[i].isalnum() or code[i] == '_'):
        name += code[i]
        i += 1
    
    while i < len(code) and code[i] in ' \t\n\r':
        i += 1
    
    # Параметры
    params = []
    if i < len(code) and code[i] == '(':
        paren_end = find_matching_paren(code, i)
        params_str = code[i + 1:paren_end].strip()
        if params_str:
            params = [p.strip() for p in params_str.split(',')]
        i = paren_end + 1
    
    while i < len(code) and code[i] in ' \t\n\r':
        i += 1
    
    # Тело
    if i < len(code) and code[i] == '{':
        body, end_i = extract_block(code, i)
    else:
        return i, None, None
    
    builder = JSFlowchartBuilder()
    prefix = 'async ' if is_async else ''
    start_id = builder.add_node('start', f'начало {prefix}{name}()')
    
    prev_ids = [start_id]
    
    if params:
        param_id = builder.add_node('input', f'Параметры: {", ".join(params)}')
        builder.add_edge(start_id, param_id)
        prev_ids = [param_id]
    
    last_ids = parse_body(body, builder, prev_ids)
    
    end_id = builder.add_node('end', '')
    
    for lid in last_ids:
        if lid is None:
            continue
        if isinstance(lid, tuple):
            marker = lid[0]
            node_id = lid[1]
            if marker == 'return':
                builder.add_edge(node_id, end_id)
            elif marker == 'no_empty':
                builder.add_edge(node_id, end_id, 'нет', 'no')
            elif marker == 'from_no_branch':
                builder.add_edge(node_id, end_id, '', 'from_no')
            elif marker == 'loop_exit':
                builder.add_edge(node_id, end_id, '', 'loop_exit')
        else:
            builder.add_edge(lid, end_id)
    
    return end_i, name, builder.get_flowchart_data()


def parse_class(code, start):
    """Парсить класс"""
    i = start
    
    if is_keyword(code, i, 'class'):
        i += 5
    
    while i < len(code) and code[i] in ' \t\n\r':
        i += 1
    
    # Имя
    name = ""
    while i < len(code) and (code[i].isalnum() or code[i] == '_'):
        name += code[i]
        i += 1
    
    # extends
    while i < len(code) and code[i] in ' \t\n\r':
        i += 1
    if is_keyword(code, i, 'extends'):
        i += 7
        while i < len(code) and code[i] not in '{':
            i += 1
    
    while i < len(code) and code[i] in ' \t\n\r':
        i += 1
    
    if i >= len(code) or code[i] != '{':
        return i, None, None, []
    
    body, end_i = extract_block(code, i)
    
    builder = JSFlowchartBuilder()
    class_id = builder.add_node('class_start', name)
    
    # Найти методы
    methods = []
    method_pattern = r'(?:async\s+)?(\w+)\s*\([^)]*\)\s*\{'
    
    for match in re.finditer(method_pattern, body):
        method_name = match.group(1)
        if method_name not in ['if', 'for', 'while', 'switch']:
            methods.append(method_name)
    
    # Методы веером
    for idx, method_name in enumerate(methods):
        method_id = builder.add_node('method', method_name + '()')
        builder.add_edge(class_id, method_id, '', f'fan_{idx}')
    
    return end_i, name, builder.get_flowchart_data(), methods


def parse_javascript(code):
    """Главная функция парсинга JavaScript"""
    code = remove_comments(code)
    
    functions = []
    classes = []
    
    i = 0
    while i < len(code):
        while i < len(code) and code[i] in ' \t\n\r':
            i += 1
        
        if i >= len(code):
            break
        
        # async function
        if is_keyword(code, i, 'async'):
            j = i + 5
            while j < len(code) and code[j] in ' \t\n\r':
                j += 1
            if is_keyword(code, j, 'function'):
                end_i, name, flowchart = parse_function(code, i)
                if name and flowchart:
                    functions.append({
                        'name': f'async {name}',
                        'type': 'function',
                        'flowchart': flowchart
                    })
                i = end_i
                continue
        
        # function
        if is_keyword(code, i, 'function'):
            end_i, name, flowchart = parse_function(code, i)
            if name and flowchart:
                functions.append({
                    'name': name,
                    'type': 'function',
                    'flowchart': flowchart
                })
            i = end_i
            continue
        
        # class
        if is_keyword(code, i, 'class'):
            end_i, name, flowchart, methods = parse_class(code, i)
            if name and flowchart:
                classes.append({
                    'name': name,
                    'type': 'class',
                    'flowchart': flowchart
                })
            i = end_i
            continue
        
        i += 1
    
    # Main код
    main_flowchart = {'nodes': [], 'edges': []}
    
    return {
        'success': True,
        'main_flowchart': main_flowchart,
        'functions': functions,
        'classes': classes,
        'code': code
    }

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


def tokenize_csharp(code):
    """Разбить C# код на токены"""
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
        if code[i] == '"':
            # Verbatim string
            if i > 0 and code[i-1] == '@':
                j = i + 1
                while j < len(code):
                    if code[j] == '"':
                        if j + 1 < len(code) and code[j+1] == '"':
                            j += 2
                        else:
                            j += 1
                            break
                    else:
                        j += 1
                tokens.append(('STRING', code[i:j]))
                i = j
                continue
            else:
                j = i + 1
                while j < len(code):
                    if code[j] == '\\':
                        j += 2
                    elif code[j] == '"':
                        j += 1
                        break
                    else:
                        j += 1
                tokens.append(('STRING', code[i:j]))
                i = j
                continue
        
        if code[i] == '\'':
            j = i + 1
            while j < len(code):
                if code[j] == '\\':
                    j += 2
                elif code[j] == '\'':
                    j += 1
                    break
                else:
                    j += 1
            tokens.append(('CHAR', code[i:j]))
            i = j
            continue
        
        # Ключевые слова и идентификаторы
        if code[i].isalpha() or code[i] == '_' or code[i] == '@':
            j = i
            if code[i] == '@':
                j += 1
            while j < len(code) and (code[j].isalnum() or code[j] == '_'):
                j += 1
            word = code[i:j]
            if word.startswith('@'):
                word = word[1:]
            
            keywords = ['if', 'else', 'for', 'foreach', 'while', 'do', 'switch',
                       'case', 'default', 'break', 'continue', 'return', 'var',
                       'class', 'struct', 'interface', 'enum', 'namespace',
                       'public', 'private', 'protected', 'internal', 'static',
                       'void', 'int', 'string', 'bool', 'float', 'double',
                       'try', 'catch', 'finally', 'throw', 'new', 'this',
                       'async', 'await', 'using', 'in', 'out', 'ref',
                       'Console', 'get', 'set', 'virtual', 'override', 'abstract']
            
            if word in keywords:
                tokens.append((word.upper(), word))
            else:
                tokens.append(('IDENT', word))
            i = j
            continue
        
        # Числа
        if code[i].isdigit():
            j = i
            while j < len(code) and (code[j].isdigit() or code[j] in '.fFdDmMlL'):
                j += 1
            tokens.append(('NUMBER', code[i:j]))
            i = j
            continue
        
        # Операторы
        three_char = code[i:i+3]
        if three_char in ['<<=', '>>=']:
            tokens.append(('OP', three_char))
            i += 3
            continue
        
        two_char = code[i:i+2]
        if two_char in ['==', '!=', '<=', '>=', '&&', '||', '++', '--', '+=', '-=', 
                        '*=', '/=', '%=', '=>', '??', '?.', '<<', '>>', '::']:
            tokens.append(('OP', two_char))
            i += 2
            continue
        
        tokens.append((code[i], code[i]))
        i += 1
    
    return tokens


def parse_cs_block(tokens, start, builder, prev_ids):
    """Парсить блок кода в фигурных скобках"""
    i = start
    
    # Найти {
    while i < len(tokens) and tokens[i][0] != '{':
        i += 1
    
    if i >= len(tokens):
        return start, prev_ids
    
    i += 1
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
            i, prev_ids = parse_cs_if(tokens, i, builder, prev_ids)
        elif token[0] == 'FOR':
            i, prev_ids = parse_cs_for(tokens, i, builder, prev_ids)
        elif token[0] == 'FOREACH':
            i, prev_ids = parse_cs_foreach(tokens, i, builder, prev_ids)
        elif token[0] == 'WHILE':
            i, prev_ids = parse_cs_while(tokens, i, builder, prev_ids)
        elif token[0] == 'DO':
            i, prev_ids = parse_cs_do_while(tokens, i, builder, prev_ids)
        elif token[0] == 'SWITCH':
            i, prev_ids = parse_cs_switch(tokens, i, builder, prev_ids)
        elif token[0] == 'TRY':
            i, prev_ids = parse_cs_try(tokens, i, builder, prev_ids)
        elif token[0] == 'RETURN':
            i, prev_ids = parse_cs_return(tokens, i, builder, prev_ids)
        elif token[0] == 'CONSOLE':
            i, prev_ids = parse_cs_console(tokens, i, builder, prev_ids)
        elif token[0] == 'VAR' or token[0] in ['INT', 'STRING', 'BOOL', 'FLOAT', 'DOUBLE']:
            i, prev_ids = parse_cs_var(tokens, i, builder, prev_ids)
        elif token[0] == 'IDENT':
            i, prev_ids = parse_cs_statement(tokens, i, builder, prev_ids)
        else:
            i += 1
    
    return i, prev_ids


def parse_cs_if(tokens, start, builder, prev_ids):
    """Парсить if/else"""
    i = start + 1
    
    # Условие
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
            if isinstance(pid, tuple):
                if pid[0] == 'no_empty':
                    builder.add_edge(pid[1], cond_id, 'нет', 'no')
                elif pid[0] == 'from_no_branch':
                    builder.add_edge(pid[1], cond_id, '', 'from_no')
            else:
                builder.add_edge(pid, cond_id)
    
    # Ветка "да"
    edge_idx = len(builder.edges)
    i, yes_ids = parse_cs_block(tokens, i, builder, [cond_id])
    
    for j in range(edge_idx, len(builder.edges)):
        if builder.edges[j]['from'] == cond_id and not builder.edges[j]['label']:
            builder.edges[j]['label'] = 'да'
            builder.edges[j]['branch'] = 'yes'
            break
    
    exit_ids = list(yes_ids) if yes_ids else []
    
    # else
    if i < len(tokens) and tokens[i][0] == 'ELSE':
        i += 1
        edge_idx = len(builder.edges)
        
        if i < len(tokens) and tokens[i][0] == 'IF':
            i, no_ids = parse_cs_if(tokens, i, builder, [cond_id])
        else:
            i, no_ids = parse_cs_block(tokens, i, builder, [cond_id])
        
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


def parse_cs_for(tokens, start, builder, prev_ids):
    """Парсить for"""
    i = start + 1
    
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
    
    loop_id = builder.add_node('loop', f'for ({header.strip()})')
    
    for pid in prev_ids:
        if pid is not None:
            if isinstance(pid, tuple):
                if pid[0] == 'no_empty':
                    builder.add_edge(pid[1], loop_id, 'нет', 'no')
                elif pid[0] == 'from_no_branch':
                    builder.add_edge(pid[1], loop_id, '', 'from_no')
            else:
                builder.add_edge(pid, loop_id)
    
    i, body_ids = parse_cs_block(tokens, i, builder, [loop_id])
    
    for bid in body_ids:
        if bid is not None and not isinstance(bid, tuple):
            builder.add_edge(bid, loop_id, '', 'loop_back')
    
    return i, [('loop_exit', loop_id)]


def parse_cs_foreach(tokens, start, builder, prev_ids):
    """Парсить foreach"""
    i = start + 1
    
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
    
    loop_id = builder.add_node('loop', f'foreach ({header.strip()})')
    
    for pid in prev_ids:
        if pid is not None:
            if isinstance(pid, tuple):
                if pid[0] == 'no_empty':
                    builder.add_edge(pid[1], loop_id, 'нет', 'no')
                elif pid[0] == 'from_no_branch':
                    builder.add_edge(pid[1], loop_id, '', 'from_no')
            else:
                builder.add_edge(pid, loop_id)
    
    i, body_ids = parse_cs_block(tokens, i, builder, [loop_id])
    
    for bid in body_ids:
        if bid is not None and not isinstance(bid, tuple):
            builder.add_edge(bid, loop_id, '', 'loop_back')
    
    return i, [('loop_exit', loop_id)]


def parse_cs_while(tokens, start, builder, prev_ids):
    """Парсить while"""
    i = start + 1
    
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
    
    loop_id = builder.add_node('loop', f'while ({condition.strip()})')
    
    for pid in prev_ids:
        if pid is not None:
            if isinstance(pid, tuple):
                if pid[0] == 'no_empty':
                    builder.add_edge(pid[1], loop_id, 'нет', 'no')
                elif pid[0] == 'from_no_branch':
                    builder.add_edge(pid[1], loop_id, '', 'from_no')
            else:
                builder.add_edge(pid, loop_id)
    
    i, body_ids = parse_cs_block(tokens, i, builder, [loop_id])
    
    for bid in body_ids:
        if bid is not None and not isinstance(bid, tuple):
            builder.add_edge(bid, loop_id, '', 'loop_back')
    
    return i, [('loop_exit', loop_id)]


def parse_cs_do_while(tokens, start, builder, prev_ids):
    """Парсить do-while"""
    i = start + 1
    
    do_id = builder.add_node('process', 'do')
    
    for pid in prev_ids:
        if pid is not None:
            builder.add_edge(pid, do_id)
    
    i, body_ids = parse_cs_block(tokens, i, builder, [do_id])
    
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
        
        if i < len(tokens) and tokens[i][0] == ';':
            i += 1
        
        return i, [('no_empty', loop_id)]
    
    return i, body_ids


def parse_cs_switch(tokens, start, builder, prev_ids):
    """Парсить switch"""
    i = start + 1
    
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
                i += 1
                
                case_id = builder.add_node('process', f'case {case_val.strip()}')
                builder.add_edge(switch_id, case_id, case_val.strip(), 'yes')
                exit_ids.append(case_id)
            elif tokens[i][0] == 'DEFAULT':
                i += 1
                if i < len(tokens) and tokens[i][0] == ':':
                    i += 1
                default_id = builder.add_node('process', 'default')
                builder.add_edge(switch_id, default_id, 'default', 'no')
                exit_ids.append(default_id)
            elif tokens[i][0] == 'BREAK':
                i += 1
                if i < len(tokens) and tokens[i][0] == ';':
                    i += 1
            else:
                i += 1
    
    return i, exit_ids if exit_ids else [switch_id]


def parse_cs_try(tokens, start, builder, prev_ids):
    """Парсить try-catch-finally"""
    i = start + 1
    
    try_id = builder.add_node('process', 'try')
    
    for pid in prev_ids:
        if pid is not None:
            builder.add_edge(pid, try_id)
    
    i, try_ids = parse_cs_block(tokens, i, builder, [try_id])
    exit_ids = list(try_ids)
    
    while i < len(tokens) and tokens[i][0] == 'CATCH':
        i += 1
        
        exception = ""
        if i < len(tokens) and tokens[i][0] == '(':
            depth = 1
            i += 1
            while i < len(tokens) and depth > 0:
                if tokens[i][0] == '(':
                    depth += 1
                elif tokens[i][0] == ')':
                    depth -= 1
                if depth > 0:
                    exception += tokens[i][1] + " "
                i += 1
        
        catch_text = f'catch ({exception.strip()})' if exception.strip() else 'catch'
        catch_id = builder.add_node('process', catch_text)
        builder.add_edge(try_id, catch_id, 'ошибка', 'no')
        
        i, catch_ids = parse_cs_block(tokens, i, builder, [catch_id])
        exit_ids.extend(catch_ids)
    
    if i < len(tokens) and tokens[i][0] == 'FINALLY':
        i += 1
        finally_id = builder.add_node('process', 'finally')
        
        for eid in exit_ids:
            if eid is not None and not isinstance(eid, tuple):
                builder.add_edge(eid, finally_id)
        
        i, finally_ids = parse_cs_block(tokens, i, builder, [finally_id])
        exit_ids = finally_ids
    
    return i, exit_ids


def parse_cs_return(tokens, start, builder, prev_ids):
    """Парсить return"""
    i = start + 1
    
    value = ""
    while i < len(tokens) and tokens[i][0] != ';':
        value += tokens[i][1] + " "
        i += 1
    
    if i < len(tokens) and tokens[i][0] == ';':
        i += 1
    
    text = f'return {value.strip()}' if value.strip() else 'return'
    ret_id = builder.add_node('process', text)
    
    for pid in prev_ids:
        if pid is not None:
            if isinstance(pid, tuple):
                if pid[0] == 'no_empty':
                    builder.add_edge(pid[1], ret_id, 'нет', 'no')
                elif pid[0] == 'from_no_branch':
                    builder.add_edge(pid[1], ret_id, '', 'from_no')
            else:
                builder.add_edge(pid, ret_id)
    
    return i, [ret_id]


def parse_cs_console(tokens, start, builder, prev_ids):
    """Парсить Console.WriteLine"""
    i = start + 1
    
    # .WriteLine или .Write
    if i < len(tokens) and tokens[i][0] == '.':
        i += 1
    method = ""
    if i < len(tokens) and tokens[i][0] == 'IDENT':
        method = tokens[i][1]
        i += 1
    
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
    
    out_id = builder.add_node('output', f'Console.{method}({args.strip()})')
    
    for pid in prev_ids:
        if pid is not None:
            if isinstance(pid, tuple):
                if pid[0] == 'no_empty':
                    builder.add_edge(pid[1], out_id, 'нет', 'no')
                elif pid[0] == 'from_no_branch':
                    builder.add_edge(pid[1], out_id, '', 'from_no')
            else:
                builder.add_edge(pid, out_id)
    
    return i, [out_id]


def parse_cs_var(tokens, start, builder, prev_ids):
    """Парсить объявление переменной"""
    i = start
    
    statement = ""
    while i < len(tokens) and tokens[i][0] != ';':
        statement += tokens[i][1] + " "
        i += 1
    
    if i < len(tokens) and tokens[i][0] == ';':
        i += 1
    
    proc_id = builder.add_node('process', statement.strip())
    
    for pid in prev_ids:
        if pid is not None:
            if isinstance(pid, tuple):
                if pid[0] == 'no_empty':
                    builder.add_edge(pid[1], proc_id, 'нет', 'no')
                elif pid[0] == 'from_no_branch':
                    builder.add_edge(pid[1], proc_id, '', 'from_no')
            else:
                builder.add_edge(pid, proc_id)
    
    return i, [proc_id]


def parse_cs_statement(tokens, start, builder, prev_ids):
    """Парсить обычный оператор"""
    i = start
    
    statement = ""
    while i < len(tokens) and tokens[i][0] != ';' and tokens[i][0] != '{':
        statement += tokens[i][1] + " "
        i += 1
    
    if i < len(tokens) and tokens[i][0] == ';':
        i += 1
    
    if statement.strip():
        proc_id = builder.add_node('process', statement.strip())
        
        for pid in prev_ids:
            if pid is not None:
                if isinstance(pid, tuple):
                    if pid[0] == 'no_empty':
                        builder.add_edge(pid[1], proc_id, 'нет', 'no')
                    elif pid[0] == 'from_no_branch':
                        builder.add_edge(pid[1], proc_id, '', 'from_no')
                else:
                    builder.add_edge(pid, proc_id)
        
        return i, [proc_id]
    
    return i, prev_ids


def parse_cs_method(tokens, start, class_name=""):
    """Парсить метод"""
    i = start
    
    # Модификаторы
    modifiers = []
    while i < len(tokens) and tokens[i][0] in ['PUBLIC', 'PRIVATE', 'PROTECTED', 
                                                 'INTERNAL', 'STATIC', 'ASYNC',
                                                 'VIRTUAL', 'OVERRIDE', 'ABSTRACT']:
        modifiers.append(tokens[i][1])
        i += 1
    
    # Тип возврата
    return_type = ""
    if i < len(tokens) and tokens[i][0] in ['VOID', 'INT', 'STRING', 'BOOL', 
                                             'FLOAT', 'DOUBLE', 'IDENT']:
        return_type = tokens[i][1]
        i += 1
        # Generic types
        if i < len(tokens) and tokens[i][0] == '<':
            return_type += '<'
            i += 1
            while i < len(tokens) and tokens[i][0] != '>':
                return_type += tokens[i][1]
                i += 1
            if i < len(tokens):
                return_type += '>'
                i += 1
    
    # Имя метода
    name = ""
    if i < len(tokens) and tokens[i][0] == 'IDENT':
        name = tokens[i][1]
        i += 1
    
    # Параметры
    params = []
    if i < len(tokens) and tokens[i][0] == '(':
        i += 1
        while i < len(tokens) and tokens[i][0] != ')':
            if tokens[i][0] in ['INT', 'STRING', 'BOOL', 'FLOAT', 'DOUBLE', 'IDENT', 'VAR']:
                param_type = tokens[i][1]
                i += 1
                if i < len(tokens) and tokens[i][0] == 'IDENT':
                    param_name = tokens[i][1]
                    params.append(f'{param_type} {param_name}')
                    i += 1
            elif tokens[i][0] == ',':
                i += 1
            else:
                i += 1
        i += 1  # )
    
    builder = CSharpFlowchartBuilder()
    display_name = f'{class_name}.{name}' if class_name else name
    start_id = builder.add_node('start', f'начало {display_name}()')
    
    prev_ids = [start_id]
    
    if params:
        param_id = builder.add_node('input', f'Параметры: {", ".join(params)}')
        builder.add_edge(start_id, param_id)
        prev_ids = [param_id]
    
    # Тело метода
    i, last_ids = parse_cs_block(tokens, i, builder, prev_ids)
    
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


def parse_cs_class(tokens, start):
    """Парсить класс"""
    i = start
    
    # Модификаторы
    while i < len(tokens) and tokens[i][0] in ['PUBLIC', 'PRIVATE', 'PROTECTED', 
                                                 'INTERNAL', 'STATIC', 'ABSTRACT']:
        i += 1
    
    if i < len(tokens) and tokens[i][0] == 'CLASS':
        i += 1
    
    # Имя класса
    name = ""
    if i < len(tokens) and tokens[i][0] == 'IDENT':
        name = tokens[i][1]
        i += 1
    
    # Наследование
    if i < len(tokens) and tokens[i][0] == ':':
        i += 1
        while i < len(tokens) and tokens[i][0] not in ['{']:
            i += 1
    
    builder = CSharpFlowchartBuilder()
    class_id = builder.add_node('class_start', name)
    
    fields = []
    methods = []
    method_flowcharts = []
    
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
            elif tokens[i][0] in ['PUBLIC', 'PRIVATE', 'PROTECTED', 'INTERNAL', 
                                   'STATIC', 'ASYNC', 'VIRTUAL', 'OVERRIDE']:
                # Проверить - это метод или поле?
                j = i
                while j < len(tokens) and tokens[j][0] in ['PUBLIC', 'PRIVATE', 
                      'PROTECTED', 'INTERNAL', 'STATIC', 'ASYNC', 'VIRTUAL', 'OVERRIDE']:
                    j += 1
                
                # Тип
                if j < len(tokens) and tokens[j][0] in ['VOID', 'INT', 'STRING', 
                                                         'BOOL', 'FLOAT', 'DOUBLE', 'IDENT']:
                    j += 1
                    # Generic
                    if j < len(tokens) and tokens[j][0] == '<':
                        while j < len(tokens) and tokens[j][0] != '>':
                            j += 1
                        j += 1
                    
                    # Имя
                    if j < len(tokens) and tokens[j][0] == 'IDENT':
                        member_name = tokens[j][1]
                        j += 1
                        
                        if j < len(tokens) and tokens[j][0] == '(':
                            # Это метод
                            end_i, m_name, flowchart = parse_cs_method(tokens, i, name)
                            methods.append(m_name)
                            method_flowcharts.append({
                                'name': f'{name}.{m_name}',
                                'type': 'method',
                                'flowchart': flowchart
                            })
                            i = end_i
                        else:
                            # Это поле
                            fields.append(member_name)
                            while i < len(tokens) and tokens[i][0] != ';':
                                i += 1
                            i += 1
                    else:
                        i += 1
                else:
                    i += 1
            else:
                i += 1
    
    # Добавить поля
    if fields:
        fields_id = builder.add_node('input', f'Поля: {", ".join(fields)}')
        builder.add_edge(class_id, fields_id)
        source_id = fields_id
    else:
        source_id = class_id
    
    # Добавить методы
    if methods:
        methods_id = builder.add_node('process', f'Методы: {", ".join(methods)}')
        builder.add_edge(source_id, methods_id)
    
    return i, name, builder.get_flowchart_data(), method_flowcharts


def parse_csharp(code):
    """Главная функция парсинга C#"""
    tokens = tokenize_csharp(code)
    
    functions = []
    classes = []
    
    i = 0
    while i < len(tokens):
        token = tokens[i]
        
        # Пропустить using и namespace
        if token[0] == 'USING':
            while i < len(tokens) and tokens[i][0] != ';':
                i += 1
            i += 1
            continue
        
        if token[0] == 'NAMESPACE':
            i += 1
            while i < len(tokens) and tokens[i][0] != '{':
                i += 1
            i += 1
            continue
        
        # Класс
        if token[0] in ['PUBLIC', 'PRIVATE', 'PROTECTED', 'INTERNAL', 'STATIC', 'ABSTRACT']:
            # Проверить - это класс?
            j = i
            while j < len(tokens) and tokens[j][0] in ['PUBLIC', 'PRIVATE', 
                  'PROTECTED', 'INTERNAL', 'STATIC', 'ABSTRACT']:
                j += 1
            
            if j < len(tokens) and tokens[j][0] == 'CLASS':
                end_i, name, flowchart, method_flowcharts = parse_cs_class(tokens, i)
                classes.append({
                    'name': name,
                    'type': 'class',
                    'flowchart': flowchart
                })
                functions.extend(method_flowcharts)
                i = end_i
                continue
        
        if token[0] == 'CLASS':
            end_i, name, flowchart, method_flowcharts = parse_cs_class(tokens, i)
            classes.append({
                'name': name,
                'type': 'class',
                'flowchart': flowchart
            })
            functions.extend(method_flowcharts)
            i = end_i
            continue
        
        i += 1
    
    return {
        'success': True,
        'main_flowchart': {'nodes': [], 'edges': []},
        'functions': functions,
        'classes': classes,
        'code': code
    }

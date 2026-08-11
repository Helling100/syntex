"""
Основной класс PredicateArgumentExtractor и функция извлечения структур.
"""

from typing import List, Dict, Any, Optional, Union


def collect_subtree(token):
    """Рекурсивно собирает все токены поддерева."""
    nodes = [token]
    for child in token.children:
        nodes.extend(collect_subtree(child))
    return nodes


def get_roots(doc, coord_deps=None):
    """Возвращает список корней и словарь родительских связей."""
    if coord_deps is None:
        coord_deps = ['conj', 'parataxis']

    root = None
    for token in doc:
        if token.dep_ == 'ROOT' and token.pos_ == 'VERB':
            root = token
            break
    if root is None:
        root = next((token for token in doc if token.head == token), None)
    if root is None:
        return [], {}

    roots = [root]
    parent_map = {root: None}
    stack = [root]

    while stack:
        current = stack.pop()
        for child in current.children:
            if child.dep_ in coord_deps and child not in roots:
                roots.append(child)
                parent_map[child] = current
                stack.append(child)

    return roots, parent_map


def _build_frames_for_doc(doc,
                         token_rules=None,
                         group_rules=None,
                         coord_deps=None,
                         allowed_args=None,
                         disallowed_args=None):
    """
    Внутренняя функция, реализующая логику извлечения фреймов.
    Возвращает список словарей с полями:
        root, root_pos,
        predicate_text, predicate_tokens,
        arguments (список с dep, text, tokens),
        parent, dep_to_parent.
    """
    if coord_deps is None:
        coord_deps = ['conj', 'parataxis']

    roots, parent_map = get_roots(doc, coord_deps)
    if not roots:
        return []

    result = []

    for root in roots:
        root_pos = root.pos_

        # --- Фильтры для аргументов ---
        final_allowed = None
        final_disallowed = None

        if allowed_args and root_pos in allowed_args:
            final_allowed = allowed_args[root_pos]

        if disallowed_args and root_pos in disallowed_args:
            final_disallowed = disallowed_args[root_pos]

        # --- Сборка предиката ---
        pred_tokens = [root]
        children = [c for c in root.children if not c.is_punct and not c.is_space]

        # Применяем одиночные правила
        if token_rules:
            for child in children:
                for rule in token_rules:
                    if rule.matches(child, root):
                        if child not in pred_tokens:
                            pred_tokens.append(child)
                        break

        # Применяем групповые правила
        if group_rules:
            for group_rule in group_rules:
                matched = group_rule.apply(children, root)
                if group_rule.action == 'add':
                    for token in matched:
                        if token not in pred_tokens:
                            pred_tokens.append(token)
                elif group_rule.action == 'remove':
                    for token in matched:
                        if token in pred_tokens:
                            pred_tokens.remove(token)

        pred_tokens.sort(key=lambda t: t.i)
        pred_text = " ".join(tok.text.lower() for tok in pred_tokens)


        #Динамическая проверка допустимых отношений к атрибутом от каждого из компонентов многокомпонентного предиката, в зависимости от части речи компонента
        def get_filters_for_head(head_token):
            """Возвращает (allowed, disallowed) для данного токена-головы."""
            head_pos = head_token.pos_
            allowed = None
            disallowed = None

            if allowed_args is not None:
                if isinstance(allowed_args, dict):
                    allowed = allowed_args.get(head_pos)
                elif isinstance(allowed_args, list):
                    allowed = allowed_args

            if disallowed_args is not None:
                if isinstance(disallowed_args, dict):
                    disallowed = disallowed_args.get(head_pos)
                elif isinstance(disallowed_args, list):
                    disallowed = disallowed_args

            return allowed, disallowed


        # --- Сбор аргументов dep ---
        arguments = []
 
        def collect_arguments(node):
            if node in pred_tokens:
                for child in node.children:
                    collect_arguments(child)
                return

            if node.head in pred_tokens:
                # Получаем фильтры для POS головы (которая в pred_tokens)
                allowed, disallowed = get_filters_for_head(node.head)                
                
                subtree = collect_subtree(node)
                sorted_nodes = sorted(subtree, key=lambda t: t.i)
                filtered_nodes = [t for t in sorted_nodes if t not in pred_tokens]
                if filtered_nodes:
                    dep = node.dep_
                    '''
                    if final_allowed is not None and dep not in final_allowed:
                        return
                    if final_disallowed is not None and dep in final_disallowed:
                        return
                    '''
                    if allowed is not None and dep not in allowed:
                        return
                    if disallowed is not None and dep in disallowed:
                        return
                    arg_text = " ".join(tok.text.lower() for tok in filtered_nodes)
                    arguments.append({
                        'dep': dep,
                        'text': arg_text,
                        'tokens': filtered_nodes,
                        'head': node
                    })
                return

            for child in node.children:
                collect_arguments(child)

        for child in root.children:
            if child.is_punct or child.is_space:
                continue
            if child.dep_ in coord_deps:
                continue
            collect_arguments(child)

        # Родительская информация
        parent = parent_map.get(root)
        dep_to_parent = root.dep_ if parent is not None else None

        result.append({
            'root': root,
            'root_pos': root_pos,
            'predicate_text': pred_text,
            'predicate_tokens': pred_tokens,
            'arguments': arguments,
            'parent': parent,
            'dep_to_parent': dep_to_parent
        })

    return result


class PredicateArgumentExtractor:
    """
    Главный класс для извлечения предикатно-аргументных структур.
    
    Позволяет настраивать:
        - одиночные правила для включения зависимых в предикат (add_rule)
        - групповые правила для совместной проверки нескольких зависимых (add_group_rule)
        - фильтры аргументов (set_arg_filters)
        - связи для разбиения на несколько структур (set_coord_deps)
    """

    def __init__(self):
        self.token_rules = []
        self.group_rules = []
        self.coord_deps = ['conj', 'parataxis']
        self.allowed_args = {}
        self.disallowed_args = {}

    def add_rule(self, conditions, logic='and'):
        """Добавляет одиночное правило для включения токена в предикат."""
        from .conditions import TokenCondition
        self.token_rules.append(TokenCondition(conditions, logic))

    def add_group_rule(self, conditions, logic='and', action='add'):
        """Добавляет групповое правило для совместной проверки нескольких токенов."""
        from .conditions import GroupCondition
        self.group_rules.append(GroupCondition(conditions, logic, action))

    def set_coord_deps(self, deps):
        """Устанавливает список зависимостей для разбиения на несколько структур."""
        self.coord_deps = deps

    def set_arg_filters(self, allowed=None, disallowed=None):
        """
        Устанавливает фильтры для аргументов.
        allowed/disallowed: словарь {POS: [список dep]}
        """
        if allowed is not None:
            self.allowed_args = allowed
        if disallowed is not None:
            self.disallowed_args = disallowed

    def extract(self, doc) -> List[Dict[str, Any]]:
        """
        Извлекает предикатно-аргументные структуры из документа spaCy.
        
        Возвращает список словарей с полями:
            root: spacy Token
            root_pos: str
            predicate_text: str
            predicate_tokens: List[spacy Token]
            arguments: List[{'dep': str, 'text': str, 'tokens': List, 'head': spacy Token}]
            parent: spacy Token or None
            dep_to_parent: str or None
        """
        return _build_frames_for_doc(
            doc,
            token_rules=self.token_rules,
            group_rules=self.group_rules,
            coord_deps=self.coord_deps,
            allowed_args=self.allowed_args,
            disallowed_args=self.disallowed_args
        )

    def extract_to_json(self, doc) -> str:
        """Возвращает результат в формате JSON."""
        import json
        frames = self.extract(doc)
        # Преобразуем токены в строки для сериализации
        for frame in frames:
            frame['root'] = {'text': frame['root'].text, 'lemma': frame['root'].lemma_, 'pos': frame['root'].pos_}
            frame['predicate_tokens'] = [t.text for t in frame['predicate_tokens']]
            for arg in frame['arguments']:
                arg['tokens'] = [t.text for t in arg['tokens']]
                arg['head'] = arg['head'].text
            if frame['parent']:
                frame['parent'] = {'text': frame['parent'].text, 'lemma': frame['parent'].lemma_}
        return json.dumps(frames, ensure_ascii=False, indent=2)


# Упрощённая функция для быстрого извлечения
def light_extract(doc,
                       token_rules=None,
                       group_rules=None,
                       coord_deps=None,
                       allowed_args=None,
                       disallowed_args=None) -> List[Dict[str, Any]]:
    """
    Быстрая функция извлечения предикатно-аргументных структур без создания экземпляра класса.
    """
    return _build_frames_for_doc(
        doc,
        token_rules=token_rules,
        group_rules=group_rules,
        coord_deps=coord_deps,
        allowed_args=allowed_args,
        disallowed_args=disallowed_args
    )
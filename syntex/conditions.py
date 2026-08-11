"""
Условия для сборки многокомпонентных предикатов
"""


class TokenCondition:
    """
    Условие для одного токена (зависимого от корня).
    
    Проверяет, соответствует ли токен заданным атрибутам (dep, pos, lemma, text, side, root_*).
    Поддерживает логику 'and' (все условия) или 'or' (хотя бы одно).
    """
    def __init__(self, conditions, logic='and'):
        self.conditions = conditions
        self.logic = logic

    def matches(self, token, root):
        if self.logic == 'and':
            return all(self._check_condition(token, root, cond) for cond in self.conditions)
        elif self.logic == 'or':
            return any(self._check_condition(token, root, cond) for cond in self.conditions)
        else:
            raise ValueError("logic must be 'and' or 'or'")

    def _check_condition(self, token, root, cond):
        attr = cond.get('attr')
        value = cond.get('value')
        operator = cond.get('operator', 'eq')
        negate = cond.get('not', False)

        # Определяем, к кому относится атрибут: к токену или к корню
        if attr.startswith('root_'):
            actual_attr = attr[5:]  # убираем 'root_'
            if actual_attr == 'dep':
                actual = root.dep_
            elif actual_attr == 'pos':
                actual = root.pos_
            elif actual_attr == 'lemma':
                actual = root.lemma_
            elif actual_attr == 'text':
                actual = root.text.lower()
            elif actual_attr == 'side':
                actual = 'self'
            else:
                raise ValueError(f"Unknown root attribute: {actual_attr}")
        elif attr.startswith('morph_'):
            morph_feature = attr[6:]  # например, 'Number', 'Tense', 'Case'
            morph_dict = token.morph.to_dict()
            actual = morph_dict.get(morph_feature)
            # spaCy может возвращать список значений, поэтому преобразуем в строку
            if isinstance(actual, list):
                actual = '|'.join(actual)
        elif attr.startswith('root_morph_'):
            morph_feature = attr[11:]
            morph_dict = root.morph.to_dict()
            actual = morph_dict.get(morph_feature)
            if isinstance(actual, list):
                actual = '|'.join(actual)        
        else:
            if attr == 'dep':
                actual = token.dep_
            elif attr == 'pos':
                actual = token.pos_
            elif attr == 'lemma':
                actual = token.lemma_
            elif attr == 'text':
                actual = token.text.lower()
            elif attr == 'side':
                if token.i < root.i:
                    actual = 'left'
                elif token.i > root.i:
                    actual = 'right'
                else:
                    actual = 'self'
            else:
                raise ValueError(f"Unknown attribute: {attr}")

        if operator == 'eq':
            result = (actual == value)
        elif operator == 'in':
            result = (actual in value)
        elif operator == 'neq':
            result = (actual != value)
        else:
            raise ValueError(f"Unknown operator: {operator}")

        if negate:
            result = not result
        return result


class GroupCondition:
    """
    Групповое условие: проверяет наличие нескольких разных токенов одновременно.
    
    Каждое условие в списке должно быть выполнено для своего токена.
    Если все условия выполнены, правило срабатывает (action='add' или 'remove').
    """
    def __init__(self, conditions, logic='and', action='add'):
        self.conditions = conditions  # список условий (словари или списки словарей)
        self.logic = logic
        self.action = action

    def apply(self, children, root):
        """
        children: список дочерних токенов корня.
        Возвращает список токенов, которые должны быть добавлены или удалены.
        """
        matched_tokens = []
        used = set()

        for cond in self.conditions:
            if isinstance(cond, list):
                rule = TokenCondition(cond, logic='and')
            else:
                rule = TokenCondition([cond], logic='and')

            found = False
            for child in children:
                if child.i in used:
                    continue
                if rule.matches(child, root):
                    matched_tokens.append(child)
                    used.add(child.i)
                    found = True
                    break

            if not found and self.logic == 'and':
                return []  # не все условия выполнены

        return matched_tokens

"""
Условия для сборки многокомпонентных предикатов
"""

#Вар 2.
class TokenCondition:
    """
    Условие для одного токена-кандидата.

    Проверяет:
      - атрибуты самого кандидата: dep, pos, lemma, text, side,
        head_lemma, head_pos, head_dep, head_text, morph_*;
      - атрибуты "корня": root_dep, root_pos, root_lemma, root_text,
        root_side, root_morph_* (в т.ч. root_morph_StyleVariant).

    Семантика root_*: условие считается выполненным, если существует
    ХОТЯ БЫ ОДИН токен r из переданного списка roots (в extractor это
    pred_tokens — все компоненты предиката), для которого все root_*
    условия выполнены одновременно (с учётом logic='and'/'or').

    Обратная совместимость: matches(token, root) со одиночным токеном
    эквивалентно matches(token, [root]).
    """

    def __init__(self, conditions, logic='and'):
        if logic not in ('and', 'or'):
            raise ValueError("logic must be 'and' or 'or'")
        self.conditions = conditions
        self.logic = logic

    # Публичный
    def matches(self, token, roots):
        """
        token : проверяемый токен-кандидат (spacy.Token)
        roots : список токенов-корней (например, pred_tokens) ИЛИ один токен
        """
        root_list = roots if isinstance(roots, (list, tuple)) else [roots]

        token_conds = [c for c in self.conditions
                       if not self._is_root_attr(c.get('attr', ''))]
        root_conds = [c for c in self.conditions
                      if self._is_root_attr(c.get('attr', ''))]

        # 1) Условия на самом кандидате — проверяются один раз
        if not self._match_group(token, None, token_conds):
            return False

        # 2) root_*-условия — должен найтись хотя бы один подходящий root
        if not root_conds:
            return True
        return any(self._match_group(token, r, root_conds) for r in root_list)

    # Внутреннее
    @staticmethod
    def _is_root_attr(attr):
        # root_* (включая root_morph_*)
        return isinstance(attr, str) and attr.startswith('root_')

    def _match_group(self, token, root, conds):
        if not conds:
            return True
        if self.logic == 'and':
            return all(self._check_condition(token, root, c) for c in conds)
        return any(self._check_condition(token, root, c) for c in conds)

    def _check_condition(self, token, root, cond):
        attr = cond.get('attr')
        value = cond.get('value')
        operator = cond.get('operator', 'eq')
        negate = cond.get('not', False)

        actual = self._extract_actual(token, root, attr)

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

    def _extract_actual(self, token, root, attr):
        """Возвращает фактическое значение атрибута для сравнения."""
        if not isinstance(attr, str):
            raise ValueError(f"Attribute must be string, got {attr!r}")

        # --- root_* : включая root_morph_* ---
        if attr.startswith('root_'):
            if root is None:
                # root_* условие при root=None — не выполнено (значение не определено)
                return _UNSET
            actual_attr = attr[5:]  # убираем 'root_'

            if actual_attr == 'dep':
                return root.dep_
            if actual_attr == 'pos':
                return root.pos_
            if actual_attr == 'lemma':
                return root.lemma_
            if actual_attr == 'text':
                return root.text.lower()
            if actual_attr == 'side':
                return 'self'
            if actual_attr.startswith('morph_'):
                # root_morph_StyleVariant -> morph_feature='StyleVariant'
                morph_feature = actual_attr[6:]
                return _morph_value(root, morph_feature)
            raise ValueError(f"Unknown root attribute: {actual_attr}")

        # --- morph_* на самом кандидате ---
        if attr.startswith('morph_'):
            morph_feature = attr[6:]
            return _morph_value(token, morph_feature)

        # --- обычные атрибуты кандидата ---
        if attr == 'dep':
            return token.dep_
        if attr == 'pos':
            return token.pos_
        if attr == 'lemma':
            return token.lemma_
        if attr == 'text':
            return token.text.lower()
        if attr == 'head_lemma':
            return token.head.lemma_
        if attr == 'head_pos':
            return token.head.pos_
        if attr == 'head_dep':
            return token.head.dep_
        if attr == 'head_text':
            return token.head.text.lower()
        if attr == 'side':
            if root is None:
                return 'self'
            if token.i < root.i:
                return 'left'
            if token.i > root.i:
                return 'right'
            return 'self'

        raise ValueError(f"Unknown attribute: {attr}")


# Сентинел 'значение не определено' — ни с чем не совпадет по eq/neq/in
class _UnsetType:
    def __repr__(self):
        return '<UNSET>'

_UNSET = _UnsetType()


def _morph_value(token, feature):
    """Достаёт морфологический признак; список склеивает через '|'."""
    morph_dict = token.morph.to_dict()
    val = morph_dict.get(feature)
    if isinstance(val, list):
        val = '|'.join(val)
    return val


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

    def apply(self, children, root, pred_tokens=None):
        """
        children: список дочерних токенов корня.
        Возвращает список токенов, которые должны быть добавлены или удалены.
        """
        matched_tokens = []
        used = set()
        roots_for_check = pred_tokens if pred_tokens is not None else [root]


        for cond in self.conditions:
            if isinstance(cond, list):
                rule = TokenCondition(cond, logic='and')
            else:
                rule = TokenCondition([cond], logic='and')

            found = False
            for child in children:
                if child.i in used:
                    continue
                #if rule.matches(child, root):
                if rule.matches(child, roots_for_check):
                    matched_tokens.append(child)
                    used.add(child.i)
                    found = True
                    break

            if not found and self.logic == 'and':
                return []  # не все условия выполнены

        return matched_tokens

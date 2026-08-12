"""
Визуализация результатов извлечения предикатно-аргументных структур.
"""

from typing import Optional, Union, List
import spacy
from spacy import displacy
import string


def show_structures(text_or_doc,
                    nlp=None,
                    extractor=None,
                    token_rules=None,
                    group_rules=None,
                    coord_deps=None,
                    allowed_args=None,
                    disallowed_args=None,
                    jupyter=True,
                    show_dep_tree=True,
                    show_morph=False,
                    strip_punct = False):
    """
    Визуализирует синтаксическое дерево и извлечённые предикатно-аргументные структуры.
    
    Параметры:
        text_or_doc: строка или spaCy Doc
        nlp: модель spaCy (нужна, если передан текст)
        extractor: экземпляр PredicateArgumentExtractor (если None, используются отдельные параметры)
        token_rules, group_rules, coord_deps, allowed_args, disallowed_args: параметры для извлечения
        jupyter: использовать ли displacy в режиме Jupyter
        show_dep_tree: показывать ли дерево зависимостей
    """
    from .extractor import _build_frames_for_doc

    # Получаем doc
    if isinstance(text_or_doc, str):
        if nlp is None:
            raise ValueError("Для текста необходимо указать nlp")
        doc = nlp(text_or_doc)
        text = text_or_doc
    else:
        doc = text_or_doc
        text = doc.text

    # Если передан extractor, используем его настройки
    if extractor is not None:
        frames = extractor.extract(doc)
        # Для вывода также используем настройки extractor
        _show_frames(doc, frames, text, jupyter, show_dep_tree, show_morph=show_morph)
        return

    # Иначе используем переданные параметры
    frames = _build_frames_for_doc(
        doc,
        token_rules=token_rules,
        group_rules=group_rules,
        coord_deps=coord_deps,
        allowed_args=allowed_args,
        disallowed_args=disallowed_args
    )
    _show_frames(doc, frames, text, jupyter, show_dep_tree, show_morph=show_morph, strip_punct = strip_punct)

def _format_morph(morph_dict):
    """Преобразует словарь морфологических признаков в строку вида 'Number=Plur|Case=Nom'."""
    if not morph_dict:
        return ""
    return " | ".join([f"{k}={v}" for k, v in morph_dict.items()])


def format_structures(text_or_doc,
                      nlp=None,
                      extractor=None,
                      token_rules=None,
                      group_rules=None,
                      coord_deps=None,
                      allowed_args=None,
                      disallowed_args=None,
                      show_morph=False,
                      frames=None,
                      strip_punct = False):
    from .extractor import _build_frames_for_doc

    # Получение doc и text
    if isinstance(text_or_doc, str):
        if nlp is None:
            raise ValueError("Для текста необходимо указать nlp")
        doc = nlp(text_or_doc)
        text = text_or_doc
    else:
        doc = text_or_doc
        text = doc.text

    # Получение фреймов (если не переданы)
    if frames is None:
        if extractor is not None:
            frames = extractor.extract(doc)
        else:
            frames = _build_frames_for_doc(
                doc,
                token_rules=token_rules,
                group_rules=group_rules,
                coord_deps=coord_deps,
                allowed_args=allowed_args,
                disallowed_args=disallowed_args
            )

    lines = []
    if not frames:
        lines.append("Predicate Structures are not found.")
        return "\n".join(lines)

    # --- Построение children_map с расширенным поиском ---
    def find_parent_frame(parent_token, frames, root_to_idx):
        parent_idx = root_to_idx.get(parent_token)
        if parent_idx is not None:
            return parent_idx
        for i, f in enumerate(frames):
            if f['root'].text == parent_token.text:
                return i
        for i, f in enumerate(frames):
            if parent_token in f['predicate_tokens']:
                return i
        return None

    root_to_idx = {f['root']: i for i, f in enumerate(frames)}
    children_map = {i: [] for i in range(len(frames))}
    for idx, frame in enumerate(frames):
        parent = frame['parent']
        if parent is not None:
            parent_idx = find_parent_frame(parent, frames, root_to_idx)
            if parent_idx is not None:
                children_map[parent_idx].append((idx, frame['dep_to_parent']))


    # --- Формирование строки ---
    for idx, frame in enumerate(frames):
        structure_num = idx + 1
        pred_text = frame['predicate_text']
        root = frame['root']
        root_pos = frame['root_pos']
        root_morph = frame.get('root_morph', {})
        root_morph_str = _format_morph(root_morph) if show_morph else ""

        base_str = f"  Structure {structure_num}: {pred_text} -> root: {root.text}, lemma: {root.lemma_}, POS: {root_pos}"
        if show_morph and root_morph_str:
            base_str += f", morph: {root_morph_str}"
        lines.append(base_str)

          
        # Аргументы
        def _strip_punct(text):
            return text.strip(string.punctuation + ' ')
 
        args = frame['arguments']
        if args:
            sorted_args = sorted(args, key=lambda a: a['tokens'][0].i if a['tokens'] else 0)
            for arg in sorted_args:
                arg_text = arg['text']
                if strip_punct:
                    arg_text = _strip_punct(arg_text)              
                arg_morph = arg.get('morph', {})
                arg_morph_str = _format_morph(arg_morph) if show_morph else ""
                head = arg['head']
                head_text = head.text
                head_lemma = head.lemma_
                head_pos = head.pos_
                arg_line = f"    {arg['dep']}: {arg_text}"
                if show_morph:
                    parts = []
                    parts.append(f"head: {head_text}, lemma: {head_lemma}, POS: {head_pos}")
                    if arg_morph_str:
                        parts.append(f"morph: {arg_morph_str}")
                    arg_line += " -> " + ", ".join(parts) #+ ")"
                lines.append(arg_line)

        # ВЫВОД ДОЧЕРНИХ СТРУКТУР 
        if children_map.get(idx):
            for child_idx, dep_type in children_map[idx]:
                child_frame = frames[child_idx]
                child_pred_text = child_frame['predicate_text']
                lines.append(f"    {dep_type}: {child_pred_text} (Structure {child_idx+1})")

        # Родительская связь
        parent = frame['parent']
        dep_to_parent = frame['dep_to_parent']
        if parent is not None:
            lines.append("    == parent structure ==")
            parent_idx = root_to_idx.get(parent)
            if parent_idx is not None:
                parent_pred_text = frames[parent_idx]['predicate_text']
                lines.append(f"    {dep_to_parent}: {parent_pred_text} (Structure {parent_idx+1})")
            else:
                lines.append(f"    {dep_to_parent}: {parent.text} (unknown structure)")


        # Если нет ни аргументов, ни родителя, ни детей
        if not args and parent is None and not children_map.get(idx):
            lines.append("    (аргументов нет)")




    lines.append("\n" + "="*80 + "\n")
    return "\n".join(lines)
    
    
def _show_frames(doc, frames, text, jupyter, show_dep_tree, show_morph=False,strip_punct = False):
    print(f"\n{'='*80}")
    print(f"Текст: {text}")
    print(f"{'='*80}\n")

    if show_dep_tree:
        print("--- ДЕРЕВО ЗАВИСИМОСТЕЙ ---")
        if jupyter:
            try:
                options = {"compact": True, "distance": 120}
                displacy.render(doc, style="dep", jupyter=True, options=options)
            except Exception:
                print("(Визуализация недоступна, текстовое представление:)")
                for token in doc:
                    print(f"{token.i}: {token.text} -> {token.head.text} ({token.dep_})")
        else:
            for token in doc:
                print(f"{token.i}: {token.text} -> {token.head.text} ({token.dep_})")

    print("\n--- PREDICATE-ARGUMENT STRUCTURES ---")
    # Используем format_structures с готовыми frames
    structures_str = format_structures(
        text_or_doc=doc,
        frames=frames,
        show_morph=show_morph,
        strip_punct = strip_punct
    )
    print(structures_str)   

def frames_to_table(frames):
    """
    Возвращает таблицу с результатами в виде списка словарей для pandas.
    """
    rows = []
    for i, frame in enumerate(frames, 1):
        row = {
            'structure_id': i,
            'predicate': frame['predicate_text'],
            'root': frame['root'].text,
            'root_pos': frame['root_pos'],
            'arguments': ', '.join([f"{a['dep']}:{a['text']}" for a in frame['arguments']]),
            'parent': frame['parent'].text if frame['parent'] else None,
            'dep_to_parent': frame['dep_to_parent']
        }
        rows.append(row)
    return rows
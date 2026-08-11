"""
Визуализация результатов извлечения предикатно-аргументных структур.
"""

from typing import Optional, Union, List
import spacy
from spacy import displacy


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
                    show_morph=False):
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
    _show_frames(doc, frames, text, jupyter, show_dep_tree, show_morph=show_morph)

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
                      frames=None,
                      show_morph=False):
    """
    Форматирует извлечённые структуры в виде многострочной строки,
    аналогичной выводу show_structures, но без печати в консоль.
    
    Возвращает строку, которую можно сохранить в файл.
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


    # --- Получение фреймов (если не переданы) ---
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

    '''
    # Если передан extractor, используем его настройки
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
    '''
    
    # Формируем строку
    lines = []
#    lines.append(f"\n{'='*80}")
#    lines.append(f"Текст: {text}")
#    lines.append(f"{'='*80}\n")

    if not frames:
        lines.append("Структуры не найдены.")
        return "\n".join(lines)

    # Строим отображение корень -> индекс
    root_to_idx = {f['root']: i for i, f in enumerate(frames)}
#    lines.append(f"Найдено структур: {len(frames)}")

    for i, frame in enumerate(frames, 1):
        pred_text = frame['predicate_text']
        root = frame['root']
        root_pos = frame['root_pos']
        root_morph = frame.get('root_morph', {})
        root_morph_str = _format_morph(root_morph)
        args = frame['arguments']
        parent = frame['parent']
        dep_to_parent = frame['dep_to_parent']

        base_str = f"  Структура {i}: {pred_text} | корень: {root.text}, POS: {root_pos}, лемма: {root.lemma_}"
        if show_morph and root_morph_str:
            base_str += f", morph: {root_morph_str}"    
        lines.append(base_str)
        #lines.append(f"  Структура {i}: {pred_text} (корень: {root.text}, POS: {root_pos}, лемма: {root.lemma_})") 

        if args:
            sorted_args = sorted(args, key=lambda a: a['tokens'][0].i if a['tokens'] else 0)
#            for arg in sorted_args:
#                lines.append(f"    {arg['dep']}: {arg['text']}")
            for arg in sorted_args:
                arg_text = arg['text']
                arg_morph = arg.get('morph', {})
                arg_morph_str = _format_morph(arg_morph)
                head_lemma = arg.get('head_lemma', '')
                head_pos = arg.get('head_pos', '')

                arg_line = f"    {arg['dep']}: {arg_text}"
                #if show_morph and arg_morph_str:
                #    arg_line += f" (morph: {arg_morph_str})"
                if show_morph:
                    parts = []
                    if arg_morph_str:
                        parts.append(f"morph: {arg_morph_str}")
                    if head_lemma and head_pos:
                        parts.append(f"head: {head_lemma} ({head_pos})")
                    if parts:
                        arg_line += " (" + ", ".join(parts) + ")"
                
                lines.append(arg_line)


        if parent is not None:
            lines.append("    == parent structure ==")
            parent_idx = root_to_idx.get(parent)
            if parent_idx is not None:
                parent_pred_text = frames[parent_idx]['predicate_text']
                lines.append(f"    {dep_to_parent}: {parent_pred_text} (Структура {parent_idx+1})")
            else:
                lines.append(f"    {dep_to_parent}: {parent.text} (неизвестная структура)")

        if not args and parent is None:
            lines.append("    (аргументов нет)")

    lines.append("\n" + "="*80 + "\n")
    return "\n".join(lines)


def _show_frames(doc, frames, text, jupyter, show_dep_tree, show_morph=False):
    """Внутренняя функция вывода."""
    print(f"\n{'='*80}")
    print(f"Текст: {text}")
    print(f"{'='*80}\n")

    if show_dep_tree:
        print("--- ДЕРЕВО ЗАВИСИМОСТЕЙ ---")
        if jupyter:
            try:
                options = {"compact": True, "distance": 120}
                displacy.render(doc, style="dep", jupyter=True, options=options)                
                #displacy.render(doc, style="dep", jupyter=True, options={'distance': 100})
            except Exception:
                print("(Визуализация недоступна, текстовое представление:)")
                for token in doc:
                    print(f"{token.i}: {token.text} -> {token.head.text} ({token.dep_})")
        else:
            for token in doc:
                print(f"{token.i}: {token.text} -> {token.head.text} ({token.dep_})")

    print("\n--- ПРЕДИКАТНО-АРГУМЕНТНЫЕ СТРУКТУРЫ ---")
    structures_str = format_structures(
        text_or_doc=doc,          # для текста
        frames=frames,            # передаем уже вычисленные фреймы
        show_morph=show_morph     # передаем флаг
    )
    print(structures_str)    
    
    '''
    if not frames:
        print("Структуры не найдены.")
        return

    # Строим отображение корень -> индекс
    root_to_idx = {f['root']: i for i, f in enumerate(frames)}
    print(f"Найдено структур: {len(frames)}")

    for i, frame in enumerate(frames, 1):
        pred_text = frame['predicate_text']
        root = frame['root']
        root_pos = frame['root_pos']
        args = frame['arguments']
        parent = frame['parent']
        dep_to_parent = frame['dep_to_parent']

        print(f"  Структура {i}: {pred_text} (корень: {root.text}, POS: {root_pos}, лемма: {root.lemma_})") 

        if args:
            sorted_args = sorted(args, key=lambda a: a['tokens'][0].i if a['tokens'] else 0)
            for arg in sorted_args:
                print(f"    {arg['dep']}: {arg['text']}")

        if parent is not None:
            print("    == parent structure ==")
            parent_idx = root_to_idx.get(parent)
            if parent_idx is not None:
                parent_pred_text = frames[parent_idx]['predicate_text']
                print(f"    {dep_to_parent}: {parent_pred_text} (Структура {parent_idx+1})")
            else:
                print(f"    {dep_to_parent}: {parent.text} (неизвестная структура)")

        if not args and parent is None:
            print("    (аргументов нет)")
      

    print("\n" + "="*80 + "\n")
    '''

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
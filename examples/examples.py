"""
Примеры использования библиотеки syntex.
"""

import spacy
from syntex import (
    PredicateArgumentExtractor,
    create_default_extractor,
    show_structures,
    load_spacy_model
)

def main():
    # Загружаем модель
    nlp = load_spacy_model('ru_core_news_lg')

    # Вариант 1: Использование предустановленного экстрактора
    print("=== Вариант 1: Предустановленный экстрактор ===")
    extractor = create_default_extractor()
    text = "Врачи стали выписывать дополнительные не нужные обследования, хотя это не помогло."
    show_structures(text, nlp, extractor=extractor)

    # Вариант 2: Создание и настройка своего экстрактора
    print("\n=== Вариант 2: Свой экстрактор ===")
    custom_extractor = PredicateArgumentExtractor()

    # Добавляем правила
    custom_extractor.add_rule([
        {'attr': 'lemma', 'value': 'не'},
        {'attr': 'root_pos', 'value': 'VERB'}
    ], logic='and')

    custom_extractor.add_rule([
        {'attr': 'pos', 'value': 'PART'},
        {'attr': 'lemma', 'value': 'бы'}
    ], logic='and')

    # Групповое правило
    custom_extractor.add_group_rule(
        conditions=[
            {'attr': 'lemma', 'value': 'а'},
            {'attr': 'lemma', 'value': 'то'}
        ],
        action='add'
    )

    # Фильтры аргументов
    custom_extractor.set_arg_filters(
        disallowed={'VERB': ['cc', 'mark']}
    )

    # Связи для разбиения (типы зависимостей, связыывающие различные предикатно-аргументные структуры)
    custom_extractor.set_coord_deps(['conj', 'parataxis'])

    # Извлекаем
    doc = nlp(text)
    frames = custom_extractor.extract(doc)

    # Вывод в JSON
    print("Результат в JSON:")
    print(custom_extractor.extract_to_json(doc))

    # Визуализация
    show_structures(text, nlp, extractor=custom_extractor)

    # Вариант 3: Быстрое извлечение без класса
    print("\n=== Вариант 3: Быстрое извлечение ===")
    from syntex import light_extract

    frames = extract_structures(
        doc,
        token_rules=custom_extractor.token_rules,
        coord_deps=['conj', 'parataxis']
    )
    for i, frame in enumerate(frames, 1):
        print(f"{i}. {frame['predicate_text']}")
        for arg in frame['arguments']:
            print(f"   {arg['dep']}: {arg['text']}")

    # Вариант 4: Английский язык
    print("\n=== Вариант 4: Английский язык ===")
    nlp_en = load_spacy_model('en_core_web_sm')
    extractor_en = PredicateArgumentExtractor()
    extractor_en.add_rule([
        {'attr': 'dep', 'value': 'aux'},
        {'attr': 'lemma', 'value': 'be'}
    ], logic='and')

    show_structures(
        "The doctor was examining the patient carefully.",
        nlp_en,
        extractor=extractor_en
    )


if __name__ == "__main__":
    main()
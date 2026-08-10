"""
Предустановленные конфигурации для PredicateArgumentExtractor.
"""

from .extractor import PredicateArgumentExtractor
from .conditions import TokenCondition


def create_default_extractor_ru():
    """
    Создаёт экстрактор с базовыми правилами для русского языка:
        - отрицание ('не') для глагольных корней,
        - частица 'бы',
        - копула ('cop'),
        - xcomp для фазовых глаголов (стал, стала, стали, стало + комплемент).
    """
    extractor = PredicateArgumentExtractor()

    # Частица "бы"
    extractor.add_rule([
        {'attr': 'pos', 'value': 'PART'},
        {'attr': 'lemma', 'value': 'бы'}
    ], logic='and')

    # Отрицание "не" для глагольных корней
    extractor.add_rule([
        {'attr': 'lemma', 'value': 'не'},
        {'attr': 'root_pos', 'value': 'VERB'}
    ], logic='and')

    # Копула
    extractor.add_rule([
        {'attr': 'dep', 'value': 'cop'}
    ])

    # xcomp для фазовых глаголов (стать)
    extractor.add_rule([
        {'attr': 'root_lemma', 'value': ['стать', 'стало', 'стал', 'стали'], 'operator': 'in'},
        {'attr': 'dep', 'value': 'xcomp'}
    ], logic='and')

    # Групповое правило: "а" + "не" вместе (пример)
    extractor.add_group_rule(
        conditions=[
            [
                {'attr': 'lemma', 'value': 'а'},
                {'attr': 'dep', 'value': 'cc'}
            ],
            {'attr': 'lemma', 'value': 'не'}
        ],
        logic='and',
        action='add'
    )

    # Стандартные фильтры аргументов
    extractor.set_arg_filters(
        disallowed={
            'VERB': ['cc', 'punkt', 'mark', 'sconj'],
            'ADJ': ['cop'],
            'NOUN': ['case']
        }
    )

    # Связи для разбиения на несколько структур
    extractor.set_coord_deps(['parataxis', 'conj', 'csubj'])

    return extractor


def create_empty_extractor():
    """Создаёт пустой экстрактор без правил (предикат = только корень)."""
    return PredicateArgumentExtractor()
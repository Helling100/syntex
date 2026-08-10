"""
Вспомогательные функции.
"""

import spacy
from typing import Optional


def load_spacy_model(lang: str = 'ru_core_news_lg', disable: Optional[list] = None):
    """
    Загружает модель spaCy для указанного языка.
    
    Параметры:
        lang: имя модели (например, 'ru_core_news_lg', 'en_core_web_sm')
        disable: список компонентов для отключения (например, ['ner'])
    """
    try:
        if disable is not None:
            return spacy.load(lang, disable=disable)
        return spacy.load(lang)
    except OSError:
        print(f"Модель '{lang}' не найдена. Установите её командой:")
        print(f"python -m spacy download {lang}")
        raise


def token_to_dict(token):
    """Преобразует spacy Token в словарь."""
    return {
        'text': token.text,
        'lemma': token.lemma_,
        'pos': token.pos_,
        'dep': token.dep_,
        'i': token.i
    }
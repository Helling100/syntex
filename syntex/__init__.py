"""
pred_arg_extract — библиотека для извлечения предикатно-аргументных структур
с настраиваемыми правилами формирования составных предикатов и фильтрации аргументов.
"""

from .extractor import PredicateArgumentExtractor, light_extract
from .conditions import TokenCondition, GroupCondition
from .presets import create_default_extractor_ru
from .visualize import show_structures
from .utils import load_spacy_model

__version__ = "0.1.0"
__all__ = [
    "PredicateArgumentExtractor",
    "TokenCondition",
    "GroupCondition",
    "create_default_extractor_ru",
    "light_extract",
    "show_structures",
    "load_spacy_model",
]
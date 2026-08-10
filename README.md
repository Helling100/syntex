# Syntex — извлечение предикатно-аргументных структур

Библиотека для гибкого извлечения предикатно-аргументных структур из текста с использованием spaCy.

## Особенности

- **Гибкая настройка правил** для сборки составных предикатов:
  - одиночные правила (TokenCondition)
  - групповые правила (GroupCondition) для совместной проверки нескольких зависимых
- **Фильтрация аргументов** по типам синтаксических связей и частям речи
- **Поддержка множественных структур** (conj, parataxis, csubj)
- **Визуализация** результатов
- **Выход в JSON** для интеграции с другими системами
- **Языконезависимость** (работает с любой моделью spaCy)

## Установка

```bash
pip install -e .
```

# Быстрый старт
```python
import spacy
from pred_arg_extract import create_default_extractor, show_structures

nlp = spacy.load('ru_core_news_lg')
extractor = create_default_extractor()

text = "Врачи стали выписывать дополнительные обследования."
show_structures(text, nlp, extractor=extractor)
```

# Получить результат в JSON

```python
doc = nlp(text)
print(extractor.extract_to_json(doc))
```

# Настройка правил
## Одиночное правило
```python
from pred_arg_extract import PredicateArgumentExtractor

extractor = PredicateArgumentExtractor()
```

## Включить в предикат токен с леммой 'не', если корень — глагол
```python
extractor.add_rule([
    {'attr': 'lemma', 'value': 'не'},
    {'attr': 'root_pos', 'value': 'VERB'}
], logic='and')
```

## Групповое правило
```python
# Добавить 'хотя' и 'бы' только если они оба присутствуют
extractor.add_group_rule(
    conditions=[
        {'attr': 'lemma', 'value': 'хотя'},
        {'attr': 'lemma', 'value': 'бы'}
    ],
    action='add'
)
```

# Доступные атрибуты

Атрибуты аргумента

* dep — синтаксическая зависимость

* pos — часть речи

* lemma — лемма

* text — точная текстовая форма

* side — позиция относительно корня (left, right, self = корень)

Атрибуты корня

* root_dep, root_pos, root_lemma, root_text

# Операторы

* eq (по умолчанию) — равно

* neq — не равно

* in — вхождение в список

## Отрицание

* Добавить 'not': True в условие.

# Фильтрация аргументов
```python
extractor.set_arg_filters(
    allowed={'VERB': ['nsubj', 'obj', 'iobj']},
    disallowed={'VERB': ['cc', 'mark']}
)
```

# Разбиение на несколько структур
Указанные типы отношений являются маркерами разбиения: рассматриваются как связь между 
предикатами двух структур

```python
extractor.set_coord_deps(['conj', 'parataxis', 'csubj'])
```

#Формат результата
```json
{
  "root": {"text": "стали", "lemma": "стать", "pos": "VERB"},
  "predicate_text": "стали выписывать",
  "predicate_tokens": ["стали", "выписывать"],
  "arguments": [
    {"dep": "nsubj", "text": "врачи"},
    {"dep": "obj", "text": "дополнительные обследования"}
  ],
  "parent": null,
  "dep_to_parent": null
}
```

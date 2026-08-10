# Syntex — извлечение предикатно-аргументных структур

Библиотека для гибкого извлечения предикатно-аргументных структур из текста с использованием spaCy.

## Функционал

- **Гибкая настройка правил** для сборки составных предикатов:
  - одиночные правила (TokenCondition) для обработки одного зависимого
  - групповые правила (GroupCondition) для совместной проверки нескольких зависимых
- **Фильтрация аргументов** по типам синтаксических связей и частям речи
- **Поддержка множественных структур** (выделение нескольких предикатно-аргументных структур)
- **Визуализация** результатов
- **Выход в JSON** для интеграции с другими системами
- **Языконезависимость** (работает с любой моделью spaCy)

## Установка

```bash
pip install git+https://github.com/Helling100/syntex.git
```

# Быстрый старт
```python
import spacy
from syntex import create_default_extractor_ru, show_structures

nlp = spacy.load('ru_core_news_lg')
extractor = create_default_extractor_ru()

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
Включает в предикат токен с леммой 'не', если корень — глагол

```python
from syntex import PredicateArgumentExtractor

extractor = PredicateArgumentExtractor()

extractor.add_rule([
    {'attr': 'lemma', 'value': 'не'},
    {'attr': 'root_pos', 'value': 'VERB'}
], logic='and')
```

## Групповое правило
Добавляет в текст предиката два непосредственно зависимых ('хотя' и 'бы') только если они оба присутствуют

```python
from syntex import PredicateArgumentExtractor

extractor = PredicateArgumentExtractor()

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

* Для отрицания: в соответствующем условии - 'not': True.

Примеры:
Добавляет к форме предиката зависимый, если у него часть речи PART и лемма не равна "же"
```python
extractor.add_rule([
    {'attr': 'pos', 'value': 'PART'},
    {'attr': 'lemma', 'value': 'же', 'operator': 'neq'}
], logic='and')
```
Добавляет к форме предиката зависимый, если его текстовая форма - одно из слов, указанных в списке значений
```python
extractor.add_rule([
    {'attr': 'text', 'value': ['был', 'было', 'были'], 'operator': 'in'}
])

```
Добавляет зависимый, если это глагол, лемма которого не из числа указанных в списке
```python
extractor.add_rule([
	{'attr': 'pos', 'value': 'VERB'},
    {'attr': 'lemma', 'value': ['мочь', 'быть'], 'operator': 'in', 'not': True}
], logic = 'and')
```

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

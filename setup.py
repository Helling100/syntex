from setuptools import setup, find_packages

def get_long_description():
    with open('README.md', encoding='utf-8') as f:
        return f.read()

setup(
    name='syntex',                         
    version="0.1.0",                       
    author='Olga Babina',
    description="Predicate-Argument Extraction from a syntactic tree",  # Краткое описание
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    url="https://github.com/helling100/syntex",  # Ссылка на репозиторий
    project_urls={
        "Source": "https://github.com/helling100/syntex",
        "Issues": "https://github.com/helling100/syntex/issues",
    },
    packages=find_packages(),              # Автоматически находит пакеты (папку syntex)
    license="MIT",
    python_requires='>=3.7',
    install_requires=[
        'spacy>=3.0.0',                    # Указываем зависимости
    ],
    classifiers=[                          # Классификаторы для PyPI
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
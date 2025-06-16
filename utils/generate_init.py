import os
import importlib
import inspect
from typing import List, Tuple
from pathlib import Path
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

EXCLUDED_NAMES = {'DirectionalElementAnalyzer', 'TerminalElementAnalyzer'}

def get_module_members(module_name: str, package_name: str) -> List[Tuple[str, str]]:
    """Извлекает публичные классы и функции из модуля.

    Args:
        module_name (str): Имя модуля (например, 'analyzer').
        package_name (str): Имя пакета (например, 'model_processing').

    Returns:
        List[Tuple[str, str]]: Список кортежей (имя, тип импорта), где тип — 'class' или 'function'.
    """
    full_module_name = f"{package_name}.{module_name}"
    logger.debug("Попытка загрузки модуля: %s", full_module_name)
    
    try:
        module = importlib.import_module(full_module_name)
    except (ImportError, AttributeError) as e:
        logger.warning("Ошибка при загрузке модуля %s: %s", full_module_name, e)
        return []

    members: List[Tuple[str, str]] = []
    for name, obj in inspect.getmembers(module):
        if inspect.isclass(obj) and obj.__module__ == full_module_name and not name.startswith('_'):
            members.append((name, 'class'))
        elif inspect.isfunction(obj) and obj.__module__ == full_module_name and not name.startswith('_'):
            members.append((name, 'function'))
    members = [(name, type_) for name, type_ in members if name not in EXCLUDED_NAMES]

    return members

def generate_init(package_dir: Path, output_path: Path, package_name: str, version: str = '1.1.0', author: str = 'Vlad Titov') -> None:
    """Генерирует файл __init__.py для указанного пакета в заданном формате.

    Args:
        package_dir (Path): Директория пакета.
        output_path (Path): Путь для сохранения __init__.py.
        package_name (str): Имя пакета (например, 'model_processing').
        version (str): Версия пакета (по умолчанию '1.1.0').
        author (str): Автор пакета (по умолчанию 'Vlad Titov').
    """
    logger.info("Генерация __init__.py для пакета %s", package_dir)
    
    # Добавляем родительскую директорию пакета в sys.path
    sys.path.insert(0, str(package_dir.parent))

    # Порядок загрузки модулей для избежания циклических импортов
    module_order = [
        'utils',
        'comparator',
        'models',
        'analyzers',
        'registry',
        'tree_builder',
        'analyzer'
    ]

    module_imports: List[Tuple[str, List[str]]] = []
    all_names: List[str] = []
    modules = []

    # Загружаем модули в указанном порядке
    for module_name in module_order:
        file = package_dir / f"{module_name}.py"
        if not file.exists():
            logger.warning("Модуль %s не найден", module_name)
            continue
        members = get_module_members(module_name, package_name)
        if members:
            member_names = [name for name, _ in members]
            modules.append((module_name, member_names))
            module_imports.append((module_name, member_names))
            all_names.extend(member_names)

    # Формируем содержимое __init__.py
    content = [
        '"""model_processing package',
        '',
        'Обеспечивает доступ к основным классам и модулям пакета для анализа электрической сети',
        'и построения ее дерева.',
        '"""',
        '',
        'import sys',
        'import os',
        '',
        '# Добавляем текущую директорию в путь поиска модулей',
        'current_dir = os.path.dirname(os.path.abspath(__file__))',
        'if current_dir not in sys.path:',
        '    sys.path.insert(0, current_dir)',
        '',
        'try:'
    ]

    # Добавляем абсолютные импорты
    for module_name, member_names in module_imports:
        content.append(f"    from {package_name}.{module_name} import {', '.join(member_names)}")

    content.extend([
        'except ImportError as e:',
        '    print(f"Ошибка импорта модуля: {e}")',
        '    try:'
    ])

    # Добавляем относительные импорты
    for module_name, member_names in module_imports:
        content.append(f"        from .{module_name} import {', '.join(member_names)}")

    content.extend([
        '    except ImportError as e2:',
        '        print(f"Ошибка импорта модуля: {e2}")',
        '        raise',
        '',
        f'__version__ = "{version}"',
        f'__author__ = "{author}"',
        '',
        f"__all__ = {all_names!r}"
    ])

    # Записываем файл
    with output_path.open('w', encoding='utf-8') as f:
        f.write('\n'.join(content))
    
    logger.info("Файл __init__.py успешно сгенерирован: %s", output_path)
    
    # Удаляем временное добавление в sys.path
    sys.path.pop(0)

if __name__ == '__main__':
    package_dir = Path('C://Users//Vlad Titov//Desktop//Work//binary_tree//model_processing')
    output_path = package_dir / '__init__.py'
    package_name = 'model_processing'
    generate_init(package_dir, output_path, package_name)